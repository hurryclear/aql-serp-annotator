from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.parser.models import TryInput, TryOutput
from src.parser.service import try_xpath
from exceptions import AnnotationNotFoundError, InvalidMarkError, InvalidXPathError


router = APIRouter(prefix="/parsers", tags=["parsers"])


# trying changes nothing, but it carries a body (the xpath), so it's a POST to a
# sub-path rather than a GET with the xpath squeezed into the URL
@router.post("/try")
def try_(body: TryInput) -> TryOutput:
    try:
        return try_xpath(body.serp_id, body.feature_type, body.xpath)
    except (InvalidXPathError, InvalidMarkError) as e:
        raise HTTPException(status_code=422, detail=str(e))


