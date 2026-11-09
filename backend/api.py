from fastapi import FastAPI
from src.cart.controller import router as carts_router
from src.serp.controller import router as serps_router


def register_routes(app: FastAPI):
    app.include_router(carts_router)
    app.include_router(serps_router)
