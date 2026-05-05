"""Multi-tenant isolation columns + retention column."""

version = "0003"
description = "tenant_id + retention_until columns"


def up(executor):  # type: ignore[no-untyped-def]
    if executor.dialect == "sqlite":
        for col in ("tenant_id TEXT", "retention_until TEXT"):
            try:
                executor.execute(f"ALTER TABLE aop_events ADD COLUMN {col}")
            except Exception:
                pass
        executor.execute(
            "CREATE INDEX IF NOT EXISTS idx_aop_events_tenant ON aop_events(tenant_id)"
        )
        executor.execute(
            "CREATE INDEX IF NOT EXISTS idx_aop_events_retention ON aop_events(retention_until)"
        )
    else:
        executor.execute("ALTER TABLE aop_events ADD COLUMN IF NOT EXISTS tenant_id TEXT")
        executor.execute("ALTER TABLE aop_events ADD COLUMN IF NOT EXISTS retention_until TIMESTAMP")
        executor.execute(
            "CREATE INDEX IF NOT EXISTS idx_aop_events_tenant ON aop_events(tenant_id)"
        )
        executor.execute(
            "CREATE INDEX IF NOT EXISTS idx_aop_events_retention ON aop_events(retention_until)"
        )


def down(executor):  # type: ignore[no-untyped-def]
    executor.execute("DROP INDEX IF EXISTS idx_aop_events_tenant")
    executor.execute("DROP INDEX IF EXISTS idx_aop_events_retention")
