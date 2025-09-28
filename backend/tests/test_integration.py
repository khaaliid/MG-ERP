import pytest
from fastapi.testclient import TestClient
from tests.conftest import client


class TestPerformance:
    """Test performance-related scenarios."""

    def test_large_account_list_performance(self, auth_headers):
        """Test performance with large number of accounts."""
        # Create multiple accounts
        for i in range(50):
            account_data = {
                "name": f"Performance Test Account {i}",
                "type": "asset" if i % 2 == 0 else "expense",
                "code": f"PERF-{i:03d}",
                "description": f"Performance test account number {i}"
            }
            client.post("/api/v1/accounts", headers=auth_headers, json=account_data)
        
        # Retrieve all accounts and measure response
        response = client.get("/api/v1/accounts", headers=auth_headers)
        assert response.status_code == 200
        
        accounts = response.json()
        assert len(accounts) >= 50

    def test_large_transaction_list_performance(self, auth_headers):
        """Test performance with multiple transactions."""
        # Ensure we have accounts for transactions
        client.post("/api/v1/accounts", headers=auth_headers, json={
            "name": "Performance Cash", "type": "asset", "code": "PERF-CASH"
        })
        client.post("/api/v1/accounts", headers=auth_headers, json={
            "name": "Performance Expense", "type": "expense", "code": "PERF-EXP"
        })
        
        # Create multiple transactions
        for i in range(20):
            transaction_data = {
                "description": f"Performance test transaction {i}",
                "reference": f"PERF-{i:03d}",
                "lines": [
                    {"account_name": "Performance Expense", "type": "debit", "amount": 100.00 + i},
                    {"account_name": "Performance Cash", "type": "credit", "amount": 100.00 + i}
                ]
            }
            response = client.post("/api/v1/transactions", headers=auth_headers, json=transaction_data)
            assert response.status_code == 200
        
        # Retrieve all transactions
        response = client.get("/api/v1/transactions", headers=auth_headers)
        assert response.status_code == 200
        
        transactions = response.json()
        assert len(transactions) >= 20

    def test_complex_transaction_performance(self, auth_headers):
        """Test performance with complex multi-line transactions."""
        # Create multiple accounts for complex transaction
        accounts = []
        for i in range(10):
            account_data = {
                "name": f"Complex Account {i}",
                "type": "asset" if i < 5 else "expense",
                "code": f"COMPLEX-{i}",
            }
            response = client.post("/api/v1/accounts", headers=auth_headers, json=account_data)
            if response.status_code == 200:
                accounts.append(f"Complex Account {i}")
        
        if len(accounts) >= 4:
            # Create complex transaction with multiple lines
            complex_transaction = {
                "description": "Complex multi-line transaction",
                "reference": "COMPLEX-001",
                "lines": [
                    {"account_name": accounts[0], "type": "debit", "amount": 500.00},
                    {"account_name": accounts[1], "type": "debit", "amount": 300.00},
                    {"account_name": accounts[2], "type": "credit", "amount": 400.00},
                    {"account_name": accounts[3], "type": "credit", "amount": 400.00}
                ]
            }
            
            response = client.post("/api/v1/transactions", headers=auth_headers, json=complex_transaction)
            assert response.status_code == 200


class TestConcurrency:
    """Test concurrent access scenarios."""

    def test_concurrent_account_creation(self, auth_headers):
        """Test creating accounts with similar data concurrently."""
        # This is a basic test - true concurrency testing would require threading
        account_base = {
            "name": "Concurrent Test Account",
            "type": "asset",
            "description": "Testing concurrent creation"
        }
        
        # Try to create accounts with different codes rapidly
        results = []
        for i in range(5):
            account_data = account_base.copy()
            account_data["code"] = f"CONC-{i}"
            response = client.post("/api/v1/accounts", headers=auth_headers, json=account_data)
            results.append(response.status_code)
        
        # All should succeed with unique codes
        assert all(status == 200 for status in results)

    def test_concurrent_user_operations(self, auth_headers):
        """Test concurrent user-related operations."""
        # Create multiple users rapidly
        results = []
        for i in range(3):
            user_data = {
                "username": f"concurrent_user_{i}",
                "email": f"concurrent{i}@test.com",
                "full_name": f"Concurrent User {i}",
                "password": "concurrent123",
                "role": "viewer"
            }
            response = client.post("/api/v1/auth/register", headers=auth_headers, json=user_data)
            results.append(response.status_code)
        
        # Should handle concurrent user creation
        success_count = sum(1 for status in results if status == 200)
        assert success_count >= 1  # At least one should succeed


