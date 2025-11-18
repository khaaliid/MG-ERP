from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone
from ..services.ledger import AccountType, TransactionSource


class AccountSchema(BaseModel):
    id: Optional[int] = Field(None, description="Account ID (auto-generated)")
    name: str = Field(..., description="Account name", min_length=1, max_length=100)
    type: AccountType = Field(..., description="Account type (asset, liability, equity, revenue, expense)")
    code: str = Field(..., description="Unique account code", min_length=1, max_length=20)
    description: Optional[str] = Field(None, description="Account description")
    is_active: Optional[bool] = Field(True, description="Whether the account is active")

    class Config:
        from_attributes = True
        use_enum_values = True
        schema_extra = {
            "example": {
                "name": "Cash in Bank",
                "type": "asset",
                "code": "1001",
                "description": "Main checking account for operations",
                "is_active": True
            }
        }


class TransactionLineSchema(BaseModel):
    account_name: str = Field(..., description="Name of the account for this journal entry")
    type: Literal["debit", "credit"] = Field(..., description="Entry type: debit or credit")
    amount: float = Field(..., description="Amount for this journal entry", gt=0)

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "account_name": "Cash in Bank",
                "type": "debit",
                "amount": 1000.00
            }
        }


class TransactionLineResponse(BaseModel):
    account_name: str
    account_type: str
    type: Literal["debit", "credit"]
    amount: float

    class Config:
        from_attributes = True


class TransactionSchema(BaseModel):
    id: Optional[int] = Field(None, description="Transaction ID (auto-generated)")
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Transaction date"
    )
    description: str = Field(..., description="Transaction description", min_length=1)
    source: Optional[TransactionSource] = Field(
        TransactionSource.manual, 
        description="Transaction source: manual, import, or system"
    )
    reference: Optional[str] = Field(None, description="External reference number")
    created_by: Optional[str] = Field(None, description="User who created the transaction")
    lines: List[TransactionLineSchema] = Field(
        ..., 
        description="Journal entry lines (must balance: total debits = total credits)",
        min_items=2
    )

    class Config:
        from_attributes = True
        use_enum_values = True
        schema_extra = {
            "example": {
                "description": "Office rent payment for January 2025",
                "source": "manual",
                "reference": "CHK-001234",
                "lines": [
                    {
                        "account_name": "Rent Expense",
                        "type": "debit",
                        "amount": 2000.00
                    },
                    {
                        "account_name": "Cash in Bank",
                        "type": "credit",
                        "amount": 2000.00
                    }
                ]
            }
        }


class TransactionResponse(BaseModel):
    id: Optional[int] = None
    date: datetime
    description: str
    source: str
    reference: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    lines: List[TransactionLineResponse]

    class Config:
        from_attributes = True