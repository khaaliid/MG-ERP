from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SizeTypeEnum(str, Enum):
    CLOTHING = "CLOTHING"
    NUMERIC = "numeric"
    SHOE = "shoe"

# Size/Stock Schemas for Product Creation
class ProductSizeCreate(BaseModel):
    size: str
    quantity: int = 0
    reorder_level: int = Field(default=5, alias='reorderLevel')
    max_stock_level: int = Field(default=100, alias='maxStockLevel')
    location: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class ProductSize(BaseModel):
    size: str
    quantity: int
    reorder_level: int
    max_stock_level: int
    
    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    size_type: SizeTypeEnum = Field(default=SizeTypeEnum.CLOTHING, alias='sizeType')
    
    class Config:
        allow_population_by_field_name = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    size_type: Optional[SizeTypeEnum] = Field(default=None, alias='sizeType')
    
    class Config:
        allow_population_by_field_name = True

class Category(CategoryBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime = Field(alias='updatedAt')

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        populate_by_name = True

# Brand Schemas
class BrandBase(BaseModel):
    name: str
    description: Optional[str] = None
    contact_info: Optional[str] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_info: Optional[str] = None

class Brand(BrandBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime = Field(alias='updatedAt')

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        populate_by_name = True

# Supplier Schemas
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = Field(default=None, alias='contactPerson')
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = Field(default=7, alias='leadTimeDays')
    
    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = Field(default=None, alias='contactPerson')
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: Optional[int] = Field(default=None, alias='leadTimeDays')
    
    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

class Supplier(SupplierBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime = Field(alias='updatedAt')

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        populate_by_name = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    cost_price: float = Field(default=0.0, alias='costPrice')
    selling_price: float = Field(default=0.0, alias='sellingPrice')
    material: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    category_id: str = Field(alias='categoryId')
    brand_id: Optional[str] = Field(default=None, alias='brandId')
    supplier_id: Optional[str] = Field(default=None, alias='supplierId')
    
    @validator('brand_id', 'supplier_id', pre=True)
    def empty_str_to_none(cls, v):
        return None if v == '' or v == 'undefined' else v
        
    @validator('category_id', pre=True)
    def validate_category_id(cls, v):
        if not v or v == '' or v == 'undefined':
            raise ValueError('Category is required')
        return v
    
    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

class ProductCreate(ProductBase):
    sizes: Optional[List[ProductSizeCreate]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    cost_price: Optional[float] = Field(default=None, alias='costPrice')
    selling_price: Optional[float] = Field(default=None, alias='sellingPrice')
    material: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    category_id: Optional[str] = Field(default=None, alias='categoryId')
    brand_id: Optional[str] = Field(default=None, alias='brandId')
    supplier_id: Optional[str] = Field(default=None, alias='supplierId')
    
    class Config:
        allow_population_by_field_name = True

class Product(ProductBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime = Field(alias='updatedAt')
    category: Optional[Category] = None
    brand: Optional[Brand] = None
    supplier: Optional[Supplier] = None
    sizes: Optional[List[ProductSize]] = []

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        populate_by_name = True

# Stock Item Schemas
class StockItemBase(BaseModel):
    product_id: str
    size: str
    quantity: int = 0
    reorder_level: int = 5
    max_stock_level: int = 100
    location: Optional[str] = None

class StockItemCreate(StockItemBase):
    pass

class StockItemUpdate(BaseModel):
    quantity: Optional[int] = None
    reorder_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    location: Optional[str] = None

class StockItem(StockItemBase):
    id: str
    created_at: datetime
    updated_at: datetime
    product: Optional[Product] = None

    class Config:
        from_attributes = True

# Purchase Order Schemas
class PurchaseOrderItemBase(BaseModel):
    product_id: str
    size: str
    quantity_ordered: int
    unit_cost: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItem(PurchaseOrderItemBase):
    id: str
    quantity_received: int = 0
    total_cost: float
    product: Optional[Product] = None

    class Config:
        from_attributes = True

class PurchaseOrderBase(BaseModel):
    supplier_id: str
    order_number: Optional[str] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]

class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None

class PurchaseOrder(PurchaseOrderBase):
    id: str
    status: str
    order_date: datetime
    total_amount: float
    created_at: datetime
    updated_at: datetime
    supplier: Optional[Supplier] = None
    items: List[PurchaseOrderItem] = []

    class Config:
        from_attributes = True

# Stock Movement Schemas
class StockMovementBase(BaseModel):
    product_id: str
    size: str
    movement_type: str
    quantity_change: int
    reference_id: Optional[str] = None
    notes: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    pass

class StockMovement(StockMovementBase):
    id: str
    created_at: datetime
    product: Optional[Product] = None

    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_products: int
    total_stock_items: int
    low_stock_items: int
    total_suppliers: int
    pending_orders: int
    total_inventory_value: float

class LowStockAlert(BaseModel):
    product: Product
    stock_item: StockItem
    shortage: int