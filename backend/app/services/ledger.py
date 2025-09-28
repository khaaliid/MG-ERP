from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, select, Enum, Table, Index, func, case, Boolean
from sqlalchemy.orm import declarative_base, relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timezone
import enum
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class AccountType(enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=False, unique=True)
    type = Column(Enum(AccountType), nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    lines = relationship("TransactionLine", back_populates="account")
    
    # Add convenience property to get transactions
    @property
    def transactions(self):
        return [line.transaction for line in self.lines]

class TransactionSource(enum.Enum):
    POS = "POS"
    API = "API" 
    IMPORT = "Import"
    MANUAL = "Manual"
    WEB = "Web"

class Transaction(Base):
    __tablename__ = "transactions" 
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    description = Column(String, nullable=False)
    source = Column(Enum(TransactionSource), nullable=False, default=TransactionSource.MANUAL)
    reference = Column(String, nullable=True)  # invoice ID, POS ticket, etc.
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=True)  # user ID or username
    lines = relationship("TransactionLine", back_populates="transaction", cascade="all, delete-orphan")
    
    # Add convenience property to get accounts
    @property 
    def accounts(self):
        return [line.account for line in self.lines]

class TransactionLine(Base):
    __tablename__ = "transaction_lines"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="lines")
    account = relationship("Account", back_populates="lines")
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_transaction_account', 'transaction_id', 'account_id'),
        Index('idx_account_type', 'account_id', 'type'),
    )

# CRUD operations for accounts
async def create_account(db: AsyncSession, account_data):
    logger.info(f"[ACCOUNT] Creating account: name='{account_data.name}', type={account_data.type}, code='{getattr(account_data, 'code', 'N/A')}'")
    
    try:
        # Check if account name already exists
        existing_account = await get_account_by_name(db, account_data.name)
        if existing_account:
            logger.warning(f"[WARNING] Account creation failed: Account '{account_data.name}' already exists")
            raise ValueError(f"Account '{account_data.name}' already exists")
        
        # Check if account code already exists
        existing_code = await get_account_by_code(db, account_data.code)
        if existing_code:
            logger.warning(f"[WARNING] Account creation failed: Account code '{account_data.code}' already exists")
            raise ValueError(f"Account code '{account_data.code}' already exists")
        
        # Validate and convert account type
        if isinstance(account_data.type, str):
            # Convert string to enum
            try:
                account_type = AccountType(account_data.type.lower())
                logger.debug(f"[PROCESSING] Converted string '{account_data.type}' to enum {account_type}")
            except ValueError:
                logger.error(f"[ERROR] Invalid account type: '{account_data.type}'")
                raise ValueError(f"Invalid account type: '{account_data.type}'. Must be one of: {[e.value for e in AccountType]}")
        else:
            account_type = account_data.type
            logger.debug(f"[PROCESSING] Using enum account type: {account_type}")
        
        account = Account(
            name=account_data.name,
            code=account_data.code, 
            type=account_type,
            description=account_data.description,
            is_active=getattr(account_data, 'is_active', True)
        )
        db.add(account)
        logger.debug(f"[SAVE] Added account to session: {account_data.name}")
        
        await db.commit()
        logger.debug(f"[SAVE] Committed account to database")
        
        await db.refresh(account)
        logger.info(f"[SUCCESS] Successfully created account: ID={account.id}, Name='{account.name}'")
        
        return account
        
    except ValueError:
        logger.warning(f"[PROCESSING] Rolling back transaction due to validation error")
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"[ERROR] Database error creating account '{account_data.name}': {str(e)}")
        await db.rollback()
        raise

async def get_all_accounts(db: AsyncSession):
    logger.debug("[LIST] Fetching all accounts from database")
    try:
        result = await db.execute(select(Account).order_by(Account.name))
        accounts = result.scalars().all()
        logger.info(f"[SUCCESS] Retrieved {len(accounts)} accounts from database")
        return accounts
    except Exception as e:
        logger.error(f"[ERROR] Error fetching accounts: {str(e)}")
        raise

