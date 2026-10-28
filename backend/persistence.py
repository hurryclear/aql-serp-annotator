import random
from datetime import datetime, UTC
from uuid import UUID, uuid4, uuid5
from hashlib import sha256
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from config import Config

from schemas import AnnotatedFeatureInput, AnnotatedFeatureOutput, CartInput, CartOutput
from exceptions import AnnotationExistsError
from namespaces import NAMESPACE_FEATURE
from manifest import search_manifest
from mapping import PROVIDERS, LANGUAGES


class Base(DeclarativeBase):
    pass


class Cart(Base):
    __tablename__ = "cart"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    provider: Mapped[str]
    language: Mapped[str]
    year: Mapped[int]
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Annotation(Base):
    __tablename__ = "annotation"
    serp_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    cart_id: Mapped[UUID] = mapped_column(ForeignKey("cart.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
                                        default=lambda: datetime.now(UTC),
                                        onupdate=lambda: datetime.now(UTC)
                                    )


class Feature(Base):
    __tablename__ = "feature"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    type: Mapped[str]
    content: Mapped[str]


class AnnotatedFeature(Base):
    __tablename__ = "annotated_feature"
    feature_id: Mapped[UUID] = mapped_column(ForeignKey("feature.id"), primary_key=True)
    annotated_serp_id: Mapped[UUID] = mapped_column(ForeignKey("annotation.serp_id"))
    xpath: Mapped[str]


class ParsedFeature(Base):
    __tablename__ = "parsed_feature"
    feature_id: Mapped[UUID] = mapped_column(ForeignKey("feature.id"), primary_key=True)
    serp_id: Mapped[UUID]
    feature_parser: Mapped[UUID] = mapped_column(ForeignKey("feature_parser.id"), primary_key=True)
    answer_text: Mapped[str | None]
    answer_source_link: Mapped[str | None]


class FeatureParser(Base):
    __tablename__ = "feature_parser"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    provider: Mapped[UUID]
    feature_type: Mapped[str]
    xpath: Mapped[str]
    text_xpath: Mapped[str]
    source_link_xpath: Mapped[str]


config = Config()
SessionLocal = sessionmaker(bind=config.persistence.sqlite_engine)


def create_cart(cart_input: CartInput) -> CartOutput:
    provider = PROVIDERS.get(cart_input.provider.lower())
    language = LANGUAGES.get(cart_input.language.lower())
    if provider is None or language is None:
        return CartOutput(id=None, serp_ids=[], total=0)

    filtered_serp_ids = search_manifest(provider, language, cart_input.year)
    with SessionLocal() as session:
        annotated_serp_rows = (
            session.query(Annotation.serp_id)
            .filter(Annotation.serp_id.in_(filtered_serp_ids))
            .all()
        )
        annotated_serp_ids = set()
        for row in annotated_serp_rows:
            annotated_serp_ids.add(row.serp_id)
        available_serp_ids = set(filtered_serp_ids) - annotated_serp_ids
        sample_size = min(cart_input.batch_size, len(available_serp_ids))
        serp_ids = random.sample(list(available_serp_ids), sample_size)

        if not serp_ids:
            return CartOutput(id=None, serp_ids=[], total=0)

        cart = Cart(
            provider=provider,
            language=language,
            year=cart_input.year,
            created_by=cart_input.created_by
        )
        session.add(cart)
        session.commit()
        session.refresh(cart)

        return CartOutput(id=cart.id, serp_ids=serp_ids, total=len(serp_ids))


def save_serp_html(serp_id: UUID, html: str) -> None:
    serp_path = config.persistence.serp_path / f"{serp_id}.html"
    serp_path.write_text(html, encoding="utf-8")


def get_serp_html(serp_id: UUID) -> str | None:
    serp_path = config.persistence.serp_path / f"{serp_id}.html"
    if not serp_path.exists():
        return None
    return serp_path.read_text(encoding="utf-8")


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

            session.add(
                AnnotatedFeature(
                    feature_id=feature_id,
                    annotated_serp_id=serp_id,
                    xpath=input_feature.xpath,
                )
            )
        session.commit()
