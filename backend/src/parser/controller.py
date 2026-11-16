from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.parser.models import (
    ParserInput,
    ParserOutput,
    TryInput,
    TryOutput,
)
from src.parser.service import create_parser, try_xpath
from exceptions import (
    AnnotationNotFoundError,
    InvalidMarkError,
    InvalidXPathError,
    ParserFindsNothingError,
)


router = APIRouter(prefix="/parsers", tags=["parsers"])


# trying changes nothing, but it carries a body (the xpath), so it's a POST to a
# sub-path rather than a GET with the xpath squeezed into the URL
@router.post("/try")
def try_(body: TryInput) -> TryOutput:
    try:
        return try_xpath(body.serp_id, body.feature_type, body.xpath)
    except (InvalidXPathError, InvalidMarkError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("", status_code=201)
def create(body: ParserInput) -> ParserOutput:
    try:
        return create_parser(body.serp_id, body.feature_type, body.xpath)
    except AnnotationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InvalidXPathError, InvalidMarkError, ParserFindsNothingError) as e:
        raise HTTPException(status_code=422, detail=str(e))


