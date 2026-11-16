"""parser development: on one annotated SERP, try xpaths, reuse an existing parser
that works, or save a new one"""
from uuid import UUID, uuid5

from src.database.core import SessionLocal
from src.entities.annotation import Annotation
from src.entities.feature import Feature
from src.entities.parser import Parser
from src.annotation.service import feature_id
from src.parser.models import LinkOutput, ParserOutput, TryOutput
from src.serp.service import get_serp_html
from utils.html_utils import marked_nodes, xpath_nodes

from namespaces import NAMESPACE_FEATURE_PARSER
from exceptions import (
    AnnotationNotFoundError,
    InvalidMarkError,
    ParserFindsNothingError,
    ParserNotFoundError,
)


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


def _found_blocks(serp_id: UUID, feature_type: str, xpath: str) -> list[tuple[int, UUID]]:
    """(aqlqa-node, Feature id) of this SERP's annotated blocks of the type that the xpath finds.

    A block's row comes from the page-order rule: the n-th element marked with
    type T is the row uuid5(serp_id:T:n).
    """
    snapshot = _snapshot(serp_id)
    found = set(xpath_nodes(snapshot, xpath))
    blocks: list[tuple[int, UUID]] = []
    n = 0
    for node, t in marked_nodes(snapshot):
        if t != feature_type:
            continue
        n += 1
        if node in found:
            blocks.append((node, feature_id(serp_id, t, n)))
    return blocks


def _annotation(session, serp_id: UUID) -> Annotation:
    annotation = session.get(Annotation, serp_id)
    if annotation is None:
        raise AnnotationNotFoundError(f"{serp_id} is not annotated")
    return annotation


def _output(session, parser: Parser) -> ParserOutput:
    linked = (
        session.query(Feature.serp_id, Annotation.year)
        .join(Annotation, Feature.serp_id == Annotation.serp_id)
        .filter(Feature.parser_id == parser.id)
        .distinct()
        .all()
    )
    return ParserOutput(
        id=parser.id,
        provider_id=parser.provider,
        feature_type=parser.feature_type,
        xpath=parser.xpath,
        created_at=parser.created_at,
        updated_at=parser.updated_at,
        serps=len({row.serp_id for row in linked}),
        years=sorted({row.year for row in linked}),
    )


def list_parsers(provider_id: str, feature_type: str | None = None) -> list[ParserOutput]:
    """A provider's parsers, of every year, optionally of one feature type."""
    with SessionLocal() as session:
        query = session.query(Parser).filter_by(provider=provider_id)
        if feature_type is not None:
            query = query.filter_by(feature_type=feature_type)
        return [_output(session, p) for p in query.order_by(Parser.feature_type, Parser.created_at).all()]


def _next_parser_id(session, provider_id: str, year: int, feature_type: str) -> UUID:
    """uuid5(provider:year:feature_type:k) with the smallest free k.

    The year is the one of the SERP the parser was designed on; it only makes
    the id unique, the parser itself can be used on any year.
    """
    k = 1
    while True:
        parser_id = uuid5(NAMESPACE_FEATURE_PARSER, f"{provider_id}:{year}:{feature_type}:{k}")
        if session.get(Parser, parser_id) is None:
            return parser_id
        k += 1


def _link(session, parser_id: UUID, feature_ids: list[UUID]) -> None:
    """Link these blocks to the parser. A block holds one parser: an older link is replaced."""
    session.query(Feature).filter(Feature.id.in_(feature_ids)).update(
        {"parser_id": parser_id}, synchronize_session=False
    )


def create_parser(serp_id: UUID, feature_type: str, xpath: str) -> ParserOutput:
    """Save an xpath that works on this SERP as a new parser, linked to the blocks it finds there.

    Raises AnnotationNotFoundError, ParserFindsNothingError (it must find at
    least one annotated block of the type), InvalidXPathError and InvalidMarkError.
    """
    blocks = _found_blocks(serp_id, feature_type, xpath)
    if not blocks:
        raise ParserFindsNothingError("the xpath finds none of this SERP's annotated blocks of this type")
    with SessionLocal() as session:
        annotation = _annotation(session, serp_id)
        parser = Parser(
            id=_next_parser_id(session, annotation.provider, annotation.year, feature_type),
            provider=annotation.provider,
            feature_type=feature_type,
            xpath=xpath,
            created_by="",  # no annotator names for parsers yet; the column stays for later
        )
        session.add(parser)
        # the parser row must exist before features point at it (no relationship())
        session.flush()
        _link(session, parser.id, [fid for _, fid in blocks])
        session.commit()
        return _output(session, parser)


def link_parser(parser_id: UUID, serp_id: UUID) -> LinkOutput:
    """Use an existing parser on this SERP: link the blocks of its type that it finds here.

    Raises ParserNotFoundError, AnnotationNotFoundError, ParserFindsNothingError
    (also when the parser belongs to another provider) and InvalidMarkError.
    """
    with SessionLocal() as session:
        parser = session.get(Parser, parser_id)
        if parser is None:
            raise ParserNotFoundError(f"parser {parser_id} does not exist")
        annotation = _annotation(session, serp_id)
        if annotation.provider != parser.provider:
            raise ParserFindsNothingError("this parser belongs to another provider")
        blocks = _found_blocks(serp_id, parser.feature_type, parser.xpath)
        if not blocks:
            raise ParserFindsNothingError("this parser finds none of this SERP's annotated blocks of its type")
        _link(session, parser.id, [fid for _, fid in blocks])
        session.commit()
        return LinkOutput(parser=_output(session, parser), linked=[node for node, _ in blocks])


def delete_parser(parser_id: UUID) -> None:
    """Unlink a parser from every block, then delete it. Raises ParserNotFoundError."""
    with SessionLocal() as session:
        parser = session.get(Parser, parser_id)
        if parser is None:
            raise ParserNotFoundError(f"parser {parser_id} does not exist")
        session.query(Feature).filter_by(parser_id=parser_id).update({"parser_id": None}, synchronize_session=False)
        session.delete(parser)
        session.commit()
