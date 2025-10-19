from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_database
from ..services.inventory_service import InventoryService
import logging
import traceback

logger = logging.getLogger(__name__)
from ..schemas.inventory_schemas import (
    Category, CategoryCreate, CategoryUpdate,
    Brand, BrandCreate, BrandUpdate,
    Supplier, SupplierCreate, SupplierUpdate,
    Product, ProductCreate, ProductUpdate,
    StockItem, StockItemCreate, StockItemUpdate,
    PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate,
    StockMovement, StockMovementCreate,
    DashboardStats
)
import traceback

router = APIRouter()

# Category Routes
@router.post("/categories/", response_model=Category)
def create_category(category: CategoryCreate, db: Session = Depends(get_database)):
    logger.info(f"category: {category}")
    service = InventoryService(db)
    return service.create_category(category)

@router.get("/categories/", response_model=List[Category])
def get_categories(db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_categories()

@router.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: str, category: CategoryUpdate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    updated_category = service.update_category(category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category

@router.delete("/categories/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    if not service.delete_category(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# Brand Routes
@router.post("/brands/", response_model=Brand)
def create_brand(brand: BrandCreate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.create_brand(brand)

@router.get("/brands/", response_model=List[Brand])
def get_brands(db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_brands()

@router.get("/brands/{brand_id}", response_model=Brand)
def get_brand(brand_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    brand = service.get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.put("/brands/{brand_id}", response_model=Brand)
def update_brand(brand_id: str, brand: BrandUpdate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    updated_brand = service.update_brand(brand_id, brand)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated_brand

@router.delete("/brands/{brand_id}")
def delete_brand(brand_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    if not service.delete_brand(brand_id):
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"message": "Brand deleted successfully"}

# Supplier Routes
@router.post("/suppliers/", response_model=Supplier, response_model_by_alias=True)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.create_supplier(supplier)

@router.get("/suppliers/", response_model=List[Supplier], response_model_by_alias=True)
def get_suppliers(db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_suppliers()

@router.get("/suppliers/{supplier_id}", response_model=Supplier, response_model_by_alias=True)
def get_supplier(supplier_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.put("/suppliers/{supplier_id}", response_model=Supplier, response_model_by_alias=True)
def update_supplier(supplier_id: str, supplier: SupplierUpdate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    updated_supplier = service.update_supplier(supplier_id, supplier)
    if not updated_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return updated_supplier

@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    if not service.delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted successfully"}

# Product Routes
@router.post("/products/", response_model=Product, response_model_by_alias=True)
def create_product(product: ProductCreate, db: Session = Depends(get_database)):
    logger.info(f"🏭 Creating new product: {product.name}")
    logger.debug(f"📦 Product data: {product.dict()}")
    
    try:
        # Convert empty strings to None for foreign key fields
        # Use by_alias=True to preserve the original field names from frontend
        product_dict = product.dict(by_alias=True)
        if product_dict.get('brandId') == '':
            product_dict['brandId'] = None
        if product_dict.get('supplierId') == '':
            product_dict['supplierId'] = None
        if product_dict.get('categoryId') == '':
            product_dict['categoryId'] = None
            
        # Recreate the product object with cleaned data
        cleaned_product = ProductCreate(**product_dict)
        
        service = InventoryService(db)
        result = service.create_product(cleaned_product)
        logger.info(f"✅ Product created successfully with ID: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"❌ Validation error for product '{product.name}': {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid product data. Please check all required fields.")
    except Exception as e:
        logger.error(f"❌ Failed to create product '{product.name}': {str(e)}")
        logger.error(f"📍 Error details: {traceback.format_exc()}")
        
        # Provide user-friendly error messages
        if "foreign key constraint" in str(e).lower():
            if "category_id" in str(e):
                raise HTTPException(status_code=400, detail="Invalid category selected. Please choose a valid category.")
            elif "brand_id" in str(e):
                raise HTTPException(status_code=400, detail="Invalid brand selected. Please choose a valid brand or leave it empty.")
            elif "supplier_id" in str(e):
                raise HTTPException(status_code=400, detail="Invalid supplier selected. Please choose a valid supplier or leave it empty.")
            else:
                raise HTTPException(status_code=400, detail="Invalid reference data. Please check your selections.")
        elif "unique constraint" in str(e).lower():
            if "sku" in str(e).lower():
                raise HTTPException(status_code=400, detail="A product with this SKU already exists. Please use a different SKU.")
            else:
                raise HTTPException(status_code=400, detail="A product with this information already exists.")
        else:
            raise HTTPException(status_code=500, detail="Unable to create product. Please try again.")

@router.get("/products/")
def get_products(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    db: Session = Depends(get_database)
):
    service = InventoryService(db)
    products = service.get_products(category_id, brand_id)
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        products = [p for p in products if 
                   search_lower in (p.name or '').lower() or 
                   search_lower in (p.sku or '').lower() or 
                   search_lower in (p.description or '').lower()]
    
    # Apply pagination
    total = len(products)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_products = products[start_idx:end_idx]
    
    # Convert products to Pydantic models to ensure proper field aliasing
    from ..schemas.inventory_schemas import Product as ProductSchema
    converted_products = [ProductSchema.from_orm(product) for product in paginated_products]
    
    return {
        "data": [product.dict(by_alias=True) for product in converted_products],
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/products/{product_id}", response_model=Product, response_model_by_alias=True)
def get_product(product_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=Product, response_model_by_alias=True)
def update_product(product_id: str, product: ProductUpdate, db: Session = Depends(get_database)):
    try:
        service = InventoryService(db)
        updated_product = service.update_product(product_id, product)
        if not updated_product:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated_product
    except Exception as e:
        logger.error(f"❌ Failed to update product '{product_id}': {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Product not found")
        else:
            raise HTTPException(status_code=500, detail="Failed to update product. Please try again.")

@router.delete("/products/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_database)):
    try:
        service = InventoryService(db)
        if not service.delete_product(product_id):
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"❌ Failed to delete product '{product_id}': {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Product not found")
        else:
            raise HTTPException(status_code=500, detail="Failed to delete product. Please try again.")

# Stock Routes
@router.post("/stock/", response_model=StockItem)
def create_stock_item(stock_item: StockItemCreate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.create_stock_item(stock_item)

@router.get("/stock/", response_model=List[StockItem])
def get_stock_items(product_id: Optional[str] = None, db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_stock_items(product_id)

@router.get("/stock/low-stock", response_model=List[StockItem])
def get_low_stock_items(db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_low_stock_items()

@router.put("/stock/{product_id}/{size}/adjust")
def adjust_stock(
    product_id: str,
    size: str,
    quantity_change: int,
    reference_id: Optional[str] = None,
    db: Session = Depends(get_database)
):
    service = InventoryService(db)
    stock_item = service.update_stock_quantity(product_id, size, quantity_change, "adjustment", reference_id)
    if not stock_item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    return {"message": "Stock adjusted successfully", "new_quantity": stock_item.quantity}

# Purchase Order Routes
@router.post("/purchase-orders/", response_model=PurchaseOrder)
def create_purchase_order(purchase_order: PurchaseOrderCreate, db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.create_purchase_order(purchase_order)

@router.get("/purchase-orders/", response_model=List[PurchaseOrder])
def get_purchase_orders(status: Optional[str] = None, db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_purchase_orders(status)

@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrder)
def get_purchase_order(po_id: str, db: Session = Depends(get_database)):
    service = InventoryService(db)
    po = service.get_purchase_order(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@router.put("/purchase-orders/{po_id}/receive/{item_id}")
def receive_purchase_order_item(
    po_id: str,
    item_id: str,
    quantity_received: int,
    db: Session = Depends(get_database)
):
    service = InventoryService(db)
    item = service.receive_purchase_order_item(po_id, item_id, quantity_received)
    if not item:
        raise HTTPException(status_code=404, detail="Purchase order item not found")
    return {"message": "Items received successfully"}

# Dashboard Routes
@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_database)):
    service = InventoryService(db)
    return service.get_dashboard_stats()

@router.post("/sync/erp")
async def sync_with_erp(db: Session = Depends(get_database)):
    service = InventoryService(db)
    success = await service.sync_with_erp()
    if success:
        return {"message": "ERP sync completed successfully"}
    else:
        raise HTTPException(status_code=500, detail="ERP sync failed")