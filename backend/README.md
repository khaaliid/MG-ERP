# Backend for MG-ERP Ledger

This folder contains the FastAPI backend for the ledger module with enterprise-grade features including authentication, authorization, comprehensive testing, and professional API documentation.

## Features
- ✅ **FastAPI** - Modern async web framework with automatic API documentation
- ✅ **SQLAlchemy 2.0** - Async ORM with declarative models
- ✅ **PostgreSQL** - Production-ready database with async support
- ✅ **JWT Authentication** - Secure token-based authentication system
- ✅ **Role-Based Access Control** - Granular permissions and user roles
- ✅ **Comprehensive Testing** - 85+ test cases with full coverage
- ✅ **Professional Documentation** - Enhanced Swagger UI with examples
- ✅ **Logging System** - Structured logging with business context

## Quick Start

### 1. Environment Setup
```powershell
# Create virtual environment
py -m venv venv

# Activate environment (Windows)
.\venv\Scripts\activate

# Activate environment (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration
Configure PostgreSQL connection in `app/config.py` or use environment variables:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mg_erp
```

### 3. Run the Server
```bash
# Development server with hot reload
uvicorn app.main:app --reload

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access the API
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Testing

We provide comprehensive testing with 85+ test cases covering all functionality. Tests are organized into three main categories:

### Test Categories
- **API Endpoints** - Testing all REST API endpoints
- **Business Logic** - Double-entry bookkeeping and validation rules  
- **Integration** - End-to-end workflows and performance tests

### Quick Test Commands

#### Windows (PowerShell)
```powershell
# Run all tests with coverage
.\run_tests.ps1 -Coverage

# Run specific test categories
.\run_tests.ps1 -Endpoints           # API endpoint tests only
.\run_tests.ps1 -Business            # Business logic tests only
.\run_tests.ps1 -Integration         # Integration tests only

# Advanced options
.\run_tests.ps1 -Verbose             # Detailed output
.\run_tests.ps1 -Fast -Coverage      # Parallel execution with coverage
.\run_tests.ps1 -Specific "test_health"  # Run specific test
```

#### Linux/macOS (Bash)
```bash
# Make script executable (first time only)
chmod +x run_tests.sh

# Run all tests with coverage
./run_tests.sh -c

# Run specific test categories
./run_tests.sh -e                   # API endpoint tests only
./run_tests.sh -b                   # Business logic tests only
./run_tests.sh -i                   # Integration tests only

# Advanced options
./run_tests.sh -v                   # Verbose output
./run_tests.sh -f -c                # Fast parallel execution with coverage
./run_tests.sh -s test_health       # Run specific test
```

#### Direct pytest Commands
```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run specific test function
pytest tests/test_api_endpoints.py::test_health_check -v

# Run tests matching pattern
pytest -k "test_auth" -v
```

### Test Configuration
- **Test Database**: Isolated SQLite database for each test run
- **Coverage Reports**: HTML reports generated in `htmlcov/`
- **Async Support**: Full async/await testing with pytest-asyncio
- **Auto Cleanup**: Automatic database cleanup between tests

### Coverage Reports
After running tests with coverage, open the HTML report:
```bash
# Open coverage report (Windows)
start htmlcov/index.html

# Open coverage report (macOS)
open htmlcov/index.html

# Open coverage report (Linux)
xdg-open htmlcov/index.html
```

## API Documentation

The API includes comprehensive documentation with examples:

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin` (full access)

### Authentication Flow
1. **Login**: POST `/auth/login` with username/password
2. **Get Token**: Receive JWT access and refresh tokens
3. **Use Token**: Include `Authorization: Bearer <token>` in headers
4. **Refresh**: POST `/auth/refresh` when token expires

### Key Endpoints
- **Health**: `GET /health` - System health check
- **Authentication**: `POST /auth/login`, `/auth/register`, `/auth/refresh`
- **Accounts**: `GET|POST /accounts/` - Chart of accounts management
- **Transactions**: `GET|POST /transactions/` - Double-entry bookkeeping

### Permission System
- **admin**: Full system access
- **manager**: Account and transaction management
- **accountant**: Transaction entry and reporting
- **viewer**: Read-only access

## Development

### Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Database and app configuration
│   ├── dependencies.py     # Shared dependencies
│   ├── logging_config.py   # Logging configuration
│   ├── api/                 # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── accounts.py      # Account management
│   │   ├── transactions.py  # Transaction management
│   │   └── router.py        # Route aggregation
│   ├── auth/                # Authentication system
│   │   ├── models.py        # User/Role/Permission models
│   │   ├── schemas.py       # Pydantic validation models
│   │   ├── security.py      # JWT and password handling
│   │   ├── service.py       # Authentication business logic
│   │   ├── dependencies.py  # Auth middleware
│   │   └── init.py          # System initialization
│   ├── schemas/             # API data models
│   │   └── schemas.py       # Request/response models
│   └── services/            # Business logic
│       └── ledger.py        # Ledger and accounting logic
├── tests/                   # Test suite
│   ├── conftest.py          # Test configuration
│   ├── test_api_endpoints.py    # API endpoint tests
│   ├── test_business_logic.py   # Business logic tests
│   └── test_integration.py     # Integration tests
├── run_tests.ps1           # PowerShell test runner
├── run_tests.sh            # Bash test runner
├── requirements.txt        # Python dependencies
└── pytest.ini             # Test configuration
```

### Running in Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --log-level debug

# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/ -- --cov=app
```

### Code Quality
- **Type Hints**: Full type annotation coverage
- **Async/Await**: Modern async patterns throughout
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging with business context
- **Testing**: 85+ test cases with comprehensive coverage
- **Documentation**: Rich API documentation with examples

## Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
JWT_SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Production Considerations
- Change default admin password
- Configure proper JWT secret keys
- Set up HTTPS/TLS
- Configure rate limiting
- Set up monitoring and alerting
- Use proper database connection pooling

## Support

For issues and questions:
1. Check the test suite for usage examples
2. Review API documentation at `/docs`
3. Examine the comprehensive logging output
4. Run specific test categories to isolate issues
