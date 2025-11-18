# Dashboard Guide

Complete guide to the AOP web dashboard.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Features](#features)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)

---

## Overview

The AOP Dashboard is a professional web-based interface for exploring and analyzing agent observability data in real-time.

**Features:**
- **Events Dashboard** - Tabular view with live updates, sorting, and click-to-view details
- **Trace Visualization** - Interactive tree view of distributed traces
- **Analytics Dashboard** - Charts, statistics, and insights
- **Real-time Updates** - WebSocket streaming pushes new events to top
- **Smart Filtering** - Filter by agent, event type, protocol, time range
- **Sorting & Search** - Sort by timestamp, agent, type, duration

**Tech Stack:**
- Backend: FastAPI (Python)
- Frontend: React (or modern web framework)
- Real-time: WebSockets
- Charts: Chart.js / D3.js

---

## Installation

### Prerequisites

- Python 3.8+
- pip

### Install Dashboard

```bash
pip install aop-pack
```

All dashboard dependencies are included:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `httpx` - HTTP client
- All required components

### Verify Installation

```bash
aop dashboard --help
```

---

## Getting Started

### Quick Start

**1. Start the dashboard:**

```bash
aop dashboard
```

This will:
- Start server on `http://localhost:8000`
- Automatically open your browser
- Connect to default storage (`sqlite:///aop_events.db`)

**2. Access the dashboard:**

Open `http://localhost:8000` in your browser.

### Custom Configuration

**Different storage:**

```bash
aop dashboard --storage postgresql://localhost/aop_db
```

**Custom port:**

```bash
aop dashboard --port 8080
```

**Don't open browser:**

```bash
aop dashboard --no-browser
```

### From Python

```python
from aop.dashboard import run_server

run_server(
    storage='sqlite:///aop_events.db',
    port=8000,
    open_browser=True
)
```

---

## Features

### 1. Events Dashboard (Main View)

**Description:**
Tabular view of all events with real-time updates, sorting, and filtering.

**How to use:**
1. Navigate to the **Events** tab (default view)
2. View events in a clean, sortable table
3. Click any row to view full event details in a side panel
4. New events automatically appear at the top with smooth animation
5. Use sorting controls to organize events
6. Filter by agent, event type, or protocol

**Features:**
- **Tabular Layout** - Professional table view with columns:
  - Timestamp (sortable)
  - Agent ID (sortable, alphabetical)
  - Event Type (sortable)
  - Duration (sortable)
  - Status/Icon
  - Quick preview
- **Live Updates** - WebSocket streaming pushes new events to top
- **Click-to-View** - Click any row to open detailed view panel
- **Sorting** - Sort by:
  - Date/Time (newest first, oldest first)
  - Agent ID (A-Z, Z-A)
  - Event Type (A-Z, Z-A)
  - Duration (fastest first, slowest first)
- **Color-Coded** - Visual indicators:
  - 🟢 Green: Completed events
  - 🔵 Blue: Called/Started events
  - 🔴 Red: Error events
  - 🟡 Yellow: Warning events
- **Smooth Animations** - New events slide in from top
- **Pagination** - Load more events on scroll

**Table View:**
```
┌────────────────────────────────────────────────────────────────────────┐
│ Events Dashboard                    [Filter ▼] [Sort: Newest First ▼] │
├──────────────┬────────────┬──────────────────┬──────────┬──────┬──────┤
│ Timestamp    │ Agent ID   │ Event Type       │ Duration │ Icon │ Data │
├──────────────┼────────────┼──────────────────┼──────────┼──────┼──────┤
│ 10:30:25     │ my-agent   │ mcp.tool.called  │ -        │ 🔵   │ ➤    │
│ 10:30:20     │ my-agent   │ mcp.tool.error   │ 1205ms   │ 🔴   │ ➤    │
│ 10:30:16     │ my-agent   │ mcp.tool.complet │ 125ms    │ 🟢   │ ➤    │
│ 10:30:15     │ my-agent   │ mcp.tool.called  │ -        │ 🔵   │ ➤    │
│ 10:30:10     │ worker-1   │ a2a.task.complet │ 523ms    │ 🟢   │ ➤    │
└──────────────┴────────────┴──────────────────┴──────────┴──────┴──────┘
```

**Detail Panel (on click):**
```
┌─────────────────────────────────────┐
│ Event Details              [Close X]│
├─────────────────────────────────────┤
│ ID: 01933d1e-7f8a-...               │
│ Timestamp: 2025-01-15T10:30:16Z     │
│ Agent: my-agent                     │
│ Type: mcp.tool.completed            │
│ Duration: 125ms                     │
│                                     │
│ Data:                               │
│ {                                   │
│   "tool_name": "search",            │
│   "result": {                       │
│     "count": 10,                    │
│     "results": [...]                │
│   }                                 │
│ }                                   │
│                                     │
│ [Copy JSON] [View Trace]            │
└─────────────────────────────────────┘
```

**Sorting Options:**

The table supports multiple sorting modes:

1. **By Timestamp** (default)
   - Newest First (default) - Latest events at top
   - Oldest First - Historical events at top

2. **By Agent ID**
   - A-Z (Alphabetical ascending)
   - Z-A (Alphabetical descending)

3. **By Event Type**
   - A-Z (Alphabetical ascending)
   - Z-A (Alphabetical descending)

4. **By Duration**
   - Slowest First - Highest duration at top
   - Fastest First - Lowest duration at top

**Live Updates Behavior:**

When new events arrive via WebSocket:
- New row smoothly animates in at the top (0.3s slide-in animation)
- Existing rows shift down with smooth transition
- New row briefly highlights (light blue background) then fades to normal
- Pagination adjusts automatically
- Scroll position maintains unless user is at top of page
- Update indicator shows in top-right: "🔴 Live" when receiving updates

**Filter Controls:**

Filter bar appears above the table:
```
┌────────────────────────────────────────────────────────────────┐
│ [Agent: All ▼] [Type: All ▼] [Protocol: All ▼] [⏱️ Last 1h ▼] │
└────────────────────────────────────────────────────────────────┘
```

### 2. Advanced Filtering

**Description:**
Powerful filtering and search capabilities for finding specific events.

**How to use:**
1. Navigate to the **Events** tab
2. Use filters to narrow results:
   - Agent ID
   - Event Type
   - Protocol (MCP, A2A, AP2)
   - Correlation ID
   - Time range
3. View results in table or JSON format
4. Click events to see full details

**Query Examples:**

```
Agent: my-agent
Type: mcp.tool.called
Last: 1 hour
Limit: 100
```

**Features:**
- Full-text search
- Time range picker
- Export to JSON/CSV
- Pagination for large result sets
- Syntax highlighting for JSON

### 3. Trace Visualization

**Description:**
Visualize distributed traces as interactive tree diagrams.

**How to use:**
1. Navigate to the **Traces** tab
2. Enter a correlation ID
3. View the reconstructed trace tree
4. Expand/collapse nodes
5. See event details on hover

**Trace View:**

```
Trace: workflow-123
Duration: 1,234ms | Events: 15 | Errors: 0

└─ orchestrator: task.assigned (0ms)
   ├─ worker-a: tool.called - fetch_data (5ms)
   │  └─ worker-a: tool.completed (52ms) ✅
   ├─ worker-b: tool.called - process (60ms)
   │  ├─ worker-b: sampling.request (65ms)
   │  │  └─ worker-b: sampling.response (320ms) ✅
   │  └─ worker-b: tool.completed (325ms) ✅
   └─ orchestrator: task.completed (330ms) ✅
```

**Features:**
- Collapsible tree view
- Duration waterfall
- Error highlighting
- Parent-child relationships
- Timeline visualization

### 4. Analytics Dashboard

**Description:**
Charts, graphs, and statistics for agent performance analysis.

**How to use:**
1. Navigate to the **Analytics** tab
2. Select an agent ID
3. Choose time window (1h, 24h, 7d, 30d)
4. View:
   - Tool usage charts
   - Latency percentiles
   - Error rates
   - Event timeline
   - Top slow tools

**Available Charts:**

**Tool Usage (Bar Chart):**
```
Tool Calls (Last 24h)
search     ███████████████████ 150
process    ████████████ 80
analyze    ████████ 45
```

**Latency Distribution (Histogram):**
```
Response Times
P50: 105ms | P95: 450ms | P99: 825ms

Count
  │     ╭─╮
  │   ╭─╯ ╰─╮
  │ ╭─╯     ╰─╮
  └─────────────────────
    0   200  400  600  800ms
```

**Event Timeline:**
```
Events per Hour
  │         ╱╲
  │      ╱╲╱  ╲
  │    ╱╯      ╲╱╲
  └────────────────────
    10am  12pm  2pm  4pm
```

**Features:**
- Interactive charts (zoom, pan, hover)
- Real-time updates
- Export charts as PNG
- Customizable time ranges
- Multiple chart types

### 5. Agent Monitoring

**Description:**
Per-agent performance metrics and health monitoring.

**How to use:**
1. Navigate to the **Agents** tab
2. See list of all agents
3. Click an agent to see detailed metrics
4. Monitor health indicators

**Agent Overview:**

```
┌──────────────────────────────────────┐
│ Agent: my-agent                       │
├──────────────────────────────────────┤
│ Status: 🟢 Active                    │
│ Last Event: 2 minutes ago             │
│ Total Events: 1,523                   │
│ Error Rate: 1.2%                      │
│ Avg Latency: 125ms (P95: 450ms)      │
└──────────────────────────────────────┘

Recent Activity:
  - tool.called: search (10:30:15)
  - tool.completed: search (10:30:16)
  - tool.called: analyze (10:31:00)
```

---

## API Reference

The dashboard backend exposes a REST API that can be used programmatically.

### Base URL

```
http://localhost:8000
```

### Endpoints

#### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "storage": "sqlite:///aop_events.db"
}
```

#### GET /api/agents

List all agent IDs in the database.

**Response:**
```json
["agent-1", "agent-2", "my-agent"]
```

#### GET /api/events

Query events with filters.

**Query Parameters:**
- `agent_id` (string, optional) - Filter by agent ID
- `event_type` (string, optional) - Filter by event type
- `correlation_id` (string, optional) - Filter by correlation ID
- `protocol` (string, optional) - Filter by protocol
- `limit` (int, default: 50) - Max results (1-1000)
- `offset` (int, default: 0) - Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/events?agent_id=my-agent&limit=10"
```

