"""
Add sample brands and suppliers
"""
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_data():
    """Add sample brands and suppliers for testing"""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    
    brands = [
        ("Hugo Boss", "Premium German luxury fashion brand"),
        ("Calvin Klein", "American luxury fashion house"),
        ("Tommy Hilfiger", "Classic American cool style"),
        ("Polo Ralph Lauren", "Timeless American luxury"),
        ("Brooks Brothers", "Traditional American clothing")
    ]
    
    suppliers = [
        ("Premium Textiles Ltd", "John Smith", "john@premiumtextiles.com", "123-456-7890", "123 Fashion Ave, NY", 14),
        ("Fashion Wholesale Co", "Sarah Johnson", "sarah@fashionwholesale.com", "987-654-3210", "456 Commerce St, LA", 7),
        ("Elite Garments Inc", "Mike Wilson", "mike@elitegarments.com", "555-123-4567", "789 Industry Blvd, Chicago", 10)
    ]
    
    with engine.begin() as conn:
        try:
            logger.info("🏷️ Adding sample brands...")
            
            for name, description in brands:
                # Check if brand already exists
                result = conn.execute(text("SELECT id FROM inventory.brands WHERE name = :name"), {"name": name})
                existing = result.fetchone()
                
                if existing:
                    logger.info(f"✅ Brand '{name}' already exists")
                    continue
                
                # Insert new brand
                result = conn.execute(text("""
                    INSERT INTO inventory.brands (id, name, description) 
                    VALUES (gen_random_uuid()::text, :name, :description)
                    RETURNING id, name
                """), {"name": name, "description": description})
                
                brand = result.fetchone()
                logger.info(f"✅ Created brand: {brand[1]} (ID: {brand[0]})")
            
            logger.info("🚚 Adding sample suppliers...")
            
            for name, contact_person, email, phone, address, lead_time in suppliers:
                # Check if supplier already exists
                result = conn.execute(text("SELECT id FROM inventory.suppliers WHERE name = :name"), {"name": name})
                existing = result.fetchone()
                
                if existing:
                    logger.info(f"✅ Supplier '{name}' already exists")
                    continue
                
                # Insert new supplier
                result = conn.execute(text("""
                    INSERT INTO inventory.suppliers (id, name, contact_person, email, phone, address, lead_time_days) 
                    VALUES (gen_random_uuid()::text, :name, :contact_person, :email, :phone, :address, :lead_time)
                    RETURNING id, name
                """), {
                    "name": name, 
                    "contact_person": contact_person, 
                    "email": email, 
                    "phone": phone, 
                    "address": address, 
                    "lead_time": lead_time
                })
                
                supplier = result.fetchone()
                logger.info(f"✅ Created supplier: {supplier[1]} (ID: {supplier[0]})")
            
            logger.info("🎉 Sample data setup completed!")
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample data: {str(e)}")
            raise

if __name__ == "__main__":
    add_sample_data()