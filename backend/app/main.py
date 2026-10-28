from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from persistence import Base, config
from app.routers.carts import router as carts_router
from app.routers.serps import router as serps_router


@asynccontextmanager
async def lifespan(app: FastAPI):

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
app.include_router(serps_router)
