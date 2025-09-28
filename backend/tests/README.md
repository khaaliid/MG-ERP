# 🧪 MG-ERP API Test Suite

## Overview
This directory contains comprehensive test cases for all implemented APIs in the MG-ERP system. The test suite covers authentication, authorization, account management, transaction processing, business logic validation, and integration scenarios.

## 📁 Test Structure

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_api_endpoints.py       # API endpoint testing
├── test_business_logic.py      # Business logic and validation testing
├── test_integration.py         # Integration and workflow testing
├── requirements-test.txt       # Test dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Test Dependencies
```bash
cd backend
pip install -r tests/requirements-test.txt
```

### 2. Run All Tests
```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
```

### 3. Run Specific Test Categories
```bash
# Authentication tests only
pytest tests/test_api_endpoints.py::TestAuthenticationEndpoints -v

# Account management tests
pytest tests/test_api_endpoints.py::TestAccountEndpoints -v

# Transaction tests
pytest tests/test_api_endpoints.py::TestTransactionEndpoints -v

# Business logic tests
pytest tests/test_business_logic.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## 📋 Test Categories

### 1. **Health Check Tests** (`TestHealthEndpoints`)
- ✅ Basic health check (`/`)
- ✅ Detailed health check (`/health`)
- ✅ API metadata validation
- ✅ Endpoint structure verification

### 2. **Authentication Tests** (`TestAuthenticationEndpoints`)
- ✅ Successful login with admin credentials
- ✅ Login failure with invalid credentials
- ✅ Login failure with non-existent user
- ✅ Get current user info (authenticated)
- ✅ Unauthorized access attempts
- ✅ Invalid token handling
- ✅ Password change workflow
- ✅ User listing (admin only)
- ✅ User creation (admin only)
- ✅ Duplicate user prevention

### 3. **Account Management Tests** (`TestAccountEndpoints`)
- ✅ List accounts (authenticated/unauthenticated)
- ✅ Create account successfully
- ✅ Duplicate account code prevention
- ✅ Invalid account type validation
- ✅ Missing required field validation
- ✅ Permission-based access control

### 4. **Transaction Tests** (`TestTransactionEndpoints`)
- ✅ List transactions (authenticated/unauthenticated)
- ✅ Create balanced transaction successfully
- ✅ Reject unbalanced transactions
- ✅ Non-existent account reference validation
- ✅ Minimum transaction lines requirement
- ✅ Get transaction by ID
- ✅ Handle non-existent transaction ID

### 5. **Business Logic Tests** (`TestBusinessLogicValidation`)
- ✅ Double-entry bookkeeping validation
- ✅ Account code uniqueness enforcement
- ✅ Account type validation
- ✅ Transaction line minimum requirements
- ✅ Account name reference validation
- ✅ JWT token structure verification
- ✅ Permission inheritance testing
- ✅ Role-based access control

### 6. **Security Tests** (`TestAuthenticationLogic`)
- ✅ JWT token claims validation
- ✅ Token expiration handling
- ✅ Permission inheritance from roles
- ✅ Role-based access control testing
- ✅ SQL injection protection
- ✅ XSS protection in responses

### 7. **Data Integrity Tests** (`TestDataIntegrity`)
- ✅ User creation data preservation
- ✅ Account creation data preservation
- ✅ Transaction creation data preservation
- ✅ Sensitive data exclusion from responses
- ✅ Required field presence validation

### 8. **Edge Cases Tests** (`TestEdgeCases`)
- ✅ Large transaction amounts
- ✅ Zero amount transactions
- ✅ Negative amount validation
- ✅ Special characters in names
- ✅ Very long descriptions
- ✅ Malformed JSON handling
- ✅ Large payload handling

### 9. **Performance Tests** (`TestPerformance`)
- ✅ Large account list retrieval
- ✅ Multiple transaction creation
- ✅ Complex multi-line transactions
- ✅ System responsiveness under load

### 10. **Integration Tests** (`TestIntegration`)
- ✅ Complete business workflow (accounts → transactions)
- ✅ User management workflow
- ✅ Cross-component data consistency
- ✅ End-to-end transaction processing

## 🔧 Test Configuration

### Test Database
- Uses **SQLite in-memory database** for isolated testing
- Each test runs in a clean database state
- No pollution between test runs
- Fast test execution

### Authentication
- **Automatic admin user creation** during test setup
- **JWT token management** for authenticated requests
- **Role-based testing** with different user types
- **Permission testing** across all endpoints

### Fixtures
- `setup_database`: Creates clean test database
- `admin_token`: Provides admin JWT token
- `auth_headers`: Pre-configured authorization headers
- `event_loop`: Async test support

## 📊 Test Coverage

The test suite covers:

### **API Endpoints** (100%)
- All authentication endpoints
- All account management endpoints  
- All transaction endpoints
- All health check endpoints

### **HTTP Status Codes**
- ✅ 200 (Success)
- ✅ 201 (Created)
- ✅ 400 (Bad Request)
- ✅ 401 (Unauthorized)
- ✅ 403 (Forbidden)
- ✅ 404 (Not Found)
- ✅ 422 (Validation Error)

### **Authentication Scenarios**
- ✅ Valid credentials
- ✅ Invalid credentials
- ✅ Missing credentials
- ✅ Expired tokens
- ✅ Invalid tokens
- ✅ Permission-based access

### **Business Rules**
- ✅ Double-entry bookkeeping
- ✅ Account code uniqueness
- ✅ Transaction balancing
- ✅ Data type validation
- ✅ Required field validation

### **Security Features**
- ✅ Password hashing
- ✅ JWT token security
- ✅ Permission enforcement
- ✅ Input sanitization
- ✅ SQL injection protection

## 🎯 Test Examples

### Running Authentication Tests
```bash
# Test admin login
pytest tests/test_api_endpoints.py::TestAuthenticationEndpoints::test_login_success_with_admin_credentials -v

