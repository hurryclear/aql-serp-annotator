"""save, read and edit human annotations of SERPs"""
from collections import Counter, defaultdict
from datetime import datetime, UTC
from uuid import UUID, uuid5

from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.annotation.models import (
    AnnotationGroup,
    AnnotationOutput,
    AnnotationSummary,
    FeatureInput,
    FeatureOutput,
)
from src.serp.service import get_question_serp_by_id, get_serp_html, save_serp_html
from utils.html_utils import mark_features, marked_nodes
from utils.resource_json_loader import PROVIDERS

from namespaces import NAMESPACE_FEATURE
from exceptions import (
    AnnotationExistsError,
    AnnotationNotFoundError,
    InvalidMarkError,
    SerpNotQuestionSerpError,
)

# AQL provider id -> display name ("google"), the reverse of PROVIDERS
PROVIDER_NAMES = {provider_id: name for name, provider_id in PROVIDERS.items()}


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


# ---- reading and editing (the editor) ------------------------------------


def _provider_name(provider_id: str) -> str:
    return PROVIDER_NAMES.get(provider_id, provider_id)


def list_groups() -> list[AnnotationGroup]:
    """Annotations grouped by provider and year, with counts per group."""
    with SessionLocal() as session:
        annotations = session.query(Annotation.provider, Annotation.year, Annotation.ground_truth).all()

    counts: dict[tuple[str, int], Counter] = defaultdict(Counter)
    for row in annotations:
        group = counts[(row.provider, row.year)]
        group["annotations"] += 1
        group["ground_truth"] += bool(row.ground_truth)

    return [
        AnnotationGroup(
            provider_id=provider_id,
            provider=_provider_name(provider_id),
            year=year,
            annotations=c["annotations"],
            ground_truth=c["ground_truth"],
        )
        # by provider name, then year
        for (provider_id, year), c in sorted(
            counts.items(), key=lambda item: (_provider_name(item[0][0]), item[0][1])
        )
    ]


def list_annotations(provider_id: str, year: int) -> list[AnnotationSummary]:
    """The annotated SERPs of one group, oldest annotation first."""
    with SessionLocal() as session:
        annotations = (
            session.query(Annotation)
            .filter_by(provider=provider_id, year=year)
            .order_by(Annotation.created_at)
            .all()
        )
        feature_counts = Counter(
            row.serp_id
            for row in session.query(Feature.serp_id).filter(
                Feature.serp_id.in_([a.serp_id for a in annotations])
            )
        )
        return [
            AnnotationSummary(
                serp_id=a.serp_id,
                created_by=a.created_by,
                ground_truth=a.ground_truth,
                feature_count=feature_counts[a.serp_id],
            )
            for a in annotations
        ]


def _features_in_page_order(serp_id: UUID, rows: list[Feature]) -> list[FeatureOutput]:
    """Pair each feature row with its element, using the page-order rule: the n-th
    element marked with type T is the row with id uuid5(serp_id:T:n)."""
    by_id = {row.id: row for row in rows}
    snapshot = get_serp_html(serp_id)
    seen: Counter[str] = Counter()
    ordered: list[FeatureOutput] = []
    for node, feature_type in (marked_nodes(snapshot) if snapshot else []):
        seen[feature_type] += 1
        row = by_id.pop(feature_id(serp_id, feature_type, seen[feature_type]), None)
        if row is not None:
            ordered.append(FeatureOutput(id=row.id, feature_type=row.feature_type, node=node, parser_id=row.parser_id))
    # rows without a mark in the page (saved before marking existed) come last, without a node
    for row in by_id.values():
        ordered.append(FeatureOutput(id=row.id, feature_type=row.feature_type, node=None, parser_id=row.parser_id))
    return ordered


def get_annotation(serp_id: UUID) -> AnnotationOutput:
    """One annotation with its features in page order. Raises AnnotationNotFoundError."""
    with SessionLocal() as session:
        annotation = session.get(Annotation, serp_id)
        if annotation is None:
            raise AnnotationNotFoundError(f"{serp_id} is not annotated")
        rows = session.query(Feature).filter_by(serp_id=serp_id).all()
        return AnnotationOutput(
            serp_id=annotation.serp_id,
            provider_id=annotation.provider,
            provider=_provider_name(annotation.provider),
            language=annotation.language,
            year=annotation.year,
            created_by=annotation.created_by,
            ground_truth=annotation.ground_truth,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            features=_features_in_page_order(serp_id, rows),
        )


def set_ground_truth(serp_id: UUID, ground_truth: bool) -> AnnotationOutput:
    """Confirm an annotation as ground truth (or take that back). Raises AnnotationNotFoundError."""
    with SessionLocal() as session:
        annotation = session.get(Annotation, serp_id)
        if annotation is None:
            raise AnnotationNotFoundError(f"{serp_id} is not annotated")
        annotation.ground_truth = ground_truth
        annotation.updated_at = datetime.now(UTC)
        session.commit()
    return get_annotation(serp_id)
