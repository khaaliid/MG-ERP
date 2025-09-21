from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from .config import SessionLocal, engine
from .services.ledger import (
    get_all_transactions,
    create_transaction,
    get_transaction_by_id,
    delete_transaction_by_id,
    Transaction,
    TransactionLine,
    Base
)

app = FastAPI()

# Add CORS middleware (already present, but ensure it's at the top before any endpoints)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # Create tables using async engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class TransactionLineSchema(BaseModel):
    account: str
    type: Literal["debit", "credit"]
    amount: float

    class Config:
        orm_mode = True

class TransactionSchema(BaseModel):
    id: Optional[int] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    description: str
    lines: List[TransactionLineSchema]

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "MG-ERP Ledger Backend is running"}

@app.get("/transactions", response_model=List[TransactionSchema])
async def list_transactions(db: AsyncSession = Depends(get_db)):
    return await get_all_transactions(db)

@app.post("/transactions", response_model=TransactionSchema)
async def add_transaction(transaction: TransactionSchema, db: AsyncSession = Depends(get_db)):
    return await create_transaction(db, transaction)

@app.get("/transactions/{transaction_id}", response_model=TransactionSchema)
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    transaction = await get_transaction_by_id(db, transaction_id)
    if transaction:
        return transaction
    raise HTTPException(status_code=404, detail="Transaction not found")

@app.delete("/transactions/{transaction_id}", response_model=dict)
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    if await delete_transaction_by_id(db, transaction_id):
        return {"message": "Transaction deleted"}
    raise HTTPException(status_code=404, detail="Transaction not found")
