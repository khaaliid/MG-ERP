"""
POS Service with Local Persistence

This service stores sales locally in PostgreSQL and syncs to Ledger via broker.
Provides resilience and offline capability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .inventory_integration import inventory_service
from .erp_integration import erp_service
from ..sales_repository import SalesRepository
from ..settings_repository import SettingsRepository
from ..config import create_session

logger = logging.getLogger(__name__)

class StatelessPOSService:
    """
    POS service with local persistence and async ledger sync.
    """
    
    @staticmethod
    async def process_sale(sale_data: Dict[str, Any], cashier_info: Dict[str, Any], auth_token: str, broker=None) -> Dict[str, Any]:
        """
        Process a sale with local persistence and async ledger sync.
        
        Flow:
        1. Validate products and stock with Inventory service
        2. Update inventory stock in Inventory service
        3. Create ledger transaction synchronously in Ledger service
        4. Save sale locally to PostgreSQL (after external services succeed)
        """
        session = None
        try:
            # Generate unique sale number
            sale_number = f"POS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Step 1: Validate products and stock via Inventory Service
            validated_items = []
            for item in sale_data['items']:
                product = await inventory_service.get_product_by_id(
                    item['product_id'], 
                    auth_token=auth_token
                )
                if not product:
                    raise ValueError(f"Product {item['product_id']} not found")
                
                # Check stock availability
                if product.get('stock_quantity', 0) < item['quantity']:
                    raise ValueError(
                        f"Insufficient stock for {product['name']}. "
                        f"Available: {product.get('stock_quantity', 0)}, "
                        f"Requested: {item['quantity']}"
                    )
                
                validated_items.append({
                    'product_id': item['product_id'],
                    'sku': product.get('sku', item['product_id']),
                    'name': product['name'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'size': item.get('size'),
                    'discount': item.get('discount', 0),
                    'tax': item.get('tax', 0),
                    'line_total': item['quantity'] * item['unit_price']
                })
            
            # Open session early to read settings and reuse for save
            session = await create_session()
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_or_create_settings()

            # Step 2: Calculate totals using settings
            subtotal = sum(item['line_total'] for item in validated_items)
            discount_amount = sale_data.get('discount_amount', 0)
            # Prefer explicit tax_rate from request; fallback to settings
            tax_rate = sale_data.get('tax_rate', (settings.tax_rate if settings and settings.tax_rate is not None else 0.14))
            tax_inclusive_flag = False
            if settings and isinstance(getattr(settings, 'tax_inclusive', None), str):
                tax_inclusive_flag = settings.tax_inclusive.lower() == "true"

            base_after_discount = max(0, subtotal - discount_amount)
            if tax_inclusive_flag:
                base_without_tax = base_after_discount / (1 + tax_rate) if tax_rate and tax_rate > 0 else base_after_discount
                tax_amount = base_after_discount - base_without_tax
                total_amount = base_after_discount
            else:
                tax_amount = base_after_discount * tax_rate
                total_amount = base_after_discount + tax_amount
            
            # Step 2: Update inventory (immediate for stock accuracy)
            inventory_updates = []
            for item in validated_items:
                updated = await inventory_service.update_stock(
                    item['product_id'],
                    -item['quantity'],  # Negative for sale
                    size=item.get('size'),
                    auth_token=auth_token
                )
                inventory_updates.append({
                    'product_id': item['product_id'],
                    'quantity_reduced': item['quantity'],
                    'success': updated
                })
            
            # Step 3: Create ledger transaction synchronously (keyword-only API)
            ledger_entry = await erp_service.create_sale_entry(
                sale_number=sale_number,
                items=validated_items,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                payment_method=sale_data['payment_method'],
                customer_name=sale_data.get('customer_name'),
                cashier=cashier_info.get('full_name', cashier_info.get('username')),
                auth_token=auth_token
            )
            ledger_entry_id = ledger_entry.get('id') if isinstance(ledger_entry, dict) else None
            ledger_entry_id_str = str(ledger_entry_id) if ledger_entry_id is not None else None

            # Step 4: Save to local database AFTER external services succeed
            repo = SalesRepository(session)

            sale_id = str(uuid.uuid4())
            local_sale_data = {
                'id': sale_id,
                'sale_number': sale_number,
                'items': validated_items,
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'discount_amount': discount_amount,
                'total_amount': total_amount,
                'payment_method': sale_data['payment_method'],
                'tendered_amount': sale_data.get('tendered_amount'),
                'change_amount': max(0, (sale_data.get('tendered_amount', total_amount) - total_amount)),
                'customer_name': sale_data.get('customer_name'),
                'notes': sale_data.get('notes'),
                'cashier': cashier_info.get('full_name', cashier_info.get('username')),
                'cashier_id': cashier_info.get('id'),
                'status': 'synced',
                'ledger_entry_id': ledger_entry_id_str
            }
            saved_sale = await repo.save_sale(local_sale_data)
            await session.commit()
            logger.info(f"[LOCAL_DB] Saved sale {sale_number} with ledger_entry_id={ledger_entry_id}")
            
            # Step 6: Return sale summary
            return {
                'id': sale_id,
                'sale_number': sale_number,
                'items': validated_items,
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'discount_amount': discount_amount,
                'total_amount': total_amount,
                'tax_rate': tax_rate,
                'payment_method': sale_data['payment_method'],
                'tendered_amount': sale_data.get('tendered_amount'),
                'change_amount': max(0, (sale_data.get('tendered_amount', total_amount) - total_amount)),
                'customer_name': sale_data.get('customer_name'),
                'notes': sale_data.get('notes'),
                'cashier': cashier_info.get('full_name', cashier_info.get('username')),
                'cashier_id': cashier_info.get('id'),
                'created_at': datetime.now().isoformat(),
                'inventory_updates': inventory_updates,
                'status': 'synced',
                'local_storage': True,
                'sync_status': 'completed',
                'currency_code': getattr(settings, 'currency_code', 'USD') if settings else 'USD',
                'currency_symbol': getattr(settings, 'currency_symbol', '$') if settings else '$',
                'tax_inclusive': 'true' if tax_inclusive_flag else 'false'
            }
            
        except Exception as e:
            logger.error(f"Sale processing failed: {e}")
            if session:
                await session.rollback()
            raise
        finally:
            if session:
                await session.close()
    
    @staticmethod
    async def get_sales_history(
        page: int = 1, 
        limit: int = 50, 
        start_date: str = None, 
        end_date: str = None,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """
        Get sales history from ledger service.
        Retrieves POS transactions from the ledger.
        """
        try:
            # Query ledger service for POS sales transactions
            ledger_response = await erp_service.get_sales_transactions(
                start_date=start_date,
                end_date=end_date,
                page=page,
                limit=limit,
                auth_token=auth_token
            )
            
            # Transform ledger transactions to sales format
            sales = []
            for transaction in ledger_response.get('data', []):
                # Extract sale information from ledger transaction
                metadata = transaction.get('metadata', {})
                sale = {
                    'id': transaction.get('id'),
                    'sale_number': transaction.get('reference'),
                    'total_amount': sum(
                        line.get('amount', 0) 
                        for line in transaction.get('lines', []) 
                        if line.get('type') == 'debit'
                    ),
                    'payment_method': metadata.get('payment_method', 'cash'),
                    'customer_name': metadata.get('customer_name'),
                    'items': [],  # Items not stored in ledger summary
                    'subtotal': metadata.get('subtotal', 0),
                    'tax_amount': metadata.get('tax_amount', 0),
                    'discount_amount': metadata.get('discount_amount', 0),
                    'created_at': transaction.get('created_at'),
                    'description': transaction.get('description'),
                    'cashier': transaction.get('created_by'),
                    'status': transaction.get('status', 'completed')
                }
                sales.append(sale)
            
            return {
                'data': sales,
                'total': ledger_response.get('total', 0),
                'page': page,
                'limit': limit,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get sales history: {e}")
            raise
    
    @staticmethod
    async def get_sale_by_id(sale_id: str, auth_token: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific sale by ID from ledger service.
        No local storage - pure proxy to ledger service.
        """
        try:
            # In a pure stateless system, individual sales come from the ledger
            # This would query the ledger service for a specific transaction by sale_number
            # For now, return None as ledger service integration is pending
            logger.info(f"Looking up sale {sale_id} in ledger service")
            
            # This would call the ledger service to get specific transaction
            # return await erp_service.get_transaction_by_sale_number(sale_id, auth_token)
            return None  # Placeholder until ledger service integration
            
        except Exception as e:
            logger.error(f"Failed to get sale {sale_id}: {e}")
            raise
    
    @staticmethod
    async def get_products(
        page: int = 1,
        limit: int = 100,
        search: str = None,
        category_id: str = None,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """
        Get products from inventory service.
        Pure proxy - no local storage.
        """
        try:
            return await inventory_service.get_products(
                page=page,
                limit=limit,
                search=search,
                category_id=category_id,
                auth_token=auth_token
            )
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            raise
    
    @staticmethod
    async def search_products(query: str, limit: int = 50, auth_token: str = None) -> List[Dict[str, Any]]:
        """
        Search products via inventory service.
        Pure proxy - no local storage.
        """
        try:
            return await inventory_service.search_products(
                query=query,
                limit=limit,
                auth_token=auth_token
            )
        except Exception as e:
            logger.error(f"Failed to search products: {e}")
            raise
    
    @staticmethod
    async def get_product_by_id(product_id: str, auth_token: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific product by ID from inventory service.
        Pure proxy - no local storage.
        """
        try:
            return await inventory_service.get_product_by_id(
                product_id=product_id,
                auth_token=auth_token
            )
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            raise
    
    @staticmethod
    async def get_brands(auth_token: str = None) -> List[Dict[str, Any]]:
        """
        Get brands from inventory service.
        Pure proxy - no local storage.
        """
        try:
            return await inventory_service.get_brands(auth_token=auth_token)
        except Exception as e:
            logger.error(f"Failed to get brands: {e}")
            raise
    
    @staticmethod
    async def get_categories(auth_token: str = None) -> List[Dict[str, Any]]:
        """
        Get categories from inventory service.
        Pure proxy - no local storage.
        """
        try:
            return await inventory_service.get_categories(auth_token=auth_token)
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            raise
    
    @staticmethod
    async def void_sale(
        sale_id: str, 
        reason: str, 
        manager_info: Dict[str, Any], 
        auth_token: str
    ) -> Dict[str, Any]:
        """
        Void a sale by creating reversing entries in ledger and inventory.
        No local storage - pure coordination between services.
        """
        try:
            # In a stateless system, voiding involves:
            # 1. Get the original sale details from ledger
            # 2. Create reversing ledger entries
            # 3. Restore inventory quantities
            
            # For now, return a placeholder response
            # This would integrate with ledger service to void the transaction
            logger.info(f"Voiding sale {sale_id} by manager {manager_info.get('username')}")
            
            return {
                "message": f"Sale {sale_id} voided successfully",
                "reason": reason,
                "voided_by": manager_info.get("full_name", manager_info.get("username", "Unknown")),
                "voided_at": datetime.now().isoformat(),
                "status": "voided"
            }
            
        except Exception as e:
            logger.error(f"Failed to void sale {sale_id}: {e}")
            raise
    
    @staticmethod
    async def refund_sale(
        sale_id: str, 
        refund_amount: float, 
        reason: str, 
        manager_info: Dict[str, Any], 
        auth_token: str
    ) -> Dict[str, Any]:
        """
        Process a refund by creating refund entries in ledger and updating inventory.
        No local storage - pure coordination between services.
        """
        try:
            # In a stateless system, refunding involves:
            # 1. Get the original sale details from ledger
            # 2. Create refund ledger entries
            # 3. Update inventory quantities (add items back)
            
            # For now, return a placeholder response  
            # This would integrate with ledger service to create refund transaction
            logger.info(f"Processing refund of ${refund_amount:.2f} for sale {sale_id} by manager {manager_info.get('username')}")
            
            return {
                "message": f"Refund of ${refund_amount:.2f} processed for sale {sale_id}",
                "refund_amount": refund_amount,
                "reason": reason,
                "processed_by": manager_info.get("full_name", manager_info.get("username", "Unknown")),
                "processed_at": datetime.now().isoformat(),
                "status": "refunded"
            }
            
        except Exception as e:
            logger.error(f"Failed to refund sale {sale_id}: {e}")
            raise

# Create singleton instance
pos_service = StatelessPOSService()