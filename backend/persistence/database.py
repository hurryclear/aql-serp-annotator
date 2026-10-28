"""session factory for the local SQLite database"""
from sqlalchemy.orm import sessionmaker

from config import config


SessionLocal = sessionmaker(bind=config.persistence.sqlite_engine)
