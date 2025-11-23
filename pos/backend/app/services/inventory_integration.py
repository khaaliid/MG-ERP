"""
Inventory Integration Service for POS System

This service handles communication between the POS system and the Inventory module.
It fetches product data from the inventory system and manages stock updates.
"""

import httpx
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from ..config import INVENTORY_SERVICE_URL

logger = logging.getLogger(__name__)

class InventoryIntegrationService:
    """Service to integrate POS with Inventory backend"""
    
    def __init__(self, inventory_base_url: Optional[str] = None):
        self.inventory_base_url = (inventory_base_url or INVENTORY_SERVICE_URL).rstrip('/')
        self._client = None
    
    @property
    def client(self):
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Don't close the client here - keep it alive for reuse
        pass
    
    def _transform_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform inventory service product data to POS format"""
        if not isinstance(product_data, dict):
            return product_data
            
        # Create a copy to avoid modifying original data
        transformed = product_data.copy()
        
        # Map sellingPrice to price for POS frontend
        if 'sellingPrice' in transformed:
            transformed['price'] = transformed['sellingPrice']
        elif 'selling_price' in transformed:
            transformed['price'] = transformed['selling_price']
        
        # Ensure price is a number, default to 0 if missing
        if 'price' not in transformed or transformed['price'] is None:
            transformed['price'] = 0
            
        # Ensure required fields exist
        if 'name' not in transformed:
            transformed['name'] = 'Unknown Product'
        if 'sku' not in transformed:
            transformed['sku'] = 'N/A'

        # Stock quantity normalization (was in _transform_product, re-added here)
        if 'stock_quantity' not in transformed:
            stock = None
            # Sum quantities from sizes list if present
            if 'sizes' in transformed and isinstance(transformed['sizes'], list):
                stock = sum(
                    s.get('quantity', 0) for s in transformed['sizes']
                    if isinstance(s, dict)
                )
            # Fallback fields that might represent stock
            if stock is None:
                for key in ['quantity', 'stock', 'current_stock']:
                    if isinstance(transformed.get(key), (int, float)):
                        stock = transformed[key]
                        break
            transformed['stock_quantity'] = int(stock) if isinstance(stock, (int, float)) and stock is not None else transformed.get('stock_quantity', 0)
            if transformed['stock_quantity'] == 0:
                logger.debug(f"Stock quantity defaulted to 0 for product id={transformed.get('id')} name={transformed.get('name')}")
            
        return transformed
    
    def _transform_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform inventory service product data to POS expected format."""
        transformed = product.copy()
        
        # Map selling_price/sellingPrice to price for POS
        if 'sellingPrice' in product:
            transformed['price'] = product['sellingPrice']
        elif 'selling_price' in product:
            transformed['price'] = product['selling_price']
        elif 'price' not in product:
            # Fallback to cost price if no selling price
            if 'costPrice' in product:
                transformed['price'] = product['costPrice']
            elif 'cost_price' in product:
                transformed['price'] = product['cost_price']
            else:
                transformed['price'] = 0.0
        
        # Ensure stock_quantity is set
        if 'stock_quantity' not in transformed and 'sizes' in product and isinstance(product['sizes'], list):
            # Calculate total stock from sizes
            total_stock = sum(size.get('quantity', 0) for size in product['sizes'] if isinstance(size, dict))
            transformed['stock_quantity'] = total_stock
        
        return transformed
    
    async def get_products(self, 
                          page: int = 1, 
                          limit: int = 100, 
                          search: Optional[str] = None,
                          category_id: Optional[str] = None,
                          brand_id: Optional[str] = None,
                          auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch products from inventory system
        
        Args:
            page: Page number for pagination
            limit: Number of products per page
            search: Search term for product name, SKU, or description
            category_id: Filter by category
            brand_id: Filter by brand
            
        Returns:
            Dict containing products data with pagination info
        """
        try:
            params = {
                "page": page,
                "limit": limit
            }
            
            if search:
                params["search"] = search
            if category_id:
                params["category_id"] = category_id
            if brand_id:
                params["brand_id"] = brand_id
            
            url = f"{self.inventory_base_url}/api/v1/products/"
            logger.info(f"Fetching products from inventory: {url} with params: {params}")
            
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched {len(data.get('data', []))} products from inventory")
            
            # Transform product data to match POS expectations
            if 'data' in data and isinstance(data['data'], list):
                data['data'] = [self._transform_product_data(product) for product in data['data']]
            
            return data
            
        except httpx.TimeoutException:
            logger.error("Timeout while fetching products from inventory service")
            raise HTTPException(status_code=503, detail="Inventory service is unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching products: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail="Error fetching products from inventory")
        except Exception as e:
            logger.error(f"Unexpected error while fetching products: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error while fetching products")
    
    async def get_product_by_id(self, product_id: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch a specific product by ID from inventory system
        
        Args:
            product_id: Product ID to fetch
            
        Returns:
            Product data or None if not found
        """
        try:
            url = f"{self.inventory_base_url}/api/v1/products/{product_id}"
            logger.info(f"Fetching product {product_id} from inventory: {url}")
            
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            product = response.json()
            
            logger.info(f"Successfully fetched product {product_id} from inventory")
            return self._transform_product_data(product)
            
        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching product {product_id} from inventory service")
            raise HTTPException(status_code=503, detail="Inventory service is unavailable")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error while fetching product {product_id}: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail="Error fetching product from inventory")
        except Exception as e:
            logger.error(f"Unexpected error while fetching product {product_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error while fetching product")
    
    async def search_products(self, query: str, limit: int = 50, auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search products in inventory system
        
        Args:
            query: Term to search for
            limit: Maximum number of results
            auth_token: JWT token for authentication
            
        Returns:
            List of matching products
        """
        try:
            data = await self.get_products(search=query, limit=limit, auth_token=auth_token)
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            raise
    
    async def get_categories(self, auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all categories from inventory system
        
        Returns:
            List of categories
        """
        try:
            url = f"{self.inventory_base_url}/api/v1/categories/"
            logger.info(f"Fetching categories from inventory: {url}")
            
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            categories = response.json()
            logger.info(f"Successfully fetched {len(categories)} categories from inventory")
            
            return categories
            
        except httpx.TimeoutException:
            logger.error("Timeout while fetching categories from inventory service")
            raise HTTPException(status_code=503, detail="Inventory service is unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching categories: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail="Error fetching categories from inventory")
        except Exception as e:
            logger.error(f"Unexpected error while fetching categories: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error while fetching categories")
    
    async def get_brands(self, auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all brands from inventory system
        
        Returns:
            List of brands
        """
        try:
            url = f"{self.inventory_base_url}/api/v1/brands/"
            logger.info(f"Fetching brands from inventory: {url}")
            
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            brands = response.json()
            logger.info(f"Successfully fetched {len(brands)} brands from inventory")
            
            return brands
            
        except httpx.TimeoutException:
            logger.error("Timeout while fetching brands from inventory service")
            raise HTTPException(status_code=503, detail="Inventory service is unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching brands: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail="Error fetching brands from inventory")
        except Exception as e:
            logger.error(f"Unexpected error while fetching brands: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error while fetching brands")
    
    async def update_stock(self, product_id: str, quantity_change: int, size: Optional[str] = None, auth_token: Optional[str] = None) -> bool:
        """
        Update stock quantity after a sale
        
        Args:
            product_id: Product ID to update
            quantity_change: Quantity change (negative for sales)
            auth_token: JWT token for authentication
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'

            # If size not provided, attempt derivation from product data
            if not size:
                product_url = f"{self.inventory_base_url}/api/v1/products/{product_id}"
                prod_resp = await self.client.get(product_url, headers=headers)
                if prod_resp.status_code == 200:
                    prod_json = prod_resp.json()
                    sizes = prod_json.get('sizes')
                    if isinstance(sizes, list) and sizes:
                        first = sizes[0]
                        if isinstance(first, dict) and 'size' in first:
                            size = first['size']
                        elif isinstance(first, str):
                            size = first
            if size is None:
                logger.warning(f"No size found for product {product_id}; cannot decrement size-specific stock. Skipping.")
                return False

            adjust_url = f"{self.inventory_base_url}/api/v1/stock/{product_id}/{size}/adjust"
            params = {"quantity_change": quantity_change, "reference_id": f"POSSALE-{product_id}"}
            logger.info(f"Adjusting stock via inventory endpoint product_id={product_id} size={size} delta={quantity_change}")
            response = await self.client.put(adjust_url, params=params, headers=headers)
            if response.status_code in (200, 201):
                logger.info(f"Stock adjusted successfully product_id={product_id} size={size} status={response.status_code} body={response.text}")
                return True
            else:
                logger.error(f"Stock adjust failed product_id={product_id} size={size} status={response.status_code} body={response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating stock for product {product_id}: {str(e)}")
            return False

# Global instance - will be created once and reused
inventory_service = InventoryIntegrationService()