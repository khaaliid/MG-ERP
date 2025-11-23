"""
Stateless POS Schemas

These schemas represent the data formats for the stateless POS system.
They match the external service response formats and request structures.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# External service response schemas (read-only)
class ExternalProduct(BaseModel):
    """Product schema from Inventory Service (read-only)"""
    id: Union[str, int]
    name: str
    sku: str
    barcode: Optional[str] = None
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    stock_quantity: int
    min_stock_level: int
    category_id: Optional[Union[str, int]] = None
    category_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ExternalCategory(BaseModel):
    """Category schema from Inventory Service (read-only)"""
    id: Union[str, int]
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

class ExternalBrand(BaseModel):
    """Brand schema from Inventory Service (read-only)"""
    id: Union[str, int]
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

# POS-specific input schemas for sale processing
class SaleItemInput(BaseModel):
    """Sale item input for creating a sale"""
    product_id: Union[str, int] = Field(..., description="Product ID from inventory service")
    quantity: int = Field(..., gt=0, description="Quantity to sell")
    unit_price: float = Field(..., gt=0, description="Unit price at time of sale")
    size: Optional[str] = Field(None, description="Product size/variant")

class SaleInput(BaseModel):
    """Sale input for processing a transaction"""
    items: List[SaleItemInput] = Field(..., min_items=1, description="Items being sold")
    payment_method: str = Field(default="cash", description="Payment method (cash, card, etc.)")
    customer_name: Optional[str] = Field(None, max_length=200, description="Optional customer name")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Optional customer phone")
    customer_email: Optional[str] = Field(None, max_length=100, description="Optional customer email")
    discount_amount: float = Field(default=0.0, ge=0, description="Discount amount")
    tax_rate: float = Field(default=0.14, ge=0, le=1, description="Tax rate (0.14 = 14%)")
    tendered_amount: Optional[float] = Field(None, ge=0, description="Amount tendered by customer")
    notes: Optional[str] = Field(None, description="Optional sale notes")

# Sale output schemas (what POS returns after processing)
class ProcessedSaleItem(BaseModel):
    """Processed sale item response"""
    product_id: Union[str, int]
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    size: Optional[str] = None

class ProcessedSale(BaseModel):
    """Processed sale response from stateless POS service"""
    id: str  # Temporary ID for response
    sale_number: str
    items: List[ProcessedSaleItem]
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    payment_method: str
    tendered_amount: Optional[float] = None
    change_amount: float
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    cashier: str
    cashier_id: Union[str, int]
    created_at: str  # ISO format
    ledger_entry_id: Optional[Union[str, int]] = None
    inventory_updates: List[Dict[str, Any]]
    status: str

# Generic response schemas
class PaginatedResponse(BaseModel):
    """Generic paginated response format"""
    data: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_next: bool = False
    has_prev: bool = False

class ServiceResponse(BaseModel):
    """Generic service response format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
    service: str
    architecture: Optional[Dict[str, Any]] = None
    external_services: Optional[Dict[str, Any]] = None

# Legacy schema aliases for backward compatibility
# (These can be removed once frontend is updated)
Product = ExternalProduct
ProductCategory = ExternalCategory
Sale = ProcessedSale
SaleCreate = SaleInput
SaleItem = ProcessedSaleItem