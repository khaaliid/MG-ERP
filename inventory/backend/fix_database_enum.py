"""
Fix database enum to match SQLAlchemy model
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_enum():
    """Fix the enum values in the database to match the Python model"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("🔧 Fixing database enum to match Python model...")
            
            # Drop the existing table and enum
            conn.execute(text("DROP TABLE IF EXISTS inventory.categories CASCADE;"))
            logger.info("✅ Dropped categories table")
            
            conn.execute(text("DROP TYPE IF EXISTS inventory.sizetype CASCADE;"))
            logger.info("✅ Dropped sizetype enum")
            
            # Create enum with uppercase values to match Python enum
            conn.execute(text("CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');"))
            logger.info("✅ Created sizetype enum with uppercase values")
            
            # Recreate the categories table
            conn.execute(text("""
                CREATE TABLE inventory.categories (
                    id character varying NOT NULL,
                    name character varying(100) NOT NULL,
                    description text,
                    size_type inventory.sizetype DEFAULT 'CLOTHING',
                    created_at timestamp without time zone DEFAULT now(),
                    updated_at timestamp without time zone DEFAULT now(),
                    PRIMARY KEY (id),
                    UNIQUE (name)
                );
            """))
            logger.info("✅ Recreated categories table")
            
            # Grant permissions
            conn.execute(text("GRANT ALL ON inventory.categories TO mguser;"))
            logger.info("✅ Granted permissions")
            
            logger.info("🎉 Database enum fix completed!")
            
        except Exception as e:
            logger.error(f"❌ Database enum fix failed: {str(e)}")
            raise

if __name__ == "__main__":
    fix_database_enum()