from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
import logging

from ..dependencies import get_db
from ..services.ledger import (
    generate_trial_balance,
    generate_balance_sheet,
    generate_income_statement,
    generate_general_ledger,
    generate_cash_flow_statement,
)
from ..external_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["financial-reports"],
)


@router.get("/trial-balance",
           summary="📊 Trial Balance Report",
           description="""
           Generate Trial Balance showing all account balances.
           
           **Permission Required:** `financial:read`
           
           The Trial Balance lists all accounts with their debit and credit balances:
           - Verifies that total debits equal total credits
           - Shows account balances by type (Assets, Liabilities, Equity, Income, Expenses)
           - Essential for ensuring books are in balance
           - Can be generated for any specific date
           """)
async def get_trial_balance(
    as_of_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: current date)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate Trial Balance report."""
    logger.info(f"[REPORT] Trial Balance requested by user: {current_user.get('username')}")
    logger.info(f"[DEBUG] User details: is_superuser={current_user.is_superuser}, role={current_user.role}, permissions={current_user.permissions}")
    
    try:
        # Parse date if provided
        parsed_date = None
        if as_of_date:
            try:
                parsed_date = datetime.fromisoformat(as_of_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        report = await generate_trial_balance(db, parsed_date)
        logger.info(f"[SUCCESS] Trial Balance generated with {len(report['accounts'])} accounts")
        return report
        
    except Exception as e:
        logger.error(f"[ERROR] Error generating trial balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate trial balance")


@router.get("/balance-sheet",
           summary="📊 Balance Sheet Report", 
           description="""
           Generate Balance Sheet showing financial position.
           
           **Permission Required:** `financial:read`
           
           The Balance Sheet shows the company's financial position:
           - 💰 **Assets**: What the company owns
           - 📋 **Liabilities**: What the company owes  
           - 🏛️ **Equity**: Owner's stake in the company
           - ✅ **Equation**: Assets = Liabilities + Equity
           - 📈 **Retained Earnings**: Automatically calculated from income/expenses
           """)
async def get_balance_sheet(
    as_of_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: current date)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate Balance Sheet report."""
    logger.info(f"[REPORT] Balance Sheet requested by user: {current_user.get('username')}")
    
    try:
        # Parse date if provided
        parsed_date = None
        if as_of_date:
            try:
                parsed_date = datetime.fromisoformat(as_of_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        report = await generate_balance_sheet(db, parsed_date)
        logger.info(f"[SUCCESS] Balance Sheet generated - Assets: {report['totals']['total_assets']}")
        return report
        
    except Exception as e:
        logger.error(f"[ERROR] Error generating balance sheet: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate balance sheet")


@router.get("/income-statement",
           summary="📊 Income Statement (P&L)",
           description="""
           Generate Income Statement showing profitability over a period.
           
           **Permission Required:** `financial:read`
           
           The Income Statement shows financial performance:
           - 💚 **Revenue/Income**: Money earned from operations
           - 💸 **Expenses**: Costs incurred during operations
           - 🎯 **Net Income**: Revenue minus Expenses (profit/loss)
           - 📅 **Period-based**: Requires start_date, optional end_date
           - 📈 **Performance Analysis**: Track profitability trends
           """)
async def get_income_statement(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (default: current date)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate Income Statement (Profit & Loss) report."""
    logger.info(f"[REPORT] Income Statement requested by user: {current_user.get('username')} from {start_date} to {end_date or 'current'}")
    
    try:
        # Parse dates
        try:
            parsed_start_date = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        parsed_end_date = None
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        report = await generate_income_statement(db, parsed_start_date, parsed_end_date)
        logger.info(f"[SUCCESS] Income Statement generated - Net Income: {report['net_income']}")
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error generating income statement: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate income statement")


@router.get("/general-ledger",
           summary="📊 General Ledger Report",
           description="""
           Generate General Ledger showing detailed transaction history.
           
           **Permission Required:** `financial:read`
           
           The General Ledger provides detailed transaction analysis:
           - 📚 **All Transactions**: Complete transaction history by account
           - 💰 **Running Balances**: Real-time balance calculation
           - 🔍 **Account Filter**: Focus on specific account or view all
           - 📅 **Date Range**: Flexible period selection
           - 🎯 **Audit Trail**: Complete transaction tracking
           """)
async def get_general_ledger(
    account_id: Optional[int] = Query(None, description="Specific account ID (optional)"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (default: current date)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate General Ledger report."""
    logger.info(f"[REPORT] General Ledger requested by user: {current_user.get('username')} for account {account_id or 'ALL'}")
    logger.info(f"[DEBUG] User details: is_superuser={current_user.get('is_superuser')}, role={current_user.get('role')}, permissions={current_user.get('permissions')}")
    
    try:
        # Parse dates
        parsed_start_date = None
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        parsed_end_date = None
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        report = await generate_general_ledger(db, account_id, parsed_start_date, parsed_end_date)
        logger.info(f"[SUCCESS] General Ledger generated with {len(report['accounts'])} accounts")
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error generating general ledger: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate general ledger")


@router.get("/cash-flow",
           summary="📊 Cash Flow Statement",
           description="""
           Generate Cash Flow Statement showing cash movements.
           
           **Permission Required:** `financial:read`
           
           The Cash Flow Statement tracks cash movements:
           - 💵 **Cash Inflows**: Money coming into cash accounts (debits)
           - 💸 **Cash Outflows**: Money going out of cash accounts (credits)
           - 📊 **Net Cash Flow**: Total inflows minus total outflows
           - 📅 **Period Analysis**: Cash movements over specified time
           - 🏦 **Liquidity Tracking**: Monitor cash position changes
           """)
async def get_cash_flow_statement(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (default: current date)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate Cash Flow Statement."""
    logger.info(f"[REPORT] Cash Flow Statement requested by user: {current_user.get('username')} from {start_date} to {end_date or 'current'}")
    
    try:
        # Parse dates
        try:
            parsed_start_date = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        parsed_end_date = None
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        report = await generate_cash_flow_statement(db, parsed_start_date, parsed_end_date)
        logger.info(f"[SUCCESS] Cash Flow Statement generated with {len(report.get('cash_flows', []))} cash movements")
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error generating cash flow statement: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate cash flow statement")


@router.get("/dashboard",
           summary="📊 Financial Dashboard",
           description="""
           Get comprehensive financial dashboard with key metrics.
           
           **Permission Required:** `financial:read`
           
           The Dashboard provides an overview of financial health:
           - 💰 **Quick Balance Sheet Summary**
           - 📈 **Current Period Income Statement**
           - 🎯 **Key Performance Indicators**
           - ✅ **Accounting Equation Status**
           - 🔍 **Recent Transaction Activity**
           """)
async def get_financial_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate comprehensive financial dashboard."""
    logger.info(f"[REPORT] Financial Dashboard requested by user: {current_user.get('username')}")
    
    try:
        current_date = datetime.now(timezone.utc)
        year_start = datetime(current_date.year, 1, 1, tzinfo=timezone.utc)
        
        # Get key reports
        balance_sheet = await generate_balance_sheet(db, current_date)
        income_statement = await generate_income_statement(db, year_start, current_date)
        trial_balance = await generate_trial_balance(db, current_date)
        
        # Calculate key metrics
        total_assets = balance_sheet['totals']['total_assets']
        total_liabilities = balance_sheet['totals']['total_liabilities_equity'] - balance_sheet['equity']['total']
        net_worth = balance_sheet['equity']['total']
        ytd_income = income_statement['net_income']
        
        dashboard = {
            'report_type': 'Financial Dashboard',
            'as_of_date': current_date.isoformat(),
            'key_metrics': {
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'net_worth': net_worth,
                'ytd_net_income': ytd_income,
                'books_balanced': trial_balance['totals']['balanced']
            },
            'balance_sheet_summary': {
                'assets': balance_sheet['assets']['total'],
                'liabilities': balance_sheet['liabilities']['total'],
                'equity': balance_sheet['equity']['total']
            },
            'income_summary': {
                'total_income': income_statement['income']['total'],
                'total_expenses': income_statement['expenses']['total'],
                'net_income': income_statement['net_income']
            },
            'system_health': {
                'trial_balance_balanced': trial_balance['totals']['balanced'],
                'balance_sheet_balanced': balance_sheet['totals']['balanced'],
                'total_accounts': len(trial_balance['accounts'])
            }
        }
        
        logger.info(f"[SUCCESS] Financial Dashboard generated - Assets: {total_assets}, Net Income: {ytd_income}")
        return dashboard
        
    except Exception as e:
        logger.error(f"[ERROR] Error generating financial dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate financial dashboard")
