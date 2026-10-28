"""save human annotations of SERPs"""
from datetime import datetime, UTC
from uuid import UUID, uuid5
from hashlib import sha256

from schemas import AnnotatedFeatureInput
from exceptions import AnnotationExistsError
from namespaces import NAMESPACE_FEATURE
from persistence.database import SessionLocal
from persistence.models import Annotation, AnnotatedFeature, Feature


def save_annotation(
    serp_id: UUID,
    cart_id: UUID,
    input_features: list[AnnotatedFeatureInput],
    overwrite: bool = False,
) -> None:
    """Record a human annotation of one SERP.

    Each input feature is stored once as a Feature (deduped by a hash of
    type+content) and linked to this SERP via an AnnotatedFeature carrying
    its xpath. A single Annotation row marks the SERP as done; if one
    already exists, raises AnnotationExistsError unless overwrite=True, in
    which case the SERP's prior feature links are replaced.
    """
    with SessionLocal() as session:
        existing = session.get(Annotation, serp_id)

        if existing is not None and not overwrite:
            raise AnnotationExistsError(f"{serp_id} is already annotated")

        if existing is None:
            session.add(Annotation(serp_id=serp_id, cart_id=cart_id))
        else:
            existing.updated_at = datetime.now(UTC)
            session.query(AnnotatedFeature).filter_by(annotated_serp_id=serp_id).delete()

        for input_feature in input_features:
            feature_id = uuid5(
                NAMESPACE_FEATURE,
                f"{serp_id}:{input_feature.type}:{sha256(input_feature.content.encode()).hexdigest()}",
            )
            feature = session.get(Feature, feature_id)
            if feature is None:
                feature = Feature(
                    id=feature_id,
                    type=input_feature.type,
                    content=input_feature.content,
                )
                session.add(feature)
                # without relationship() SQLAlchemy doesn't know Feature must be
                # inserted before the AnnotatedFeature pointing at it, so do it now
                session.flush()

            session.add(
                AnnotatedFeature(
                    feature_id=feature_id,
                    annotated_serp_id=serp_id,
                    xpath=input_feature.xpath,
                )
            )
        session.commit()
