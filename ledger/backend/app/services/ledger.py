from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, select, Enum, Table, Index, func, case, Boolean, CheckConstraint, UniqueConstraint, and_
from sqlalchemy.orm import declarative_base, relationship, selectinload, validates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import enum
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Schema configuration
SCHEMA_NAME = "ledger"

class AccountType(enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {'schema': SCHEMA_NAME}
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
    POS = "pos"
    API = "api" 
    IMPORT = "import"
    MANUAL = "MANUAL"
    WEB = "web"

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {'schema': SCHEMA_NAME} 
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    description = Column(String, nullable=False)
    source = Column(Enum(TransactionSource), nullable=False, default=TransactionSource.MANUAL)
    reference = Column(String, nullable=True)  # invoice ID, POS ticket, etc.
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=True)  # user ID or username
    lines = relationship("TransactionLine", back_populates="transaction", cascade="all, delete-orphan")
    
    # Add convenience property to get accounts
    @property 
    def accounts(self):
        return [line.account for line in self.lines]

class TransactionLine(Base):
    __tablename__ = "transaction_lines"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.transactions.id", ondelete="CASCADE"), index=True)
    account_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.accounts.id"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="lines")
    account = relationship("Account", back_populates="lines")
    
    # Add composite indexes for common queries and schema
    __table_args__ = (
        Index('idx_transaction_account', 'transaction_id', 'account_id'),
        Index('idx_account_type', 'account_id', 'type'),
        # Database-level constraints for double-entry validation
        CheckConstraint('amount > 0', name='check_positive_amount'),
        CheckConstraint("type IN ('debit', 'credit')", name='check_valid_type'),
        {'schema': SCHEMA_NAME}
    )

    @validates('amount')
    def validate_amount(self, key, amount):
        """Validate amount is positive and properly formatted"""
        if amount <= 0:
            raise ValueError("Transaction line amount must be positive")
        # Round to 2 decimal places for monetary precision
        return round(float(amount), 2)

    @validates('type')
    def validate_type(self, key, type_value):
        """Validate transaction type is debit or credit"""
        if type_value not in ('debit', 'credit'):
            raise ValueError("Transaction line type must be 'debit' or 'credit'")
        return type_value

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
    
    # Enhanced validation with detailed error reporting
    validation_result = await validate_transaction_data(db, transaction_data)
    if not validation_result.is_valid:
        error_msg = f"Transaction validation failed: {', '.join(validation_result.errors)}"
        logger.error(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[SUCCESS] Transaction validation passed")
    
    try:
        # Handle timezone conversion for date
        transaction_date = transaction_data.date
        if hasattr(transaction_date, 'tzinfo') and transaction_date.tzinfo is not None:
            # Convert timezone-aware datetime to naive UTC
            transaction_date = transaction_date.replace(tzinfo=None)
            logger.debug(f"[TIMEZONE] Converted timezone-aware date to naive: {transaction_date}")
        
        # Create transaction object
        transaction = Transaction(
            date=transaction_date,
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
        
        # Final validation after commit
        post_commit_validation = await validate_transaction_integrity(db, transaction_with_lines.id)
        if not post_commit_validation.is_valid:
            logger.error(f"[ERROR] Post-commit validation failed: {post_commit_validation.errors}")
            # This should not happen if pre-validation worked correctly
        
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

# ============================================================================
# ENHANCED DOUBLE-ENTRY VALIDATION SYSTEM
# ============================================================================

class ValidationResult:
    """Container for validation results with detailed error reporting"""
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)

async def validate_transaction_data(db: AsyncSession, transaction_data) -> ValidationResult:
    """
    Comprehensive validation for transaction data before creation
    Implements enterprise-grade double-entry bookkeeping validation
    """
    logger.debug("[VALIDATION] Starting comprehensive transaction validation")
    result = ValidationResult()
    
    # 1. Basic data validation
    if not hasattr(transaction_data, 'lines') or not transaction_data.lines:
        result.add_error("Transaction must have at least one line")
        return result
    
    if len(transaction_data.lines) < 2:
        result.add_error("Double-entry transactions must have at least 2 lines")
    
    # 2. Validate transaction description
    if not hasattr(transaction_data, 'description') or not transaction_data.description.strip():
        result.add_error("Transaction description is required")
    
    # 3. Validate amounts and precision
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')
    accounts_used = set()
    
    for i, line in enumerate(transaction_data.lines, 1):
        # Check required fields
        if not hasattr(line, 'account_name') or not line.account_name:
            result.add_error(f"Line {i}: Account name is required")
            continue
        
        if not hasattr(line, 'type') or line.type not in ('debit', 'credit'):
            result.add_error(f"Line {i}: Type must be 'debit' or 'credit'")
            continue
        
        if not hasattr(line, 'amount') or line.amount <= 0:
            result.add_error(f"Line {i}: Amount must be positive")
            continue
        
        # Validate account exists
        account = await get_account_by_name(db, line.account_name)
        if not account:
            result.add_error(f"Line {i}: Account '{line.account_name}' does not exist")
            continue
        
        # Check account is active
        if not account.is_active:
            result.add_error(f"Line {i}: Account '{line.account_name}' is inactive")
        
        # Convert to Decimal for precise monetary calculation
        try:
            amount = Decimal(str(line.amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            result.add_error(f"Line {i}: Invalid amount format")
            continue
        
        # Add to totals
        if line.type == 'debit':
            total_debits += amount
        else:
            total_credits += amount
        
        # Track accounts for duplicate checking
        account_key = (line.account_name, line.type)
        if account_key in accounts_used:
            result.add_warning(f"Line {i}: Account '{line.account_name}' appears multiple times with same type")
        accounts_used.add(account_key)
    
    # 4. Critical double-entry validation
    if total_debits != total_credits:
        result.add_error(f"Transaction not balanced: Debits ({total_debits}) ≠ Credits ({total_credits})")
    
    # 5. Business logic validation
    if len(set(line.account_name for line in transaction_data.lines)) < 2:
        result.add_warning("Transaction involves only one account (internal transfer)")
    
    # 6. Validate accounting equation implications
    await validate_accounting_equation_impact(db, transaction_data, result)
    
    logger.info(f"[VALIDATION] Validation complete: {'PASSED' if result.is_valid else 'FAILED'}")
    if result.errors:
        logger.error(f"[VALIDATION] Errors: {'; '.join(result.errors)}")
    if result.warnings:
        logger.warning(f"[VALIDATION] Warnings: {'; '.join(result.warnings)}")
    
    return result

async def validate_accounting_equation_impact(db: AsyncSession, transaction_data, result: ValidationResult):
    """
    Validate that the transaction maintains the fundamental accounting equation:
    Assets = Liabilities + Equity
    """
    logger.debug("[VALIDATION] Checking accounting equation impact")
    
    asset_change = Decimal('0.00')
    liability_change = Decimal('0.00')
    equity_change = Decimal('0.00')
    
    for line in transaction_data.lines:
        account = await get_account_by_name(db, line.account_name)
        if not account:
            continue  # Already handled in main validation
        
        amount = Decimal(str(line.amount))
        
        # Calculate net change by account type and debit/credit nature
        if account.type == AccountType.ASSET:
            if line.type == 'debit':
                asset_change += amount  # Assets increase with debits
            else:
                asset_change -= amount  # Assets decrease with credits
        
        elif account.type == AccountType.LIABILITY:
            if line.type == 'credit':
                liability_change += amount  # Liabilities increase with credits
            else:
                liability_change -= amount  # Liabilities decrease with debits
        
        elif account.type == AccountType.EQUITY:
            if line.type == 'credit':
                equity_change += amount  # Equity increases with credits
            else:
                equity_change -= amount  # Equity decreases with debits
        
        elif account.type == AccountType.INCOME:
            # Income increases equity
            if line.type == 'credit':
                equity_change += amount  # Income increases equity
            else:
                equity_change -= amount  # Contra-income decreases equity
        
        elif account.type == AccountType.EXPENSE:
            # Expenses decrease equity
            if line.type == 'debit':
                equity_change -= amount  # Expenses decrease equity
            else:
                equity_change += amount  # Contra-expense increases equity
    
    # The accounting equation change should balance: ΔAssets = ΔLiabilities + ΔEquity
    equation_balance = asset_change - (liability_change + equity_change)
    
    if abs(equation_balance) > Decimal('0.01'):  # Allow for small rounding differences
        result.add_warning(f"Accounting equation impact: Assets Δ{asset_change} ≠ Liabilities Δ{liability_change} + Equity Δ{equity_change}")
    
    logger.debug(f"[VALIDATION] Equation impact: Assets±{asset_change}, Liabilities±{liability_change}, Equity±{equity_change}")

async def validate_transaction_integrity(db: AsyncSession, transaction_id: int) -> ValidationResult:
    """
    Post-commit validation to ensure transaction integrity in the database
    """
    logger.debug(f"[VALIDATION] Performing post-commit integrity check for transaction {transaction_id}")
    result = ValidationResult()
    
    # Get transaction with lines
    transaction = await get_transaction_by_id(db, transaction_id)
    if not transaction:
        result.add_error(f"Transaction {transaction_id} not found")
        return result
    
    # Validate balance at database level
    total_debits = sum(Decimal(str(line.amount)) for line in transaction.lines if line.type == 'debit')
    total_credits = sum(Decimal(str(line.amount)) for line in transaction.lines if line.type == 'credit')
    
    if total_debits != total_credits:
        result.add_error(f"Database integrity violation: Transaction {transaction_id} is not balanced")
    
    # Validate all lines have valid accounts
    for line in transaction.lines:
        if not line.account:
            result.add_error(f"Transaction line {line.id} has invalid account reference")
        elif not line.account.is_active:
            result.add_warning(f"Transaction line {line.id} references inactive account '{line.account.name}'")
    
    return result

async def validate_all_transactions_integrity(db: AsyncSession) -> ValidationResult:
    """
    System-wide validation to check integrity of all transactions
    Useful for periodic audits and data quality checks
    """
    logger.info("[VALIDATION] Starting system-wide transaction integrity check")
    result = ValidationResult()
    
    # Get all transactions
    transactions = await get_all_transactions(db)
    
    for transaction in transactions:
        transaction_result = await validate_transaction_integrity(db, transaction.id)
        
        # Aggregate errors and warnings
        for error in transaction_result.errors:
            result.add_error(f"Transaction {transaction.id}: {error}")
        
        for warning in transaction_result.warnings:
            result.add_warning(f"Transaction {transaction.id}: {warning}")
    
    logger.info(f"[VALIDATION] System integrity check complete: {len(transactions)} transactions checked")
    return result

async def get_accounting_equation_status(db: AsyncSession) -> Dict[str, Decimal]:
    """
    Calculate current accounting equation status: Assets = Liabilities + Equity
    Returns dictionary with totals and equation balance
    """
    logger.debug("[ACCOUNTING] Calculating accounting equation status")
    
    # Query balances by account type
    result = await db.execute(
        select(
            Account.type,
            func.sum(case((TransactionLine.type == 'debit', TransactionLine.amount), else_=0)).label('debit_total'),
            func.sum(case((TransactionLine.type == 'credit', TransactionLine.amount), else_=0)).label('credit_total')
        )
        .join(TransactionLine, Account.id == TransactionLine.account_id)
        .group_by(Account.type)
    )
    
    account_balances = {}
    for row in result:
        account_type = row.type
        debit_total = Decimal(str(row.debit_total or 0))
        credit_total = Decimal(str(row.credit_total or 0))
        
        # Calculate net balance based on normal account balance type
        if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            net_balance = debit_total - credit_total  # Normal debit balance
        else:
            net_balance = credit_total - debit_total  # Normal credit balance
        
        account_balances[account_type.value] = net_balance
    
    # Calculate equation components
    assets = account_balances.get('asset', Decimal('0'))
    liabilities = account_balances.get('liability', Decimal('0'))
    equity = account_balances.get('equity', Decimal('0'))
    
    # Income and expenses affect retained earnings (part of equity)
    income = account_balances.get('income', Decimal('0'))
    expenses = account_balances.get('expense', Decimal('0'))
    retained_earnings = income - expenses
    
    total_equity = equity + retained_earnings
    equation_balance = assets - (liabilities + total_equity)
    
    return {
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'income': income,
        'expenses': expenses,
        'retained_earnings': retained_earnings,
        'total_equity': total_equity,
        'equation_balance': equation_balance,
        'equation_balanced': abs(equation_balance) < Decimal('0.01')
    }

# ============================================================================
# FINANCIAL REPORTING SYSTEM
# ============================================================================

async def generate_trial_balance(db: AsyncSession, as_of_date: datetime = None) -> Dict:
    """
    Generate Trial Balance report showing all accounts with their debit/credit balances
    """
    logger.info(f"[REPORT] Generating Trial Balance as of {as_of_date or 'current date'}")
    
    if as_of_date is None:
        as_of_date = datetime.now(timezone.utc)
    
    # Convert timezone-aware datetime to naive for database comparison
    as_of_date_naive = as_of_date.replace(tzinfo=None) if as_of_date.tzinfo else as_of_date
    
    # Query all accounts with their transaction totals up to the specified date
    query = select(
        Account.id,
        Account.name,
        Account.code,
        Account.type,
        func.coalesce(func.sum(case((TransactionLine.type == 'debit', TransactionLine.amount), else_=0)), 0).label('total_debits'),
        func.coalesce(func.sum(case((TransactionLine.type == 'credit', TransactionLine.amount), else_=0)), 0).label('total_credits')
    ).select_from(
        Account.__table__.outerjoin(
            TransactionLine.__table__.join(
                Transaction.__table__, 
                TransactionLine.transaction_id == Transaction.id
            )
        )
    ).where(
        (Transaction.date <= as_of_date_naive) | (Transaction.date.is_(None))
    ).group_by(
        Account.id, Account.name, Account.code, Account.type
    ).order_by(Account.code)
    
    result = await db.execute(query)
    account_balances = result.all()
    
    trial_balance = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')
    
    for row in account_balances:
        debit_total = Decimal(str(row.total_debits))
        credit_total = Decimal(str(row.total_credits))
        
        # Calculate account balance based on normal balance type
        if row.type in [AccountType.ASSET, AccountType.EXPENSE]:
            # Normal debit balance accounts
            balance = debit_total - credit_total
            debit_balance = balance if balance > 0 else Decimal('0.00')
            credit_balance = abs(balance) if balance < 0 else Decimal('0.00')
        else:
            # Normal credit balance accounts (LIABILITY, EQUITY, INCOME)
            balance = credit_total - debit_total
            credit_balance = balance if balance > 0 else Decimal('0.00')
            debit_balance = abs(balance) if balance < 0 else Decimal('0.00')
        
        # Only include accounts with non-zero balances
        if debit_balance != 0 or credit_balance != 0:
            trial_balance.append({
                'account_id': row.id,
                'account_code': row.code,
                'account_name': row.name,
                'account_type': row.type.value,
                'debit_balance': float(debit_balance),
                'credit_balance': float(credit_balance),
            })
            
            total_debits += debit_balance
            total_credits += credit_balance
    
    return {
        'report_type': 'Trial Balance',
        'as_of_date': as_of_date.isoformat(),
        'accounts': trial_balance,
        'totals': {
            'total_debits': float(total_debits),
            'total_credits': float(total_credits),
            'difference': float(total_debits - total_credits),
            'balanced': abs(total_debits - total_credits) < Decimal('0.01')
        },
        'summary': f"Trial Balance with {len(trial_balance)} accounts"
    }

async def generate_balance_sheet(db: AsyncSession, as_of_date: datetime = None) -> Dict:
    """
    Generate Balance Sheet showing Assets, Liabilities, and Equity
    """
    logger.info(f"[REPORT] Generating Balance Sheet as of {as_of_date or 'current date'}")
    
    if as_of_date is None:
        as_of_date = datetime.now(timezone.utc)
    
    # Get trial balance data
    trial_balance_data = await generate_trial_balance(db, as_of_date)
    accounts = trial_balance_data['accounts']
    
    # Categorize accounts
    assets = []
    liabilities = []
    equity = []
    
    total_assets = Decimal('0.00')
    total_liabilities = Decimal('0.00')
    total_equity = Decimal('0.00')
    
    for account in accounts:
        balance = Decimal(str(account['debit_balance'] - account['credit_balance']))
        
        if account['account_type'] == 'asset':
            if balance != 0:
                assets.append({
                    'account_code': account['account_code'],
                    'account_name': account['account_name'],
                    'balance': float(balance)
                })
                total_assets += balance
        
        elif account['account_type'] == 'liability':
            if balance != 0:
                liabilities.append({
                    'account_code': account['account_code'],
                    'account_name': account['account_name'],
                    'balance': float(-balance)  # Show as positive for liabilities
                })
                total_liabilities += -balance
        
        elif account['account_type'] == 'equity':
            if balance != 0:
                equity.append({
                    'account_code': account['account_code'],
                    'account_name': account['account_name'],
                    'balance': float(-balance)  # Show as positive for equity
                })
                total_equity += -balance
    
    # Calculate retained earnings from income and expenses
    retained_earnings = await calculate_retained_earnings(db, as_of_date)
    if retained_earnings != 0:
        equity.append({
            'account_code': 'RE',
            'account_name': 'Retained Earnings',
            'balance': float(retained_earnings)
        })
        total_equity += retained_earnings
    
    return {
        'report_type': 'Balance Sheet',
        'as_of_date': as_of_date.isoformat(),
        'assets': {
            'accounts': assets,
            'total': float(total_assets)
        },
        'liabilities': {
            'accounts': liabilities,
            'total': float(total_liabilities)
        },
        'equity': {
            'accounts': equity,
            'total': float(total_equity)
        },
        'totals': {
            'total_assets': float(total_assets),
            'total_liabilities_equity': float(total_liabilities + total_equity),
            'difference': float(total_assets - (total_liabilities + total_equity)),
            'balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal('0.01')
        }
    }

async def generate_income_statement(db: AsyncSession, start_date: datetime, end_date: datetime = None) -> Dict:
    """
    Generate Income Statement (Profit & Loss) for a specified period
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    
    logger.info(f"[REPORT] Generating Income Statement from {start_date} to {end_date}")
    
    # Convert timezone-aware datetimes to naive for database comparison
    start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
    end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
    
    # Query income and expense accounts for the period
    query = select(
        Account.id,
        Account.name,
        Account.code,
        Account.type,
        func.coalesce(func.sum(case((TransactionLine.type == 'debit', TransactionLine.amount), else_=0)), 0).label('total_debits'),
        func.coalesce(func.sum(case((TransactionLine.type == 'credit', TransactionLine.amount), else_=0)), 0).label('total_credits')
    ).select_from(
        Account.__table__.join(
            TransactionLine.__table__.join(
                Transaction.__table__, 
                TransactionLine.transaction_id == Transaction.id
            )
        )
    ).where(
        Account.type.in_([AccountType.INCOME, AccountType.EXPENSE]),
        Transaction.date >= start_date_naive,
        Transaction.date <= end_date_naive
    ).group_by(
        Account.id, Account.name, Account.code, Account.type
    ).order_by(Account.type, Account.code)
    
    result = await db.execute(query)
    account_data = result.all()
    
    income_accounts = []
    expense_accounts = []
    total_income = Decimal('0.00')
    total_expenses = Decimal('0.00')
    
    for row in account_data:
        debit_total = Decimal(str(row.total_debits))
        credit_total = Decimal(str(row.total_credits))
        
        if row.type == AccountType.INCOME:
            # Income accounts have normal credit balance
            balance = credit_total - debit_total
            if balance != 0:
                income_accounts.append({
                    'account_code': row.code,
                    'account_name': row.name,
                    'amount': float(balance)
                })
                total_income += balance
        
        elif row.type == AccountType.EXPENSE:
            # Expense accounts have normal debit balance
            balance = debit_total - credit_total
            if balance != 0:
                expense_accounts.append({
                    'account_code': row.code,
                    'account_name': row.name,
                    'amount': float(balance)
                })
                total_expenses += balance
    
    net_income = total_income - total_expenses
    
    return {
        'report_type': 'Income Statement',
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'income': {
            'accounts': income_accounts,
            'total': float(total_income)
        },
        'expenses': {
            'accounts': expense_accounts,
            'total': float(total_expenses)
        },
        'net_income': float(net_income),
        'summary': f"Net {'Income' if net_income >= 0 else 'Loss'}: {abs(float(net_income)):.2f}"
    }

async def generate_general_ledger(db: AsyncSession, account_id: int = None, start_date: datetime = None, end_date: datetime = None) -> Dict:
    """
    Generate General Ledger report for specific account or all accounts
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)  # Default to beginning of time
    
    logger.info(f"[REPORT] Generating General Ledger for account {account_id or 'ALL'} from {start_date} to {end_date}")
    
    # Convert timezone-aware datetimes to naive for database comparison
    start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
    end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
    
    # Base query for transactions
    query = select(
        Transaction.id.label('transaction_id'),
        Transaction.date,
        Transaction.description,
        Transaction.reference,
        Account.id.label('account_id'),
        Account.name.label('account_name'),
        Account.code.label('account_code'),
        TransactionLine.type,
        TransactionLine.amount
    ).select_from(
        Transaction.__table__.join(
            TransactionLine.__table__.join(
                Account.__table__,
                TransactionLine.account_id == Account.id
            )
        )
    ).where(
        Transaction.date >= start_date_naive,
        Transaction.date <= end_date_naive
    )
    
    # Filter by specific account if provided
    if account_id:
        query = query.where(Account.id == account_id)
    
    query = query.order_by(Account.code, Transaction.date, Transaction.id)
    
    result = await db.execute(query)
    transactions = result.all()
    
    # Group by account
    accounts_ledger = {}
    
    for row in transactions:
        account_key = f"{row.account_code} - {row.account_name}"
        
        if account_key not in accounts_ledger:
            accounts_ledger[account_key] = {
                'account_id': row.account_id,
                'account_code': row.account_code,
                'account_name': row.account_name,
                'transactions': [],
                'running_balance': Decimal('0.00')
            }
        
        # Calculate running balance
        amount = Decimal(str(row.amount))
        if row.type == 'debit':
            accounts_ledger[account_key]['running_balance'] += amount
        else:
            accounts_ledger[account_key]['running_balance'] -= amount
        
        accounts_ledger[account_key]['transactions'].append({
            'transaction_id': row.transaction_id,
            'date': row.date.isoformat(),
            'description': row.description,
            'reference': row.reference,
            'type': row.type,
            'amount': float(amount),
            'running_balance': float(accounts_ledger[account_key]['running_balance'])
        })
    
    # Convert to list and calculate totals
    ledger_accounts = []
    for account_data in accounts_ledger.values():
        account_data['running_balance'] = float(account_data['running_balance'])
        account_data['transaction_count'] = len(account_data['transactions'])
        ledger_accounts.append(account_data)
    
    return {
        'report_type': 'General Ledger',
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'account_filter': account_id,
        'accounts': ledger_accounts,
        'summary': f"General Ledger with {len(ledger_accounts)} accounts and {sum(acc['transaction_count'] for acc in ledger_accounts)} transactions"
    }

async def calculate_retained_earnings(db: AsyncSession, as_of_date: datetime) -> Decimal:
    """
    Calculate retained earnings (accumulated net income) as of a specific date
    """
    # Convert timezone-aware datetime to naive for database comparison
    as_of_date_naive = as_of_date.replace(tzinfo=None) if as_of_date.tzinfo else as_of_date
    
    # Get all income and expense transactions up to the date
    query = select(
        func.coalesce(func.sum(case((and_(Account.type == AccountType.INCOME, TransactionLine.type == 'credit'), TransactionLine.amount), else_=0)), 0).label('income_credits'),
        func.coalesce(func.sum(case((and_(Account.type == AccountType.INCOME, TransactionLine.type == 'debit'), TransactionLine.amount), else_=0)), 0).label('income_debits'),
        func.coalesce(func.sum(case((and_(Account.type == AccountType.EXPENSE, TransactionLine.type == 'debit'), TransactionLine.amount), else_=0)), 0).label('expense_debits'),
        func.coalesce(func.sum(case((and_(Account.type == AccountType.EXPENSE, TransactionLine.type == 'credit'), TransactionLine.amount), else_=0)), 0).label('expense_credits')
    ).select_from(
        TransactionLine.__table__.join(
            Transaction.__table__, TransactionLine.transaction_id == Transaction.id
        ).join(
            Account.__table__, TransactionLine.account_id == Account.id
        )
    ).where(
        Transaction.date <= as_of_date_naive,
        Account.type.in_([AccountType.INCOME, AccountType.EXPENSE])
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if row:
        total_income = Decimal(str(row.income_credits)) - Decimal(str(row.income_debits))
        total_expenses = Decimal(str(row.expense_debits)) - Decimal(str(row.expense_credits))
        retained_earnings = total_income - total_expenses
    else:
        retained_earnings = Decimal('0.00')
    
    return retained_earnings

async def generate_cash_flow_statement(db: AsyncSession, start_date: datetime, end_date: datetime = None) -> Dict:
    """
    Generate simplified Cash Flow Statement focusing on cash account movements
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    
    logger.info(f"[REPORT] Generating Cash Flow Statement from {start_date} to {end_date}")
    
    # Convert timezone-aware datetimes to naive for database comparison
    start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
    end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
    
    # Find cash accounts (assuming accounts with "cash" in the name)
    cash_accounts_query = select(Account).where(
        Account.name.ilike('%cash%'),
        Account.type == AccountType.ASSET
    )
    cash_accounts_result = await db.execute(cash_accounts_query)
    cash_accounts = cash_accounts_result.scalars().all()
    
    if not cash_accounts:
        return {
            'report_type': 'Cash Flow Statement',
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
            'error': 'No cash accounts found',
            'cash_flows': []
        }
    
    cash_flows = []
    total_inflows = Decimal('0.00')
    total_outflows = Decimal('0.00')
    
    for cash_account in cash_accounts:
        # Get cash account transactions for the period
        query = select(
            Transaction.date,
            Transaction.description,
            Transaction.reference,
            TransactionLine.type,
            TransactionLine.amount
        ).select_from(
            Transaction.__table__.join(
                TransactionLine.__table__,
                Transaction.id == TransactionLine.transaction_id
            )
        ).where(
            TransactionLine.account_id == cash_account.id,
            Transaction.date >= start_date_naive,
            Transaction.date <= end_date_naive
        ).order_by(Transaction.date)
        
        result = await db.execute(query)
        transactions = result.all()
        
        for row in transactions:
            amount = Decimal(str(row.amount))
            is_inflow = row.type == 'debit'  # Cash increases with debits
            
            cash_flows.append({
                'date': row.date.isoformat(),
                'description': row.description,
                'reference': row.reference,
                'account': cash_account.name,
                'type': 'Inflow' if is_inflow else 'Outflow',
                'amount': float(amount)
            })
            
            if is_inflow:
                total_inflows += amount
            else:
                total_outflows += amount
    
    net_cash_flow = total_inflows - total_outflows
    
    return {
        'report_type': 'Cash Flow Statement',
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'cash_flows': cash_flows,
        'summary': {
            'total_inflows': float(total_inflows),
            'total_outflows': float(total_outflows),
            'net_cash_flow': float(net_cash_flow)
        }
    }
