import httpx
from typing import Optional
import logging
from ..config import ERP_BASE_URL, ERP_USERNAME, ERP_PASSWORD

logger = logging.getLogger(__name__)

class ERPIntegrationService:
    """Service to integrate POS sales with the main ERP ledger system"""
    
    def __init__(self):
        self.base_url = ERP_BASE_URL
        self.username = ERP_USERNAME
        self.password = ERP_PASSWORD
        self.token = None
    
    async def get_auth_token(self) -> Optional[str]:
        """Authenticate with ERP and get JWT token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    data={
                        "username": self.username,
                        "password": self.password
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    return self.token
                else:
                    logger.error(f"Failed to authenticate with ERP: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error authenticating with ERP: {str(e)}")
            return None
    
    async def create_pos_transaction(self, sale_data: dict) -> Optional[int]:
        """Create a transaction in the ERP ledger for POS sale"""
        if not self.token:
            await self.get_auth_token()
        
        if not self.token:
            logger.error("No auth token available for ERP integration")
            return None
        
        try:
            # Prepare transaction data for double-entry bookkeeping
            transaction_data = {
                "description": f"POS Sale #{sale_data['sale_number']} - {sale_data.get('customer_name', 'Walk-in Customer')}",
                "date": sale_data["sale_date"],
                "source": "POS",
                "reference": sale_data["sale_number"],
                "lines": [
                    {
                        "account_id": 2,  # Cash in Bank - Checking (assuming this exists)
                        "type": "debit",
                        "amount": sale_data["total_amount"]
                    },
                    {
                        "account_id": 3,  # Sales Revenue (assuming this exists)
                        "type": "credit", 
                        "amount": sale_data["total_amount"]
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/transactions",
                    json=transaction_data,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 201:
                    transaction = response.json()
                    logger.info(f"Created ERP transaction {transaction['id']} for POS sale {sale_data['sale_number']}")
                    return transaction["id"]
                else:
                    logger.error(f"Failed to create ERP transaction: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating ERP transaction: {str(e)}")
            return None
    
    async def get_accounts(self) -> list:
        """Get chart of accounts from ERP"""
        if not self.token:
            await self.get_auth_token()
        
        if not self.token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/accounts/",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get accounts from ERP: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting accounts from ERP: {str(e)}")
            return []

# Global instance
erp_service = ERPIntegrationService()