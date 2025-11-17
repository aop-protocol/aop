# Troubleshooting

Common issues and solutions for AOP.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Storage Issues](#storage-issues)
- [Performance Issues](#performance-issues)
- [Query Issues](#query-issues)
- [Dashboard Issues](#dashboard-issues)
- [Exporter Issues](#exporter-issues)
- [Integration Issues](#integration-issues)
- [Debugging Tips](#debugging-tips)

---

## Installation Issues

### ImportError: No module named 'aop'

**Problem:** AOP not installed.

**Solution:**

```bash
pip install aop
```

**Verify installation:**

```bash
python -c "import aop; print(aop.__version__)"
```

### Missing Optional Dependencies

**Problem:**

```
ImportError: No module named 'click'
ImportError: No module named 'prometheus_client'
```

**Solution:** Install with optional features:

```bash
# CLI tools
pip install aop[cli]

# Dashboard
pip install aop[dashboard]

# Prometheus
pip install aop[prometheus]

# OpenTelemetry
pip install aop[otel]

# Everything
pip install aop[cli,dashboard,otel,prometheus]
```

### Version Conflicts

**Problem:**

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solution:** Use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install aop[cli,dashboard]
```

---

## Storage Issues

### Database Locked (SQLite)

**Problem:**

```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple writers to SQLite database.

**Solutions:**

**1. Use WAL mode:**

```python
client = AOPClient(storage='sqlite:///aop_events.db?mode=wal')
```

**2. Use PostgreSQL for multi-writer scenarios:**

```python
client = AOPClient(storage='postgresql://localhost/aop')
```

**3. Increase timeout:**

```python
from aop.storage import SQLiteStorage

storage = SQLiteStorage(
    'sqlite:///aop_events.db',
    timeout=30.0  # Wait up to 30 seconds
)
client = AOPClient(storage=storage)
```

### Database File Not Found

**Problem:**

```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/aop_events.db'
```

**Cause:** Parent directory doesn't exist.

**Solution:**

```python
from pathlib import Path

db_path = Path('/path/to/aop_events.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

client = AOPClient(storage=f'sqlite:///{db_path}')
```

### PostgreSQL Connection Failed

**Problem:**

```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

**1. Verify PostgreSQL is running:**

```bash
pg_isready -h localhost -p 5432
```

**2. Check connection string:**

```python
# Correct format
storage = 'postgresql://user:password@localhost:5432/dbname'

# With special characters in password
from urllib.parse import quote_plus
password = quote_plus('p@ssw0rd!')
storage = f'postgresql://user:{password}@localhost:5432/dbname'
```

**3. Check firewall/network:**

```bash
telnet localhost 5432
```

### Permission Denied

**Problem:**

```
PermissionError: [Errno 13] Permission denied: 'aop_events.db'
```

**Solution:**

```bash
# Fix file permissions
chmod 644 aop_events.db
chmod 755 $(dirname aop_events.db)

# Or use a writable directory
client = AOPClient(storage='sqlite:///~/.aop/events.db')
```

---

## Performance Issues

### Slow Event Logging

**Problem:** Event logging takes >10ms.

**Diagnosis:**

```python
import time

start = time.time()
client.log_event(event)
duration = (time.time() - start) * 1000
print(f"Log duration: {duration:.2f}ms")
```

**Solutions:**

**1. Disable validation in production:**

```python
client.log_event(event, validate=False)
```

**2. Use connection pooling (PostgreSQL):**

```python
from aop.storage import PostgreSQLStorage

storage = PostgreSQLStorage(
    connection_string,
    pool_size=20,
    max_overflow=40
)
```

**3. Check disk I/O:**

```bash
# Linux
iostat -x 1

# Mac
iostat -w 1
```

**4. Use faster storage:**

- RAM disk for SQLite
- SSD instead of HDD
- Local PostgreSQL instead of remote

### Slow Queries

**Problem:** Queries take >5 seconds.

**Diagnosis:**

```python
import time

start = time.time()
events = client.query(agent_id='my-agent', limit=1000)
duration = time.time() - start
print(f"Query duration: {duration:.2f}s")
print(f"Events returned: {len(events)}")
```

**Solutions:**

**1. Add time filters:**

```python
from datetime import datetime, timedelta

# Instead of querying all time
events = client.query(agent_id='my-agent')  # Slow

# Query recent events only
events = client.query(
    agent_id='my-agent',
    start_time=datetime.now() - timedelta(hours=1)  # Fast
)
```

**2. Reduce limit:**

```python
# Instead of
events = client.query(limit=100000)  # Slow

# Use
events = client.query(limit=1000)  # Fast
```

**3. Add database indexes (PostgreSQL):**

```sql
-- Check existing indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'events';

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_agent_timestamp
ON events(agent_id, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_correlation
ON events(correlation_id);

CREATE INDEX CONCURRENTLY idx_event_type
ON events(event_type);
```

**4. Analyze query plan:**

```sql
EXPLAIN ANALYZE
SELECT * FROM events
WHERE agent_id = 'my-agent'
AND timestamp > '2025-01-15T00:00:00Z'
ORDER BY timestamp DESC
LIMIT 100;
```

**5. Vacuum and analyze (PostgreSQL):**

```sql
VACUUM ANALYZE events;
```

### High Memory Usage

**Problem:** Process using too much RAM.

**Cause:** Large query results held in memory.

**Solutions:**

**1. Use pagination:**

```python
# Instead of loading all events
all_events = client.query(limit=1000000)  # High memory

# Use pagination
page_size = 1000
offset = 0
while True:
    page = client.query(limit=page_size, offset=offset)
    if not page:
        break

    process_page(page)
    offset += page_size
```

**2. Stream processing:**

```python
# Process events one at a time
for event in client.query_stream(agent_id='my-agent'):
    process_event(event)
    # Event garbage collected after processing
```

---

## Query Issues

### No Events Returned

**Problem:** Query returns empty list.

**Diagnosis:**

```python
# Check if any events exist
all_events = client.query(limit=10)
print(f"Total events in DB: {len(all_events)}")

# Check specific query
filtered = client.query(agent_id='my-agent', limit=10)
print(f"Filtered events: {len(filtered)}")
```

**Common Causes:**

**1. Wrong agent_id:**

```python
# Check what agent IDs exist
events = client.query(limit=1000)
agent_ids = set(e['agent_id'] for e in events)
print(f"Available agent IDs: {agent_ids}")
```

**2. Time filter too restrictive:**

```python
# Remove time filter to test
events = client.query(agent_id='my-agent')  # No time filter
```

**3. Case sensitivity:**

```python
# agent_id is case-sensitive
client.query(agent_id='My-Agent')  # Won't match 'my-agent'
```

### Timezone Issues

**Problem:** Time-based queries return unexpected results.

**Cause:** Timestamp timezone mismatch.

**Solution:** Always use UTC:

```python
from datetime import datetime, timezone

# Correct: UTC timezone
start_time = datetime.now(timezone.utc) - timedelta(hours=1)
events = client.query(start_time=start_time)

# Wrong: Naive datetime
start_time = datetime.now() - timedelta(hours=1)  # Local time
```

### Correlation ID Not Found

**Problem:** `get_trace()` returns empty.

**Diagnosis:**

```python
# Check if correlation_id exists
correlation_id = 'trace-123'
events = client.query(correlation_id=correlation_id)
print(f"Events with correlation_id: {len(events)}")

# List all correlation IDs
all_events = client.query(limit=10000)
correlation_ids = {e.get('correlation_id') for e in all_events if e.get('correlation_id')}
print(f"Available correlation IDs: {correlation_ids}")
```

**Common Causes:**

- Typo in correlation_id
- Events not logged with correlation_id
- Case sensitivity

---

## Dashboard Issues

### Dashboard Won't Start

**Problem:**

```
Error: Dashboard dependencies not installed.
```

**Solution:**

```bash
pip install aop[dashboard]
```

### Port Already in Use

**Problem:**

```
OSError: [Errno 48] Address already in use
```

**Solution:**

**1. Use different port:**

```bash
aop dashboard --port 8080
```

**2. Kill process on port:**

```bash
# Find process
lsof -ti:8000

# Kill it
lsof -ti:8000 | xargs kill -9
```

### WebSocket Connection Failed

**Problem:** Live feed not working, browser console shows:

```
WebSocket connection to 'ws://localhost:8000/ws/events' failed
```

**Solutions:**

**1. Check server is running:**

```bash
curl http://localhost:8000/api/health
```

**2. Check firewall:**

```bash
# Allow port 8000
sudo ufw allow 8000  # Linux
```

**3. Check CORS:**

```python
# In production, CORS may block WebSocket
# Check server logs for CORS errors
```

### Slow Dashboard

**Problem:** Dashboard takes >10s to load.

**Diagnosis:**

```bash
# Check API response time
time curl http://localhost:8000/api/events?limit=100
```

**Solutions:**

**1. Reduce query limits:**

```
# In dashboard config
MAX_EVENTS = 100  # Instead of 10000
```

**2. Add database indexes**

See [Slow Queries](#slow-queries) above.

**3. Use time filters:**

```
# Only query recent events
start_time = now - 1 hour
```

---

## Exporter Issues

### OpenTelemetry Export Failed

**Problem:**

```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Cause:** OTEL collector not running.

**Solution:**

**1. Start OTEL collector:**

```bash
docker run -p 4317:4317 -p 4318:4318 \
  otel/opentelemetry-collector:latest
```

**2. Verify endpoint:**

```bash
telnet localhost 4317
```

**3. Check endpoint in code:**

```python
# Correct gRPC endpoint
exporter.export_to_collector(
    events,
    endpoint='http://localhost:4317'  # Not 4318 (HTTP)
)
```

### Prometheus Metrics Not Updating

**Problem:** Prometheus shows stale metrics.

**Diagnosis:**

```bash
# Check if exporter is running
curl http://localhost:9090/metrics

# Check poll interval
# Should update every 30 seconds by default
```

**Solutions:**

**1. Reduce poll interval:**

```bash
aop prometheus --poll-interval 10.0
```

**2. Check if new events are being logged:**

```python
client.log_event({...})

# Wait for poll interval, then check
curl http://localhost:9090/metrics | grep aop_events_total
```

**3. Check for errors in server logs:**

```python
# Server should print errors
server = PrometheusExporterServer(...)
server.start()
# Watch console for errors
```

### Duplicate Metrics (Prometheus)

**Problem:** Event counts doubling on each poll.

**Cause:** Old bug (fixed in v0.1.0).

**Solution:** Upgrade to latest version:

```bash
pip install --upgrade aop
```

---

## Integration Issues

### LangChain Integration Not Working

**Problem:** Events not logged when using LangChain.

**Diagnosis:**

```python
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='langchain-agent')
def my_tool(query: str):
    print(f"Tool called with: {query}")
    return "result"

# Test directly
result = my_tool("test")

# Check if events were logged
events = client.query(agent_id='langchain-agent')
print(f"Events logged: {len(events)}")
```

**Solution:** Make sure decorator is applied to the actual function passed to LangChain:

```python
# Correct
@client.mcp.observe_tool(agent_id='agent')
def search(query: str):
    return do_search(query)

lc_tool = Tool(name="Search", func=search, ...)

# Wrong
def search(query: str):
    return do_search(query)

lc_tool = Tool(
    name="Search",
    func=client.mcp.observe_tool(agent_id='agent')(search),  # Won't work
    ...
)
```

### OpenTelemetry Trace IDs Not Matching

**Problem:** Spans have different trace_ids even with same correlation_id.

**Cause:** Old bug (fixed in v0.1.0).

**Solution:** Upgrade to latest version:

```bash
pip install --upgrade aop
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('aop')
logger.setLevel(logging.DEBUG)

# Now you'll see debug logs
client = AOPClient()
```

### Inspect Raw Events

```python
# Get events as Python dicts
events = client.query(limit=10)

# Pretty print
import json
print(json.dumps(events[0], indent=2))
```

### Check Database Directly

**SQLite:**

```bash
sqlite3 aop_events.db

sqlite> SELECT COUNT(*) FROM events;
sqlite> SELECT agent_id, COUNT(*) FROM events GROUP BY agent_id;
sqlite> SELECT * FROM events ORDER BY timestamp DESC LIMIT 5;
```

**PostgreSQL:**

```bash
psql -U user -d aop_db

SELECT COUNT(*) FROM events;
SELECT agent_id, COUNT(*) FROM events GROUP BY agent_id;
SELECT * FROM events ORDER BY timestamp DESC LIMIT 5;
```

### Validate Event Manually

```python
from aop.validation import validate_event

event = {...}

try:
    validate_event(event)
    print("Event is valid")
except Exception as e:
    print(f"Validation error: {e}")
```

### Test Storage Connection

```python
from aop import AOPClient

try:
    client = AOPClient(storage='sqlite:///test.db')
    client.log_event({
        'agent_id': 'test',
        'event_type': 'test.event',
        'protocol': 'mcp'
    })
    events = client.query(limit=1)
    print(f"✓ Storage working. Events: {len(events)}")
    client.close()
except Exception as e:
    print(f"✗ Storage error: {e}")
```

### Profile Performance

```python
import cProfile
import pstats

def benchmark():
    client = AOPClient()
    for i in range(1000):
        client.log_event({
            'agent_id': 'test',
            'event_type': 'test.event',
            'protocol': 'mcp',
            'data': {'index': i}
        })
    client.close()

# Profile
cProfile.run('benchmark()', 'profile_stats')

# Analyze
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative').print_stats(10)
```

### Check Disk Space

```bash
# Linux/Mac
df -h

# Check database size
du -h aop_events.db
```

### Monitor System Resources

```bash
# CPU and memory usage
top

# Disk I/O
iostat -x 1

# Network (if using PostgreSQL)
netstat -an | grep 5432
```

---

## Getting Help

### Search Documentation

- [User Guide](user-guide.md)
- [API Reference](api-reference.md)
- [Architecture](architecture.md)

### Check Examples

- [Getting Started](getting-started.md)
- [Examples Directory](examples/)

### Report Issues

If you've found a bug:

1. Check [GitHub Issues](https://github.com/aop-protocol/aop/issues)
2. Search for existing issues
3. Create new issue with:
   - AOP version (`pip show aop`)
   - Python version (`python --version`)
   - Operating system
   - Minimal reproduction code
   - Error message and traceback

### Ask Questions

- [GitHub Discussions](https://github.com/aop-protocol/aop/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/aop) (tag: `aop`)

---

## Next Steps

- **[User Guide](user-guide.md)** - Comprehensive usage guide
- **[API Reference](api-reference.md)** - Complete API docs
- **[Architecture](architecture.md)** - System design
- **[Getting Started](getting-started.md)** - Quick start guide
