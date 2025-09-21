# MG-ERP Ledger Module

This project contains a FastAPI backend (Python) with PostgreSQL and SQLAlchemy, and a React frontend for a simple ledger application.

## Structure
- `backend/` - FastAPI app, SQLAlchemy models, PostgreSQL integration
- `frontend/` - React app to interact with the backend

---

## Getting Started

### 1. Database (PostgreSQL)

We use PostgreSQL as a Docker container.  
You can start the database (and pgAdmin) using Docker Compose:

```sh
cd db
docker compose up -d
```

This will start:
- PostgreSQL (`mguser`/`mgpassword`, database: `mgledger`)
- pgAdmin (web UI at http://localhost:8088, login: `user@mgdonlinestore.com` / `password`)

To connect in pgAdmin, use:
- Host: `postgres`
- Port: `5432`
- Username: `mguser`
- Password: `mgpassword`
- Database: `mgledger`

If you want to run the database manually (not recommended if using Docker Compose):

```sh
docker run --name mg-erp-postgres -e POSTGRES_USER=mguser -e POSTGRES_PASSWORD=mgpassword -e POSTGRES_DB=mgledger -v mg-erp-pgdata:/var/lib/postgresql/data -p 5432:5432 -d postgres:15
```

---

### 2. Backend (FastAPI)

```sh
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
cd app
uvicorn main:app --reload
```

- The backend expects the database to be running and accessible.
- By default, it connects to `localhost:5432` (see `backend/app/config.py`).
- If running inside Docker Compose, set `DATABASE_URL` to use `postgres` as the host.

---

### 3. Frontend (React + TypeScript)

```sh
cd frontend
npm install
npm run dev
```

- The frontend will start on http://localhost:5173 (the exact URL will be printed in the CMD after run the command !) and interact with the backend API.

---

## Environment Variables

You can override the backend database connection by creating a `.env` file in `backend/app/`:

```
DATABASE_URL=postgresql+asyncpg://mguser:mgpassword@localhost/mgledger
```

If running backend inside Docker Compose, use:

```
DATABASE_URL=postgresql+asyncpg://mguser:mgpassword@postgres/mgledger
```

---

## Notes

- Make sure the database is running before starting the backend.
- If you change database credentials, update them everywhere and restart containers.
- For first-time setup or after changing DB credentials, you may need to remove the Docker volume:  
  `docker compose down -v && docker compose up -d`

---