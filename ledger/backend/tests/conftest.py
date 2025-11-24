import pytest
import pytest_asyncio
import asyncio
import sys
import os
from pathlib import Path
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to Python path so we can import 'app'
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# IMPORTANT: Override database config BEFORE importing anything
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Import and patch the config module directly
from app import config
config.DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Patch the engine and session in config too
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create test engine and override config
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True
)

# Override the config engine
config.engine = test_engine

# Create test session factory
TestAsyncSession = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Override config SessionLocal
config.SessionLocal = TestAsyncSession

# Now import app components
from app.main import app
from app.dependencies import get_db
from app.services.ledger import Base

# Import all models to ensure they're registered with Base
from app.services.ledger import Account, Transaction, TransactionLine
# Note: Ledger uses external auth service - no local auth models needed

# Override the get_db dependency immediately
async def override_get_db():
    async with TestAsyncSession() as session:
        try:
            yield session
        finally:
            await session.close()

# Override before importing the app
app.dependency_overrides[get_db] = override_get_db

# Create tables immediately when module loads
async def setup_test_database():
    """Setup test database with all tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Run the async setup synchronously using asyncio
import asyncio

def run_async_setup():
    """Run async setup in a new event loop."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_test_database())
        loop.close()
    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise

# Execute database setup
run_async_setup()

# Now create the test client after everything is set up
client = TestClient(app)


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Setup test database - tables already created above."""
    yield
    # Cleanup
    await test_engine.dispose()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def admin_token():
    """Get admin token for authenticated requests."""
    try:
        # First, trigger system initialization
        response = client.get("/")
        print(f"Health check: {response.status_code}")
        assert response.status_code == 200
        
        # Login with admin credentials
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        
        print(f"Login response: {response.status_code}")
        if response.status_code != 200:
            print(f"Login error: {response.text}")
            
        assert response.status_code == 200
        token_data = response.json()
        return token_data["access_token"]
    except Exception as e:
        print(f"Error in admin_token fixture: {e}")
        raise


@pytest.fixture
def auth_headers(admin_token):
    """Generate authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}