async def get_account_by_name(db: AsyncSession, name: str) -> Optional[Account]:
    logger.debug(f"[SEARCH] Looking for account by name: '{name}'")
    try:
        result = await db.execute(select(Account).where(Account.name == name))
        account = result.scalars().first()
        if account:
            logger.debug(f"[SUCCESS] Found account: ID={account.id}, Name='{account.name}'")
        else:
            logger.debug(f"[WARNING] Account not found: '{name}'")
        return account
    except Exception as e:
        logger.error(f"[ERROR] Error finding account '{name}': {str(e)}")
        raise

async def get_account_by_code(db: AsyncSession, code: str) -> Optional[Account]:
    logger.debug(f"[SEARCH] Looking for account by code: '{code}'")
    try:
        result = await db.execute(select(Account).where(Account.code == code))
        account = result.scalars().first()
        if account:
            logger.debug(f"[SUCCESS] Found account: ID={account.id}, Code='{account.code}'")
        else:
            logger.debug(f"[WARNING] Account code not found: '{code}'")
        return account
    except Exception as e:
        logger.error(f"[ERROR] Error finding account by code '{code}': {str(e)}")
        raise

# CRUD operations for transactions
async def get_all_transactions(db: AsyncSession):
    logger.debug("[DATABASE] Fetching all transactions from database with relationships")
    try:
        result = await db.execute(
            select(Transaction).options(
                selectinload(Transaction.lines).selectinload(TransactionLine.account)
            ).order_by(Transaction.date.desc())
        )
        transactions = result.scalars().unique().all()
        logger.info(f"[SUCCESS] Retrieved {len(transactions)} transactions from database")
        
        # Log summary of transactions
        for tx in transactions:
            logger.debug(f"[DOCUMENT] Transaction ID={tx.id}: '{tx.description}' - {len(tx.lines)} lines")
        
        return transactions
    except Exception as e:
        logger.error(f"[ERROR] Error fetching transactions: {str(e)}")
        raise

async def create_transaction(db: AsyncSession, transaction_data):
    logger.info(f"[TRANSACTION] Starting transaction creation: '{transaction_data.description}'")
    logger.debug(f"[DATE] Transaction date: {transaction_data.date}")
    logger.debug(f"[DETAILS] Transaction source: {transaction_data.source}")
    logger.debug(f"🔖 Transaction reference: {transaction_data.reference}")
    
    # Validate transaction balance
    debit_total = sum(line.amount for line in transaction_data.lines if line.type == 'debit')
    credit_total = sum(line.amount for line in transaction_data.lines if line.type == 'credit')
    
    logger.info(f"[DATABASE] Balance validation: Debits={debit_total}, Credits={credit_total}")
    
    if debit_total != credit_total:
        error_msg = f"Transaction not balanced: Debits ({debit_total}) != Credits ({credit_total})"
        logger.error(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[SUCCESS] Transaction is balanced")
    
    try:
        # Create transaction object
        transaction = Transaction(
            date=transaction_data.date,
            description=transaction_data.description,
            source=transaction_data.source if hasattr(transaction_data, 'source') else TransactionSource.MANUAL,
            reference=getattr(transaction_data, 'reference', None),
            created_by=getattr(transaction_data, 'created_by', None),
        )
        db.add(transaction)
        logger.debug(f"[SAVE] Added transaction to session")
        
        await db.flush()  # get transaction.id
        logger.debug(f"🆆 Transaction flushed, received ID={transaction.id}")
        
        # Process transaction lines
        logger.info(f"[DETAILS] Processing {len(transaction_data.lines)} transaction lines")
        
        for i, line in enumerate(transaction_data.lines, 1):
            logger.debug(f"[DETAILS] Line {i}: Account='{line.account_name}', Type={line.type}, Amount={line.amount}")
            
            # Get account by name
            account = await get_account_by_name(db, line.account_name)
            if not account:
                error_msg = f"Account '{line.account_name}' not found"
                logger.error(f"[ERROR] {error_msg}")
                raise ValueError(error_msg)
            
            logger.debug(f"[SUCCESS] Found account: ID={account.id}, Name='{account.name}', Type={account.type}")
            
            transaction_line = TransactionLine(
                transaction_id=transaction.id,
                account_id=account.id,
                type=line.type,
                amount=line.amount
            )
            db.add(transaction_line)
            logger.debug(f"[SAVE] Added transaction line to session")
        
        await db.commit()
        logger.info(f"[SUCCESS] Transaction committed to database")
        
        # Re-query with selectinload to ensure lines and accounts are loaded
        logger.debug(f"[PROCESSING] Re-querying transaction with relationships")
        result = await db.execute(
            select(Transaction).options(
                selectinload(Transaction.lines).selectinload(TransactionLine.account)
            ).where(Transaction.id == transaction.id)
        )
        transaction_with_lines = result.scalars().first()
        
        logger.info(f"[SUCCESS] Successfully created transaction: ID={transaction_with_lines.id}, Lines={len(transaction_with_lines.lines)}")
        return transaction_with_lines
        
    except ValueError:
        logger.warning(f"[PROCESSING] Rolling back transaction due to validation error")
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"[ERROR] Database error creating transaction: {str(e)}")
        await db.rollback()
        raise

