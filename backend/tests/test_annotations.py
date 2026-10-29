from uuid import uuid4

from schemas import AnnotatedFeatureInput
from persistence.annotations import save_annotation
from persistence.database import SessionLocal
from persistence.models import AnnotatedFeature


def test_save_annotation_stores_null_xpath(client, cart_id):
    serp_id = uuid4()
    save_annotation(serp_id, cart_id, [AnnotatedFeatureInput(type="carousel", content="<div>x</div>")])
    with SessionLocal() as session:
        row = session.query(AnnotatedFeature).filter_by(annotated_serp_id=serp_id).one()
    assert row.xpath is None
