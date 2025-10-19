"""
Add multiple sample categories
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_categories():
    """Add multiple sample categories for testing"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    categories = [
        ("Formal Shirts", "Business and formal dress shirts", "clothing"),
        ("Casual Pants", "Jeans and casual trousers", "numeric"),
        ("Dress Shoes", "Formal footwear", "shoe"),
        ("Suits & Blazers", "Formal suits and blazers", "clothing"),
        ("Accessories", "Ties, belts, and other accessories", "clothing")
    ]
    
    with engine.begin() as conn:
        try:
            logger.info("📦 Adding sample categories...")
            
            for name, description, size_type in categories:
                # Check if category already exists
                result = conn.execute(text("SELECT id FROM inventory.categories WHERE name = :name"), {"name": name})
                existing = result.fetchone()
                
                if existing:
                    logger.info(f"✅ Category '{name}' already exists")
                    continue
                
                # Insert new category
                result = conn.execute(text("""
                    INSERT INTO inventory.categories (id, name, description, size_type) 
                    VALUES (gen_random_uuid()::text, :name, :description, :size_type)
                    RETURNING id, name
                """), {"name": name, "description": description, "size_type": size_type})
                
                category = result.fetchone()
                logger.info(f"✅ Created category: {category[1]} (ID: {category[0]})")
            
            logger.info("🎉 Sample categories setup completed!")
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample categories: {str(e)}")
            raise

if __name__ == "__main__":
    add_sample_categories()