async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Optional[Transaction]:
    logger.debug(f"[SEARCH] Fetching transaction by ID: {transaction_id}")
    try:
        result = await db.execute(
            select(Transaction).options(
                selectinload(Transaction.lines).selectinload(TransactionLine.account)
            ).where(Transaction.id == transaction_id)
        )
        transaction = result.scalars().first()
        
        if transaction:
            logger.info(f"[SUCCESS] Found transaction: ID={transaction.id}, Description='{transaction.description}', Lines={len(transaction.lines)}")
        else:
            logger.warning(f"[WARNING] Transaction not found: ID={transaction_id}")
            
        return transaction
    except Exception as e:
        logger.error(f"[ERROR] Error fetching transaction ID={transaction_id}: {str(e)}")
        raise

# Helper functions
async def get_transactions_for_account(db: AsyncSession, account_name: str):
    """Get all transactions that involve a specific account"""
    result = await db.execute(
        select(Transaction)
        .join(TransactionLine)
        .join(Account)
        .where(Account.name == account_name)
        .options(selectinload(Transaction.lines).selectinload(TransactionLine.account))
    )
    return result.scalars().unique().all()

async def get_account_balance(db: AsyncSession, account_name: str) -> float:
    """Calculate account balance (debits - credits for assets/expenses, credits - debits for others)"""
    account = await get_account_by_name(db, account_name)
    if not account:
        return 0.0
    
    debit_total = sum(line.amount for line in account.lines if line.type == 'debit')
    credit_total = sum(line.amount for line in account.lines if line.type == 'credit')
    
    # For assets and expenses: positive balance = debit balance
    # For liabilities, equity, income: positive balance = credit balance
    if account.type in [AccountType.ASSET, AccountType.EXPENSE]:
        return debit_total - credit_total
    else:
        return credit_total - debit_total

async def get_account_transactions_optimized(db: AsyncSession, account_id: int):
    """Get transactions for account using optimized query"""
    result = await db.execute(
        select(Transaction)
        .join(TransactionLine, Transaction.id == TransactionLine.transaction_id)
        .where(TransactionLine.account_id == account_id)
        .options(selectinload(Transaction.lines).selectinload(TransactionLine.account))
        .order_by(Transaction.date.desc())
    )
    return result.scalars().unique().all()

async def get_account_balance_optimized(db: AsyncSession, account_id: int) -> dict:
    """Get account balance using optimized DB query"""
    result = await db.execute(
        select(
            func.sum(case((TransactionLine.type == 'debit', TransactionLine.amount), else_=0)).label('debit_total'),
            func.sum(case((TransactionLine.type == 'credit', TransactionLine.amount), else_=0)).label('credit_total')
        )
        .where(TransactionLine.account_id == account_id)
    )
    
    row = result.first()
    debit_total = row.debit_total or 0.0
    credit_total = row.credit_total or 0.0
    
    return {
        'debit_total': debit_total,
        'credit_total': credit_total,
        'balance': debit_total - credit_total  # Adjust based on account type
    }
