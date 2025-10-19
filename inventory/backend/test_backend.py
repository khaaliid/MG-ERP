"""
Test inventory backend connectivity
"""
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_backend():
    """Test if the inventory backend is responding"""
    try:
        # Test health endpoint
        logger.info("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:8002/health", timeout=5)
        logger.info(f"Health check: {response.status_code} - {response.json()}")
        
        # Test categories endpoint
        logger.info("🔍 Testing categories endpoint...")
        response = requests.get("http://localhost:8002/api/v1/categories/", timeout=5)
        logger.info(f"Categories: {response.status_code}")
        if response.status_code == 200:
            categories = response.json()
            logger.info(f"Found {len(categories)} categories")
            for cat in categories[:3]:  # Show first 3
                logger.info(f"  - {cat['name']}")
        else:
            logger.error(f"Categories error: {response.text}")
        
        # Test CORS headers
        logger.info("🔍 Testing CORS headers...")
        headers = {"Origin": "http://localhost:3002"}
        response = requests.options("http://localhost:8002/api/v1/categories/", headers=headers, timeout=5)
        logger.info(f"CORS preflight: {response.status_code}")
        logger.info(f"CORS headers: {dict(response.headers)}")
        
    except Exception as e:
        logger.error(f"❌ Backend test failed: {str(e)}")

if __name__ == "__main__":
    test_backend()