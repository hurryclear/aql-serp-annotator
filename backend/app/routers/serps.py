from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from elasticsearch.exceptions import ConnectionError as EsConnectionError
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from aql.client import fetch_serp_html
from utils.html_utils import clean_serp_html
from persistence.serp_store import get_serp_html, save_serp_html
from persistence.annotations import save_annotation
from schemas import AnnotationInput
from exceptions import AnnotationExistsError, CartNotFoundError, SerpNotFoundError, SerpHtmlUnavailableError


router = APIRouter(prefix="/serps", tags=["serps"])


# The cleaned HTML served here is also saved as the ground-truth snapshot, so
# xpath tests and the future parser run against exactly what the annotator saw.
@router.get("/{serp_id}", response_class=HTMLResponse)
def get_serp(serp_id: UUID, raw: bool = False) -> HTMLResponse:
    if not raw:
        snapshot = get_serp_html(serp_id)
        if snapshot is not None:
            return HTMLResponse(snapshot)

    try:
        html, capture_url = fetch_serp_html(serp_id)
    except SerpNotFoundError:
        raise HTTPException(status_code=404, detail=f"SERP {serp_id} does not exist in AQL")
    except SerpHtmlUnavailableError:
        # from the caller's view, this SERP's page simply doesn't exist (yet)
        raise HTTPException(status_code=404, detail=f"SERP {serp_id} has no archived HTML")
    except (EsConnectionError, BotoCoreError, ClientError) as e:
        # AQL (Elasticsearch or S3) failed, not us -> 502 Bad Gateway
        raise HTTPException(status_code=502, detail=f"Could not reach AQL: {e}")

    if raw:
        return HTMLResponse(html)

    cleaned = clean_serp_html(html, base_url=capture_url)
    save_serp_html(serp_id, cleaned)
    return HTMLResponse(cleaned)


# an empty features list is a real answer ("No blocks"): the SERP is marked done
@router.post("/{serp_id}/annotation", status_code=204)
def create_annotation(serp_id: UUID, annotation: AnnotationInput) -> None:
    try:
        save_annotation(serp_id, annotation.cart_id, annotation.features)
    except AnnotationExistsError:
        raise HTTPException(status_code=409, detail=f"SERP {serp_id} is already annotated")
    except CartNotFoundError:
        raise HTTPException(status_code=404, detail=f"Cart {annotation.cart_id} does not exist")
