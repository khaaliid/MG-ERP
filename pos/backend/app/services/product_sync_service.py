"""
Product Sync Service - Fetch from Inventory and Cache Locally

Provides functionality to:
- Fetch all products from Inventory service
- Store/update them in local POS database
- Schedule automatic hourly sync
- Provide manual sync endpoint
"""

import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import INVENTORY_SERVICE_URL, SessionLocal
from ..localdb import Product, Category

logger = logging.getLogger(__name__)


class ProductSyncService:
    """Service to sync products from Inventory to POS local cache"""
    
    def __init__(self):
        self.inventory_base_url = INVENTORY_SERVICE_URL.rstrip('/')
        self._client = None
    
    @property
    def client(self):
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def fetch_all_products_from_inventory(self, auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all products from inventory service with pagination"""
        all_products = []
        page = 1
        limit = 100
        
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        try:
            while True:
                url = f"{self.inventory_base_url}/api/v1/products/"
                params = {"page": page, "limit": limit}
                
                logger.info(f"Fetching inventory products page {page}...")
                response = await self.client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                products = data.get('data', [])
                
                if not products:
                    break
                
                all_products.extend(products)
                logger.info(f"Retrieved {len(products)} products from page {page}")
                
                # Check if there are more pages
                total = data.get('total', 0)
                if len(all_products) >= total:
                    break
                    
                page += 1
            
            logger.info(f"Total products fetched from inventory: {len(all_products)}")
            return all_products
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching products from inventory: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching products from inventory: {str(e)}")
            raise

    async def fetch_all_categories_from_inventory(self, auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all categories from inventory service"""
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        try:
            url = f"{self.inventory_base_url}/api/v1/categories/"
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            categories = data.get('data')
            return categories if isinstance(categories, list) else []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching categories from inventory: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching categories from inventory: {str(e)}")
            raise
    
    def _transform_inventory_product(self, inv_product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform inventory product to POS product format"""
        # Calculate stock from sizes if present
        stock_quantity = 0
        if 'sizes' in inv_product and isinstance(inv_product['sizes'], list):
            stock_quantity = sum(
                size.get('quantity', 0) 
                for size in inv_product['sizes'] 
                if isinstance(size, dict)
            )
        elif 'stock_quantity' in inv_product:
            stock_quantity = inv_product.get('stock_quantity', 0)
        
        # Get price (prefer selling_price/sellingPrice)
        price = 0.0
        if 'sellingPrice' in inv_product:
            price = inv_product['sellingPrice']
        elif 'selling_price' in inv_product:
            price = inv_product['selling_price']
        elif 'price' in inv_product:
            price = inv_product['price']
        
        cost_price = inv_product.get('costPrice') or inv_product.get('cost_price')
        
        return {
            'id': str(inv_product.get('id')),
            'sku': inv_product.get('sku', 'N/A'),
            'name': inv_product.get('name', 'Unknown Product'),
            'description': inv_product.get('description'),
            'price': float(price) if price else 0.0,
            'cost_price': float(cost_price) if cost_price else None,
            'stock_quantity': int(stock_quantity),
            'category_id': str(inv_product['category']['id']) if inv_product.get('category') and isinstance(inv_product['category'], dict) else None,
            'category_name': inv_product['category'].get('name') if inv_product.get('category') and isinstance(inv_product['category'], dict) else None,
            'brand_id': str(inv_product['brand']['id']) if inv_product.get('brand') and isinstance(inv_product['brand'], dict) else None,
            'brand_name': inv_product['brand'].get('name') if inv_product.get('brand') and isinstance(inv_product['brand'], dict) else None,
            'barcode': inv_product.get('barcode'),
            'is_active': 'true',
            'synced_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    
    async def sync_products_to_local_db(self, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Sync all products from inventory to local POS database"""
        start_time = datetime.now(timezone.utc)
        
        # Check if auth token is provided
        if not auth_token:
            logger.warning("[PRODUCT_SYNC] No auth token provided - skipping sync")
            return {
                "status": "skipped",
                "message": "Sync skipped: authentication required",
                "synced": 0,
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
        
        logger.info("[PRODUCT_SYNC] Starting product sync from inventory...")
        
        try:
            # Fetch products from inventory
            inventory_products = await self.fetch_all_products_from_inventory(auth_token)
            
            if not inventory_products:
                logger.warning("[PRODUCT_SYNC] No products found in inventory")
                return {
                    "status": "success",
                    "message": "No products to sync",
                    "synced": 0,
                    "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
                }
            
            # Transform and upsert to local DB
            async with SessionLocal() as db:
                synced_count = 0
                
                for inv_product in inventory_products:
                    try:
                        pos_product_data = self._transform_inventory_product(inv_product)
                        
                        # Check if product exists
                        result = await db.execute(
                            select(Product).where(Product.id == pos_product_data['id'])
                        )
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            # Update existing product
                            logger.info(f"Updating product {pos_product_data['id']} - {pos_product_data['name']}")
                            await db.execute(
                                update(Product)
                                .where(Product.id == pos_product_data['id'])
                                .values(**pos_product_data)
                            )
                        else:
                            # Insert new product
                            logger.info(f"Inserting new product {pos_product_data['id']} - {pos_product_data['name']}")
                            new_product = Product(**pos_product_data)
                            db.add(new_product)
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing product {inv_product.get('id')}: {str(e)}")
                        continue
                
                await db.commit()
                logger.info(f"[PRODUCT_SYNC] Successfully synced {synced_count} products to local database")
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                "status": "success",
                "message": f"Successfully synced {synced_count} products",
                "synced": synced_count,
                "duration_seconds": duration,
                "synced_at": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"[PRODUCT_SYNC] Failed to sync products: {str(e)}")
            return {
                "status": "error",
                "message": f"Sync failed: {str(e)}",
                "synced": 0,
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
    
    async def sync_categories_to_local_db(self, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Sync all categories from inventory to local POS database"""
        start_time = datetime.now(timezone.utc)
        
        # Check if auth token is provided
        if not auth_token:
            logger.warning("[CATEGORY_SYNC] No auth token provided - skipping sync")
            return {
                "status": "skipped",
                "message": "Sync skipped: authentication required",
                "synced": 0,
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
        
        logger.info("[CATEGORY_SYNC] Starting category sync from inventory...")
        
        try:
            # Fetch categories from inventory
            inventory_categories = await self.fetch_all_categories_from_inventory(auth_token)
            
            if not inventory_categories:
                logger.warning("[CATEGORY_SYNC] No categories found in inventory")
                return {
                    "status": "success",
                    "message": "No categories to sync",
                    "synced": 0,
                    "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
                }
            
            # Upsert to local DB
            async with SessionLocal() as db:
                synced_count = 0
                
                for cat in inventory_categories:
                    try:
                        cat_id = str(cat.get('id')) if cat.get('id') is not None else None
                        if not cat_id:
                            continue
                        
                        cat_data = {
                            'id': cat_id,
                            'name': cat.get('name') or '',
                            'description': cat.get('description')
                        }
                        
                        result = await db.execute(select(Category).where(Category.id == cat_id))
                        existing_cat = result.scalar_one_or_none()
                        
                        if existing_cat:
                            await db.execute(
                                update(Category)
                                .where(Category.id == cat_id)
                                .values(**cat_data)
                            )
                        else:
                            db.add(Category(**cat_data))
                        
                        synced_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing category {cat.get('id')}: {str(e)}")
                        continue
                
                await db.commit()
                logger.info(f"[CATEGORY_SYNC] Successfully synced {synced_count} categories to local database")
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                "status": "success",
                "message": f"Successfully synced {synced_count} categories",
                "synced": synced_count,
                "duration_seconds": duration,
                "synced_at": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"[CATEGORY_SYNC] Failed to sync categories: {str(e)}")
            return {
                "status": "error",
                "message": f"Sync failed: {str(e)}",
                "synced": 0,
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
    
    async def get_cached_products(
        self, 
        db: AsyncSession,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Product]:
        """Get products from local cache with optional search"""
        query = select(Product).where(Product.is_active == 'true')
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Product.name.ilike(search_pattern)) |
                (Product.sku.ilike(search_pattern)) |
                (Product.description.ilike(search_pattern))
            )
        
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


# Global service instance
product_sync_service = ProductSyncService()
