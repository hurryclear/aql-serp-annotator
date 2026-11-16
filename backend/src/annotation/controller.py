from fastapi import APIRouter, HTTPException

from src.annotation.models import AnnotationInput
from src.annotation.service import create_annotation
from exceptions import AnnotationExistsError, InvalidMarkError, SerpNotQuestionSerpError


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
