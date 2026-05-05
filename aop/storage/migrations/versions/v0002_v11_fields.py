"""Add v1.1 fields: trace_id, span_id, parent_span_id, resource, links,
attributes, tokens, cost. Plus indexes critical for query performance."""

version = "0002"
description = "v1.1 fields + indexes"


def up(executor):  # type: ignore[no-untyped-def]
    if executor.dialect == "sqlite":
        for col in (
            "trace_id TEXT",
            "span_id TEXT",
            "parent_span_id TEXT",
            "resource TEXT",
            "links TEXT",
            "attributes TEXT",
            "tokens TEXT",
            "cost TEXT",
        ):
            try:
                executor.execute(f"ALTER TABLE aop_events ADD COLUMN {col}")
            except Exception:
                # SQLite raises if column already exists; idempotent
                pass

        for sql in (
            "CREATE INDEX IF NOT EXISTS idx_aop_events_agent_ts ON aop_events(agent_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_corr ON aop_events(correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_trace ON aop_events(trace_id)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_event_type ON aop_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_parent_span ON aop_events(parent_span_id)",
        ):
            executor.execute(sql)
    else:
        for col in (
            "trace_id TEXT",
            "span_id TEXT",
            "parent_span_id TEXT",
            "resource JSONB",
            "links JSONB",
            "attributes JSONB",
            "tokens JSONB",
            "cost JSONB",
        ):
            executor.execute(f"ALTER TABLE aop_events ADD COLUMN IF NOT EXISTS {col}")

        for sql in (
            "CREATE INDEX IF NOT EXISTS idx_aop_events_agent_ts ON aop_events(agent_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_corr ON aop_events(correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_trace ON aop_events(trace_id)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_event_type ON aop_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_aop_events_parent_span ON aop_events(parent_span_id)",
        ):
            executor.execute(sql)


def down(executor):  # type: ignore[no-untyped-def]
    # SQLite doesn't support DROP COLUMN universally; we only drop indexes.
    for sql in (
        "DROP INDEX IF EXISTS idx_aop_events_agent_ts",
        "DROP INDEX IF EXISTS idx_aop_events_corr",
        "DROP INDEX IF EXISTS idx_aop_events_trace",
        "DROP INDEX IF EXISTS idx_aop_events_event_type",
        "DROP INDEX IF EXISTS idx_aop_events_parent_span",
    ):
        executor.execute(sql)
