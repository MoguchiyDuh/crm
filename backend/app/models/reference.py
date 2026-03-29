from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(Base):
    __tablename__ = "project_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="status")  # noqa: F821


class ProjectPriority(Base):
    __tablename__ = "project_priorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    projects: Mapped[list["Project"]] = relationship(back_populates="priority")  # noqa: F821
