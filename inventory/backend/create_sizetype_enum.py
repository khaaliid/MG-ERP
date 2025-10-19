"""
Create missing sizetype enum in PostgreSQL
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sizetype_enum():
    """Create the missing sizetype enum in PostgreSQL"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("🔧 Creating missing sizetype enum...")
            
            # Check if the enum type already exists
            result = conn.execute(text("""
                SELECT typname FROM pg_type 
                WHERE typname = 'sizetype' 
                AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'inventory')
            """))
            
            if result.fetchone():
                logger.info("✅ sizetype enum already exists")
                return
            
            # Create the enum type in the inventory schema
            conn.execute(text("CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');"))
            logger.info("✅ Created sizetype enum with values: CLOTHING, NUMERIC, SHOE")
            
            # Now we need to update the column to use the enum type
            # First, let's see what type the column currently has
            result = conn.execute(text("""
                SELECT data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_schema = 'inventory' 
                AND table_name = 'categories' 
                AND column_name = 'size_type'
            """))
            
            column_info = result.fetchone()
            if column_info:
                logger.info(f"Current column type: {column_info[0]} ({column_info[1]})")
                
                # If it's not already the enum type, we need to convert it
                if column_info[1] != 'sizetype':
                    # Update existing data to match enum values
                    conn.execute(text("""
                        UPDATE inventory.categories 
                        SET size_type = 'CLOTHING' 
                        WHERE size_type IS NULL OR size_type = ''
                    """))
                    
                    # Convert the column to use the enum type
                    conn.execute(text("""
                        ALTER TABLE inventory.categories 
                        ALTER COLUMN size_type TYPE inventory.sizetype 
                        USING size_type::inventory.sizetype
                    """))
                    logger.info("✅ Converted size_type column to use enum type")
            
            logger.info("🎉 Sizetype enum creation completed!")
            
        except Exception as e:
            logger.error(f"❌ Failed to create sizetype enum: {str(e)}")
            raise

if __name__ == "__main__":
    create_sizetype_enum()