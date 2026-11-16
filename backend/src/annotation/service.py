"""save human annotations of SERPs"""
from collections import Counter
from uuid import UUID, uuid5

from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.annotation.models import FeatureInput
from src.serp.service import get_question_serp_by_id, get_serp_html, save_serp_html
from utils.html_utils import mark_features

from namespaces import NAMESPACE_FEATURE
from exceptions import AnnotationExistsError, InvalidMarkError, SerpNotQuestionSerpError


def feature_id(serp_id: UUID, feature_type: str, n: int) -> UUID:
    """Deterministic id: the n-th block of this type on this SERP always gets the same id."""
    return uuid5(NAMESPACE_FEATURE, f"{serp_id}:{feature_type}:{n}")


def build_features(serp_id: UUID, input_features: list[FeatureInput]) -> list[tuple[Feature, int]]:
    """Turn the browser's list into Feature rows, each paired with its element number.

    Each type is numbered 1, 2, 3, ... in page order (aqlqa-node numbers follow the
    document), not in the order the annotator clicked, so the same blocks always
    get the same ids. Raises InvalidMarkError if two features share one element.
    """
    nodes = [f.node for f in input_features]
    if len(nodes) != len(set(nodes)):
        raise InvalidMarkError("two features are marked on the same element")

    seen: Counter[str] = Counter()
    features = []
    for input_feature in sorted(input_features, key=lambda f: f.node):
        seen[input_feature.feature_type] += 1
        n = seen[input_feature.feature_type]
        feature = Feature(
            id=feature_id(serp_id, input_feature.feature_type, n),
            serp_id=serp_id,
            feature_type=input_feature.feature_type,
            parser_id=None,  # filled in later, during parser development
        )
        features.append((feature, input_feature.node))
    return features


def create_annotation(
    serp_id: UUID,
    created_by: str,
    input_features: list[FeatureInput],
) -> None:
    """Record a human annotation of one SERP.

    Writes one Annotation row (provider/language/year come from the question
    SERPs file, not from the browser), one Feature row per block, and marks each
    block in the SERP's snapshot with aqlqa-sf-type. The page holds no ids: the
    n-th element of a type in page order is that type's Feature n (see
    build_features). An empty feature list is valid: it means "this SERP has no
    features".

    Raises SerpNotQuestionSerpError if the SERP isn't in the question file,
    AnnotationExistsError if it's already annotated, and InvalidMarkError if a
    marked element can't be found in the snapshot.
    """
    serp = get_question_serp_by_id(serp_id)
    if serp is None:
        raise SerpNotQuestionSerpError(f"{serp_id} is not a question SERP")

    features = build_features(serp_id, input_features)

    # prepare the marked snapshot before touching the database, so a bad element
    # number stops the save before anything is written
    marked_html = None
    if features:
        snapshot = get_serp_html(serp_id)
        if snapshot is None:
            raise InvalidMarkError(f"SERP {serp_id} has no cached snapshot; open it first")
        marked_html = mark_features(
            snapshot,
            [(node, feature.feature_type) for feature, node in features],
        )

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
        session.add_all(feature for feature, _ in features)
        session.flush()

        # written last, inside the transaction: if writing fails, nothing is committed
        if marked_html is not None:
            save_serp_html(serp_id, marked_html)
        session.commit()
