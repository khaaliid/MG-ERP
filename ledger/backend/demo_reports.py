"""
Demo script to showcase the enhanced ledger system with financial reporting.
This script creates sample data and generates all financial reports.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.dependencies import get_db
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
        self.source = source or TransactionSource.MANUAL
        self.reference = reference


class MockTransactionLine:
    def __init__(self, account_name, type, amount):
        self.account_name = account_name
        self.type = type
        self.amount = amount


async def create_sample_data():
    """Create sample chart of accounts and transactions"""
    
    print("🏦 Creating Enhanced MG-ERP Ledger Demo")
    print("=" * 50)
    
    async with get_db_session() as db:
        print("\n📋 Creating Chart of Accounts...")
        
        # Create comprehensive chart of accounts
        accounts = [
            # Assets
            MockAccountData("Cash", "1001", AccountType.ASSET, "Primary cash account"),
            MockAccountData("Accounts Receivable", "1100", AccountType.ASSET, "Customer receivables"),
            MockAccountData("Inventory", "1200", AccountType.ASSET, "Product inventory"),
            MockAccountData("Equipment", "1500", AccountType.ASSET, "Office equipment"),
            
            # Liabilities
            MockAccountData("Accounts Payable", "2001", AccountType.LIABILITY, "Supplier payables"),
            MockAccountData("Loan Payable", "2500", AccountType.LIABILITY, "Bank loan"),
            
            # Equity
            MockAccountData("Owner's Capital", "3001", AccountType.EQUITY, "Owner's investment"),
            
            # Income
            MockAccountData("Sales Revenue", "4001", AccountType.INCOME, "Product sales"),
            MockAccountData("Service Revenue", "4002", AccountType.INCOME, "Service income"),
            
            # Expenses
            MockAccountData("Cost of Goods Sold", "5001", AccountType.EXPENSE, "Direct costs"),
            MockAccountData("Salary Expense", "6001", AccountType.EXPENSE, "Employee salaries"),
            MockAccountData("Rent Expense", "6100", AccountType.EXPENSE, "Office rent"),
            MockAccountData("Utilities Expense", "6200", AccountType.EXPENSE, "Electricity, water"),
        ]
        
        for account_data in accounts:
            try:
                await create_account(db, account_data)
                print(f"   ✅ Created: {account_data.code} - {account_data.name}")
            except Exception as e:
                print(f"   ⚠️  Account {account_data.name} may already exist")
        
        print(f"\n📊 Creating Sample Transactions...")
        
        base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        transactions = [
            # Initial investment
            MockTransactionData(
                description="Owner initial investment",
                lines=[
                    MockTransactionLine("Cash", "debit", 100000.00),
                    MockTransactionLine("Owner's Capital", "credit", 100000.00),
                ],
                date=base_date,
                reference="INV-001"
            ),
            
            # Equipment purchase
            MockTransactionData(
                description="Purchase office equipment",
                lines=[
                    MockTransactionLine("Equipment", "debit", 25000.00),
                    MockTransactionLine("Cash", "credit", 20000.00),
                    MockTransactionLine("Loan Payable", "credit", 5000.00),
                ],
                date=base_date + timedelta(days=5),
                reference="PO-001"
            ),
            
            # Sales transactions
            MockTransactionData(
                description="January cash sales",
                lines=[
                    MockTransactionLine("Cash", "debit", 15000.00),
                    MockTransactionLine("Sales Revenue", "credit", 15000.00),
                ],
                date=base_date + timedelta(days=15),
                reference="SAL-001"
            ),
            
            MockTransactionData(
                description="Credit sales to customer",
                lines=[
                    MockTransactionLine("Accounts Receivable", "debit", 8000.00),
                    MockTransactionLine("Service Revenue", "credit", 8000.00),
                ],
                date=base_date + timedelta(days=20),
                reference="SAL-002"
            ),
            
            # Inventory and COGS
            MockTransactionData(
                description="Purchase inventory",
                lines=[
                    MockTransactionLine("Inventory", "debit", 6000.00),
                    MockTransactionLine("Accounts Payable", "credit", 6000.00),
                ],
                date=base_date + timedelta(days=25),
                reference="PUR-001"
            ),
            
            MockTransactionData(
                description="Cost of goods sold",
                lines=[
                    MockTransactionLine("Cost of Goods Sold", "debit", 3000.00),
                    MockTransactionLine("Inventory", "credit", 3000.00),
                ],
                date=base_date + timedelta(days=30),
                reference="COGS-001"
            ),
            
            # Operating expenses
            MockTransactionData(
                description="Monthly rent payment",
                lines=[
                    MockTransactionLine("Rent Expense", "debit", 4000.00),
                    MockTransactionLine("Cash", "credit", 4000.00),
                ],
                date=base_date + timedelta(days=35),
                reference="RENT-001"
            ),
            
            MockTransactionData(
                description="Employee salary payments",
                lines=[
                    MockTransactionLine("Salary Expense", "debit", 8000.00),
                    MockTransactionLine("Cash", "credit", 8000.00),
                ],
                date=base_date + timedelta(days=40),
                reference="SAL-PAY-001"
            ),
            
            MockTransactionData(
                description="Utilities payment",
                lines=[
                    MockTransactionLine("Utilities Expense", "debit", 1200.00),
                    MockTransactionLine("Cash", "credit", 1200.00),
                ],
                date=base_date + timedelta(days=45),
                reference="UTIL-001"
            ),
        ]
        
        for i, transaction_data in enumerate(transactions, 1):
            try:
                transaction = await create_transaction(db, transaction_data)
                print(f"   ✅ Transaction {i}: {transaction_data.description}")
            except Exception as e:
                print(f"   ❌ Failed to create transaction: {e}")


async def generate_reports():
    """Generate and display all financial reports"""
    
    print("\n" + "=" * 50)
    print("📊 GENERATING FINANCIAL REPORTS")
    print("=" * 50)
    
    async with get_db_session() as db:
        
        # Trial Balance
        print("\n📋 TRIAL BALANCE")
        print("-" * 30)
        trial_balance = await generate_trial_balance(db)
        
        print(f"Report Date: {trial_balance['as_of_date']}")
        print(f"Total Accounts: {len(trial_balance['accounts'])}")
        print(f"Total Debits: ${trial_balance['totals']['total_debits']:,.2f}")
        print(f"Total Credits: ${trial_balance['totals']['total_credits']:,.2f}")
        print(f"Balanced: {'✅' if trial_balance['totals']['balanced'] else '❌'}")
        
        print("\nAccount Balances:")
        for account in trial_balance['accounts'][:10]:  # Show first 10
            debit = account['debit_balance']
            credit = account['credit_balance']
            if debit > 0:
                print(f"  {account['account_code']} - {account['account_name']:<25} Debit:  ${debit:>10,.2f}")
            if credit > 0:
                print(f"  {account['account_code']} - {account['account_name']:<25} Credit: ${credit:>10,.2f}")
        
        # Balance Sheet
        print("\n🏛️  BALANCE SHEET")
        print("-" * 30)
        balance_sheet = await generate_balance_sheet(db)
        
        print(f"Assets Total: ${balance_sheet['assets']['total']:,.2f}")
        print("  Key Assets:")
        for asset in balance_sheet['assets']['accounts'][:5]:
            print(f"    {asset['account_code']} - {asset['account_name']:<20} ${asset['balance']:>10,.2f}")
        
        print(f"\nLiabilities Total: ${balance_sheet['liabilities']['total']:,.2f}")
        for liability in balance_sheet['liabilities']['accounts']:
            print(f"    {liability['account_code']} - {liability['account_name']:<20} ${liability['balance']:>10,.2f}")
        
        print(f"\nEquity Total: ${balance_sheet['equity']['total']:,.2f}")
        for equity in balance_sheet['equity']['accounts']:
            print(f"    {equity['account_code']} - {equity['account_name']:<20} ${equity['balance']:>10,.2f}")
        
        print(f"\nEquation Check: Assets (${balance_sheet['totals']['total_assets']:,.2f}) = Liabilities + Equity (${balance_sheet['totals']['total_liabilities_equity']:,.2f})")
        print(f"Balanced: {'✅' if balance_sheet['totals']['balanced'] else '❌'}")
        
        # Income Statement
        print("\n💰 INCOME STATEMENT")
        print("-" * 30)
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        income_statement = await generate_income_statement(db, start_date, end_date)
        
        print(f"Period: {income_statement['period']['start_date']} to {income_statement['period']['end_date']}")
        
        print(f"\nRevenue: ${income_statement['income']['total']:,.2f}")
        for income in income_statement['income']['accounts']:
            print(f"  {income['account_code']} - {income['account_name']:<25} ${income['amount']:>10,.2f}")
        
        print(f"\nExpenses: ${income_statement['expenses']['total']:,.2f}")
        for expense in income_statement['expenses']['accounts']:
            print(f"  {expense['account_code']} - {expense['account_name']:<25} ${expense['amount']:>10,.2f}")
        
        net_income = income_statement['net_income']
        print(f"\nNet Income: ${net_income:,.2f} {'📈' if net_income > 0 else '📉'}")
        
        # Cash Flow
        print("\n💵 CASH FLOW STATEMENT")
        print("-" * 30)
        cash_flow = await generate_cash_flow_statement(db, start_date, end_date)
        
        if 'error' in cash_flow:
            print(f"Cash Flow: {cash_flow['error']}")
        else:
            summary = cash_flow['summary']
            print(f"Total Inflows: ${summary['total_inflows']:,.2f}")
            print(f"Total Outflows: ${summary['total_outflows']:,.2f}")
            print(f"Net Cash Flow: ${summary['net_cash_flow']:,.2f}")
            
            print(f"\nRecent Cash Movements:")
            for flow in cash_flow['cash_flows'][-5:]:  # Last 5 movements
                print(f"  {flow['date'][:10]} - {flow['description']:<30} {flow['type']:<8} ${flow['amount']:>10,.2f}")


async def main():
    """Main demo function"""
    try:
        await create_sample_data()
        await generate_reports()
        
        print("\n" + "=" * 50)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("\n📋 System Features Demonstrated:")
        print("  ✅ Double-entry bookkeeping with automatic validation")
        print("  ✅ Comprehensive chart of accounts")
        print("  ✅ Complex multi-line transactions")
        print("  ✅ Trial Balance with balance verification")
        print("  ✅ Balance Sheet with accounting equation")
        print("  ✅ Income Statement with profit calculation")
        print("  ✅ Cash Flow Statement with liquidity tracking")
        print("  ✅ Enterprise-grade financial reporting")
        
        print("\n🌐 Access the API documentation at: http://localhost:8000/docs")
        print("📊 Use the reporting endpoints to generate these reports via API")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())