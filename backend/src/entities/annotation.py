from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.database.core import Base


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