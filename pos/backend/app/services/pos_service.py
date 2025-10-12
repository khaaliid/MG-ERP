from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from ..models.pos_models import Product, ProductCategory, Sale, SaleItem
from ..schemas import ProductCreate, ProductUpdate, SaleCreate
from .erp_integration import erp_service

class ProductService:
    """Service for product management"""
    
    @staticmethod
    async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[Product]:
        query = select(Product).options(selectinload(Product.category))
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        query = query.filter(Product.is_active == True).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
        query = select(Product).options(selectinload(Product.category)).filter(Product.id == product_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_product_by_sku(db: AsyncSession, sku: str) -> Optional[Product]:
        query = select(Product).options(selectinload(Product.category)).filter(Product.sku == sku)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search_products(db: AsyncSession, search_term: str) -> List[Product]:
        query = select(Product).options(selectinload(Product.category)).filter(
            (Product.name.ilike(f"%{search_term}%")) |
            (Product.sku.ilike(f"%{search_term}%")) |
            (Product.barcode.ilike(f"%{search_term}%"))
        ).filter(Product.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_product(db: AsyncSession, product: ProductCreate) -> Product:
        db_product = Product(**product.dict())
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        return db_product

class SaleService:
    """Service for sales management"""
    
    @staticmethod
    async def create_sale(db: AsyncSession, sale: SaleCreate) -> Sale:
        # Generate sale number
        sale_number = f"POS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate totals
        subtotal = sum(item.quantity * item.unit_price for item in sale.items)
        tax_amount = subtotal * 0.1  # 10% tax (configurable)
        total_amount = subtotal + tax_amount - sale.discount_amount
        
        # Create sale record
        db_sale = Sale(
            sale_number=sale_number,
            customer_name=sale.customer_name,
            customer_phone=sale.customer_phone,
            customer_email=sale.customer_email,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=sale.discount_amount,
            total_amount=total_amount,
            payment_method=sale.payment_method,
            notes=sale.notes,
            cashier_name=sale.cashier_name,
            sale_date=datetime.now(timezone.utc)
        )
        
        db.add(db_sale)
        await db.flush()  # Get the sale ID
        
        # Create sale items
        for item in sale.items:
            line_total = item.quantity * item.unit_price
            db_item = SaleItem(
                sale_id=db_sale.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total
            )
            db.add(db_item)
            
            # Update product stock
            product = await ProductService.get_product_by_id(db, item.product_id)
            if product:
                product.stock_quantity -= item.quantity
        
        await db.commit()
        await db.refresh(db_sale)
        
        # Sync with ERP system
        try:
            sale_data = {
                "sale_number": db_sale.sale_number,
                "customer_name": db_sale.customer_name,
                "total_amount": db_sale.total_amount,
                "sale_date": db_sale.sale_date.isoformat()
            }
            
            erp_transaction_id = await erp_service.create_pos_transaction(sale_data)
            if erp_transaction_id:
                db_sale.erp_transaction_id = erp_transaction_id
                db_sale.is_synced_to_erp = True
                await db.commit()
                
        except Exception as e:
            # Log error but don't fail the sale
            print(f"Failed to sync sale with ERP: {str(e)}")
        
        # Reload with items
        query = select(Sale).options(
            selectinload(Sale.items).selectinload(SaleItem.product)
        ).filter(Sale.id == db_sale.id)
        result = await db.execute(query)
        return result.scalar_one()
    
    @staticmethod
    async def get_sales(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Sale]:
        query = select(Sale).options(
            selectinload(Sale.items).selectinload(SaleItem.product)
        ).order_by(Sale.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_sale_by_id(db: AsyncSession, sale_id: int) -> Optional[Sale]:
        query = select(Sale).options(
            selectinload(Sale.items).selectinload(SaleItem.product)
        ).filter(Sale.id == sale_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()