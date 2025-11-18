import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

from ..config import ERP_BASE_URL

# Import TransactionSource from ledger service and create alias
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../ledger/backend'))
try:
    from app.services import ledger
    # Now you can use ledger.TransactionSource
except ImportError:
    # Fallback if import fails - create ledger module with TransactionSource
    import enum
    class _LedgerModule:
        class TransactionSource(enum.Enum):
            POS = "pos"
            API = "api"
            IMPORT = "import"
            MANUAL = "manual"
            WEB = "web"
    ledger = _LedgerModule()

logger = logging.getLogger(__name__)

class ERPIntegrationService:
    """Service responsible for posting accounting entries to the Ledger service.

    The ledger implements double-entry bookkeeping. For a POS cash sale we record:
    - Debit: Cash in Bank - Checking (asset increases)
    - Credit: Sales Revenue (revenue increases)

    If tax is present we still credit Sales Revenue for full amount (simple mode). This
    can be expanded later to split tax into a liability account once that account exists.
    """

    def __init__(self, ledger_base_url: Optional[str] = None):
        self.ledger_base_url = (ledger_base_url or ERP_BASE_URL).rstrip('/')
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def create_sale_entry(
        self,
        *,
        sale_number: str,
        total_amount: float,
        tax_amount: float = 0.0,
        discount_amount: float = 0.0,
        payment_method: str,
        items,  # List of SaleItemCreate; kept generic to avoid circular import
        customer_name: Optional[str] = None,
        notes: Optional[str] = None,
        auth_token: Optional[str] = None,
        cashier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a ledger transaction for a completed POS sale.

        Returns ledger transaction response or raises exception on failure. Failures
        should be caught by caller so the sale itself is not blocked.
        """
        logger.info(
            "LEDGER_POST_ATTEMPT sale_number=%s total=%.2f tax=%.2f discount=%.2f items=%d", 
            sale_number, total_amount, tax_amount, discount_amount, len(items)
        )

        # Basic double-entry lines (cash sale). Future enhancement: handle payment methods.
        lines = [
            {"account_name": "Cash in Bank - Checking", "type": "debit", "amount": round(total_amount, 2)},
            {"account_name": "Sales Revenue", "type": "credit", "amount": round(total_amount, 2)}
        ]

        # Use ledger.TransactionSource enum for type safety
        payload = {
            "description": f"POS Sale {sale_number}",
            "source": ledger.TransactionSource.pos.value,  # Uses enum value "pos"
            "reference": sale_number,
            "created_by": cashier,
            "lines": lines
        }

        # Log full payload before sending
        logger.info("=LEDGER_POST_PAYLOAD sale_number=%s payload=%s", sale_number, payload)

        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        url = f"{self.ledger_base_url}/transactions"
        logger.debug("LEDGER_POST_URL url=%s", url)
        try:
            response = await self.client.post(url, json=payload, headers=headers)
            logger.info("LEDGER_POST_STATUS sale_number=%s status=%s", sale_number, response.status_code)
            if response.status_code >= 400:
                detail = response.text
                logger.warning(
                    "LEDGER_POST_FAILED sale_number=%s status=%s body=%s", 
                    sale_number, response.status_code, detail
                )
                raise RuntimeError(f"Ledger transaction failed: {response.status_code} {detail}")
            data = response.json()
            logger.info("LEDGER_POST_SUCCESS sale_number=%s ledger_id=%s", sale_number, data.get("id"))
            return data
        except Exception as e:
            logger.error("LEDGER_POST_EXCEPTION sale_number=%s error=%s", sale_number, str(e))
            raise

erp_service = ERPIntegrationService()