**Response:**
```json
[
  {
    "id": "01933d1e-...",
    "timestamp": "2025-01-15T10:30:00Z",
    "agent_id": "my-agent",
    "event_type": "mcp.tool.called",
    ...
  }
]
```

#### GET /api/events/{event_id}

Get single event by ID.

**Response:**
```json
{
  "id": "01933d1e-...",
  "timestamp": "2025-01-15T10:30:00Z",
  ...
}
```

#### GET /api/traces/{correlation_id}

Reconstruct trace by correlation ID.

**Response:**
```json
{
  "correlation_id": "trace-123",
  "root_event": {...},
  "children": [...],
  "total_duration_ms": 1234,
  "event_count": 15,
  "error_count": 0
}
```

#### GET /api/stats

Get comprehensive statistics for an agent.

**Query Parameters:**
- `agent_id` (string, required) - Agent ID
- `start_time` (string, optional) - ISO format
- `end_time` (string, optional) - ISO format

**Example:**
```bash
curl "http://localhost:8000/api/stats?agent_id=my-agent"
```

**Response:**
```json
{
  "agent_id": "my-agent",
  "tool_counts": {
    "search": 150,
    "process": 80
  },
  "event_counts": {
    "mcp.tool.called": 275,
    "mcp.tool.completed": 270
  },
  "avg_durations": {
    "search": 125.5,
    "process": 45.2
  },
  "percentiles": {
    "p50": 105.2,
    "p95": 450.8,
    "p99": 825.3
  }
}
```

