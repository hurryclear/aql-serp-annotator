from fastapi import APIRouter
from fastapi.repsonses import HTMLResponse


router = APIRouter()

class Serp():


@router.get("/{id}", tags=["serps"])
def search() -> Serp:
