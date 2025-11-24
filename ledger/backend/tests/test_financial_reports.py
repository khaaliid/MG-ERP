"""
Comprehensive tests for the financial reporting system.
Tests all major financial reports and their accuracy.
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.services.ledger import (
    create_account,
    create_transaction,
    generate_trial_balance,
    generate_balance_sheet,
    generate_income_statement,
    generate_general_ledger,
    generate_cash_flow_statement,
    AccountType,
    TransactionSource,
)


class MockAccountData:
    def __init__(self, name, code, type, description):
        self.name = name
        self.code = code
        self.type = type
        self.description = description
        self.is_active = True


class MockTransactionData:
    def __init__(self, description, lines, date=None, source=None, reference=None):
        self.description = description
        self.lines = lines
        self.date = date or datetime.now(timezone.utc)
        self.source = source or TransactionSource.manual
        self.reference = reference


class MockTransactionLine:
    def __init__(self, account_name, type, amount):
        self.account_name = account_name
        self.type = type
        self.amount = amount


@pytest_asyncio.fixture
async def setup_comprehensive_accounts(db_session: AsyncSession):
    """Setup comprehensive chart of accounts for testing"""
    
    accounts = [
        # Assets
        MockAccountData("Cash", "1001", AccountType.ASSET, "Primary cash account"),
        MockAccountData("Petty Cash", "1002", AccountType.ASSET, "Small cash fund"),
        MockAccountData("Accounts Receivable", "1100", AccountType.ASSET, "Customer receivables"),
        MockAccountData("Inventory", "1200", AccountType.ASSET, "Product inventory"),
        MockAccountData("Equipment", "1500", AccountType.ASSET, "Office equipment"),
        
        # Liabilities
        MockAccountData("Accounts Payable", "2001", AccountType.LIABILITY, "Supplier payables"),
        MockAccountData("Accrued Expenses", "2100", AccountType.LIABILITY, "Accrued liabilities"),
        MockAccountData("Loan Payable", "2500", AccountType.LIABILITY, "Bank loan"),
        
        # Equity
        MockAccountData("Owner's Capital", "3001", AccountType.EQUITY, "Owner's investment"),
        MockAccountData("Retained Earnings", "3100", AccountType.EQUITY, "Accumulated earnings"),
        
        # Income
        MockAccountData("Sales Revenue", "4001", AccountType.INCOME, "Product sales"),
        MockAccountData("Service Revenue", "4002", AccountType.INCOME, "Service income"),
        MockAccountData("Interest Income", "4100", AccountType.INCOME, "Interest earned"),
        
        # Expenses
        MockAccountData("Cost of Goods Sold", "5001", AccountType.EXPENSE, "Direct costs"),
        MockAccountData("Salary Expense", "6001", AccountType.EXPENSE, "Employee salaries"),
        MockAccountData("Rent Expense", "6100", AccountType.EXPENSE, "Office rent"),
        MockAccountData("Utilities Expense", "6200", AccountType.EXPENSE, "Electricity, water"),
        MockAccountData("Marketing Expense", "6300", AccountType.EXPENSE, "Advertising costs"),
    ]
    
    created_accounts = []
    for account_data in accounts:
        account = await create_account(db_session, account_data)
        created_accounts.append(account)
    
    return created_accounts


@pytest_asyncio.fixture
async def setup_sample_transactions(db_session: AsyncSession, setup_comprehensive_accounts):
    """Create sample transactions for testing reports"""
    
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    transactions = [
        # Initial investment
        MockTransactionData(
            description="Owner initial investment",
            lines=[
                MockTransactionLine("Cash", "debit", 50000.00),
                MockTransactionLine("Owner's Capital", "credit", 50000.00),
            ],
            date=base_date
        ),
        
        # Equipment purchase
        MockTransactionData(
            description="Purchase office equipment",
            lines=[
                MockTransactionLine("Equipment", "debit", 15000.00),
                MockTransactionLine("Cash", "credit", 10000.00),
                MockTransactionLine("Loan Payable", "credit", 5000.00),
            ],
            date=base_date + timedelta(days=5)
        ),
        
        # Sales transactions
        MockTransactionData(
            description="Cash sales",
            lines=[
                MockTransactionLine("Cash", "debit", 8000.00),
                MockTransactionLine("Sales Revenue", "credit", 8000.00),
            ],
            date=base_date + timedelta(days=10)
        ),
        
        MockTransactionData(
            description="Credit sales",
            lines=[
                MockTransactionLine("Accounts Receivable", "debit", 5000.00),
                MockTransactionLine("Service Revenue", "credit", 5000.00),
            ],
            date=base_date + timedelta(days=15)
        ),
        
        # Expenses
        MockTransactionData(
            description="Monthly rent payment",
            lines=[
                MockTransactionLine("Rent Expense", "debit", 2000.00),
                MockTransactionLine("Cash", "credit", 2000.00),
            ],
            date=base_date + timedelta(days=20)
        ),
        
        MockTransactionData(
            description="Salary payments",
            lines=[
                MockTransactionLine("Salary Expense", "debit", 3000.00),
                MockTransactionLine("Cash", "credit", 3000.00),
            ],
            date=base_date + timedelta(days=25)
        ),
        
        # Purchase on credit
        MockTransactionData(
            description="Purchase inventory on credit",
            lines=[
                MockTransactionLine("Inventory", "debit", 3000.00),
                MockTransactionLine("Accounts Payable", "credit", 3000.00),
            ],
            date=base_date + timedelta(days=30)
        ),
        
        # Cost of goods sold
        MockTransactionData(
            description="Cost of goods sold",
            lines=[
                MockTransactionLine("Cost of Goods Sold", "debit", 1500.00),
                MockTransactionLine("Inventory", "credit", 1500.00),
            ],
            date=base_date + timedelta(days=35)
        ),
    ]
    
    created_transactions = []
    for transaction_data in transactions:
        transaction = await create_transaction(db_session, transaction_data)
        created_transactions.append(transaction)
    
    return created_transactions


class TestFinancialReports:
    """Test suite for financial reporting system"""

    @pytest.mark.asyncio
    async def test_trial_balance_generation(self, db_session: AsyncSession, setup_sample_transactions):
        """Test trial balance report generation and accuracy"""
        
        report = await generate_trial_balance(db_session)
        
        # Verify report structure
        assert report['report_type'] == 'Trial Balance'
        assert 'accounts' in report
        assert 'totals' in report
        assert len(report['accounts']) > 0
        
        # Verify trial balance is balanced
        assert report['totals']['balanced'] == True
        assert report['totals']['total_debits'] == report['totals']['total_credits']
        
        # Verify account data structure
        for account in report['accounts']:
            assert 'account_code' in account
            assert 'account_name' in account
            assert 'account_type' in account
            assert 'debit_balance' in account
            assert 'credit_balance' in account
            assert isinstance(account['debit_balance'], (int, float))
            assert isinstance(account['credit_balance'], (int, float))

    @pytest.mark.asyncio
    async def test_balance_sheet_generation(self, db_session: AsyncSession, setup_sample_transactions):
        """Test balance sheet report generation and equation balance"""
        
        report = await generate_balance_sheet(db_session)
        
        # Verify report structure
        assert report['report_type'] == 'Balance Sheet'
        assert 'assets' in report
        assert 'liabilities' in report
        assert 'equity' in report
        assert 'totals' in report
        
        # Verify accounting equation: Assets = Liabilities + Equity
        assert report['totals']['balanced'] == True
        total_assets = report['totals']['total_assets']
        total_liabilities_equity = report['totals']['total_liabilities_equity']
        assert abs(total_assets - total_liabilities_equity) < 0.01
        
        # Verify assets are positive (typical for assets)
        assert report['assets']['total'] > 0
        
        # Verify section structure
        for section in ['assets', 'liabilities', 'equity']:
            assert 'accounts' in report[section]
            assert 'total' in report[section]
            assert isinstance(report[section]['accounts'], list)

    @pytest.mark.asyncio
    async def test_income_statement_generation(self, db_session: AsyncSession, setup_sample_transactions):
        """Test income statement report generation and profit calculation"""
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        report = await generate_income_statement(db_session, start_date, end_date)
        
        # Verify report structure
        assert report['report_type'] == 'Income Statement'
        assert 'period' in report
        assert 'income' in report
        assert 'expenses' in report
        assert 'net_income' in report
        
        # Verify period dates
        assert report['period']['start_date'] == start_date.isoformat()
        assert report['period']['end_date'] == end_date.isoformat()
        
        # Verify income and expenses are properly categorized
        assert isinstance(report['income']['accounts'], list)
        assert isinstance(report['expenses']['accounts'], list)
        assert isinstance(report['income']['total'], (int, float))
        assert isinstance(report['expenses']['total'], (int, float))
        
        # Net income should equal income minus expenses
        expected_net_income = report['income']['total'] - report['expenses']['total']
        assert abs(report['net_income'] - expected_net_income) < 0.01
        
        # Should have some revenue and expenses from our sample data
        assert report['income']['total'] > 0  # We had sales
        assert report['expenses']['total'] > 0  # We had expenses

    @pytest.mark.asyncio
    async def test_general_ledger_generation(self, db_session: AsyncSession, setup_sample_transactions):
        """Test general ledger report generation and transaction tracking"""
        
        report = await generate_general_ledger(db_session)
        
        # Verify report structure
        assert report['report_type'] == 'General Ledger'
        assert 'accounts' in report
        assert 'period' in report
        assert len(report['accounts']) > 0
        
        # Verify account structure
        for account in report['accounts']:
            assert 'account_id' in account
            assert 'account_code' in account
            assert 'account_name' in account
            assert 'transactions' in account
            assert 'running_balance' in account
            assert 'transaction_count' in account
            
            # Verify transaction structure
            for transaction in account['transactions']:
                assert 'transaction_id' in transaction
                assert 'date' in transaction
                assert 'description' in transaction
                assert 'type' in transaction
                assert 'amount' in transaction
                assert 'running_balance' in transaction
                assert transaction['type'] in ['debit', 'credit']

    @pytest.mark.asyncio
    async def test_general_ledger_specific_account(self, db_session: AsyncSession, setup_sample_transactions):
        """Test general ledger for specific account"""
        
        # Get cash account (should have ID 1 based on our setup)
        cash_account_id = 1
        
        report = await generate_general_ledger(db_session, account_id=cash_account_id)
        
        # Should only have one account (Cash)
        assert len(report['accounts']) == 1
        
        cash_account = report['accounts'][0]
        assert cash_account['account_name'] == 'Cash'
        assert len(cash_account['transactions']) > 0
        
        # Verify running balance calculation
        running_balance = 0.0
        for transaction in cash_account['transactions']:
            if transaction['type'] == 'debit':
                running_balance += transaction['amount']
            else:
                running_balance -= transaction['amount']
            
            # Allow small floating point differences
            assert abs(transaction['running_balance'] - running_balance) < 0.01

    @pytest.mark.asyncio
    async def test_cash_flow_statement(self, db_session: AsyncSession, setup_sample_transactions):
        """Test cash flow statement generation and cash tracking"""
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        report = await generate_cash_flow_statement(db_session, start_date, end_date)
        
        # Verify report structure
        assert report['report_type'] == 'Cash Flow Statement'
        assert 'period' in report
        assert 'cash_flows' in report
        assert 'summary' in report
        
        # Verify summary calculations
        summary = report['summary']
        assert 'total_inflows' in summary
        assert 'total_outflows' in summary
        assert 'net_cash_flow' in summary
        
        # Verify cash flows
        total_inflows = 0.0
        total_outflows = 0.0
        
        for flow in report['cash_flows']:
            assert 'date' in flow
            assert 'description' in flow
            assert 'account' in flow
            assert 'type' in flow
            assert 'amount' in flow
            assert flow['type'] in ['Inflow', 'Outflow']
            
            if flow['type'] == 'Inflow':
                total_inflows += flow['amount']
            else:
                total_outflows += flow['amount']
        
        # Verify summary matches individual flows
        assert abs(summary['total_inflows'] - total_inflows) < 0.01
        assert abs(summary['total_outflows'] - total_outflows) < 0.01
        assert abs(summary['net_cash_flow'] - (total_inflows - total_outflows)) < 0.01

    @pytest.mark.asyncio
    async def test_date_filtering_in_reports(self, db_session: AsyncSession, setup_sample_transactions):
        """Test that date filtering works correctly in reports"""
        
        # Test with a narrow date range
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        # Income statement with date range
        income_report = await generate_income_statement(db_session, start_date, end_date)
        
        # Should have limited transactions in this range
        # Based on our sample data, should have initial sales but not all expenses
        assert income_report['income']['total'] > 0
        
        # General ledger with date range
        ledger_report = await generate_general_ledger(db_session, start_date=start_date, end_date=end_date)
        
        # Verify all transactions are within date range
        for account in ledger_report['accounts']:
            for transaction in account['transactions']:
                transaction_date = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
                assert start_date <= transaction_date <= end_date

    @pytest.mark.asyncio
    async def test_trial_balance_with_specific_date(self, db_session: AsyncSession, setup_sample_transactions):
        """Test trial balance generation as of a specific date"""
        
        # Test trial balance as of middle of our transaction period
        as_of_date = datetime(2024, 1, 20, tzinfo=timezone.utc)
        
        report = await generate_trial_balance(db_session, as_of_date)
        
        assert report['report_type'] == 'Trial Balance'
        assert report['as_of_date'] == as_of_date.isoformat()
        assert report['totals']['balanced'] == True

    @pytest.mark.asyncio
    async def test_empty_database_reports(self, db_session: AsyncSession, setup_comprehensive_accounts):
        """Test reports with accounts but no transactions"""
        
        # Trial balance with no transactions should still work
        trial_balance = await generate_trial_balance(db_session)
        assert trial_balance['totals']['total_debits'] == 0.0
        assert trial_balance['totals']['total_credits'] == 0.0
        assert trial_balance['totals']['balanced'] == True
        
        # Balance sheet with no transactions
        balance_sheet = await generate_balance_sheet(db_session)
        assert balance_sheet['totals']['total_assets'] == 0.0
        assert balance_sheet['totals']['balanced'] == True
        
        # Income statement with no transactions
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        income_statement = await generate_income_statement(db_session, start_date, end_date)
        assert income_statement['income']['total'] == 0.0
        assert income_statement['expenses']['total'] == 0.0
        assert income_statement['net_income'] == 0.0

    @pytest.mark.asyncio
    async def test_report_data_consistency(self, db_session: AsyncSession, setup_sample_transactions):
        """Test that data is consistent across different reports"""
        
        # Generate all reports for the same date
        as_of_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        trial_balance = await generate_trial_balance(db_session, as_of_date)
        balance_sheet = await generate_balance_sheet(db_session, as_of_date)
        
        # Trial balance totals should match balance sheet equation
        tb_total_debits = trial_balance['totals']['total_debits']
        tb_total_credits = trial_balance['totals']['total_credits']
        
        bs_total_assets = balance_sheet['totals']['total_assets']
        bs_total_liab_equity = balance_sheet['totals']['total_liabilities_equity']
        
        # In a properly balanced system, these should all be equal
        assert abs(tb_total_debits - tb_total_credits) < 0.01
        assert abs(bs_total_assets - bs_total_liab_equity) < 0.01

    @pytest.mark.asyncio
    async def test_report_error_handling(self, db_session: AsyncSession):
        """Test report error handling with invalid inputs"""
        
        # Test with invalid account ID for general ledger
        report = await generate_general_ledger(db_session, account_id=99999)
        assert len(report['accounts']) == 0
        
        # Test cash flow with no cash accounts (should handle gracefully)
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        cash_flow = await generate_cash_flow_statement(db_session, start_date, end_date)
        # Should either return empty flows or error message
        assert 'cash_flows' in cash_flow