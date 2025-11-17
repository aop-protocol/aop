# Integrations

Complete guide to integrating AOP with other observability tools and frameworks.

## Table of Contents

- [OpenTelemetry](#opentelemetry)
- [Prometheus](#prometheus)
- [Jaeger](#jaeger)
- [Grafana](#grafana)
- [Framework Integrations](#framework-integrations)
- [Custom Integrations](#custom-integrations)

---

## OpenTelemetry

Export AOP events to OpenTelemetry format for distributed tracing.

### Installation

```bash
pip install aop[otel]
```

This installs:
- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp`

### Basic Usage

#### Export to OTEL Collector

```python
from aop import AOPClient
from aop.exporters import OpenTelemetryExporter

# Create client and get events
client = AOPClient()
events = client.query(correlation_id='trace-123')

# Export to OTEL collector
exporter = OpenTelemetryExporter(client=client)
spans = exporter.export_events(events)

# Send to collector
exporter.export_to_collector(
    spans=spans,
    endpoint='http://localhost:4317'  # OTEL collector gRPC endpoint
)
```

#### Export to File

```python
# Export to JSON file for analysis
exporter.export_to_file(
    spans=spans,
    filepath='trace.json'
)
```

### Event to Span Mapping

AOP events are converted to OTEL spans:

**AOP Event:**
```python
{
    'id': '01933d1e-...',
    'timestamp': '2025-01-15T10:30:00.123456Z',
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'correlation_id': 'trace-123',
    'parent_id': '01933d1d-...',
    'duration_ms': 125,
    'data': {
        'tool_name': 'search',
        'params': {'query': 'AI'}
    }
}
```

**OTEL Span:**
```python
{
    'trace_id': '...',           # Derived from correlation_id
    'span_id': '...',            # Derived from event id
    'parent_span_id': '...',     # Derived from parent_id
    'name': 'search',            # From tool_name
    'start_time': 1705318200123, # From timestamp
    'end_time': 1705318200248,   # timestamp + duration_ms
    'attributes': {
        'aop.event_id': '01933d1e-...',
        'aop.event_type': 'mcp.tool.called',
        'aop.agent_id': 'my-agent',
        'aop.protocol': 'mcp',
        'tool.name': 'search',
        'tool.params': '{"query":"AI"}'
    }
}
```

### Custom Service Name

```python
exporter = OpenTelemetryExporter(
    client=client,
    service_name='my-agent-service',
    resource_attributes={
        'service.version': '1.0.0',
        'deployment.environment': 'production'
    }
)
```

### CLI Export

```bash
# Export trace to OTEL collector
aop export-otel \
  --correlation-id trace-123 \
  --endpoint http://localhost:4317

# Export to JSON file
aop export-otel \
  --correlation-id trace-123 \
  --output trace.json
```

### OTEL Collector Configuration

**collector-config.yaml:**

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, logging]
```

**Run collector:**

```bash
docker run -p 4317:4317 -p 4318:4318 \
  -v $(pwd)/collector-config.yaml:/etc/otel-collector-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

### Automatic Export

Auto-export new events to OTEL:

```python
from aop import AOPClient
from aop.exporters import OpenTelemetryExporter
import threading
import time

client = AOPClient()
exporter = OpenTelemetryExporter(client)

def auto_export():
    """Background thread that exports new events."""
    last_timestamp = None

    while True:
        # Get new events since last export
        events = client.query(
            start_time=last_timestamp,
            limit=1000
        )

        if events:
            spans = exporter.export_events(events)
            exporter.export_to_collector(
                spans=spans,
                endpoint='http://localhost:4317'
            )
            last_timestamp = events[-1]['timestamp']

        time.sleep(10)  # Export every 10 seconds

# Start background exporter
thread = threading.Thread(target=auto_export, daemon=True)
thread.start()
```

---

## Prometheus

Expose AOP metrics for Prometheus scraping.

### Installation

```bash
pip install aop[prometheus]
```

This installs:
- `prometheus-client`

### Basic Usage

#### Standalone Server

```python
from aop.exporters import PrometheusExporterServer

server = PrometheusExporterServer(
    storage='sqlite:///aop_events.db',
    port=9090,
    poll_interval=30.0  # Poll storage every 30 seconds
)

server.start()

# Metrics available at http://localhost:9090/metrics
```

#### CLI

```bash
aop prometheus --port 9090 --poll-interval 30
```

### Metrics Exposed

**1. Total Events Counter**
```prometheus
# HELP aop_events_total Total number of AOP events
# TYPE aop_events_total counter
aop_events_total{event_type="mcp.tool.called",agent_id="my-agent",protocol="mcp"} 150
aop_events_total{event_type="mcp.tool.completed",agent_id="my-agent",protocol="mcp"} 145
aop_events_total{event_type="mcp.tool.error",agent_id="my-agent",protocol="mcp"} 5
```

**2. Tool Duration Histogram**
```prometheus
# HELP aop_tool_duration_seconds Tool execution duration in seconds
# TYPE aop_tool_duration_seconds histogram
aop_tool_duration_seconds_bucket{tool_name="search",agent_id="my-agent",le="0.001"} 5
aop_tool_duration_seconds_bucket{tool_name="search",agent_id="my-agent",le="0.01"} 25
aop_tool_duration_seconds_bucket{tool_name="search",agent_id="my-agent",le="0.1"} 120
aop_tool_duration_seconds_bucket{tool_name="search",agent_id="my-agent",le="1.0"} 150
aop_tool_duration_seconds_sum{tool_name="search",agent_id="my-agent"} 18.75
aop_tool_duration_seconds_count{tool_name="search",agent_id="my-agent"} 150
```

**3. Tool Errors Counter**
```prometheus
# HELP aop_tool_errors_total Total number of tool errors
# TYPE aop_tool_errors_total counter
aop_tool_errors_total{tool_name="search",agent_id="my-agent",error_code="TIMEOUT"} 3
aop_tool_errors_total{tool_name="search",agent_id="my-agent",error_code="NOT_FOUND"} 2
```

**4. Event Rate Gauge**
```prometheus
# HELP aop_event_rate Event rate (events per minute)
# TYPE aop_event_rate gauge
aop_event_rate{agent_id="my-agent"} 45.3
```

### Prometheus Configuration

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'aop'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Run Prometheus:**

```bash
docker run -p 9091:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

Access Prometheus UI at `http://localhost:9091`

### Example Queries

**Event rate over time:**
```promql
rate(aop_events_total[5m])
```

**P95 latency:**
```promql
histogram_quantile(0.95,
  rate(aop_tool_duration_seconds_bucket[5m])
)
```

**Error rate:**
```promql
rate(aop_tool_errors_total[5m])
```

**Events by agent:**
```promql
sum(aop_events_total) by (agent_id)
```

**Slow tools (P99 > 1s):**
```promql
histogram_quantile(0.99,
  rate(aop_tool_duration_seconds_bucket[5m])
) > 1.0
```

---

## Jaeger

Visualize AOP traces in Jaeger UI.

### Setup

**1. Start Jaeger:**

```bash
docker run -d \
  -p 16686:16686 \
  -p 14250:14250 \
  jaegertracing/all-in-one:latest
```

**2. Start OTEL Collector (with Jaeger exporter):**

See [OTEL Collector Configuration](#otel-collector-configuration) above.

**3. Export AOP traces:**

```bash
# Export to OTEL collector (which forwards to Jaeger)
aop export-otel \
  --correlation-id trace-123 \
  --endpoint http://localhost:4317
```

**4. View in Jaeger:**

Open `http://localhost:16686` and search for your trace.

### Direct Integration (Alternative)

```python
from aop import AOPClient
from aop.exporters import OpenTelemetryExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)

# Create tracer provider
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

# Export AOP events
client = AOPClient()
exporter = OpenTelemetryExporter(client=client)

events = client.query(correlation_id='trace-123')
spans = exporter.export_events(events)

# Send to Jaeger
for span in spans:
    span.end()
```

---

## Grafana

Visualize AOP metrics and traces in Grafana.

### Setup

**1. Start Grafana:**

```bash
docker run -d \
  -p 3000:3000 \
  grafana/grafana:latest
```

Access at `http://localhost:3000` (default: admin/admin)

**2. Add Prometheus Data Source:**

- Go to Configuration → Data Sources
- Add Prometheus
- URL: `http://localhost:9091`
- Save & Test

**3. Add Jaeger Data Source (for traces):**

- Add Jaeger
- URL: `http://localhost:16686`
- Save & Test

### Example Dashboard

**AOP Overview Dashboard:**

```json
{
  "dashboard": {
    "title": "AOP Agent Monitoring",
    "panels": [
      {
        "title": "Event Rate",
        "targets": [
          {
            "expr": "rate(aop_events_total[5m])",
            "legendFormat": "{{agent_id}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Tool Latency (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(aop_tool_duration_seconds_bucket[5m]))",
            "legendFormat": "{{tool_name}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(aop_tool_errors_total[5m])",
            "legendFormat": "{{error_code}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Agents",
        "targets": [
          {
            "expr": "count(count by (agent_id) (aop_events_total))",
            "legendFormat": "Agents"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

**Import Dashboard:**

1. Create → Import
2. Paste JSON above
3. Select Prometheus data source
4. Import

### Alerts

**High Error Rate:**

```yaml
- alert: HighErrorRate
  expr: rate(aop_tool_errors_total[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"
    description: "Agent {{ $labels.agent_id }} has error rate {{ $value }}"
```

**Slow Tools:**

```yaml
- alert: SlowTools
  expr: histogram_quantile(0.95, rate(aop_tool_duration_seconds_bucket[5m])) > 1.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Tool latency is high"
    description: "Tool {{ $labels.tool_name }} P95 latency is {{ $value }}s"
```

---

## Framework Integrations

### LangChain

Integrate AOP with LangChain agents:

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from aop import AOPClient

client = AOPClient()

# Wrap LangChain tools with AOP observability
@client.mcp.observe_tool(agent_id='langchain-agent')
def search_tool(query: str) -> str:
    """Search for information."""
    # Your search implementation
    return f"Results for: {query}"

# Create LangChain tool
lc_tool = Tool(
    name="Search",
    func=search_tool,
    description="Search for information"
)

# Use in agent
agent = create_openai_functions_agent(llm, [lc_tool], prompt)
executor = AgentExecutor(agent=agent, tools=[lc_tool])

# All tool calls are now logged to AOP
result = executor.invoke({"input": "What is AI?"})
```

### AutoGen

Integrate with Microsoft AutoGen:

```python
from autogen import AssistantAgent, UserProxyAgent
from aop import AOPClient

client = AOPClient()

# Create custom function
@client.mcp.observe_tool(agent_id='autogen-assistant')
def analyze_data(data: dict) -> dict:
    """Analyze data."""
    return {"analysis": "complete"}

# Register with AutoGen
assistant = AssistantAgent(
    name="assistant",
    llm_config={"functions": [analyze_data]}
)

user_proxy = UserProxyAgent(
    name="user",
    function_map={"analyze_data": analyze_data}
)

# Conversations are logged
user_proxy.initiate_chat(assistant, message="Analyze this data: {...}")
```

### Haystack

Integrate with Haystack pipelines:

```python
from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from aop import AOPClient

client = AOPClient()

# Wrap pipeline components
class AOPWrappedPromptBuilder(PromptBuilder):
    def run(self, **kwargs):
        with client.mcp.tool_execution(
            agent_id='haystack-pipeline',
            tool_name='prompt_builder',
            params=kwargs
        ) as handle:
            result = super().run(**kwargs)
            handle.set_result(result)
            return result

# Use in pipeline
pipeline = Pipeline()
pipeline.add_component("builder", AOPWrappedPromptBuilder(template="..."))
```

### CrewAI

```python
from crewai import Agent, Task, Crew
from aop import AOPClient

client = AOPClient()

# Wrap crew tools
@client.mcp.observe_tool(agent_id='crew-agent')
def research_tool(query: str) -> str:
    """Research a topic."""
    return f"Research results for {query}"

# Create agent with observed tool
researcher = Agent(
    role='Researcher',
    goal='Research topics',
    tools=[research_tool]
)

task = Task(
    description='Research AI agents',
    agent=researcher
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

---

## Custom Integrations

### Custom Exporter

Implement your own exporter:

```python
from aop.exporters.base import BaseExporter
from typing import List, Dict, Any

class CustomExporter(BaseExporter):
    """Export to custom format or service."""

    def export(self, events: List[Dict[str, Any]]) -> str:
        """
        Export events to custom format.

        Args:
            events: List of AOP event dictionaries

        Returns:
            Exported data as string
        """
        # Your export logic
        lines = []
        for event in events:
            line = f"{event['timestamp']} | {event['agent_id']} | {event['event_type']}"
            lines.append(line)

        return '\n'.join(lines)

    def export_to_service(self, events: List[Dict[str, Any]], endpoint: str):
        """Export to external service."""
        import requests

        data = self.export(events)
        response = requests.post(endpoint, data=data)
        response.raise_for_status()
```

**Usage:**

```python
from aop import AOPClient

client = AOPClient()
events = client.query(limit=100)

exporter = CustomExporter()
exported = exporter.export(events)
print(exported)
```

### Webhook Integration

Send events to webhooks:

```python
import requests
from aop import AOPClient

client = AOPClient()

def send_to_webhook(event: dict, webhook_url: str):
    """Send event to webhook."""
    response = requests.post(
        webhook_url,
        json=event,
        headers={'Content-Type': 'application/json'}
    )
    return response.status_code == 200

# Monitor and forward events
def event_forwarder(webhook_url: str):
    """Forward new events to webhook."""
    last_id = None

    while True:
        events = client.query(limit=100)

        for event in events:
            if last_id and event['id'] <= last_id:
                continue

            send_to_webhook(event, webhook_url)
            last_id = event['id']

        time.sleep(5)
```

### Elasticsearch

Export to Elasticsearch for search and analysis:

```python
from elasticsearch import Elasticsearch
from aop import AOPClient

es = Elasticsearch(['http://localhost:9200'])
client = AOPClient()

def export_to_elasticsearch(events: List[dict], index: str = 'aop-events'):
    """Bulk export to Elasticsearch."""
    from elasticsearch.helpers import bulk

    actions = [
        {
            '_index': index,
            '_id': event['id'],
            '_source': event
        }
        for event in events
    ]

    bulk(es, actions)

# Export all events
events = client.query(limit=10000)
export_to_elasticsearch(events)
```

### Datadog

Send metrics to Datadog:

```python
from datadog import initialize, api
from aop import AOPClient, Analytics

# Initialize Datadog
initialize(api_key='YOUR_API_KEY', app_key='YOUR_APP_KEY')

client = AOPClient()
analytics = Analytics(client)

def send_metrics_to_datadog():
    """Send AOP metrics to Datadog."""
    # Get tool counts
    tool_counts = analytics.count_by_tool('my-agent')

    for tool, count in tool_counts.items():
        api.Metric.send(
            metric='aop.tool.count',
            points=count,
            tags=[f'tool:{tool}', 'agent:my-agent']
        )

    # Get percentiles
    p95 = analytics.percentile_duration('my-agent', percentile=95)

    api.Metric.send(
        metric='aop.tool.latency.p95',
        points=p95,
        tags=['agent:my-agent']
    )
```

---

## Best Practices

### 1. Choose the Right Integration

- **OpenTelemetry**: Distributed tracing across services
- **Prometheus**: Time-series metrics and alerting
- **Grafana**: Visualization and dashboards
- **Jaeger**: Trace visualization and analysis
- **Custom**: Domain-specific requirements

### 2. Avoid Double-Instrumentation

```python
# Good: Use AOP OR framework instrumentation
@client.mcp.observe_tool(agent_id='my-agent')
def my_tool():
    return process()

# Avoid: Double instrumentation
@otel_tracer.start_as_current_span("my_tool")  # OTEL
@client.mcp.observe_tool(agent_id='my-agent')  # AOP
def my_tool():
    return process()  # Both systems trace this
```

### 3. Use Sampling for High Volume

```python
# Sample 10% of events for export
import random

events = client.query(limit=10000)
sampled = [e for e in events if random.random() < 0.1]

exporter.export_to_collector(sampled)
```

### 4. Batch Exports

```python
# Export in batches of 100
batch_size = 100
for i in range(0, len(events), batch_size):
    batch = events[i:i+batch_size]
    exporter.export_to_collector(batch)
```

---

## Next Steps

- **[User Guide](user-guide.md)** - Core usage patterns
- **[API Reference](api-reference.md)** - Complete API docs
- **[Architecture](architecture.md)** - System design
- **[Troubleshooting](troubleshooting.md)** - Common issues
