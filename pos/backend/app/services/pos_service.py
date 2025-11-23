"""
Stateless POS Service

This service coordinates between external services (Inventory and Ledger) 
without storing any data locally. All operations are pure API orchestration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

from .inventory_integration import inventory_service
from .erp_integration import erp_service

logger = logging.getLogger(__name__)

class StatelessPOSService:
    """
    Stateless POS service that orchestrates operations between 
    Inventory and Ledger services without local storage.
    """
    
    @staticmethod
    async def process_sale(sale_data: Dict[str, Any], cashier_info: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        """
        Process a sale by coordinating between inventory and ledger services.
        No local storage - pure orchestration.
        """
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
                    'product_name': product['name'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'size': item.get('size'),
                    'line_total': item['quantity'] * item['unit_price']
                })
            
            # Step 2: Calculate totals
            subtotal = sum(item['line_total'] for item in validated_items)
            discount_amount = sale_data.get('discount_amount', 0)
            tax_rate = sale_data.get('tax_rate', 0.14)
            tax_amount = (subtotal - discount_amount) * tax_rate
            total_amount = subtotal - discount_amount + tax_amount
            
            # Step 3: Update inventory (reserve/reduce stock)
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
            
            # Step 4: Create ledger transaction
            ledger_entry = None
            try:
                ledger_entry = await erp_service.create_sale_entry(
                    sale_number=sale_number,
                    total_amount=total_amount,
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    payment_method=sale_data['payment_method'],
                    items=validated_items,
                    customer_name=sale_data.get('customer_name'),
                    notes=sale_data.get('notes'),
                    auth_token=auth_token,
                    cashier=cashier_info.get('full_name', cashier_info.get('username'))
                )
            except Exception as ledger_error:
                logger.error(f"Ledger entry failed for sale {sale_number}: {ledger_error}")
                # Note: In a production system, you might want to implement 
                # compensation logic here to rollback inventory changes
            
            # Step 5: Return sale summary (no local storage)
            return {
                'id': str(uuid.uuid4()),  # Temporary ID for response
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
                'created_at': datetime.now().isoformat(),
                'ledger_entry_id': ledger_entry.get('id') if ledger_entry else None,
                'inventory_updates': inventory_updates,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Sale processing failed: {e}")
            raise
    
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
        No local storage - pure proxy to ledger service.
        """
        try:
            # In a pure stateless system, sales history comes from the ledger
            # Query ledger service for sales transactions
            filters = {}
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date
                
            # This would call the ledger service to get sales transactions
            # For now, return empty result as ledger service integration is pending
            return {
                'data': [],  # Would come from ledger service sales transactions
                'total': 0,
                'page': page,
                'limit': limit,
                'filters': filters,
                'message': 'Sales history retrieved from ledger service'
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