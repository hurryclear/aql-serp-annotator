"""session factory for the local SQLite database"""
from sqlalchemy.orm import sessionmaker, declarative_base

from config import config


SessionLocal = sessionmaker(bind=config.persistence.sqlite_engine)

Base = declarative_base()
