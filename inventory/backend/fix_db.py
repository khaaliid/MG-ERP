"""
Database repair script to fix enum issues
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """Fix database enum issues"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("🔧 Fixing database enum issues...")
            
            # Drop existing enum if it exists
            conn.execute(text("DROP TYPE IF EXISTS inventory.sizetype CASCADE;"))
            logger.info("✅ Dropped existing sizetype enum")
            
            # Recreate the enum
            conn.execute(text("CREATE TYPE inventory.sizetype AS ENUM ('clothing', 'numeric', 'shoe');"))
            logger.info("✅ Recreated sizetype enum")
            
            # Drop and recreate categories table to use the new enum
            conn.execute(text("DROP TABLE IF EXISTS inventory.categories CASCADE;"))
            logger.info("✅ Dropped categories table")
            
            # Recreate categories table
            conn.execute(text("""
                CREATE TABLE inventory.categories (
                    id character varying NOT NULL,
                    name character varying(100) NOT NULL,
                    description text,
                    size_type inventory.sizetype DEFAULT 'clothing',
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
            
            logger.info("🎉 Database repair completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database repair failed: {str(e)}")
            raise

if __name__ == "__main__":
    fix_database()