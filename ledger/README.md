# Ledger Microservice

Standalone ledger service for the MG-ERP system. This service can run independently or as part of the larger ERP system.

## Features

- Double-entry bookkeeping
- Account management (Assets, Liabilities, Equity, Revenue, Expenses)
- Transaction recording
- Balance sheet and income statement generation
- Trial balance reports
- General ledger views

## Directory Structure

```
ledger/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── auth/      # Authentication
│   │   ├── schemas/   # Pydantic models
│   │   └── services/  # Business logic
│   └── requirements.txt
├── frontend/          # React TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
└── db/                # Database configuration
    └── docker-compose.yml
```

## Quick Start

### 1. Database Setup
```bash
cd ledger/db
docker-compose up -d
```

### 2. Backend Setup
```bash
cd ledger/backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Update `app/config.py` if needed for database connection.

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd ledger/frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173
The backend API will be available at http://localhost:8000

## API Endpoints

- `GET /accounts` - List all accounts
- `POST /accounts` - Create new account
- `GET /transactions` - List transactions
- `POST /transactions` - Create new transaction
- `GET /reports/balance-sheet` - Generate balance sheet
- `GET /reports/income-statement` - Generate income statement
- `GET /reports/trial-balance` - Generate trial balance

## Configuration

The service runs on the following ports by default:
- Backend: 8000
- Frontend: 5173
- Database: 5432

These can be changed in the respective configuration files if running multiple instances.