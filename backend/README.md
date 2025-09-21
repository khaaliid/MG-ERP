# Backend for MG-ERP Ledger

This folder contains the FastAPI backend for the ledger module.

- Uses FastAPI for API endpoints
- SQLAlchemy for ORM
- PostgreSQL as the database

## Setup
1. Create a virtual environment:
   py -m venv venv
2. Activate the environment:
   .\venv\Scripts\activate
3. Install dependencies (to be listed in requirements.txt) - pip install -r requirements.txt
4. Configure PostgreSQL connection in `app/config.py`
5. Run the server:
   uvicorn app.main:app --reload
