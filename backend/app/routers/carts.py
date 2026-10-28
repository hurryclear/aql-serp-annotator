from fastapi import APIRouter

from schemas import CartInput, CartOutput
from persistence.carts import create_cart


router = APIRouter()


# FastAPI registers the function as the handler for "any POST request that arrives at the path /carts"
@router.post("/carts", tags=["carts"])
def create(cart_input: CartInput) -> CartOutput:
    return create_cart(cart_input=cart_input)
