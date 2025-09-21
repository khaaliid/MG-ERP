from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, select
from sqlalchemy.orm import declarative_base, relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(String, nullable=False)
    lines = relationship("TransactionLine", back_populates="transaction", cascade="all, delete-orphan")

class TransactionLine(Base):
    __tablename__ = "transaction_lines"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"))
    account = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'debit' or 'credit'
    amount = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="lines")

# CRUD operations
async def get_all_transactions(db: AsyncSession):
    result = await db.execute(
        select(Transaction).options(selectinload(Transaction.lines)).order_by(Transaction.date.desc())
    )
    transactions = result.scalars().unique().all()
    return transactions

async def create_transaction(db: AsyncSession, transaction_data):
    transaction = Transaction(
        date=transaction_data.date,
        description=transaction_data.description
    )
    db.add(transaction)
    await db.flush()  # get transaction.id
    for line in transaction_data.lines:
        db.add(TransactionLine(
            transaction_id=transaction.id,
            account=line.account,
            type=line.type,
            amount=line.amount
        ))
    await db.commit()
    # Re-query with selectinload to ensure lines are loaded in the async context
    result = await db.execute(
        select(Transaction).options(selectinload(Transaction.lines)).where(Transaction.id == transaction.id)
    )
    transaction_with_lines = result.scalars().first()
    return transaction_with_lines

async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction).options(selectinload(Transaction.lines)).where(Transaction.id == transaction_id)
    )
    transaction = result.scalars().first()
    return transaction

async def delete_transaction_by_id(db: AsyncSession, transaction_id: int) -> bool:
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalars().first()
    if transaction:
        await db.delete(transaction)
        await db.commit()
        return True
    return False
    return False
