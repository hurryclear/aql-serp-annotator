from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.database.core import Base


class Feature(Base):
    """Annotated feature"""

    __tablename__ = "feature"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    serp_id: Mapped[UUID] = mapped_column(ForeignKey("annotation.serp_id"))
    feature_type: Mapped[str]
    parser_id: Mapped[UUID | None] = mapped_column(ForeignKey("parser.id"))
