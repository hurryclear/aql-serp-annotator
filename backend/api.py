from fastapi import FastAPI
from src.serp.controller import router as serps_router
from src.annotation.controller import router as annotations_router
from src.feature_type.controller import router as feature_types_router
from src.parser.controller import router as parsers_router


def register_routes(app: FastAPI):
    app.include_router(serps_router)
    app.include_router(annotations_router)
    app.include_router(feature_types_router)
    app.include_router(parsers_router)
