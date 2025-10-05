"""
Storage Factory Tests

Tests for connection string parsing and storage backend selection.
"""

import pytest
from aop.storage import create_storage, SQLiteStorage, InMemoryStorage, PostgreSQLStorage


# ============================================================================
# VALID CONNECTION STRINGS
# ============================================================================

def test_factory_defaults_to_sqlite():
    """Test: No connection string defaults to SQLite."""
    storage = create_storage()
    assert isinstance(storage, SQLiteStorage)
    storage.close()


def test_factory_none_defaults_to_sqlite():
    """Test: None explicitly defaults to SQLite."""
    storage = create_storage(None)
    assert isinstance(storage, SQLiteStorage)
    storage.close()


def test_factory_sqlite_with_path():
    """Test: SQLite with file path."""
    storage = create_storage('sqlite:///test.db')
    assert isinstance(storage, SQLiteStorage)
    storage.close()


def test_factory_sqlite_with_memory():
    """Test: SQLite in-memory database."""
    storage = create_storage('sqlite:///:memory:')
    assert isinstance(storage, SQLiteStorage)
    storage.close()


def test_factory_sqlite_relative_path():
    """Test: SQLite with relative path."""
    storage = create_storage('sqlite://./data/events.db')
    assert isinstance(storage, SQLiteStorage)
    storage.close()


def test_factory_memory_keyword():
    """Test: 'memory' keyword creates InMemoryStorage."""
    storage = create_storage('memory')
    assert isinstance(storage, InMemoryStorage)
    storage.close()


def test_factory_memory_url():
    """Test: 'memory://' URL creates InMemoryStorage."""
    storage = create_storage('memory://')
    assert isinstance(storage, InMemoryStorage)
    storage.close()


def test_factory_postgresql():
    """Test: PostgreSQL connection string."""
    try:
        storage = create_storage('postgresql://localhost/aop_test')
        assert isinstance(storage, PostgreSQLStorage)
        storage.close()
    except (ImportError, Exception) as e:
        # Skip if psycopg2 not installed or database not available
        if "psycopg2" in str(e) or "does not exist" in str(e) or "connection" in str(e).lower():
            pytest.skip(f"PostgreSQL not available: {e}")
        raise


def test_factory_postgres_alias():
    """Test: 'postgres://' is alias for 'postgresql://'."""
    try:
        storage = create_storage('postgres://localhost/aop_test')
        assert isinstance(storage, PostgreSQLStorage)
        storage.close()
    except (ImportError, Exception) as e:
        # Skip if psycopg2 not installed or database not available
        if "psycopg2" in str(e) or "does not exist" in str(e) or "connection" in str(e).lower():
            pytest.skip(f"PostgreSQL not available: {e}")
        raise


def test_factory_postgresql_with_credentials():
    """Test: PostgreSQL with user/password in URL."""
    try:
        storage = create_storage('postgresql://user:pass@localhost:5432/aop')
        assert isinstance(storage, PostgreSQLStorage)
        storage.close()
    except (ValueError, ImportError) as e:
        # Skip - PostgreSQL not available
        pytest.skip(f"PostgreSQL not available: {e}")


# ============================================================================
# INVALID CONNECTION STRINGS
# ============================================================================

def test_factory_invalid_scheme_raises_error():
    """Test: Invalid scheme raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        create_storage('invalid://localhost/db')
    
    assert 'Unsupported storage backend' in str(exc_info.value)
    assert 'invalid' in str(exc_info.value)


def test_factory_empty_string_raises_error():
    """Test: Empty string raises ValueError."""
    with pytest.raises(ValueError):
        create_storage('')


def test_factory_malformed_url():
    """Test: Malformed URL raises ValueError."""
    with pytest.raises(ValueError):
        create_storage('not-a-valid-url')


# ============================================================================
# STORAGE FUNCTIONALITY AFTER FACTORY
# ============================================================================

def test_factory_created_storage_works():
    """Test: Storage created by factory is functional."""
    storage = create_storage('memory')
    
    # Can log and retrieve events
    event = {
        'id': '01234567-89ab-cdef-0123-456789abcdef',
        'version': '1.0',
        'timestamp': '2025-10-05T10:00:00Z',
        'agent_id': 'test-agent',
        'instance_id': '01234567-89ab-cdef-0123-456789abcdef',
        'protocol': 'mcp',
        'event_type': 'mcp.tool.call',
        'data': {'tool_name': 'test'}
    }
    
    storage.log_event(event)
    retrieved = storage.get_event(event['id'])
    
    assert retrieved is not None
    assert retrieved['id'] == event['id']
    
    storage.close()


# ============================================================================
# CONNECTION STRING PARSING EDGE CASES
# ============================================================================

def test_factory_handles_case_insensitive_schemes():
    """Test: Schemes are case-insensitive."""
    storage1 = create_storage('SQLITE:///:memory:')
    storage2 = create_storage('Memory')
    
    assert isinstance(storage1, SQLiteStorage)
    assert isinstance(storage2, InMemoryStorage)
    
    storage1.close()
    storage2.close()



def test_factory_sqlite_absolute_path():
    """Test: SQLite with absolute path."""
    storage = create_storage('sqlite:////tmp/test.db')
    assert isinstance(storage, SQLiteStorage)
    storage.close()


# ============================================================================
# SUMMARY
# ============================================================================

"""
Factory Test Summary:

✅ Valid Connection Strings (9 tests)
   - Default to SQLite
   - None defaults to SQLite
   - SQLite with path
   - SQLite in-memory
   - SQLite relative path
   - Memory keyword
   - Memory URL
   - PostgreSQL
   - Postgres alias

✅ Invalid Connection Strings (3 tests)
   - Invalid scheme
   - Empty string
   - Malformed URL

✅ Functionality (1 test)
   - Factory-created storage works

✅ Edge Cases (3 tests)
   - Case-insensitive schemes
   - PostgreSQL with credentials
   - SQLite absolute path

Total: 16 factory tests
"""