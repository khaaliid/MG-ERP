"""
Main entry point for the Light Ads Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import API_HOST, API_PORT, CORS_ORIGINS, APP_NAME, APP_VERSION
from database import init_db
from routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="Standalone ad management service for the Light ERP frontend AdSlot.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.on_event("startup")
    def on_startup():
        init_db()

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
