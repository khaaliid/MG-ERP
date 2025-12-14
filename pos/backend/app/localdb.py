from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
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
