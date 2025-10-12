from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Product schemas
class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategory(ProductCategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=50)
    barcode: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    cost: Optional[float] = Field(None, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=0, ge=0)
    category_id: Optional[int] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    barcode: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategory] = None
    
    class Config:
        from_attributes = True

# Sale schemas
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)

class SaleItemCreate(SaleItemBase):
    pass

class SaleItem(SaleItemBase):
    id: int
    line_total: float
    product: Product
    
    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    payment_method: str = Field(default="cash", max_length=50)
    notes: Optional[str] = None
    cashier_name: Optional[str] = Field(None, max_length=100)
    discount_amount: float = Field(default=0.0, ge=0)

class SaleCreate(SaleBase):
    items: List[SaleItemCreate] = Field(..., min_items=1)

class Sale(SaleBase):
    id: int
    sale_number: str
    subtotal: float
    tax_amount: float
    total_amount: float
    sale_date: datetime
    created_at: datetime
    is_synced_to_erp: bool
    erp_transaction_id: Optional[int]
    items: List[SaleItem]
    
    class Config:
        from_attributes = True

# Response schemas
class SaleResponse(BaseModel):
    success: bool
    message: str
    sale: Optional[Sale] = None