#### GET /api/timeline

Get event counts over time.

**Query Parameters:**
- `agent_id` (string, required) - Agent ID
- `bucket_size` (string, default: "1h") - Time bucket (1h, 1d, etc.)

**Response:**
```json
[
  {"time": "2025-01-15T10:00:00Z", "count": 45},
  {"time": "2025-01-15T11:00:00Z", "count": 62}
]
```

#### WebSocket /ws/events

Real-time event streaming via WebSocket.

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New event:', data);
};
```

**Message format:**
```json
{
  "type": "event",
  "data": {
    "id": "...",
    "event_type": "mcp.tool.called",
    ...
  }
}
```

---

## Configuration

### Server Configuration

**Environment Variables:**

```bash
# Storage
export AOP_STORAGE="postgresql://localhost/aop"

# Server
export AOP_DASHBOARD_PORT=8000
export AOP_DASHBOARD_HOST="0.0.0.0"

# CORS (for production)
export AOP_CORS_ORIGINS="https://yourdomain.com"
```

**Python Configuration:**

```python
from aop.dashboard import run_server

run_server(
    storage='postgresql://localhost/aop',
    port=8000,
    host='0.0.0.0',
    open_browser=False
)
```

### Frontend Configuration

**Custom Refresh Interval:**

Default is 5 seconds. To change, modify the frontend config or use query parameter:

```
http://localhost:8000?refresh=10
```

**Theme:**

```
http://localhost:8000?theme=dark
```

---

## Deployment

### Production Deployment

#### 1. Using Docker

**Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install AOP with dashboard
RUN pip install aop[dashboard]

# Expose port
EXPOSE 8000

# Run dashboard
CMD ["aop", "dashboard", "--port", "8000", "--storage", "${AOP_STORAGE}", "--no-browser"]
```

