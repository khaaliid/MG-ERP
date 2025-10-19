"""
Initialize the database with sample data for testing
"""
import logging
from sqlalchemy.orm import Session
from .database import get_database
from .models.inventory_models import Category, Brand, Supplier, SizeType

logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample categories, brands, and suppliers if they don't exist"""
    db = next(get_database())
    
    try:
        logger.info("🎯 Initializing sample data...")
        
        # Sample Categories
        categories_data = [
            {"name": "Shirts", "description": "Dress shirts and casual shirts", "size_type": SizeType.CLOTHING},
            {"name": "Pants", "description": "Trousers and casual pants", "size_type": SizeType.NUMERIC},
            {"name": "Shoes", "description": "Formal and casual footwear", "size_type": SizeType.SHOE},
            {"name": "Suits", "description": "Formal suits and blazers", "size_type": SizeType.CLOTHING},
            {"name": "Accessories", "description": "Ties, belts, and other accessories", "size_type": SizeType.CLOTHING}
        ]
        
        for cat_data in categories_data:
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                try:
                    category = Category(**cat_data)
                    db.add(category)
                    db.flush()  # Flush to catch any issues early
                    logger.info(f"✅ Created category: {cat_data['name']}")
                except Exception as e:
                    logger.error(f"❌ Failed to create category {cat_data['name']}: {str(e)}")
                    db.rollback()
                    raise
        
        # Sample Brands
        brands_data = [
            {"name": "Hugo Boss", "description": "Premium menswear brand"},
            {"name": "Calvin Klein", "description": "Modern American luxury"},
            {"name": "Tommy Hilfiger", "description": "Classic American style"},
            {"name": "Polo Ralph Lauren", "description": "Timeless American luxury"},
            {"name": "Brooks Brothers", "description": "Traditional American clothing"}
        ]
        
        for brand_data in brands_data:
            existing = db.query(Brand).filter(Brand.name == brand_data["name"]).first()
            if not existing:
                brand = Brand(**brand_data)
                db.add(brand)
                logger.info(f"✅ Created brand: {brand_data['name']}")
        
        # Sample Suppliers
        suppliers_data = [
            {"name": "Premium Textiles Ltd", "contact_person": "John Smith", "email": "john@premiumtextiles.com", "lead_time_days": 14},
            {"name": "Fashion Wholesale Co", "contact_person": "Sarah Johnson", "email": "sarah@fashionwholesale.com", "lead_time_days": 7},
            {"name": "Elite Garments", "contact_person": "Mike Wilson", "email": "mike@elitegarments.com", "lead_time_days": 10}
        ]
        
        for supplier_data in suppliers_data:
            existing = db.query(Supplier).filter(Supplier.name == supplier_data["name"]).first()
            if not existing:
                supplier = Supplier(**supplier_data)
                db.add(supplier)
                logger.info(f"✅ Created supplier: {supplier_data['name']}")
        
        db.commit()
        logger.info("🎉 Sample data initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error initializing sample data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()