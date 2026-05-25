"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import TransactionType, PaymentMethod, UserRole, ExpenseCategory


# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.CASHIER


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# Ledger Schemas
class LedgerRecordBase(BaseModel):
    transaction_type: TransactionType
    description: str
    amount: float
    reference_id: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    notes: Optional[str] = None


class LedgerRecordCreate(LedgerRecordBase):
    pass


class LedgerRecordResponse(LedgerRecordBase):
    id: int
    transaction_date: datetime
    balance: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Inventory Schemas
class InventoryItemBase(BaseModel):
    name: str
    sku: str
    barcode: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: float = Field(gt=0)
    cost_price: float = Field(gt=0)
    quantity: int = Field(ge=0)
    reorder_level: int = 10


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    cost_price: Optional[float] = None
    quantity: Optional[int] = None
    reorder_level: Optional[int] = None


class InventoryItemResponse(InventoryItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# POS Schemas
class POSItemBase(BaseModel):
    inventory_id: int
    quantity: int = Field(gt=0)


class POSItemCreate(POSItemBase):
    pass


class POSItemResponse(POSItemBase):
    id: int
    product_name: str
    unit_price: float
    subtotal: float
    created_at: datetime

    class Config:
        from_attributes = True


class POSTransactionBase(BaseModel):
    customer_name: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    payment_received: float = Field(gt=0)
    discount: float = Field(ge=0, default=0.0)
    sales_user_id: Optional[int] = None
    notes: Optional[str] = None


class POSTransactionCreate(POSTransactionBase):
    items: List[POSItemCreate]


class POSTransactionResponse(POSTransactionBase):
    id: int
    transaction_number: str
    transaction_date: datetime
    subtotal: float
    tax: float
    total: float
    change_returned: float
    sales_user_id: Optional[int]
    ledger_id: Optional[int]
    created_at: datetime
    items: List[POSItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class POSTransactionPageResponse(BaseModel):
    items: List[POSTransactionResponse]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True


class LedgerPageResponse(BaseModel):
    items: List[LedgerRecordResponse]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True


# POS Cashier Closure Schemas
class POSClosureRequest(BaseModel):
    sales_user_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    save_to_ledger: bool = True


class POSClosureResponse(BaseModel):
    sales_user_id: int
    start_date: datetime
    end_date: datetime
    total_sales: float
    transaction_count: int
    by_payment_method: dict
    transactions: List[POSTransactionResponse]

    class Config:
        from_attributes = True


# Refund Schemas
class RefundRequest(BaseModel):
    amount: float = Field(gt=0)
    reason: Optional[str] = None
    restock: bool = False
    refund_payment_method: Optional[PaymentMethod] = None


class RefundResponse(BaseModel):
    transaction_id: int
    refunded_amount: float
    refund_date: datetime
    new_balance: float
    restocked: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ItemRefundRequest(BaseModel):
    pos_item_id: int
    quantity: int = Field(gt=0)
    reason: Optional[str] = None
    restock: bool = True
    refund_payment_method: Optional[PaymentMethod] = None


class ItemRefundResponse(BaseModel):
    transaction_id: int
    pos_item_id: int
    refunded_quantity: int
    refunded_amount: float
    refund_date: datetime
    new_balance: float
    restocked: bool
    remaining_quantity: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class WhatsAppReceiptRequest(BaseModel):
    phone_number: str


class WhatsAppReceiptResponse(BaseModel):
    transaction_id: int
    phone_number: str
    message: str
    provider_response: dict


# Report Schemas
class SalesReportResponse(BaseModel):
    total_sales: float
    total_transactions: int
    average_transaction: float
    total_tax: float
    total_discount: float


class InventoryReportResponse(BaseModel):
    total_items: int
    total_value: float
    low_stock_items: int
    out_of_stock_items: int


class LedgerReportResponse(BaseModel):
    current_balance: float
    total_income: float
    total_expenses: float
    transaction_count: int


# Sales User Performance Report Schemas
class ProductBreakdown(BaseModel):
    product_name: str
    quantity: int
    total_amount: float


class SalesUserPerformance(BaseModel):
    sales_user_id: int
    sales_user_name: str
    employee_code: Optional[str]
    total_transactions: int
    total_pieces: int
    total_revenue: float
    product_breakdown: List[ProductBreakdown]


class SalesUserPerformanceReportResponse(BaseModel):
    report_date: datetime
    start_date: datetime
    end_date: datetime
    sales_users: List[SalesUserPerformance]
    total_transactions: int
    total_pieces: int
    total_revenue: float


# Expense Schemas
class ExpenseBase(BaseModel):
    expense_date: datetime
    category: ExpenseCategory
    description: str
    amount: float
    payment_method: PaymentMethod = PaymentMethod.CASH
    vendor: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    expense_date: Optional[datetime] = None
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    payment_method: Optional[PaymentMethod] = None
    vendor: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    id: int
    recorded_by: Optional[int]
    ledger_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpensePageResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    skip: int
    limit: int
    total_amount: float

    class Config:
        from_attributes = True


# Sales User Schemas
class SalesUserBase(BaseModel):
    name: str
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True


class SalesUserCreate(SalesUserBase):
    pass


class SalesUserUpdate(BaseModel):
    name: Optional[str] = None
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


class SalesUserResponse(SalesUserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

