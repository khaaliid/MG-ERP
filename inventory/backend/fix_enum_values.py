"""
Fix enum values in database to match SQLAlchemy expectations
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_enum_values():
    """Update database to use uppercase enum values"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    with engine.begin() as conn:
        try:
            logger.info("🔧 Fixing enum values in database...")
            
            # Drop existing enum and table
            conn.execute(text("DROP TABLE IF EXISTS inventory.categories CASCADE;"))
            conn.execute(text("DROP TYPE IF EXISTS inventory.sizetype CASCADE;"))
            logger.info("✅ Dropped existing table and enum")
            
            # Recreate enum with uppercase values
            conn.execute(text("CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');"))
            logger.info("✅ Recreated enum with uppercase values")
            
            # Recreate categories table
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
            
            # Add sample data with uppercase enum values
            categories = [
                ("Formal Shirts", "Business and formal dress shirts", "CLOTHING"),
                ("Casual Pants", "Jeans and casual trousers", "NUMERIC"),
                ("Dress Shoes", "Formal footwear", "SHOE"),
                ("Suits & Blazers", "Formal suits and blazers", "CLOTHING"),
                ("Accessories", "Ties, belts, and other accessories", "CLOTHING")
            ]
            
            for name, description, size_type in categories:
                conn.execute(text("""
                    INSERT INTO inventory.categories (id, name, description, size_type) 
                    VALUES (gen_random_uuid()::text, :name, :description, :size_type)
                """), {"name": name, "description": description, "size_type": size_type})
                logger.info(f"✅ Added category: {name}")
            
            logger.info("🎉 Enum fix completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Enum fix failed: {str(e)}")
            raise

if __name__ == "__main__":
    fix_enum_values()