#!/usr/bin/env python3
"""
Create sample cash accounts and transactions for testing the Cash Flow Statement
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import create_session
from app.services.ledger import Account, Transaction, TransactionLine, AccountType, TransactionSource

async def create_sample_data():
    """Create sample cash accounts and transactions"""
    print("Creating sample cash accounts and transactions...")
    
    async with create_session() as db:
        try:
            # Check if cash accounts already exist
            existing_accounts = await db.execute(
                "SELECT COUNT(*) FROM accounts WHERE name ILIKE '%cash%'"
            )
            count = existing_accounts.scalar()
            
            if count > 0:
                print(f"Found {count} existing cash accounts. Skipping creation.")
                return
            
            # Create sample cash accounts
            cash_accounts = [
                Account(
                    name="Petty Cash",
                    code="1100",
                    type=AccountType.ASSET,
                    description="Small cash on hand for minor expenses"
                ),
                Account(
                    name="Cash in Bank - Checking",
                    code="1110", 
                    type=AccountType.ASSET,
                    description="Primary checking account"
                ),
                Account(
                    name="Cash in Bank - Savings",
                    code="1120",
                    type=AccountType.ASSET,
                    description="Savings account"
                )
            ]
            
            # Create other accounts for transactions
            other_accounts = [
                Account(
                    name="Sales Revenue",
                    code="4000",
                    type=AccountType.INCOME,
                    description="Revenue from sales"
                ),
                Account(
                    name="Office Supplies Expense", 
                    code="5100",
                    type=AccountType.EXPENSE,
                    description="Office supplies and materials"
                ),
                Account(
                    name="Rent Expense",
                    code="5200", 
                    type=AccountType.EXPENSE,
                    description="Monthly rent payments"
                )
            ]
            
            all_accounts = cash_accounts + other_accounts
            
            # Add accounts to database
            for account in all_accounts:
                db.add(account)
            
            await db.commit()
            
            # Refresh to get IDs
            for account in all_accounts:
                await db.refresh(account)
            
            print(f"Created {len(all_accounts)} accounts")
            
            # Create sample transactions
            base_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            transactions = [
                # Sale - cash inflow
                {
                    'date': base_date + timedelta(days=1),
                    'description': 'Cash sale to customer',
                    'lines': [
                        {'account': cash_accounts[1], 'type': 'debit', 'amount': Decimal('1500.00')},  # Cash in Bank
                        {'account': other_accounts[0], 'type': 'credit', 'amount': Decimal('1500.00')}  # Sales Revenue
                    ]
                },
                # Rent payment - cash outflow
                {
                    'date': base_date + timedelta(days=5),
                    'description': 'Monthly rent payment',
                    'lines': [
                        {'account': other_accounts[2], 'type': 'debit', 'amount': Decimal('800.00')},   # Rent Expense  
                        {'account': cash_accounts[1], 'type': 'credit', 'amount': Decimal('800.00')}   # Cash in Bank
                    ]
                },
                # Office supplies - cash outflow
                {
                    'date': base_date + timedelta(days=10),
                    'description': 'Office supplies purchase',
                    'lines': [
                        {'account': other_accounts[1], 'type': 'debit', 'amount': Decimal('150.00')},   # Office Supplies
                        {'account': cash_accounts[0], 'type': 'credit', 'amount': Decimal('150.00')}    # Petty Cash
                    ]
                },
                # Another sale - cash inflow
                {
                    'date': base_date + timedelta(days=15),
                    'description': 'Customer payment received',
                    'lines': [
                        {'account': cash_accounts[1], 'type': 'debit', 'amount': Decimal('2200.00')},  # Cash in Bank
                        {'account': other_accounts[0], 'type': 'credit', 'amount': Decimal('2200.00')} # Sales Revenue
                    ]
                },
                # Transfer between cash accounts
                {
                    'date': base_date + timedelta(days=20),
                    'description': 'Transfer to savings',
                    'lines': [
                        {'account': cash_accounts[2], 'type': 'debit', 'amount': Decimal('1000.00')},  # Savings
                        {'account': cash_accounts[1], 'type': 'credit', 'amount': Decimal('1000.00')} # Checking
                    ]
                }
            ]
            
            for transaction_data in transactions:
                # Create transaction
                transaction = Transaction(
                    date=transaction_data['date'],
                    description=transaction_data['description'],
                    source=TransactionSource.manual
                )
                db.add(transaction)
                await db.flush()  # Get the ID
                
                # Create transaction lines
                for line_data in transaction_data['lines']:
                    line = TransactionLine(
                        transaction_id=transaction.id,
                        account_id=line_data['account'].id,
                        type=line_data['type'],
                        amount=line_data['amount']
                    )
                    db.add(line)
            
            await db.commit()
            print(f"Created {len(transactions)} sample transactions")
            print("Sample data creation completed successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"Error creating sample data: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(create_sample_data())