from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.annotation.models import (
    AnnotationGroup,
    AnnotationInput,
    AnnotationOutput,
    AnnotationPatch,
    AnnotationSummary,
)
from src.annotation.service import (
    create_annotation,
    get_annotation,
    list_annotations,
    list_groups,
    set_ground_truth,
)
from exceptions import (
    AnnotationExistsError,
    AnnotationNotFoundError,
    InvalidMarkError,
    SerpNotQuestionSerpError,
)


router = APIRouter(prefix="/annotations", tags=["annotations"])


# POST to the collection = "create one". An empty features list is a real
# answer ("No features"): the SERP is still marked as done
@router.post("", status_code=201)
def create(annotation: AnnotationInput) -> None:
    try:
        create_annotation(annotation.serp_id, annotation.created_by, annotation.features)
    except AnnotationExistsError:
        raise HTTPException(status_code=409, detail=f"SERP {annotation.serp_id} is already annotated")
    except SerpNotQuestionSerpError:
        raise HTTPException(status_code=404, detail=f"SERP {annotation.serp_id} is not a question SERP")
    except InvalidMarkError as e:
        raise HTTPException(status_code=422, detail=str(e))


# declared before /{serp_id}, or FastAPI would try to read "groups" as a SERP id
@router.get("/groups")
def groups() -> list[AnnotationGroup]:
    return list_groups()


# the editor's group page: GET /annotations?provider_id=f205…&year=2023
@router.get("")
def list_all(provider_id: str, year: int) -> list[AnnotationSummary]:
    return list_annotations(provider_id, year)


@router.get("/{serp_id}")
def read(serp_id: UUID) -> AnnotationOutput:
    try:
        return get_annotation(serp_id)
    except AnnotationNotFoundError:
        raise HTTPException(status_code=404, detail=f"SERP {serp_id} is not annotated")


# Confirm as ground truth: {"ground_truth": true}
@router.patch("/{serp_id}")
def patch(serp_id: UUID, body: AnnotationPatch) -> AnnotationOutput:
    try:
        return set_ground_truth(serp_id, body.ground_truth)
    except AnnotationNotFoundError:
        raise HTTPException(status_code=404, detail=f"SERP {serp_id} is not annotated")
