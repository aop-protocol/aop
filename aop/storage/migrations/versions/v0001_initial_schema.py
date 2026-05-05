"""Initial schema (matches v1.0 of the SDK)."""

version = "0001"
description = "Initial aop_events table"


def up(executor):  # type: ignore[no-untyped-def]
    if executor.dialect == "sqlite":
        executor.execute(
            """
            CREATE TABLE IF NOT EXISTS aop_events (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                instance_id TEXT NOT NULL,
                protocol TEXT NOT NULL,
                event_type TEXT NOT NULL,
                correlation_id TEXT,
                parent_id TEXT,
                severity TEXT,
                duration_ms INTEGER,
                data TEXT,
                metadata TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    else:
        executor.execute(
            """
            CREATE TABLE IF NOT EXISTS aop_events (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                agent_id TEXT NOT NULL,
                instance_id TEXT NOT NULL,
                protocol TEXT NOT NULL,
                event_type TEXT NOT NULL,
                correlation_id TEXT,
                parent_id TEXT,
                severity TEXT,
                duration_ms BIGINT,
                data JSONB,
                metadata JSONB,
                error JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )


def down(executor):  # type: ignore[no-untyped-def]
    executor.execute("DROP TABLE IF EXISTS aop_events")
