"""Schema migration runner for AOP storage backends.

A simple, dependency-free alternative to Alembic that handles version
tracking and forward-only migration of the SQLite and PostgreSQL schemas.

Usage:
    from aop.storage.migrations import migrate
    migrate("sqlite:///aop_events.db")

Migrations live in ``aop/storage/migrations/versions/`` as Python modules
each exposing ``version: str`` and ``up(executor)`` / ``down(executor)``
callables.
"""

from .runner import migrate, current_version, list_migrations

__all__ = ["migrate", "current_version", "list_migrations"]
