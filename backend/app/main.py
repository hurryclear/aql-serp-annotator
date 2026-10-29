import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import config
from persistence.models import Base
from app.routers.carts import router as carts_router
from app.routers.features import router as features_router
from app.routers.serps import router as serps_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # uvicorn's own logger, so this line shows up next to "Application startup complete"
    logging.getLogger("uvicorn.error").info(
        "APP_ENV=%s · data: %s · candidate SERPs: %s",
        config.app_env, config.persistence.data_path, config.candidates.file_name,
    )
    Base.metadata.create_all(config.persistence.sqlite_engine)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(carts_router)
app.include_router(features_router)
app.include_router(serps_router)
