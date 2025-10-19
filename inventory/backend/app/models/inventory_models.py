from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
import enum

Base = declarative_base()

# Schema configuration
SCHEMA_NAME = "inventory"

class SizeType(enum.Enum):
    CLOTHING = "CLOTHING"  # S, M, L, XL, XXL
    NUMERIC = "NUMERIC"    # 30, 32, 34, etc.
    SHOE = "SHOE"          # 7, 8, 9, 10, etc.

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    size_type = Column(Enum(SizeType), default=SizeType.CLOTHING)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="category")

class Brand(Base):
    __tablename__ = "brands"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    contact_info = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="brand")

class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    lead_time_days = Column(Integer, default=7)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    sku = Column(String(50), unique=True)
    barcode = Column(String(50), unique=True)
    
    # Pricing
    cost_price = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)
    
    # Product Details
    material = Column(String(100))
    color = Column(String(50))
    season = Column(String(20))  # Spring/Summer, Fall/Winter
    
    # Relationships
    category_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.categories.id"), nullable=False)
    brand_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.brands.id"))
    supplier_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.suppliers.id"))
    
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    
    # Stock tracking
    stock_items = relationship("StockItem", back_populates="product")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @property
    def sizes(self):
        """Convert stock_items to sizes format for API response"""
        return [
            {
                "size": item.size,
                "quantity": item.quantity,
                "reorder_level": item.reorder_level,
                "max_stock_level": item.max_stock_level
            }
            for item in self.stock_items
        ]

class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    product_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.products.id"), nullable=False)
    size = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, default=5)
    max_stock_level = Column(Integer, default=100)
    
    # Location in store
    location = Column(String(50))  # Shelf, Rack number, etc.
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="stock_items")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    supplier_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.suppliers.id"), nullable=False)
    order_number = Column(String(50), unique=True)
    status = Column(String(20), default="pending")  # pending, ordered, received, cancelled
    order_date = Column(DateTime, server_default=func.now())
    expected_delivery = Column(DateTime)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    purchase_order_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.purchase_orders.id"), nullable=False)
    product_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.products.id"), nullable=False)
    size = Column(String(10), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    product_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.products.id"), nullable=False)
    size = Column(String(10), nullable=False)
    movement_type = Column(String(20), nullable=False)  # purchase, sale, adjustment, return
    quantity_change = Column(Integer, nullable=False)  # Positive for inbound, negative for outbound
    reference_id = Column(String(50))  # PO number, sale ID, etc.
    notes = Column(Text)
    
    # Relationships
    product = relationship("Product")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())