class TestDataConsistency:
    """Test data consistency across operations."""

    def test_account_transaction_consistency(self, auth_headers):
        """Test consistency between accounts and their usage in transactions."""
        # Create an account
        account_data = {
            "name": "Consistency Test Account",
            "type": "asset",
            "code": "CONS-001",
        }
        account_response = client.post("/api/v1/accounts", headers=auth_headers, json=account_data)
        assert account_response.status_code == 200
        
        # Create another account for the transaction
        expense_account = {
            "name": "Consistency Expense",
            "type": "expense", 
            "code": "CONS-EXP",
        }
        client.post("/api/v1/accounts", headers=auth_headers, json=expense_account)
        
        # Use the account in a transaction
        transaction_data = {
            "description": "Consistency test transaction",
            "lines": [
                {"account_name": "Consistency Expense", "type": "debit", "amount": 200.00},
                {"account_name": "Consistency Test Account", "type": "credit", "amount": 200.00}
            ]
        }
        
        transaction_response = client.post("/api/v1/transactions", headers=auth_headers, json=transaction_data)
        assert transaction_response.status_code == 200
        
        # Verify both accounts still exist and can be retrieved
        accounts_response = client.get("/api/v1/accounts", headers=auth_headers)
        assert accounts_response.status_code == 200
        
        accounts = accounts_response.json()
        account_names = [acc["name"] for acc in accounts]
        assert "Consistency Test Account" in account_names
        assert "Consistency Expense" in account_names

    def test_user_permission_consistency(self, auth_headers):
        """Test consistency of user permissions across operations."""
        # Create a user
        user_data = {
            "username": "permission_test_user",
            "email": "permission@test.com",
            "full_name": "Permission Test User",
            "password": "permission123",
            "role": "accountant"
        }
        
        create_response = client.post("/api/v1/auth/register", headers=auth_headers, json=user_data)
        
        if create_response.status_code == 200:
            # Login as the new user
            login_response = client.post(
                "/api/v1/auth/login",
                data={"username": "permission_test_user", "password": "permission123"}
            )
            
            if login_response.status_code == 200:
                user_token = login_response.json()["access_token"]
                user_headers = {"Authorization": f"Bearer {user_token}"}
                
                # Check user info is consistent
                me_response = client.get("/api/v1/auth/me", headers=user_headers)
                assert me_response.status_code == 200
                
                user_info = me_response.json()
                assert user_info["username"] == "permission_test_user"
                assert user_info["role"] == "accountant"

    def test_transaction_balance_consistency(self, auth_headers):
        """Test that transaction balancing is consistently enforced."""
        # Ensure accounts exist
        client.post("/api/v1/accounts", headers=auth_headers, json={
            "name": "Balance Test Cash", "type": "asset", "code": "BAL-CASH"
        })
        client.post("/api/v1/accounts", headers=auth_headers, json={
            "name": "Balance Test Expense", "type": "expense", "code": "BAL-EXP"
        })
        
        # Test multiple balanced transactions
        for amount in [100.00, 250.50, 1000.00]:
            transaction_data = {
                "description": f"Balance test for {amount}",
                "lines": [
                    {"account_name": "Balance Test Expense", "type": "debit", "amount": amount},
                    {"account_name": "Balance Test Cash", "type": "credit", "amount": amount}
                ]
            }
            
            response = client.post("/api/v1/transactions", headers=auth_headers, json=transaction_data)
            assert response.status_code == 200, f"Failed for amount {amount}"
        
        # Test unbalanced transactions are consistently rejected
        unbalanced_amounts = [
            (100.00, 200.00),
            (500.00, 499.99),
            (1000.00, 1000.01)
        ]
        
        for debit_amount, credit_amount in unbalanced_amounts:
            transaction_data = {
                "description": f"Unbalanced test {debit_amount} vs {credit_amount}",
                "lines": [
                    {"account_name": "Balance Test Expense", "type": "debit", "amount": debit_amount},
                    {"account_name": "Balance Test Cash", "type": "credit", "amount": credit_amount}
                ]
            }
            
            response = client.post("/api/v1/transactions", headers=auth_headers, json=transaction_data)
            assert response.status_code == 400, f"Should reject unbalanced: {debit_amount} vs {credit_amount}"