**Build and run:**

```bash
docker build -t aop-dashboard .
docker run -p 8000:8000 \
  -e AOP_STORAGE="postgresql://db:5432/aop" \
  aop-dashboard
```

#### 2. Using systemd

**Service file:** `/etc/systemd/system/aop-dashboard.service`

```ini
[Unit]
Description=AOP Dashboard
After=network.target

[Service]
Type=simple
User=aop
WorkingDirectory=/opt/aop
Environment="AOP_STORAGE=postgresql://localhost/aop"
ExecStart=/usr/local/bin/aop dashboard --port 8000 --no-browser
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl enable aop-dashboard
sudo systemctl start aop-dashboard
```

#### 3. Behind Nginx

**Nginx configuration:**

```nginx
server {
    listen 80;
    server_name dashboard.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Security Considerations

**1. Authentication:**

The dashboard doesn't include built-in authentication. For production:

```nginx
# Add basic auth in Nginx
location / {
    auth_basic "AOP Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```

**2. CORS:**

Restrict origins in production:

```python
# In server.py or via environment
CORS_ORIGINS = ["https://dashboard.example.com"]
```

**3. HTTPS:**

Always use HTTPS in production (via Nginx/Caddy).

**4. Rate Limiting:**

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20;
    proxy_pass http://localhost:8000;
}
```

---

## Troubleshooting

### Dashboard won't start

**Error:** `Dashboard dependencies not installed`

**Solution:**
```bash
pip install aop[dashboard]
```

### WebSocket connection fails

**Error:** `WebSocket connection to 'ws://localhost:8000/ws/events' failed`

**Solutions:**
- Check firewall allows port 8000
- Verify server is running: `curl http://localhost:8000/api/health`
- Check browser console for CORS errors

### Slow query performance

**Issue:** Event queries taking >5 seconds

**Solutions:**
1. Add database indexes (PostgreSQL):
   ```sql
   CREATE INDEX idx_agent_timestamp ON events(agent_id, timestamp);
   CREATE INDEX idx_correlation ON events(correlation_id);
   ```

2. Reduce query limit:
   ```
   limit=50  # Instead of 1000
   ```

3. Use time filters:
   ```bash
   curl "http://localhost:8000/api/events?agent_id=my-agent&start_time=2025-01-15T00:00:00Z"
   ```

### Port already in use

**Error:** `Port 8000 is already in use`

**Solution:**
```bash
# Use different port
aop dashboard --port 8080

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

---

## Development

### Running in Dev Mode

```bash
# Install dev dependencies
pip install -e ".[dashboard,dev]"

# Run with auto-reload
uvicorn aop.dashboard.server:app --reload --port 8000
```

### Frontend Development

The dashboard frontend (if separate) should be developed with:

```bash
# Install frontend dependencies
cd frontend
npm install

# Run dev server
npm run dev
```

Then configure proxy to backend:

```javascript
// vite.config.js or similar
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
}
```

---

## Next Steps

- **[CLI Reference](cli.md)** - Command-line tools
- **[User Guide](user-guide.md)** - Programmatic usage
- **[Integrations](integrations.md)** - Connect with other tools
- **[API Reference](api-reference.md)** - Complete API docs
