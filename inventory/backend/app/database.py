from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models.inventory_models import Base
from .config import settings

# Create both sync and async engines
engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))  # Sync engine for initial setup
async_engine = create_async_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_database():
    async with AsyncSessionLocal() as session:
        yield session

async def create_schema_and_tables():
    """Create inventory schema and all tables"""
    import logging
    logger = logging.getLogger(__name__)
    
    async with async_engine.begin() as conn:
        # Create schema
        logger.info("[SCHEMA] Creating inventory schema...")
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS inventory;"))
        await conn.execute(text("GRANT ALL ON SCHEMA inventory TO mguser;"))
        logger.info("[SUCCESS] Inventory schema created or already exists")
        
        # Create enum types first
        logger.info("[ENUM] Creating sizetype enum...")
        await conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type t 
                    JOIN pg_namespace n ON t.typnamespace = n.oid 
                    WHERE t.typname = 'sizetype' AND n.nspname = 'inventory'
                ) THEN
                    CREATE TYPE inventory.sizetype AS ENUM ('CLOTHING', 'NUMERIC', 'SHOE');
                    RAISE NOTICE 'Created inventory.sizetype enum';
                ELSE
                    RAISE NOTICE 'inventory.sizetype enum already exists';
                END IF;
            END $$;
        """))
        logger.info("[SUCCESS] Sizetype enum processed")
        
        # Create tables
        logger.info("[TABLES] Creating inventory tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[SUCCESS] Inventory tables created")
        
        # Grant permissions
        await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA inventory TO mguser;"))
        await conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA inventory TO mguser;"))

def create_tables():
    """Legacy sync table creation - use create_schema_and_tables() instead"""
    Base.metadata.create_all(bind=engine)