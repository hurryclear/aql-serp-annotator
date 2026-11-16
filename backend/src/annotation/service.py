"""save human annotations of SERPs"""
from collections import Counter
from uuid import UUID, uuid5

from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.annotation.models import FeatureInput
from src.serp.service import get_question_serp_by_id

from namespaces import NAMESPACE_FEATURE
from exceptions import AnnotationExistsError, SerpNotQuestionSerpError


def feature_id(serp_id: UUID, feature_type: str, n: int) -> UUID:
    """Deterministic id: the n-th block of this type on this SERP always gets the same id."""
    return uuid5(NAMESPACE_FEATURE, f"{serp_id}:{feature_type}:{n}")


def build_features(serp_id: UUID, input_features: list[FeatureInput]) -> list[Feature]:
    """Turn the browser's list into Feature rows, numbering each type 1, 2, 3, ...

    For now n follows the order the blocks were sent in: the browser doesn't
    say yet where on the page each block is.
    """
    seen: Counter[str] = Counter()
    features = []
    for input_feature in input_features:
        seen[input_feature.feature_type] += 1
        n = seen[input_feature.feature_type]
        features.append(
            Feature(
                id=feature_id(serp_id, input_feature.feature_type, n),
                serp_id=serp_id,
                feature_type=input_feature.feature_type,
                parser_id=None,  # filled in later, during parser development
            )
        )
    return features


def create_annotation(
    serp_id: UUID,
    created_by: str,
    input_features: list[FeatureInput],
) -> None:
    """Record a human annotation of one SERP.

    Writes one Annotation row (provider/language/year come from the question
    SERPs file, not from the browser) and one Feature row per block. An empty
    feature list is valid: it means "this SERP has no features".

    Raises SerpNotQuestionSerpError if the SERP isn't in the question file, and
    AnnotationExistsError if it's already annotated.
    """
    serp = get_question_serp_by_id(serp_id)
    if serp is None:
        raise SerpNotQuestionSerpError(f"{serp_id} is not a question SERP")

    with SessionLocal() as session:
        if session.get(Annotation, serp_id) is not None:
            raise AnnotationExistsError(f"{serp_id} is already annotated")

        session.add(
            Annotation(
                serp_id=serp_id,
                provider=serp.provider,
                language=serp.language,
                year=serp.year,
                created_by=created_by,
            )
        )
        # without relationship() SQLAlchemy doesn't know the annotation row must
        # be inserted before the features pointing at it, so insert it now
        session.flush()

        session.add_all(build_features(serp_id, input_features))
        session.commit()
