"""fts: tsvector on projects and employees

Revision ID: c55930196f22
Revises: b44829085f21
Create Date: 2026-03-29 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c55930196f22"
down_revision: Union[str, None] = "b44829085f21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE projects ADD COLUMN search_vector tsvector")
    op.execute("ALTER TABLE employees ADD COLUMN search_vector tsvector")

    op.execute(
        "CREATE INDEX ix_projects_search_vector ON projects USING GIN(search_vector)"
    )
    op.execute(
        "CREATE INDEX ix_employees_search_vector ON employees USING GIN(search_vector)"
    )

    op.execute("""
        CREATE FUNCTION projects_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.name, '') || ' ' ||
                coalesce(NEW.description, '') || ' ' ||
                coalesce(NEW.client_name, '') || ' ' ||
                coalesce(NEW.tags, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER projects_search_vector_trigger
        BEFORE INSERT OR UPDATE ON projects
        FOR EACH ROW EXECUTE FUNCTION projects_search_vector_update();
    """)

    op.execute("""
        CREATE FUNCTION employees_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                coalesce(NEW.full_name, '') || ' ' ||
                coalesce(NEW.role, '') || ' ' ||
                coalesce(NEW.email, '') || ' ' ||
                coalesce(NEW.notes, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER employees_search_vector_trigger
        BEFORE INSERT OR UPDATE ON employees
        FOR EACH ROW EXECUTE FUNCTION employees_search_vector_update();
    """)

    # Populate existing rows
    op.execute("""
        UPDATE projects SET search_vector = to_tsvector('english',
            coalesce(name, '') || ' ' ||
            coalesce(description, '') || ' ' ||
            coalesce(client_name, '') || ' ' ||
            coalesce(tags, '')
        )
    """)
    op.execute("""
        UPDATE employees SET search_vector = to_tsvector('english',
            coalesce(full_name, '') || ' ' ||
            coalesce(role, '') || ' ' ||
            coalesce(email, '') || ' ' ||
            coalesce(notes, '')
        )
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS projects_search_vector_trigger ON projects")
    op.execute("DROP TRIGGER IF EXISTS employees_search_vector_trigger ON employees")
    op.execute("DROP FUNCTION IF EXISTS projects_search_vector_update()")
    op.execute("DROP FUNCTION IF EXISTS employees_search_vector_update()")
    op.execute("DROP INDEX IF EXISTS ix_projects_search_vector")
    op.execute("DROP INDEX IF EXISTS ix_employees_search_vector")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS search_vector")
    op.execute("ALTER TABLE employees DROP COLUMN IF EXISTS search_vector")
