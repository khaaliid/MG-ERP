"""
Check sample data in database
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_sample_data():
    """Check what sample data exists in the database"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("📊 Checking sample data...")
            
            # Check categories
            result = conn.execute(text("SELECT id, name, size_type FROM inventory.categories ORDER BY name"))
            categories = result.fetchall()
            logger.info(f"📦 Categories ({len(categories)}):")
            for cat in categories:
                logger.info(f"  - {cat[1]} (ID: {cat[0]}, Type: {cat[2]})")
            
            # Check brands
            result = conn.execute(text("SELECT id, name FROM inventory.brands ORDER BY name"))
            brands = result.fetchall()
            logger.info(f"🏷️ Brands ({len(brands)}):")
            for brand in brands:
                logger.info(f"  - {brand[1]} (ID: {brand[0]})")
            
            # Check suppliers
            result = conn.execute(text("SELECT id, name, lead_time_days FROM inventory.suppliers ORDER BY name"))
            suppliers = result.fetchall()
            logger.info(f"🚚 Suppliers ({len(suppliers)}):")
            for supplier in suppliers:
                logger.info(f"  - {supplier[1]} (ID: {supplier[0]}, Lead time: {supplier[2]} days)")
            
            logger.info("✅ Sample data check completed!")
            
        except Exception as e:
            logger.error(f"❌ Failed to check sample data: {str(e)}")
            raise

if __name__ == "__main__":
    check_sample_data()