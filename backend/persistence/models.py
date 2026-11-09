from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Base lives next to the tables so importing it always registers every table on
# Base.metadata, which create_all in app/main.py relies on
class Base(DeclarativeBase):
    pass


class Annotation(Base):
    """One annotation refers to one SERP"""

    __tablename__ = "annotation"
    serp_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    provider: Mapped[str]  # id
    language: Mapped[str]
    year: Mapped[int]
    ground_truth: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    created_by: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class Parser(Base):
    """Parser constructed with information and xpath"""

    __tablename__ = "parser"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    provider: Mapped[str]  # id
    feature_type: Mapped[str]
    xpath: Mapped[str]
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class Feature(Base):
    """Annotated feature"""

    __tablename__ = "feature"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    serp_id: Mapped[UUID] = mapped_column(ForeignKey("annotation.serp_id"))
    feature_type: Mapped[str]
    parser_id: Mapped[UUID | None] = mapped_column(ForeignKey("parser.id"))
