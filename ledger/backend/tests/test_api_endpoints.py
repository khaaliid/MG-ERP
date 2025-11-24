import pytest
from fastapi.testclient import TestClient
import json

from tests.conftest import client, auth_headers, admin_token


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health_check(self):
        """Test basic health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "MG-ERP Ledger API is running"
        assert data["version"] == "1.0.0"

    def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "MG-ERP Ledger API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "documentation" in data
        assert "default_credentials" in data
        
        # Check endpoint structure
        endpoints = data["endpoints"]
        assert endpoints["authentication"] == "/api/v1/auth"
        assert endpoints["accounts"] == "/api/v1/accounts"
        assert data["endpoints"]["transactions"] == "/api/v1/transactions"


@pytest.mark.skip(reason="Ledger uses external auth service - no local auth endpoints")
class TestAuthenticationEndpoints:
    """Test authentication and authorization endpoints.
    
    NOTE: Ledger service uses external auth. These endpoints don't exist locally.
    """

    def test_login_success_with_admin_credentials(self):
        """Test successful login with admin credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50  # JWT tokens are long

    def test_login_failure_with_invalid_credentials(self):
        """Test login failure with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid username or password"

    def test_login_failure_with_nonexistent_user(self):
        """Test login failure with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid username or password"

    def test_get_current_user_info_success(self, auth_headers):
        """Test getting current user info with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["email"] == "admin@mgledger.com"
        assert data["full_name"] == "System Administrator"
        assert data["is_active"] == True
        assert data["is_superuser"] == True
        assert data["role"] == "admin"
        assert isinstance(data["permissions"], list)
        assert len(data["permissions"]) > 0

    def test_get_current_user_info_unauthorized(self):
        """Test getting current user info without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403

    def test_get_current_user_info_invalid_token(self):
        """Test getting current user info with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_change_password_success(self, auth_headers):
        """Test successful password change."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "admin123",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"
        
        # Test login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200
        
        # Change back to original password for other tests
        new_token = login_response.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        
        client.post(
            "/api/v1/auth/change-password",
            headers=new_headers,
            json={
                "current_password": "newpassword123",
                "new_password": "admin123"
            }
        )

    def test_change_password_wrong_current_password(self, auth_headers):
        """Test password change with wrong current password."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Invalid current password"

    def test_list_users_as_admin(self, auth_headers):
        """Test listing users as admin."""
        response = client.get("/api/v1/auth/users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least admin user
        
        # Check admin user in list
        admin_user = next((user for user in data if user["username"] == "admin"), None)
        assert admin_user is not None
        assert admin_user["email"] == "admin@mgledger.com"
        assert admin_user["is_superuser"] == True

    def test_create_user_as_admin(self, auth_headers):
        """Test creating a new user as admin."""
        new_user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "testpassword123",
            "role": "viewer"
        }
        
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_headers,
            json=new_user_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] == True
        
        # Test login with new user
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test_user",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200

    def test_create_user_duplicate_username(self, auth_headers):
        """Test creating user with duplicate username."""
        new_user_data = {
            "username": "admin",  # Already exists
            "email": "admin2@example.com",
            "full_name": "Admin Two",
            "password": "testpassword123",
            "role": "viewer"
        }
        
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_headers,
            json=new_user_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()


class TestAccountEndpoints:
    """Test account management endpoints."""

    def test_list_accounts_authenticated(self, auth_headers):
        """Test listing accounts with authentication."""
        response = client.get("/api/v1/accounts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_accounts_unauthenticated(self):
        """Test listing accounts without authentication."""
        response = client.get("/api/v1/accounts")
        
        assert response.status_code == 403

    def test_create_account_success(self, auth_headers):
        """Test creating a new account successfully."""
        account_data = {
            "name": "Test Cash Account",
            "type": "asset",
            "code": "1001",
            "description": "Test cash account for unit tests",
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/accounts",
            headers=auth_headers,
            json=account_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Cash Account"
        assert data["type"] == "asset"
        assert data["code"] == "1001"
        assert data["description"] == "Test cash account for unit tests"
        assert data["is_active"] == True
        assert "id" in data

    def test_create_account_duplicate_code(self, auth_headers):
        """Test creating account with duplicate code."""
        account_data = {
            "name": "Duplicate Code Account",
            "type": "asset",
            "code": "1001",  # Same as previous test
            "description": "This should fail due to duplicate code"
        }
        
        response = client.post(
            "/api/v1/accounts",
            headers=auth_headers,
            json=account_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower() or "duplicate" in data["detail"].lower()

    def test_create_account_invalid_type(self, auth_headers):
        """Test creating account with invalid type."""
        account_data = {
            "name": "Invalid Type Account",
            "type": "invalid_type",
            "code": "9999",
            "description": "This should fail due to invalid type"
        }
        
        response = client.post(
            "/api/v1/accounts",
            headers=auth_headers,
            json=account_data
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_account_missing_required_fields(self, auth_headers):
        """Test creating account with missing required fields."""
        account_data = {
            "name": "Incomplete Account",
            # Missing type and code
        }
        
        response = client.post(
            "/api/v1/accounts",
            headers=auth_headers,
            json=account_data
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_account_unauthenticated(self):
        """Test creating account without authentication."""
        account_data = {
            "name": "Unauthorized Account",
            "type": "asset",
            "code": "2001",
            "description": "Should fail without auth"
        }
        
        response = client.post("/api/v1/accounts", json=account_data)
        assert response.status_code == 403


class TestTransactionEndpoints:
    """Test transaction management endpoints."""

    def test_list_transactions_authenticated(self, auth_headers):
        """Test listing transactions with authentication."""
        response = client.get("/api/v1/transactions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_transactions_unauthenticated(self):
        """Test listing transactions without authentication."""
        response = client.get("/api/v1/transactions")
        
        assert response.status_code == 403

    def test_create_transaction_success(self, auth_headers):
        """Test creating a balanced transaction successfully."""
        # First create necessary accounts
        cash_account = {
            "name": "Test Cash",
            "type": "asset", 
            "code": "1100",
            "description": "Cash account for transaction test"
        }
        client.post("/api/v1/accounts", headers=auth_headers, json=cash_account)
        
        expense_account = {
            "name": "Test Expense",
            "type": "expense",
            "code": "5100", 
            "description": "Expense account for transaction test"
        }
        client.post("/api/v1/accounts", headers=auth_headers, json=expense_account)
        
        # Create transaction
        transaction_data = {
            "description": "Test transaction for unit tests",
            "source": "manual",
            "reference": "TEST-001",
            "lines": [
                {
                    "account_name": "Test Expense",
                    "type": "debit",
                    "amount": 500.00
                },
                {
                    "account_name": "Test Cash",
                    "type": "credit", 
                    "amount": 500.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Test transaction for unit tests"
        assert data["source"] == "manual"
        assert data["reference"] == "TEST-001"
        assert len(data["lines"]) == 2
        assert "id" in data

    def test_create_transaction_unbalanced(self, auth_headers):
        """Test creating unbalanced transaction (should fail)."""
        transaction_data = {
            "description": "Unbalanced transaction",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit",
                    "amount": 100.00
                },
                {
                    "account_name": "Test Expense", 
                    "type": "credit",
                    "amount": 200.00  # Different amount - unbalanced
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "balance" in data["detail"].lower() or "equal" in data["detail"].lower()

    def test_create_transaction_nonexistent_account(self, auth_headers):
        """Test creating transaction with non-existent account."""
        transaction_data = {
            "description": "Transaction with non-existent account",
            "lines": [
                {
                    "account_name": "Non Existent Account",
                    "type": "debit",
                    "amount": 100.00
                },
                {
                    "account_name": "Test Cash",
                    "type": "credit",
                    "amount": 100.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["detail"].lower() or "does not exist" in data["detail"].lower()

    def test_create_transaction_single_line(self, auth_headers):
        """Test creating transaction with only one line (should fail)."""
        transaction_data = {
            "description": "Single line transaction",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit", 
                    "amount": 100.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        assert response.status_code == 422 or response.status_code == 400

    def test_create_transaction_unauthenticated(self):
        """Test creating transaction without authentication."""
        transaction_data = {
            "description": "Unauthorized transaction",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit",
                    "amount": 100.00
                },
                {
                    "account_name": "Test Expense",
                    "type": "credit",
                    "amount": 100.00
                }
            ]
        }
        
        response = client.post("/api/v1/transactions", json=transaction_data)
        assert response.status_code == 403

    def test_get_transaction_by_id(self, auth_headers):
        """Test getting transaction by ID."""
        # Create a transaction first
        transaction_data = {
            "description": "Transaction for ID test",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit",
                    "amount": 250.00
                },
                {
                    "account_name": "Test Expense",
                    "type": "credit",
                    "amount": 250.00
                }
            ]
        }
        
        create_response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        assert create_response.status_code == 200
        transaction_id = create_response.json()["id"]
        
        # Get transaction by ID
        response = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
        assert data["description"] == "Transaction for ID test"

    def test_get_transaction_by_nonexistent_id(self, auth_headers):
        """Test getting transaction with non-existent ID."""
        response = client.get("/api/v1/transactions/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Transaction not found"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_large_transaction_amounts(self, auth_headers):
        """Test transaction with large amounts."""
        transaction_data = {
            "description": "Large amount transaction",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit",
                    "amount": 999999999.99
                },
                {
                    "account_name": "Test Expense",
                    "type": "credit",
                    "amount": 999999999.99
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["lines"][0]["amount"] == 999999999.99

    def test_zero_amount_transaction(self, auth_headers):
        """Test transaction with zero amounts."""
        transaction_data = {
            "description": "Zero amount transaction",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit",
                    "amount": 0.00
                },
                {
                    "account_name": "Test Expense",
                    "type": "credit",
                    "amount": 0.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        # This might fail due to validation rules
        assert response.status_code in [200, 400, 422]

    def test_negative_amount_transaction(self, auth_headers):
        """Test transaction with negative amounts."""
        transaction_data = {
            "description": "Negative amount transaction",
            "lines": [
                {
                    "account_name": "Test Cash",
                    "type": "debit",
                    "amount": -100.00
                },
                {
                    "account_name": "Test Expense",
                    "type": "credit",
                    "amount": -100.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json=transaction_data
        )
        
        # Should fail due to validation
        assert response.status_code in [400, 422]

    def test_special_characters_in_names(self, auth_headers):
        """Test accounts and transactions with special characters."""
        account_data = {
            "name": "Test Account with Special Chars: !@#$%^&*()",
            "type": "asset",
            "code": "SPEC-001",
            "description": "Testing special characters: äöüß€£¥"
        }
        
        response = client.post(
            "/api/v1/accounts",
            headers=auth_headers,
            json=account_data
        )
        
        # Should handle special characters gracefully
        assert response.status_code in [200, 400]

    def test_very_long_descriptions(self, auth_headers):
        """Test with very long descriptions."""
        long_description = "A" * 1000  # 1000 character description
        
        account_data = {
            "name": "Long Description Account",
            "type": "asset",
            "code": "LONG-001",
            "description": long_description
        }
        
        response = client.post(
            "/api/v1/accounts",
            headers=auth_headers,
            json=account_data
        )
        
        # Should handle or reject appropriately
        assert response.status_code in [200, 400, 422]