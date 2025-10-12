from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from ..dependencies import get_db
from ..schemas.schemas import AccountSchema
from ..services.ledger import get_all_accounts, create_account
from ..auth.dependencies import require_permission
from ..auth.schemas import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.get("", response_model=List[AccountSchema], 
           summary="[LIST] List All Accounts",
           description="""
           Retrieve all accounts in the chart of accounts.
           
           **Permission Required:** `account:read`
           
           Returns the complete chart of accounts including:
           - Account codes and names
           - Account types (asset, liability, equity, revenue, expense)
           - Current balances
           - Active status
           """)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("account:read"))
):
    """Get all accounts."""
    logger.info(f"[LIST] Retrieving all accounts for user: {current_user.username}")
    try:
        accounts = await get_all_accounts(db)
        logger.info(f"[SUCCESS] Successfully retrieved {len(accounts)} accounts")
        return accounts
    except Exception as e:
        logger.error(f"[ERROR] Error retrieving accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accounts")


@router.post("", response_model=AccountSchema,
            summary="➕ Create New Account", 
            description="""
            Create a new account in the chart of accounts.
            
            **Permission Required:** `account:create`
            
            **Account Types:**
            - `asset` - Assets (cash, inventory, equipment)
            - `liability` - Liabilities (accounts payable, loans)
            - `equity` - Owner's equity (capital, retained earnings)
            - `revenue` - Income accounts (sales, service revenue)
            - `expense` - Expense accounts (rent, utilities, salaries)
            """)
async def add_account(
    account: AccountSchema, 
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("account:create"))
):
    """Create a new account."""
    logger.info(f"[CREATE] Creating new account: {account.name} (Type: {account.type}, Code: {getattr(account, 'code', 'N/A')}) by user: {current_user.username}")
    try:
        new_account = await create_account(db, account)
        logger.info(f"[SUCCESS] Successfully created account: ID={new_account.id}, Name='{new_account.name}'")
        return new_account
    except ValueError as e:
        logger.warning(f"[WARNING] Business validation error creating account '{account.name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error creating account '{account.name}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create account")