"""
/// script
requires-python = ">=3.13"
dependencies = ["sqlalchemy[asyncio]", "asyncpg", "passlib[bcrypt]", "python-dotenv"]
///
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Employee, Meeting, MeetingParticipant, Project, User
from app.models.reference import ProjectPriority, ProjectStatus
from app.services.auth import hash_password

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def seed() -> None:
    async with SessionLocal() as db:
        # Skip if already seeded
        from sqlalchemy import select
        existing = await db.execute(select(ProjectStatus).limit(1))
        if existing.scalar_one_or_none():
            print("Already seeded, skipping.")
            return

        # Statuses
        statuses = [
            ProjectStatus(name="Planning", is_default=True),
            ProjectStatus(name="In Progress"),
            ProjectStatus(name="Review"),
            ProjectStatus(name="Completed"),
            ProjectStatus(name="On Hold"),
        ]
        db.add_all(statuses)
        await db.flush()

        # Priorities
        priorities = [
            ProjectPriority(name="Critical", order=1, color="#ef4444"),
            ProjectPriority(name="High", order=2, color="#f97316"),
            ProjectPriority(name="Medium", order=3, color="#eab308"),
            ProjectPriority(name="Low", order=4, color="#22c55e"),
        ]
        db.add_all(priorities)
        await db.flush()

        # Admin user
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("admin1234"),
            role="admin",
        )
        db.add(admin)
        await db.flush()

        # Employees
        employees = [
            Employee(full_name="Alex Petrov", role="Project Manager", email="alex@example.com", telegram="@alex_p"),
            Employee(full_name="Maria Ivanova", role="Backend Developer", email="maria@example.com", telegram="@maria_i"),
            Employee(full_name="Dmitri Sokolov", role="Frontend Developer", email="dmitri@example.com", telegram="@dmitri_s"),
            Employee(full_name="Elena Kozlova", role="Designer", email="elena@example.com", telegram="@elena_k"),
            Employee(full_name="Ivan Novikov", role="DevOps", email="ivan@example.com", telegram="@ivan_n"),
            Employee(full_name="Olga Smirnova", role="QA Engineer", email="olga@example.com", telegram="@olga_s"),
            Employee(full_name="Kirill Volkov", role="Tech Lead", email="kirill@example.com", telegram="@kirill_v"),
            Employee(full_name="Anna Morozova", role="Backend Developer", email="anna@example.com"),
            Employee(full_name="Pavel Lebedev", role="Mobile Developer", email="pavel@example.com"),
        ]
        db.add_all(employees)
        await db.flush()

        # Projects
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        projects = [
            Project(
                name="E-Commerce Platform",
                description="Full rewrite of the client e-commerce platform",
                status_id=statuses[1].id,
                priority_id=priorities[0].id,
                manager_id=employees[0].id,
                client_name="RetailCorp",
                client_contact="cto@retailcorp.com",
                start_date=now,
                progress=45,
                budget=120000,
                tags="web,backend,payments",
            ),
            Project(
                name="Mobile App v2",
                description="iOS and Android app redesign",
                status_id=statuses[0].id,
                priority_id=priorities[1].id,
                manager_id=employees[6].id,
                client_name="StartupXYZ",
                client_contact="pm@startupxyz.com",
                progress=10,
                budget=80000,
                tags="mobile,ios,android",
            ),
            Project(
                name="Internal CRM",
                description="CRM system for internal use",
                status_id=statuses[1].id,
                priority_id=priorities[2].id,
                manager_id=employees[0].id,
                progress=70,
                tags="internal,web",
            ),
            Project(
                name="Data Analytics Dashboard",
                description="Real-time analytics for client",
                status_id=statuses[2].id,
                priority_id=priorities[1].id,
                manager_id=employees[6].id,
                client_name="DataCo",
                progress=90,
                budget=50000,
                tags="analytics,dashboard",
            ),
            Project(
                name="API Gateway Migration",
                description="Migrate from legacy gateway to new infra",
                status_id=statuses[3].id,
                priority_id=priorities[0].id,
                manager_id=employees[4].id,
                progress=100,
                tags="devops,infra",
            ),
        ]
        db.add_all(projects)
        await db.flush()

        # Meetings
        meetings = [
            Meeting(
                title="E-Commerce Kickoff",
                scheduled_at=now,
                project_id=projects[0].id,
                status="completed",
                notes="Initial planning session",
            ),
            Meeting(
                title="Mobile App Sprint Review",
                scheduled_at=now,
                project_id=projects[1].id,
                status="planned",
                meeting_link="https://meet.google.com/abc-def-ghi",
            ),
            Meeting(
                title="Analytics Dashboard Demo",
                scheduled_at=now,
                project_id=projects[3].id,
                status="planned",
            ),
        ]
        db.add_all(meetings)
        await db.flush()

        # Participants
        participants = [
            MeetingParticipant(meeting_id=meetings[0].id, employee_id=employees[0].id),
            MeetingParticipant(meeting_id=meetings[0].id, employee_id=employees[1].id),
            MeetingParticipant(meeting_id=meetings[0].id, employee_id=employees[2].id),
            MeetingParticipant(meeting_id=meetings[1].id, employee_id=employees[6].id),
            MeetingParticipant(meeting_id=meetings[1].id, employee_id=employees[8].id),
            MeetingParticipant(meeting_id=meetings[2].id, employee_id=employees[0].id),
            MeetingParticipant(meeting_id=meetings[2].id, employee_id=employees[3].id),
        ]
        db.add_all(participants)
        await db.commit()

    print("Seed complete.")
    print("Admin login: admin@example.com / admin1234")


if __name__ == "__main__":
    asyncio.run(seed())
