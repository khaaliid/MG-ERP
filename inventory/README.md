# MG-ERP Inventory Management System

A comprehensive inventory management system designed specifically for menswear shops. This microservice provides complete inventory control, stock tracking, and purchase order management.

## 🌟 Features

### Product Management
- **Multi-variant Products**: Support for different sizes, colors, and materials
- **Brand & Category Management**: Organize products by brands and categories
- **SKU & Barcode Support**: Efficient product identification and scanning
- **Cost & Pricing Control**: Track purchase costs and set selling prices
- **Material & Season Tracking**: Monitor fabric types and seasonal collections

### Stock Management
- **Real-time Stock Levels**: Live inventory tracking per size/color combination
- **Location Tracking**: Track products by shelf/rack locations in store
- **Reorder Alerts**: Automatic notifications when stock falls below reorder levels
- **Stock Movements**: Complete audit trail of all inventory changes
- **Adjustment Capabilities**: Easy stock adjustments with reason tracking

### Supplier Management
- **Supplier Profiles**: Complete contact information and lead times
- **Purchase History**: Track all purchases from each supplier
- **Performance Tracking**: Monitor supplier reliability and delivery times

### Purchase Orders
- **Order Creation**: Easy purchase order generation with multiple items
- **Receiving Process**: Track received quantities vs ordered quantities
- **Status Management**: Pending, ordered, received, cancelled statuses
- **Cost Tracking**: Monitor total order values and individual item costs

### Dashboard & Analytics
- **Inventory Overview**: Total products, stock levels, and values
- **Low Stock Alerts**: Quick identification of items needing reorder
- **Supplier Statistics**: Performance metrics and order counts
- **Financial Tracking**: Total inventory value calculations

## 🏗️ Architecture

### Backend (Port 8002)
- **FastAPI**: Modern, fast web framework for Python
- **SQLAlchemy**: Robust ORM for database operations
- **PostgreSQL**: Reliable relational database
- **Pydantic**: Data validation and serialization
- **RESTful API**: Clean, intuitive API design

### Frontend (Port 3002)
- **React 18**: Modern React with hooks and TypeScript
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Responsive Design**: Mobile-friendly interface

## 🚀 Getting Started

### Backend Setup

1. **Create Virtual Environment**:
```bash
cd inventory/backend
py -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate     # Linux/Mac
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure Database**:
Create a `.env` file with:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/mg_erp
SECRET_KEY=your-secret-key-here
ERP_API_URL=http://localhost:8000
```

4. **Run Backend**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### Frontend Setup

1. **Install Dependencies**:
```bash
cd inventory/frontend
npm install
```

2. **Start Development Server**:
```bash
npm run dev
```

Access the application at `http://localhost:3002`

## 📋 API Endpoints

### Categories
- `GET /api/v1/categories/` - List all categories
- `POST /api/v1/categories/` - Create new category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

### Products
- `GET /api/v1/products/` - List products (with filtering)
- `POST /api/v1/products/` - Create new product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Stock Management
- `GET /api/v1/stock/` - List stock items
- `POST /api/v1/stock/` - Create stock item
- `PUT /api/v1/stock/{product_id}/{size}/adjust` - Adjust stock quantity
- `GET /api/v1/stock/low-stock` - Get low stock alerts

### Purchase Orders
- `GET /api/v1/purchase-orders/` - List purchase orders
- `POST /api/v1/purchase-orders/` - Create purchase order
- `PUT /api/v1/purchase-orders/{id}/receive/{item_id}` - Receive items

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics

## 🎯 Menswear Shop Specific Features

### Size Management
- **Clothing Sizes**: S, M, L, XL, XXL, 3XL
- **Numeric Sizes**: 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50
- **Shoe Sizes**: 6, 7, 8, 9, 10, 11, 12, 13, 14

### Category Examples
- **Shirts**: Dress shirts, casual shirts, polo shirts, t-shirts
- **Pants**: Dress pants, jeans, chinos, shorts
- **Suits**: Business suits, formal wear, blazers
- **Outerwear**: Jackets, coats, vests
- **Accessories**: Ties, belts, socks, underwear
- **Shoes**: Dress shoes, casual shoes, sneakers, boots

### Season Management
- **Spring/Summer**: Lightweight fabrics, bright colors
- **Fall/Winter**: Heavy fabrics, warm clothing, darker colors

### Material Tracking
- **Cotton**: 100% cotton, cotton blends
- **Wool**: Wool suits, wool coats
- **Synthetic**: Polyester, nylon blends
- **Linen**: Summer lightweight clothing
- **Denim**: Jeans and denim jackets

## 🔧 Customization

The system is designed to be easily customizable for different types of retail operations:

1. **Size Types**: Modify size options in the database models
2. **Categories**: Add/remove product categories as needed
3. **Stock Levels**: Adjust reorder points based on sales velocity
4. **Supplier Integration**: Connect with supplier APIs for automated ordering

## 🔗 ERP Integration

The inventory system integrates with the main ERP system:
- **Automatic Sync**: Regular synchronization of inventory data
- **Sales Integration**: Stock updates from POS sales
- **Financial Reporting**: Inventory values for accounting reports

## 📊 Reports & Analytics

Future enhancements will include:
- **Sales Velocity Reports**: Identify fast/slow-moving items
- **Seasonal Analysis**: Track seasonal demand patterns
- **Supplier Performance**: Delivery time and quality metrics
- **Inventory Turnover**: Calculate inventory turnover ratios
- **Profitability Analysis**: Cost vs selling price analysis

## 🛡️ Security Features

- **Data Validation**: Comprehensive input validation
- **Error Handling**: Graceful error management
- **API Security**: Rate limiting and authentication ready
- **Database Security**: Parameterized queries prevent SQL injection

## 🔄 Future Enhancements

1. **Barcode Scanning**: Mobile app for inventory management
2. **Automated Reordering**: AI-driven purchase suggestions
3. **Vendor Portals**: Supplier access for order management
4. **Mobile App**: Native mobile application for staff
5. **Advanced Analytics**: Machine learning for demand prediction

This inventory management system provides a solid foundation for managing a menswear shop's inventory efficiently while maintaining flexibility for future growth and customization.