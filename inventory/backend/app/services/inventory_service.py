from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import List, Optional
from ..models.inventory_models import (
    Product, Category, Brand, Supplier, StockItem, 
    PurchaseOrder, PurchaseOrderItem, StockMovement
)
from ..schemas.inventory_schemas import (
    ProductCreate, ProductUpdate,
    CategoryCreate, CategoryUpdate,
    BrandCreate, BrandUpdate,
    SupplierCreate, SupplierUpdate,
    StockItemCreate, StockItemUpdate,
    PurchaseOrderCreate, PurchaseOrderUpdate,
    StockMovementCreate
)
import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    # Category Methods
    def create_category(self, category_data: CategoryCreate) -> Category:
        category = Category(**category_data.dict())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_categories(self) -> List[Category]:
        return self.db.query(Category).all()

    def get_category(self, category_id: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def update_category(self, category_id: str, category_data: CategoryUpdate) -> Optional[Category]:
        category = self.get_category(category_id)
        if category:
            for field, value in category_data.dict(exclude_unset=True).items():
                setattr(category, field, value)
            self.db.commit()
            self.db.refresh(category)
        return category

    def delete_category(self, category_id: str) -> bool:
        category = self.get_category(category_id)
        if category:
            self.db.delete(category)
            self.db.commit()
            return True
        return False

    # Brand Methods
    def create_brand(self, brand_data: BrandCreate) -> Brand:
        brand = Brand(**brand_data.dict())
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand

    def get_brands(self) -> List[Brand]:
        return self.db.query(Brand).all()

    def get_brand(self, brand_id: str) -> Optional[Brand]:
        return self.db.query(Brand).filter(Brand.id == brand_id).first()

    def update_brand(self, brand_id: str, brand_data: BrandUpdate) -> Optional[Brand]:
        brand = self.get_brand(brand_id)
        if brand:
            for field, value in brand_data.dict(exclude_unset=True).items():
                setattr(brand, field, value)
            self.db.commit()
            self.db.refresh(brand)
        return brand

    def delete_brand(self, brand_id: str) -> bool:
        brand = self.get_brand(brand_id)
        if brand:
            self.db.delete(brand)
            self.db.commit()
            return True
        return False

    # Supplier Methods
    def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        supplier = Supplier(**supplier_data.dict())
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def get_suppliers(self) -> List[Supplier]:
        return self.db.query(Supplier).all()

    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def update_supplier(self, supplier_id: str, supplier_data: SupplierUpdate) -> Optional[Supplier]:
        supplier = self.get_supplier(supplier_id)
        if supplier:
            for field, value in supplier_data.dict(exclude_unset=True).items():
                setattr(supplier, field, value)
            self.db.commit()
            self.db.refresh(supplier)
        return supplier

    def delete_supplier(self, supplier_id: str) -> bool:
        supplier = self.get_supplier(supplier_id)
        if supplier:
            self.db.delete(supplier)
            self.db.commit()
            return True
        return False

    # Product Methods
    def create_product(self, product_data: ProductCreate) -> Product:
        logger.info(f"🏭 Service: Creating product '{product_data.name}'")
        
        try:
            # Extract sizes data before creating product
            sizes_data = product_data.sizes if hasattr(product_data, 'sizes') and product_data.sizes else []
            logger.info(f"📏 Product has {len(sizes_data)} size variants")
            
            # Create product without sizes
            product_dict = product_data.dict(exclude={'sizes'})
            logger.debug(f"📦 Product dict: {product_dict}")
            
            product = Product(**product_dict)
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            logger.info(f"✅ Product created with ID: {product.id}")
            
            # Create stock items for each size
            for i, size_data in enumerate(sizes_data):
                logger.info(f"📏 Creating stock item {i+1}/{len(sizes_data)}: {size_data.size}")
                stock_item = StockItem(
                    product_id=product.id,
                    size=size_data.size,
                    quantity=size_data.quantity,
                    reorder_level=size_data.reorder_level,
                    max_stock_level=size_data.max_stock_level,
                    location=getattr(size_data, 'location', None)
                )
                self.db.add(stock_item)
            
            if sizes_data:
                self.db.commit()
                self.db.refresh(product)
                logger.info(f"✅ Created {len(sizes_data)} stock items for product {product.id}")
            
            return product
            
        except Exception as e:
            logger.error(f"❌ Error creating product: {str(e)}")
            self.db.rollback()
            raise

    def get_products(self, category_id: Optional[str] = None, brand_id: Optional[str] = None) -> List[Product]:
        query = self.db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.brand),
            joinedload(Product.supplier),
            joinedload(Product.stock_items)
        )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if brand_id:
            query = query.filter(Product.brand_id == brand_id)
        
        products = query.all()
        
        # Debug: Log the first product's prices if any products exist
        if products:
            first_product = products[0]
            logger.info(f"Debug - First product: {first_product.name}, cost_price: {first_product.cost_price}, selling_price: {first_product.selling_price}")
            
        return products

    def get_product(self, product_id: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def update_product(self, product_id: str, product_data: ProductUpdate) -> Optional[Product]:
        product = self.get_product(product_id)
        if product:
            for field, value in product_data.dict(exclude_unset=True).items():
                setattr(product, field, value)
            self.db.commit()
            self.db.refresh(product)
        return product

    def delete_product(self, product_id: str) -> bool:
        product = self.get_product(product_id)
        if product:
            try:
                # First delete all related stock items
                self.db.query(StockItem).filter(StockItem.product_id == product_id).delete()
                
                # Then delete the product
                self.db.delete(product)
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error deleting product {product_id}: {str(e)}")
                raise
        return False

    # Stock Item Methods
    def create_stock_item(self, stock_data: StockItemCreate) -> StockItem:
        stock_item = StockItem(**stock_data.dict())
        self.db.add(stock_item)
        self.db.commit()
        self.db.refresh(stock_item)
        return stock_item

    def get_stock_items(self, product_id: Optional[str] = None) -> List[StockItem]:
        query = self.db.query(StockItem)
        if product_id:
            query = query.filter(StockItem.product_id == product_id)
        return query.all()

    def get_stock_item(self, stock_item_id: str) -> Optional[StockItem]:
        return self.db.query(StockItem).filter(StockItem.id == stock_item_id).first()

    def update_stock_quantity(self, product_id: str, size: str, quantity_change: int, movement_type: str = "adjustment", reference_id: Optional[str] = None):
        # Find stock item
        stock_item = self.db.query(StockItem).filter(
            and_(StockItem.product_id == product_id, StockItem.size == size)
        ).first()
        
        if stock_item:
            stock_item.quantity += quantity_change
            
            # Record stock movement
            movement = StockMovement(
                product_id=product_id,
                size=size,
                movement_type=movement_type,
                quantity_change=quantity_change,
                reference_id=reference_id
            )
            self.db.add(movement)
            self.db.commit()
            self.db.refresh(stock_item)
            return stock_item
        return None

    def get_low_stock_items(self) -> List[StockItem]:
        return self.db.query(StockItem).filter(
            StockItem.quantity <= StockItem.reorder_level
        ).all()

    # Purchase Order Methods
    def create_purchase_order(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        # Create purchase order
        po_dict = po_data.dict(exclude={'items'})
        purchase_order = PurchaseOrder(**po_dict)
        self.db.add(purchase_order)
        self.db.flush()  # Get the ID without committing
        
        # Add items and calculate total
        total_amount = 0.0
        for item_data in po_data.items:
            item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                **item_data.dict(),
                total_cost=item_data.quantity_ordered * item_data.unit_cost
            )
            total_amount += item.total_cost
            self.db.add(item)
        
        purchase_order.total_amount = total_amount
        self.db.commit()
        self.db.refresh(purchase_order)
        return purchase_order

    def get_purchase_orders(self, status: Optional[str] = None) -> List[PurchaseOrder]:
        query = self.db.query(PurchaseOrder)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        return query.all()

    def get_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    def receive_purchase_order_item(self, po_id: str, item_id: str, quantity_received: int):
        item = self.db.query(PurchaseOrderItem).filter(
            and_(PurchaseOrderItem.purchase_order_id == po_id, PurchaseOrderItem.id == item_id)
        ).first()
        
        if item:
            item.quantity_received += quantity_received
            
            # Update stock
            self.update_stock_quantity(
                item.product_id, 
                item.size, 
                quantity_received, 
                "purchase", 
                po_id
            )
            
            self.db.commit()
            return item
        return None

    # Dashboard Methods
    def get_dashboard_stats(self):
        total_products = self.db.query(Product).count()
        total_stock_items = self.db.query(StockItem).count()
        low_stock_items = self.db.query(StockItem).filter(
            StockItem.quantity <= StockItem.reorder_level
        ).count()
        total_suppliers = self.db.query(Supplier).count()
        pending_orders = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.status == "pending"
        ).count()
        
        # Calculate inventory value
        inventory_value = self.db.query(
            func.sum(StockItem.quantity * Product.cost_price)
        ).join(Product).scalar() or 0.0
        
        return {
            "total_products": total_products,
            "total_stock_items": total_stock_items,
            "low_stock_items": low_stock_items,
            "total_suppliers": total_suppliers,
            "pending_orders": pending_orders,
            "total_inventory_value": float(inventory_value)
        }

    # ERP Integration
    async def sync_with_erp(self):
        """Sync inventory data with main ERP system"""
        try:
            async with httpx.AsyncClient() as client:
                # Get all products with stock
                products_with_stock = self.db.query(Product).join(StockItem).all()
                
                for product in products_with_stock:
                    stock_data = {
                        "product_id": product.id,
                        "name": product.name,
                        "total_quantity": sum([stock.quantity for stock in product.stock_items]),
                        "cost_price": product.cost_price,
                        "selling_price": product.selling_price
                    }
                    
                    # Send to ERP system
                    await client.post(
                        f"{settings.erp_api_url}/inventory/sync",
                        json=stock_data
                    )
        except Exception as e:
            print(f"ERP sync error: {e}")
            return False
        return True