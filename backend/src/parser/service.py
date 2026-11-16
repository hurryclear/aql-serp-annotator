"""parser development: on one annotated SERP, try xpaths, reuse an existing parser
that works, or save a new one"""
from uuid import UUID, uuid5

from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.entities.parser import Parser
from src.annotation.service import feature_id
from src.parser.models import TryOutput
from src.serp.service import get_serp_html
from utils.html_utils import marked_nodes, xpath_nodes

from namespaces import NAMESPACE_FEATURE_PARSER
from exceptions import AnnotationNotFoundError, InvalidMarkError


def _snapshot(serp_id: UUID) -> str:
    snapshot = get_serp_html(serp_id)
    if snapshot is None:
        raise InvalidMarkError(f"SERP {serp_id} has no cached snapshot; open it first")
    return snapshot


def try_xpath(serp_id: UUID, feature_type: str, xpath: str) -> TryOutput:
    """Compare what the xpath finds on one SERP with its annotated blocks of this type.

    Both sides are aqlqa-node numbers read from the same snapshot, so "found"
    means the xpath returns that very element. Raises InvalidXPathError and
    InvalidMarkError (no snapshot).
    """
    snapshot = _snapshot(serp_id)
    found = set(xpath_nodes(snapshot, xpath))
    annotated = {node for node, t in marked_nodes(snapshot) if t == feature_type}
    return TryOutput(
        serp_id=serp_id,
        found=sorted(found),
        matched=sorted(found & annotated),
        missed=sorted(annotated - found),
        extra=sorted(found - annotated),
    )


