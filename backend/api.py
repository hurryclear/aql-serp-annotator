from fastapi import FastAPI
from src.serp.controller import router as serps_router


def register_routes(app: FastAPI):
    app.include_router(serps_router)