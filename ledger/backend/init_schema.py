"""
Schema initialization for MG-ERP Ledger service
Creates the ledger schema in the mgerp database
"""
from sqlalchemy import text
from app.config import engine
import asyncio
import logging

logger = logging.getLogger(__name__)

async def create_schema():
    """Create the ledger schema if it doesn't exist"""
    async with engine.begin() as conn:
        # Create schema
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS ledger;"))
        logger.info("Schema 'ledger' created or already exists")
        
        # Grant permissions to mguser
        await conn.execute(text("GRANT ALL ON SCHEMA ledger TO mguser;"))
        await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA ledger TO mguser;"))
        await conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA ledger TO mguser;"))
        logger.info("Permissions granted to mguser on ledger schema")

async def initialize_database():
    """Initialize database schema and tables"""
    try:
        # Create schema first
        await create_schema()
        
        # Import models to ensure they're registered
        from app.services.ledger import Base
        # Note: Ledger uses external auth service via HTTP - no local auth models
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("All tables created successfully in ledger schema")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_database())