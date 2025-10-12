from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SizeTypeEnum(str, Enum):
    CLOTHING = "clothing"
    NUMERIC = "numeric"
    SHOE = "shoe"

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    size_type: SizeTypeEnum = SizeTypeEnum.CLOTHING

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    size_type: Optional[SizeTypeEnum] = None

class Category(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Supplier Schemas
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = 7

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: Optional[int] = None

class Supplier(SupplierBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    cost_price: float = 0.0
    selling_price: float = 0.0
    material: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    category_id: str
    brand_id: Optional[str] = None
    supplier_id: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    material: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    supplier_id: Optional[str] = None

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    brand: Optional[Brand] = None
    supplier: Optional[Supplier] = None

    class Config:
        from_attributes = True

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