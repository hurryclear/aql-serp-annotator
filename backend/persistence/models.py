"""SQLite tables (SQLAlchemy models) for carts, annotations and features (ADR 0004)"""
from datetime import datetime, UTC
from uuid import UUID, uuid4
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Base lives next to the tables so importing it always registers every table on
# Base.metadata, which create_all in app/main.py relies on
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