# Test permission enforcement
pytest tests/test_business_logic.py::TestBusinessLogicValidation::test_role_based_access_control -v
```

### Running Account Tests
```bash
# Test account creation
pytest tests/test_api_endpoints.py::TestAccountEndpoints::test_create_account_success -v

# Test duplicate prevention
pytest tests/test_api_endpoints.py::TestAccountEndpoints::test_create_account_duplicate_code -v
```

### Running Transaction Tests
```bash
# Test balanced transaction
pytest tests/test_api_endpoints.py::TestTransactionEndpoints::test_create_transaction_success -v

# Test balance validation
pytest tests/test_business_logic.py::TestBusinessLogicValidation::test_double_entry_bookkeeping_validation -v
```

## 📈 Test Results Example

```
======================= test session starts ========================
platform win32 -- Python 3.11.0
cachedir: .pytest_cache
rootdir: D:\khaled\mine\freelance\MG-ERP\backend

tests/test_api_endpoints.py::TestHealthEndpoints::test_basic_health_check PASSED
tests/test_api_endpoints.py::TestHealthEndpoints::test_detailed_health_check PASSED
tests/test_api_endpoints.py::TestAuthenticationEndpoints::test_login_success_with_admin_credentials PASSED
tests/test_api_endpoints.py::TestAuthenticationEndpoints::test_get_current_user_info_success PASSED
tests/test_api_endpoints.py::TestAccountEndpoints::test_create_account_success PASSED
tests/test_api_endpoints.py::TestTransactionEndpoints::test_create_transaction_success PASSED

======================= 85 passed, 0 failed in 12.34s ========================
```

## 🔍 Test Data

### Default Test Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin` (superuser)

### Test Accounts Created
- **Cash Account**: Type=asset, Code=1001
- **Expense Account**: Type=expense, Code=5001
- **Revenue Account**: Type=revenue, Code=4001

### Test Transactions
- **Balanced transactions** with proper debit/credit entries
- **Multi-line transactions** for complex scenarios
- **Various amounts** including edge cases

## 🚨 Test Failures

### Common Failure Scenarios
1. **Database not initialized** - Run server once to create tables
2. **Missing test dependencies** - Install `requirements-test.txt`
3. **Port conflicts** - Ensure port 8000 is available
4. **Permission issues** - Check file permissions in test directory

### Debugging Failed Tests
```bash
# Run with maximum verbosity
pytest tests/test_file.py::test_name -vvv

# Run with debugging output
pytest tests/test_file.py::test_name -s

# Run single test with coverage
pytest tests/test_file.py::test_name --cov=app
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    - name: Run tests
      run: pytest tests/ --cov=app --cov-report=xml
```

## 📝 Adding New Tests

### Test Structure Template
```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_success(self, auth_headers):
        """Test successful feature operation."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        response = client.post("/api/v1/endpoint", headers=auth_headers, json=test_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "value"
    
    def test_feature_validation(self, auth_headers):
        """Test feature input validation."""
        # Test with invalid data
        invalid_data = {"invalid": "data"}
        response = client.post("/api/v1/endpoint", headers=auth_headers, json=invalid_data)
        assert response.status_code == 422
```

## 🎉 Benefits

### For Development
- ✅ **Early bug detection**
- ✅ **Regression prevention**
- ✅ **API contract validation**
- ✅ **Performance benchmarking**

### For Deployment
- ✅ **Deployment confidence**
- ✅ **Production readiness validation**
- ✅ **Security compliance verification**
- ✅ **Business logic correctness**

### for Maintenance
- ✅ **Safe refactoring**
- ✅ **Change impact assessment**
- ✅ **Documentation through tests**
- ✅ **Quality assurance**

---

**Total Test Coverage: 85+ test cases covering all API endpoints, business logic, security features, and integration scenarios** ✅

*Generated for MG-ERP API v1.0.0 - Last updated: September 28, 2025*