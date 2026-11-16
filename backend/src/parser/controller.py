from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.parser.models import (
    LinkOutput,
    ParserInput,
    ParserOutput,
    TryInput,
    TryOutput,
)
from src.parser.service import create_parser, link_parser, try_xpath
from exceptions import (
    AnnotationNotFoundError,
    InvalidMarkError,
    InvalidXPathError,
    ParserFindsNothingError,
    ParserNotFoundError,
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


# "use this parser on this SERP": PUT, because linking twice ends in the same state
@router.put("/{parser_id}/serps/{serp_id}")
def link(parser_id: UUID, serp_id: UUID) -> LinkOutput:
    try:
        return link_parser(parser_id, serp_id)
    except (ParserNotFoundError, AnnotationNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InvalidMarkError, ParserFindsNothingError) as e:
        raise HTTPException(status_code=422, detail=str(e))


