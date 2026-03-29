from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    telegram: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=True
    )
    user: Mapped["User | None"] = relationship(back_populates="employee")  # noqa: F821

    managed_projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        back_populates="manager", foreign_keys="Project.manager_id"
    )
    meeting_participations: Mapped[list["MeetingParticipant"]] = relationship(  # noqa: F821
        back_populates="employee"
    )