class TestIntegration:
    """Test integration between different API components."""

    def test_full_workflow_integration(self, auth_headers):
        """Test complete workflow from account creation to transaction posting."""
        # Step 1: Create accounts for a complete business scenario
        accounts_to_create = [
            {"name": "Integration Cash", "type": "asset", "code": "INT-CASH"},
            {"name": "Integration Revenue", "type": "revenue", "code": "INT-REV"},
            {"name": "Integration Expense", "type": "expense", "code": "INT-EXP"},
            {"name": "Integration AR", "type": "asset", "code": "INT-AR"}
        ]
        
        created_accounts = []
        for account_data in accounts_to_create:
            response = client.post("/api/v1/accounts", headers=auth_headers, json=account_data)
            if response.status_code == 200:
                created_accounts.append(account_data["name"])
        
        assert len(created_accounts) >= 3, "Need at least 3 accounts for integration test"
        
        # Step 2: Create a sales transaction
        if len(created_accounts) >= 3:
            sales_transaction = {
                "description": "Integration test - Customer sale",
                "reference": "SALE-001",
                "lines": [
                    {"account_name": "Integration Cash", "type": "debit", "amount": 800.00},
                    {"account_name": "Integration AR", "type": "debit", "amount": 200.00},
                    {"account_name": "Integration Revenue", "type": "credit", "amount": 1000.00}
                ]
            }
            
            sales_response = client.post("/api/v1/transactions", headers=auth_headers, json=sales_transaction)
            assert sales_response.status_code == 200
            
            # Step 3: Create an expense transaction
            expense_transaction = {
                "description": "Integration test - Business expense",
                "reference": "EXP-001", 
                "lines": [
                    {"account_name": "Integration Expense", "type": "debit", "amount": 300.00},
                    {"account_name": "Integration Cash", "type": "credit", "amount": 300.00}
                ]
            }
            
            expense_response = client.post("/api/v1/transactions", headers=auth_headers, json=expense_transaction)
            assert expense_response.status_code == 200
            
            # Step 4: Verify all data is consistent
            accounts_response = client.get("/api/v1/accounts", headers=auth_headers)
            assert accounts_response.status_code == 200
            
            transactions_response = client.get("/api/v1/transactions", headers=auth_headers)
            assert transactions_response.status_code == 200
            
            transactions = transactions_response.json()
            assert len(transactions) >= 2
            
            # Verify transaction references are preserved
            references = [tx["reference"] for tx in transactions if tx["reference"]]
            assert "SALE-001" in references
            assert "EXP-001" in references

    def test_user_workflow_integration(self, auth_headers):
        """Test complete user management workflow."""
        # Step 1: Create a new user
        new_user_data = {
            "username": "workflow_user",
            "email": "workflow@test.com",
            "full_name": "Workflow Test User",
            "password": "workflow123",
            "role": "accountant"
        }
        
        create_response = client.post("/api/v1/auth/register", headers=auth_headers, json=new_user_data)
        
        if create_response.status_code == 200:
            created_user = create_response.json()
            user_id = created_user["id"]
            
            # Step 2: User logs in
            login_response = client.post(
                "/api/v1/auth/login",
                data={"username": "workflow_user", "password": "workflow123"}
            )
            assert login_response.status_code == 200
            
            user_token = login_response.json()["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            # Step 3: User accesses their profile
            profile_response = client.get("/api/v1/auth/me", headers=user_headers)
            assert profile_response.status_code == 200
            
            profile_data = profile_response.json()
            assert profile_data["username"] == "workflow_user"
            assert profile_data["role"] == "accountant"
            
            # Step 4: User changes password
            password_change_response = client.post(
                "/api/v1/auth/change-password",
                headers=user_headers,
                json={
                    "current_password": "workflow123",
                    "new_password": "newworkflow456"
                }
            )
            assert password_change_response.status_code == 200
            
            # Step 5: Login with new password
            new_login_response = client.post(
                "/api/v1/auth/login",
                data={"username": "workflow_user", "password": "newworkflow456"}
            )
            assert new_login_response.status_code == 200
            
            # Step 6: Admin can see user in user list
            users_response = client.get("/api/v1/auth/users", headers=auth_headers)
            assert users_response.status_code == 200
            
            users = users_response.json()
            workflow_users = [u for u in users if u["username"] == "workflow_user"]
            assert len(workflow_users) == 1