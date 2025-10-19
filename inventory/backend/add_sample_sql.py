"""
Add sample category using raw SQL
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_category_sql():
    """Add a sample category using raw SQL"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("📦 Adding sample category with raw SQL...")
            
            # Check if category already exists
            result = conn.execute(text("SELECT id FROM inventory.categories WHERE name = 'Test Shirts'"))
            existing = result.fetchone()
            
            if existing:
                logger.info("✅ Sample category 'Test Shirts' already exists")
                return existing[0]
            
            # Insert new category
            result = conn.execute(text("""
                INSERT INTO inventory.categories (id, name, description, size_type) 
                VALUES (gen_random_uuid()::text, 'Test Shirts', 'Sample category for testing', 'clothing')
                RETURNING id, name
            """))
            
            category = result.fetchone()
            logger.info(f"✅ Successfully created sample category: {category[1]} (ID: {category[0]})")
            return category[0]
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample category: {str(e)}")
            raise

if __name__ == "__main__":
    add_sample_category_sql()