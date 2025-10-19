"""
Add sample category to the database
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.inventory_models import Category, SizeType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_category():
    """Add a sample category to test the system"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        logger.info("📦 Adding sample category...")
        
        # Check if category already exists
        existing = db.query(Category).filter(Category.name == "Test Shirts").first()
        if existing:
            logger.info("✅ Sample category 'Test Shirts' already exists")
            return existing
        
        # Create new category
        category = Category(
            name="Test Shirts",
            description="Sample category for testing - dress shirts and casual shirts",
            size_type=SizeType.CLOTHING  # Use the enum directly, not .value
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        logger.info(f"✅ Successfully created sample category: {category.name} (ID: {category.id})")
        return category
        
    except Exception as e:
        logger.error(f"❌ Failed to create sample category: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_category()