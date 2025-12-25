from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import enum

Base = declarative_base()

# Schema configuration
SCHEMA_NAME = "pos"

class SaleStatus(enum.Enum):
    PENDING = "pending"  # Locally saved, not yet sent to ledger
    SYNCED = "synced"    # Successfully sent to ledger
    FAILED = "failed"    # Failed to sync to ledger

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True)
    sale_number = Column(String, index=True, unique=True, nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    tendered_amount = Column(Float, nullable=True)
    change_amount = Column(Float, nullable=True)
    customer_name = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    cashier = Column(String, nullable=True)
    cashier_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    status = Column(String, default="pending", nullable=False)
    ledger_entry_id = Column(String, nullable=True)  # Reference to ledger transaction

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(String, ForeignKey(f"{SCHEMA_NAME}.sales.id"), index=True, nullable=False)
    product_id = Column(String, nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    line_total = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(String, primary_key=True)
    sku = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    category_id = Column(String, nullable=True)
    category_name = Column(String, nullable=True)
    brand_id = Column(String, nullable=True)
    brand_name = Column(String, nullable=True)
    barcode = Column(String, nullable=True)
    is_active = Column(String, default="true", nullable=False)  # "true" or "false"
    synced_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {'schema': SCHEMA_NAME}

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

class POSSettings(Base):
    __tablename__ = "settings"
    __table_args__ = {'schema': SCHEMA_NAME}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Tax settings
    tax_rate = Column(Float, default=0.14, nullable=False)  # Default 14%
    tax_inclusive = Column(String, default="false", nullable=False)  # "true" or "false"
    
    # Currency settings
    currency_code = Column(String, default="USD", nullable=False)
    currency_symbol = Column(String, default="$", nullable=False)
    
    # Business information
    business_name = Column(String, nullable=True)
    business_address = Column(String, nullable=True)
    business_phone = Column(String, nullable=True)
    business_email = Column(String, nullable=True)
    business_tax_id = Column(String, nullable=True)
    
    # Receipt settings
    receipt_header = Column(String, nullable=True)
    receipt_footer = Column(String, nullable=True)
    print_receipt = Column(String, default="true", nullable=False)  # "true" or "false"
    
    # Other settings
    require_customer_name = Column(String, default="false", nullable=False)  # "true" or "false"
    allow_discounts = Column(String, default="true", nullable=False)  # "true" or "false"
    low_stock_threshold = Column(Integer, default=10, nullable=False)
    
    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String, nullable=True)
