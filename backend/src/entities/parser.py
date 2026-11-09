from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.database.core import Base


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
