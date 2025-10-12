# MG-ERP POS System

A standalone Point of Sale system that integrates with the main MG-ERP ledger system.

## Features

- 🛒 **Product Management**: Catalog, inventory, and pricing
- 💳 **Sales Processing**: Fast checkout with receipt generation
- 📊 **Stock Management**: Real-time inventory tracking
- 🔄 **ERP Integration**: Automatic sync with main ledger system
- 💰 **Payment Methods**: Cash, card, and other payment options

## Architecture

- **Backend**: FastAPI (Python) - Port 8001
- **Frontend**: React TypeScript - Port 3001
- **Database**: PostgreSQL (shared with main ERP or separate)
- **Integration**: HTTP API calls to main ERP system

## Quick Start

### Backend
```bash
cd pos/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend
```bash
cd pos/frontend
npm install
npm run dev -- --port 3001
```

## API Endpoints

- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/search?q=term` - Search products
- `POST /api/v1/sales` - Process sale
- `GET /api/v1/sales` - List sales

## Integration

The POS system automatically creates transactions in the main ERP ledger:
- Sales → Revenue account (credit)
- Cash/Card → Asset account (debit)
- Inventory → Cost of goods sold (if configured)

## Configuration

Set environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `ERP_BASE_URL`: Main ERP API URL (default: http://localhost:8000/api/v1)
- `ERP_USERNAME`: ERP user for integration
- `ERP_PASSWORD`: ERP password for integration