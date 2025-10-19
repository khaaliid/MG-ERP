"""
Add missing size_type column to categories table
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_size_type_column():
    """Add the missing size_type column to categories table"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("🔧 Adding missing size_type column...")
            
            # First, create the enum type if it doesn't exist
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sizetype') THEN
                        CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');
                    END IF;
                END $$;
            """))
            logger.info("✅ Ensured sizetype enum exists")
            
            # Check if the column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'inventory' 
                AND table_name = 'categories' 
                AND column_name = 'size_type'
            """))
            
            if result.fetchone():
                logger.info("✅ size_type column already exists")
                return
            
            # Add the size_type column
            conn.execute(text("""
                ALTER TABLE inventory.categories 
                ADD COLUMN size_type inventory.sizetype DEFAULT 'CLOTHING'
            """))
            logger.info("✅ Added size_type column to categories table")
            
            # Update existing rows to have a default value
            conn.execute(text("""
                UPDATE inventory.categories 
                SET size_type = 'CLOTHING' 
                WHERE size_type IS NULL
            """))
            logger.info("✅ Updated existing categories with default size_type")
            
            logger.info("🎉 Size type column addition completed!")
            
        except Exception as e:
            logger.error(f"❌ Failed to add size_type column: {str(e)}")
            raise

if __name__ == "__main__":
    add_size_type_column()