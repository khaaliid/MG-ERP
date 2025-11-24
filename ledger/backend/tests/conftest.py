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
# Use PostgreSQL if DATABASE_URL is provided (CI), otherwise use SQLite (local)
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Import and patch the config module directly
from app import config
config.DATABASE_URL = TEST_DATABASE_URL

# Patch the engine and session in config too
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Determine if we're using PostgreSQL or SQLite
is_postgres = TEST_DATABASE_URL.startswith("postgresql")

# Create test engine and override config
# For PostgreSQL, use NullPool to avoid connection pool issues in tests
# For SQLite, use default pooling
engine_kwargs = {
    "echo": False,
    "future": True,
}

if is_postgres:
    from sqlalchemy.pool import NullPool
    engine_kwargs["poolclass"] = NullPool

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    **engine_kwargs
)

# Override the config engine
config.engine = test_engine

# Create test session factory
TestAsyncSession = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
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

# Patch schema for SQLite only (SQLite doesn't support PostgreSQL schemas)
if not is_postgres:
    import app.services.ledger as ledger_module
    ledger_module.SCHEMA_NAME = None
    
    # Remove schema from all table args for SQLite compatibility
    for table in Base.metadata.tables.values():
        if hasattr(table, 'schema'):
            table.schema = None

# Create tables immediately when module loads
async def setup_test_database():
    """Setup test database with all tables."""
    async with test_engine.begin() as conn:
        # For PostgreSQL, create schema first
        if is_postgres:
            from sqlalchemy import text
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS ledger"))
        
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


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_session():
    """Create a new database session for each test with cleanup.
    
    This fixture is autouse=True so every test gets a clean database.
    """
    # Clean up BEFORE test to ensure clean state
    try:
        async with test_engine.begin() as conn:
            if is_postgres:
                from sqlalchemy import text
                await conn.execute(text("TRUNCATE TABLE ledger.transaction_lines CASCADE"))
                await conn.execute(text("TRUNCATE TABLE ledger.transactions CASCADE"))
                await conn.execute(text("TRUNCATE TABLE ledger.accounts CASCADE"))
            else:
                from sqlalchemy import text
                await conn.execute(text("DELETE FROM transaction_lines"))
                await conn.execute(text("DELETE FROM transactions"))
                await conn.execute(text("DELETE FROM accounts"))
    except Exception as e:
        # On first run, tables might not exist yet
        pass
    
    # Provide session for test
    async with TestAsyncSession() as session:
        yield session
        # Rollback any uncommitted changes
        try:
            await session.rollback()
        except:
            pass
        finally:
            await session.close()


# Override the get_db dependency to use per-test session
async def override_get_db():
    """Override database dependency with test session."""
    async with TestAsyncSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

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
def mock_current_user():
    """Mock user data for tests (simulates authenticated user from external auth)."""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "admin",
        "permissions": ["read", "write", "delete"]
    }


@pytest.fixture
def admin_token():
    """Mock admin token for authenticated requests.
    
    Note: Ledger uses external auth service. In tests, we mock the auth
    by overriding the get_current_user dependency.
    """
    # Return a dummy token - the actual validation is mocked
    return "mock_test_token_12345"


@pytest.fixture
def auth_headers(admin_token):
    """Generate authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def authenticated(mock_current_user):
    """Override the authentication dependency for tests that need authentication.
    
    Use this fixture in tests that should be authenticated.
    Tests without this fixture will require actual authentication.
    """
    from app.external_auth import get_current_user
    
    async def mock_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def auto_authenticated(request, mock_current_user):
    """Automatically authenticate tests unless they're testing unauthenticated access.
    
    Tests can opt-out by using the marker: @pytest.mark.unauthenticated
    """
    # Check if test is marked as unauthenticated or has "unauthenticated" in name
    test_name = request.node.name.lower()
    if 'unauthenticated' in request.keywords or 'unauthenticated' in test_name or 'unauthorized' in test_name:
        # Don't mock auth for unauthenticated tests
        yield
        return
    
    from app.external_auth import get_current_user
    
    async def mock_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()