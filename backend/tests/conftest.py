"""shared pytest fixtures: a throwaway database, an app client and a cart"""
import os
import tempfile

# set before any app import: the shared config is built on import, and this keeps
# tests away from data/test and data/prod
os.environ["APP_ENV"] = "test"
os.environ["PERSISTENCE_DATA_PATH"] = tempfile.mkdtemp(prefix="annotator-test-")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from persistence.database import SessionLocal
from persistence.models import Cart


@pytest.fixture
def client():
    # entering the client runs the lifespan, which creates the tables
    with TestClient(app) as c:
        yield c


@pytest.fixture
def cart_id(client):
    with SessionLocal() as session:
        cart = Cart(provider="google", language="en", year=2012, created_by="pytest")
        session.add(cart)
        session.commit()
        return cart.id
