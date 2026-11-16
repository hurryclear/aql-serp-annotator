from typing import Annotated
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from elasticsearch.exceptions import ConnectionError as EsConnectionError
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from aql.client import fetch_serp_html
from src.serp.model import SerpSimple
from src.serp.service import get_serp_html, save_serp_html, list_serps

from utils.html_utils import clean_serp_html
from exceptions import (
    SerpNotFoundError,
    SerpHtmlUnavailableError,
    UnknownOptionError,
)

router = APIRouter(prefix="/serps", tags=["serps"])


# GET /serps?provider=Google&language=English&year=2011&annotated=false
@router.get("")
def list_all(
    provider: str,
    language: str,
    year: int,
    annotated: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[SerpSimple]:
    try:
        return list_serps(provider, language, year, annotated, limit)
    except UnknownOptionError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{serp_id}", response_class=HTMLResponse)
def get_serp(serp_id: UUID, raw: bool = False) -> HTMLResponse:
    if not raw:
        snapshot = get_serp_html(serp_id)
        if snapshot is not None:
            return HTMLResponse(snapshot)

    try:
        html, capture_url = fetch_serp_html(serp_id)
    except SerpNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"SERP {serp_id} does not exist in AQL"
        )
    except SerpHtmlUnavailableError:
        raise HTTPException(
            status_code=404, detail=f"SERP {serp_id} has no archived HTML"
        )
    except (EsConnectionError, BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=502, detail=f"Could not reach AQL: {e}")

    if raw:
        return HTMLResponse(html)

    cleaned = clean_serp_html(html, base_url=capture_url)
    save_serp_html(serp_id, cleaned)
    return HTMLResponse(cleaned)
