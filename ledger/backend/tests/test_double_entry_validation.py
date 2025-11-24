"""
Comprehensive tests for double-entry bookkeeping validation system.
Tests enterprise-grade validation features and accounting equation integrity.
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.services.ledger import (
    create_account,
    validate_transaction_data,
    validate_transaction_integrity,
    validate_all_transactions_integrity,
    get_accounting_equation_status,
    create_transaction,
    ValidationResult,
    AccountType,
    TransactionSource,
)


class MockTransactionData:
    """Mock transaction data for testing"""
    def __init__(self, description, lines, date=None, source=None, reference=None):
        self.description = description
        self.lines = lines
        self.date = date or datetime.now(timezone.utc)
        self.source = source or TransactionSource.manual
        self.reference = reference


class MockTransactionLine:
    """Mock transaction line for testing"""
    def __init__(self, account_name, type, amount):
        self.account_name = account_name
        self.type = type
        self.amount = amount


@pytest_asyncio.fixture
async def setup_test_accounts(db_session: AsyncSession):
    """Setup test accounts for validation testing"""
    
    class MockAccountData:
        def __init__(self, name, code, type, description):
            self.name = name
            self.code = code
            self.type = type
            self.description = description
            self.is_active = True
    
    # Create test accounts
    accounts = [
        MockAccountData("Cash", "1001", AccountType.ASSET, "Cash account"),
        MockAccountData("Accounts Receivable", "1002", AccountType.ASSET, "Customer receivables"),
        MockAccountData("Accounts Payable", "2001", AccountType.LIABILITY, "Supplier payables"),
        MockAccountData("Owner's Equity", "3001", AccountType.EQUITY, "Owner's equity"),
        MockAccountData("Sales Revenue", "4001", AccountType.INCOME, "Sales income"),
        MockAccountData("Office Expenses", "5001", AccountType.EXPENSE, "Office expenses"),
        MockAccountData("Inactive Account", "9999", AccountType.ASSET, "Inactive account"),
    ]
    
    created_accounts = []
    for account_data in accounts:
        account = await create_account(db_session, account_data)
        created_accounts.append(account)
    
    # Make one account inactive for testing
    inactive_account = next(acc for acc in created_accounts if acc.name == "Inactive Account")
    inactive_account.is_active = False
    await db_session.commit()
    
    return created_accounts


class TestDoubleEntryValidation:
    """Test suite for double-entry validation system"""

    @pytest.mark.asyncio
    async def test_valid_transaction_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation of a properly balanced transaction"""
        
        # Create a valid sale transaction
        transaction_data = MockTransactionData(
            description="Sale to customer",
            lines=[
                MockTransactionLine("Cash", "debit", 1000.00),
                MockTransactionLine("Sales Revenue", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_unbalanced_transaction_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation fails for unbalanced transaction"""
        
        transaction_data = MockTransactionData(
            description="Unbalanced transaction",
            lines=[
                MockTransactionLine("Cash", "debit", 1000.00),
                MockTransactionLine("Sales Revenue", "credit", 800.00),  # Unbalanced!
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("not balanced" in error for error in result.errors)
        assert "Debits (1000.00) ≠ Credits (800.00)" in str(result.errors)

    @pytest.mark.asyncio
    async def test_insufficient_lines_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation fails for single-line transaction"""
        
        transaction_data = MockTransactionData(
            description="Single line transaction",
            lines=[
                MockTransactionLine("Cash", "debit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("at least 2 lines" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_nonexistent_account_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation fails for non-existent account"""
        
        transaction_data = MockTransactionData(
            description="Transaction with invalid account",
            lines=[
                MockTransactionLine("Cash", "debit", 1000.00),
                MockTransactionLine("Nonexistent Account", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("does not exist" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_inactive_account_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation warns for inactive account"""
        
        transaction_data = MockTransactionData(
            description="Transaction with inactive account",
            lines=[
                MockTransactionLine("Cash", "debit", 1000.00),
                MockTransactionLine("Inactive Account", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("inactive" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_negative_amount_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation fails for negative amounts"""
        
        transaction_data = MockTransactionData(
            description="Transaction with negative amount",
            lines=[
                MockTransactionLine("Cash", "debit", -1000.00),
                MockTransactionLine("Sales Revenue", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("must be positive" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_invalid_transaction_type_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation fails for invalid transaction types"""
        
        transaction_data = MockTransactionData(
            description="Transaction with invalid type",
            lines=[
                MockTransactionLine("Cash", "invalid_type", 1000.00),
                MockTransactionLine("Sales Revenue", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("must be 'debit' or 'credit'" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_empty_description_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation fails for empty description"""
        
        transaction_data = MockTransactionData(
            description="",
            lines=[
                MockTransactionLine("Cash", "debit", 1000.00),
                MockTransactionLine("Sales Revenue", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert not result.is_valid
        assert any("description is required" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_complex_multi_line_transaction(self, db_session: AsyncSession, setup_test_accounts):
        """Test validation of complex multi-line transaction"""
        
        transaction_data = MockTransactionData(
            description="Complex purchase with multiple accounts",
            lines=[
                MockTransactionLine("Office Expenses", "debit", 500.00),
                MockTransactionLine("Accounts Receivable", "debit", 300.00),
                MockTransactionLine("Cash", "credit", 200.00),
                MockTransactionLine("Accounts Payable", "credit", 600.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_post_commit_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test post-commit validation of created transaction"""
        
        # Create a valid transaction
        transaction_data = MockTransactionData(
            description="Test transaction for post-commit validation",
            lines=[
                MockTransactionLine("Cash", "debit", 1500.00),
                MockTransactionLine("Sales Revenue", "credit", 1500.00),
            ]
        )
        
        # Create the transaction
        created_transaction = await create_transaction(db_session, transaction_data)
        
        # Validate the created transaction
        result = await validate_transaction_integrity(db_session, created_transaction.id)
        
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_accounting_equation_status(self, db_session: AsyncSession, setup_test_accounts):
        """Test accounting equation status calculation"""
        
        # Create some transactions to affect the equation
        transactions = [
            MockTransactionData(
                description="Initial investment",
                lines=[
                    MockTransactionLine("Cash", "debit", 10000.00),
                    MockTransactionLine("Owner's Equity", "credit", 10000.00),
                ]
            ),
            MockTransactionData(
                description="Purchase supplies",
                lines=[
                    MockTransactionLine("Office Expenses", "debit", 500.00),
                    MockTransactionLine("Cash", "credit", 500.00),
                ]
            ),
            MockTransactionData(
                description="Sales transaction",
                lines=[
                    MockTransactionLine("Cash", "debit", 2000.00),
                    MockTransactionLine("Sales Revenue", "credit", 2000.00),
                ]
            ),
        ]
        
        # Create all transactions
        for transaction_data in transactions:
            await create_transaction(db_session, transaction_data)
        
        # Get accounting equation status
        equation_status = await get_accounting_equation_status(db_session)
        
        # Verify basic structure
        assert "assets" in equation_status
        assert "liabilities" in equation_status
        assert "equity" in equation_status
        assert "equation_balanced" in equation_status
        
        # The equation should be balanced
        assert equation_status["equation_balanced"]
        
        # Check expected values
        assert equation_status["assets"] == Decimal('11500.00')  # 10000 + 2000 - 500
        assert equation_status["expenses"] == Decimal('500.00')
        assert equation_status["income"] == Decimal('2000.00')

    @pytest.mark.asyncio
    async def test_system_wide_validation(self, db_session: AsyncSession, setup_test_accounts):
        """Test system-wide validation of all transactions"""
        
        # Create multiple transactions
        transactions = [
            MockTransactionData(
                description="Transaction 1",
                lines=[
                    MockTransactionLine("Cash", "debit", 1000.00),
                    MockTransactionLine("Sales Revenue", "credit", 1000.00),
                ]
            ),
            MockTransactionData(
                description="Transaction 2",
                lines=[
                    MockTransactionLine("Office Expenses", "debit", 200.00),
                    MockTransactionLine("Cash", "credit", 200.00),
                ]
            ),
        ]
        
        # Create all transactions
        for transaction_data in transactions:
            await create_transaction(db_session, transaction_data)
        
        # Perform system-wide validation
        result = await validate_all_transactions_integrity(db_session)
        
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_precision_handling(self, db_session: AsyncSession, setup_test_accounts):
        """Test precise decimal handling in validation"""
        
        transaction_data = MockTransactionData(
            description="Precision test transaction",
            lines=[
                MockTransactionLine("Cash", "debit", 100.005),  # Should round to 100.01
                MockTransactionLine("Sales Revenue", "credit", 100.004),  # Should round to 100.00
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        # This should fail due to rounding differences
        assert not result.is_valid
        assert any("not balanced" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_duplicate_account_warning(self, db_session: AsyncSession, setup_test_accounts):
        """Test warning for duplicate account usage with same type"""
        
        transaction_data = MockTransactionData(
            description="Transaction with duplicate account usage",
            lines=[
                MockTransactionLine("Cash", "debit", 500.00),
                MockTransactionLine("Cash", "debit", 500.00),  # Duplicate usage
                MockTransactionLine("Sales Revenue", "credit", 1000.00),
            ]
        )
        
        result = await validate_transaction_data(db_session, transaction_data)
        
        assert result.is_valid  # Should still be valid
        assert len(result.warnings) > 0
        assert any("appears multiple times" in warning for warning in result.warnings)


class TestValidationResult:
    """Test ValidationResult helper class"""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation and basic functionality"""
        result = ValidationResult()
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_add_error_invalidates_result(self):
        """Test that adding error invalidates result"""
        result = ValidationResult()
        result.add_error("Test error")
        
        assert not result.is_valid
        assert "Test error" in result.errors
    
    def test_add_warning_keeps_valid(self):
        """Test that adding warning keeps result valid"""
        result = ValidationResult()
        result.add_warning("Test warning")
        
        assert result.is_valid
        assert "Test warning" in result.warnings
    
    def test_multiple_errors_and_warnings(self):
        """Test handling multiple errors and warnings"""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")
        result.add_warning("Warning 2")
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 2