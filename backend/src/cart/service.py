"""create annotation carts: a random batch of not-yet-annotated candidate SERPs"""
import random

from utils.resource_json_loader import PROVIDERS, LANGUAGES

from src.cart.models import CartInput, CartOutput
from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.serp.service import search_candidate_serps

def create_cart(cart_input: CartInput) -> None:
    raise NotImplementedError  # TODO: restore the cart logic below
#     provider = PROVIDERS.get(cart_input.provider.lower())
#     language = LANGUAGES.get(cart_input.language.lower())
#     if provider is None or language is None:
#         return CartOutput(id=None, serp_ids=[], total=0)

#     filtered_serp_ids = search_candidate_serps(provider, language, cart_input.year)
#     with SessionLocal() as session:
#         annotated_serp_rows = (
#             session.query(Annotation.serp_id)
#             .filter(Annotation.serp_id.in_(filtered_serp_ids))
#             .all()
#         )
#         annotated_serp_ids = set()
#         for row in annotated_serp_rows:
#             annotated_serp_ids.add(row.serp_id)
#         available_serp_ids = set(filtered_serp_ids) - annotated_serp_ids
#         sample_size = min(cart_input.batch_size, len(available_serp_ids))
#         serp_ids = random.sample(list(available_serp_ids), sample_size)

#         if not serp_ids:
#             return CartOutput(id=None, serp_ids=[], total=0)

#         cart = Cart(
#             provider=provider,
#             language=language,
#             year=cart_input.year,
#             created_by=cart_input.created_by
#         )
#         session.add(cart)
#         session.commit()
#         session.refresh(cart)

#         return CartOutput(id=cart.id, serp_ids=serp_ids, total=len(serp_ids))
