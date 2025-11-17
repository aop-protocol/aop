# Protocol Guide

Complete guide to the protocols supported by AOP.

## Table of Contents

- [Overview](#overview)
- [MCP - Model Context Protocol](#mcp---model-context-protocol)
- [A2A - Agent-to-Agent Protocol](#a2a---agent-to-agent-protocol)
- [AP2 - Agent Payments Protocol](#ap2---agent-payments-protocol)
- [Multi-Protocol Workflows](#multi-protocol-workflows)

---

## Overview

AOP supports three protocols for AI agent observability:

| Protocol | Purpose | Use Cases |
|----------|---------|-----------|
| **MCP** | Model Context Protocol | Tool calls, LLM sampling, resource access |
| **A2A** | Agent-to-Agent | Multi-agent communication, task delegation |
| **AP2** | Agent Payments | Payment transactions, cost tracking |

All protocols share the same core event structure but have protocol-specific event types and data formats.

---

## MCP - Model Context Protocol

The Model Context Protocol (MCP) is used for observing interactions between agents and tools, LLMs, and resources.

### Event Types

#### Tool Events

**mcp.tool.called**
- Logged when a tool is invoked
- Contains: tool name, parameters

**mcp.tool.completed**
- Logged when a tool execution succeeds
- Contains: result, duration

**mcp.tool.error**
- Logged when a tool execution fails
- Contains: error code, error message

#### Sampling Events

**mcp.sampling.request**
- Logged when LLM sampling is requested
- Contains: model, prompt, parameters

**mcp.sampling.response**
- Logged when LLM responds
- Contains: model, response text, token usage

#### Resource Events

**mcp.resource.accessed**
- Logged when a resource is accessed
- Contains: resource URI, access type

**mcp.resource.updated**
- Logged when a resource is modified
- Contains: resource URI, changes

### Using MCPAdapter

#### Decorator Pattern (Recommended)

```python
from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(
    agent_id='my-agent',
    correlation_id='trace-123',  # Optional
    capture_result=True,         # Default: True
    capture_params=True          # Default: True
)
def search_tool(query: str, max_results: int = 10):
    """Search for information."""
    results = perform_search(query, max_results)
    return {'results': results, 'count': len(results)}

# Use the tool
result = search_tool(query='AI agents', max_results=5)
```

**What gets logged:**

Two events are created:

1. **mcp.tool.called** event:
```python
{
    'id': '01933d1e-...',
    'timestamp': '2025-01-15T10:30:00.123456Z',
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.called',
    'protocol': 'mcp',
    'correlation_id': 'trace-123',
    'data': {
        'tool_name': 'search_tool',
        'params': {
            'query': 'AI agents',
            'max_results': 5
        }
    }
}
```

2. **mcp.tool.completed** event:
```python
{
    'id': '01933d1e-...',
    'timestamp': '2025-01-15T10:30:00.175892Z',
    'agent_id': 'my-agent',
    'event_type': 'mcp.tool.completed',
    'protocol': 'mcp',
    'correlation_id': 'trace-123',
    'parent_id': '01933d1e-...',  # Links to called event
    'duration_ms': 52,
    'data': {
        'tool_name': 'search_tool',
        'result': {
            'results': ['...'],
            'count': 3
        }
    }
}
```

**Async tools:**

```python
@client.mcp.observe_tool(agent_id='my-agent')
async def async_search(query: str):
    """Async search tool."""
    results = await fetch_from_api(query)
    return results

# Works with async/await
result = await async_search('test')
```

**Error handling:**

```python
@client.mcp.observe_tool(agent_id='my-agent')
def risky_tool(value: int):
    """Tool that might fail."""
    if value == 0:
        raise ValueError("Value cannot be zero")
    return 100 / value

try:
    risky_tool(0)
except ValueError:
    pass  # Error automatically logged
```

Creates **mcp.tool.error** event:
```python
{
    'event_type': 'mcp.tool.error',
    'parent_id': '...',  # Links to called event
    'error': {
        'code': 'ValueError',
        'message': 'Value cannot be zero'
    }
}
```

#### Context Manager Pattern

```python
with client.mcp.tool_execution(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'AI', 'limit': 10},
    correlation_id='trace-123'
) as handle:
    # Your tool code
    results = perform_search('AI', limit=10)

    # Optionally set result
    handle.set_result(results)

    # Duration and errors are automatic
```

**EventHandle methods:**

```python
handle.set_result(result)           # Set successful result
handle.set_error(code, message)     # Set error
```

#### Manual Logging

**Tool call:**

```python
call_id = client.mcp.log_tool_call(
    agent_id='my-agent',
    tool_name='search',
    params={'query': 'AI', 'max_results': 10},
    correlation_id='trace-123'
)
```

**Tool result:**

```python
client.mcp.log_tool_result(
    agent_id='my-agent',
    tool_name='search',
    result={'results': [...], 'count': 5},
    parent_id=call_id,
    correlation_id='trace-123',
    duration_ms=125
)
```

**Tool error:**

```python
client.mcp.log_tool_error(
    agent_id='my-agent',
    tool_name='search',
    error_code='TIMEOUT',
    error_message='Request timed out after 30s',
    parent_id=call_id,
    correlation_id='trace-123'
)
```

### LLM Sampling

**Request:**

```python
req_id = client.mcp.log_sampling_request(
    agent_id='my-agent',
    model='gpt-4',
    prompt='Explain quantum computing in simple terms',
    sampling_params={
        'temperature': 0.7,
        'max_tokens': 500
    },
    correlation_id='trace-123'
)
```

**Response:**

```python
client.mcp.log_sampling_response(
    agent_id='my-agent',
    model='gpt-4',
    response='Quantum computing is...',
    parent_id=req_id,
    correlation_id='trace-123',
    token_usage={
        'prompt_tokens': 15,
        'completion_tokens': 120,
        'total_tokens': 135
    }
)
```

### Resource Access

```python
client.mcp.log_resource_accessed(
    agent_id='my-agent',
    resource_uri='file:///data/dataset.csv',
    access_type='read',
    correlation_id='trace-123'
)
```

---

## A2A - Agent-to-Agent Protocol

The Agent-to-Agent Protocol (A2A) is used for multi-agent systems where agents communicate and delegate tasks.

### Event Types

#### Task Events

**a2a.task.assigned**
- Agent assigns a task to another agent
- Contains: task ID, assigned_to, task data

**a2a.task.accepted**
- Agent accepts an assigned task
- Contains: task ID

**a2a.task.rejected**
- Agent rejects a task
- Contains: task ID, reason

**a2a.task.completed**
- Agent completes a task
- Contains: task ID, result

**a2a.task.failed**
- Task execution failed
- Contains: task ID, error

#### Message Events

**a2a.message.sent**
- Agent sends a message
- Contains: recipient, message content

**a2a.message.received**
- Agent receives a message
- Contains: sender, message content

### Using A2AAdapter

#### Task Assignment

```python
from aop import AOPClient

client = AOPClient()

# Orchestrator assigns task
task_id = 'task-123'
client.a2a.log_task_assigned(
    agent_id='orchestrator',
    task_id=task_id,
    assigned_to='worker-agent',
    task_data={
        'action': 'process_data',
        'input': {'file': 'data.csv'},
        'priority': 'high'
    },
    correlation_id='workflow-456'
)
```

**Event created:**

```python
{
    'event_type': 'a2a.task.assigned',
    'protocol': 'a2a',
    'agent_id': 'orchestrator',
    'correlation_id': 'workflow-456',
    'data': {
        'task_id': 'task-123',
        'assigned_to': 'worker-agent',
        'task_data': {
            'action': 'process_data',
            'input': {'file': 'data.csv'},
            'priority': 'high'
        }
    }
}
```

#### Task Acceptance

```python
# Worker accepts task
client.a2a.log_task_accepted(
    agent_id='worker-agent',
    task_id=task_id,
    correlation_id='workflow-456'
)
```

#### Task Completion

```python
# Worker completes task
client.a2a.log_task_completed(
    agent_id='worker-agent',
    task_id=task_id,
    result={
        'status': 'success',
        'output': {'processed_rows': 1000},
        'duration_seconds': 5.2
    },
    correlation_id='workflow-456'
)
```

#### Task Failure

```python
# Worker fails task
client.a2a.log_task_failed(
    agent_id='worker-agent',
    task_id=task_id,
    error_code='PROCESSING_ERROR',
    error_message='Invalid data format in row 523',
    correlation_id='workflow-456'
)
```

### Messaging

#### Send Message

```python
client.a2a.log_message_sent(
    agent_id='agent-1',
    recipient='agent-2',
    message={
        'type': 'query',
        'content': {'question': 'What is your status?'}
    },
    correlation_id='conv-789'
)
```

#### Receive Message

```python
client.a2a.log_message_received(
    agent_id='agent-2',
    sender='agent-1',
    message={
        'type': 'query',
        'content': {'question': 'What is your status?'}
    },
    correlation_id='conv-789'
)
```

### Complete Multi-Agent Workflow

```python
from aop import AOPClient
import uuid

client = AOPClient()
workflow_id = str(uuid.uuid4())

# Step 1: Orchestrator assigns task to Worker A
task_a_id = 'task-a'
client.a2a.log_task_assigned(
    agent_id='orchestrator',
    task_id=task_a_id,
    assigned_to='worker-a',
    task_data={'action': 'fetch_data'},
    correlation_id=workflow_id
)

# Step 2: Worker A accepts and processes
client.a2a.log_task_accepted(
    agent_id='worker-a',
    task_id=task_a_id,
    correlation_id=workflow_id
)

# Worker A uses MCP tool (cross-protocol!)
@client.mcp.observe_tool(agent_id='worker-a', correlation_id=workflow_id)
def fetch_data():
    return {'data': [...]}

data = fetch_data()

# Worker A completes task
client.a2a.log_task_completed(
    agent_id='worker-a',
    task_id=task_a_id,
    result=data,
    correlation_id=workflow_id
)

# Step 3: Orchestrator assigns processing to Worker B
task_b_id = 'task-b'
client.a2a.log_task_assigned(
    agent_id='orchestrator',
    task_id=task_b_id,
    assigned_to='worker-b',
    task_data={'action': 'process', 'input': data},
    correlation_id=workflow_id
)

# ... Worker B processes ...

# Now you can reconstruct the entire workflow
from aop import Analytics
analytics = Analytics(client)
trace = analytics.reconstruct_trace(correlation_id=workflow_id)

print(f"Workflow had {trace['event_count']} events")
print(f"Total duration: {trace['total_duration_ms']}ms")
```

---

## AP2 - Agent Payments Protocol

The Agent Payments Protocol (AP2) tracks payment transactions and costs in agentic systems.

### Event Types

**ap2.payment.initiated**
- Payment initiated
- Contains: payment ID, amount, currency, recipient

**ap2.payment.completed**
- Payment succeeded
- Contains: payment ID, transaction ID

**ap2.payment.failed**
- Payment failed
- Contains: payment ID, error

**ap2.cost.incurred**
- Cost tracked (API calls, resources)
- Contains: cost amount, resource type

### Using AP2Adapter

#### Payment Lifecycle

**Initiate payment:**

```python
from aop import AOPClient

client = AOPClient()

payment_id = 'pay-123'
client.ap2.log_payment_initiated(
    agent_id='my-agent',
    payment_id=payment_id,
    amount=10.50,
    currency='USD',
    recipient='api-service-provider',
    payment_data={
        'service': 'API access',
        'plan': 'premium',
        'billing_period': 'monthly'
    },
    correlation_id='workflow-789'
)
```

**Event created:**

```python
{
    'event_type': 'ap2.payment.initiated',
    'protocol': 'ap2',
    'agent_id': 'my-agent',
    'correlation_id': 'workflow-789',
    'data': {
        'payment_id': 'pay-123',
        'amount': 10.50,
        'currency': 'USD',
        'recipient': 'api-service-provider',
        'payment_data': {
            'service': 'API access',
            'plan': 'premium',
            'billing_period': 'monthly'
        }
    }
}
```

**Complete payment:**

```python
client.ap2.log_payment_completed(
    agent_id='my-agent',
    payment_id=payment_id,
    transaction_id='txn-456',
    correlation_id='workflow-789'
)
```

**Failed payment:**

```python
client.ap2.log_payment_failed(
    agent_id='my-agent',
    payment_id=payment_id,
    error_code='INSUFFICIENT_FUNDS',
    error_message='Account balance too low',
    correlation_id='workflow-789'
)
```

### Cost Tracking

Track costs for API calls, LLM usage, etc:

```python
# Track LLM API cost
client.ap2.log_cost_incurred(
    agent_id='my-agent',
    cost_amount=0.15,
    currency='USD',
    resource_type='llm_api',
    resource_id='gpt-4-call-789',
    cost_data={
        'model': 'gpt-4',
        'tokens': 1500,
        'cost_per_1k_tokens': 0.10
    },
    correlation_id='workflow-789'
)

# Track compute cost
client.ap2.log_cost_incurred(
    agent_id='my-agent',
    cost_amount=2.30,
    currency='USD',
    resource_type='compute',
    resource_id='vm-instance-123',
    cost_data={
        'instance_type': 'c5.large',
        'duration_hours': 1.5,
        'hourly_rate': 1.53
    },
    correlation_id='workflow-789'
)
```

### Analyzing Costs

```python
from aop import AOPClient, Analytics

client = AOPClient()

# Get all cost events
cost_events = client.query(event_type='ap2.cost.incurred')

# Calculate total cost
total_cost = sum(
    event['data']['cost_amount']
    for event in cost_events
    if event['data']['currency'] == 'USD'
)

print(f"Total cost: ${total_cost:.2f}")

# Cost by resource type
from collections import defaultdict
costs_by_type = defaultdict(float)

for event in cost_events:
    resource_type = event['data']['resource_type']
    amount = event['data']['cost_amount']
    costs_by_type[resource_type] += amount

for resource, cost in costs_by_type.items():
    print(f"{resource}: ${cost:.2f}")
```

---

## Multi-Protocol Workflows

Real-world agentic systems often use multiple protocols. AOP makes it easy to trace across protocols using `correlation_id`.

### Example: E-Commerce Agent Workflow

```python
from aop import AOPClient
import uuid

client = AOPClient()
order_id = str(uuid.uuid4())

# 1. A2A: Order assigned to fulfillment agent
client.a2a.log_task_assigned(
    agent_id='order-orchestrator',
    task_id=order_id,
    assigned_to='fulfillment-agent',
    task_data={'order': {'item': 'laptop', 'quantity': 1}},
    correlation_id=order_id
)

# 2. MCP: Fulfillment agent checks inventory
@client.mcp.observe_tool(agent_id='fulfillment-agent', correlation_id=order_id)
def check_inventory(item: str):
    return {'available': True, 'quantity': 5}

inventory = check_inventory('laptop')

# 3. AP2: Process payment
payment_id = f'pay-{order_id}'
client.ap2.log_payment_initiated(
    agent_id='fulfillment-agent',
    payment_id=payment_id,
    amount=999.99,
    currency='USD',
    recipient='customer',
    correlation_id=order_id
)

client.ap2.log_payment_completed(
    agent_id='fulfillment-agent',
    payment_id=payment_id,
    transaction_id='txn-abc',
    correlation_id=order_id
)

# 4. A2A: Ship order to shipping agent
client.a2a.log_task_assigned(
    agent_id='fulfillment-agent',
    task_id=f'ship-{order_id}',
    assigned_to='shipping-agent',
    task_data={'order_id': order_id},
    correlation_id=order_id
)

# 5. MCP: Shipping agent prints label
@client.mcp.observe_tool(agent_id='shipping-agent', correlation_id=order_id)
def print_shipping_label(order_id: str):
    return {'label_id': 'label-123', 'tracking': 'TRACK123'}

label = print_shipping_label(order_id)

# 6. A2A: Complete shipping task
client.a2a.log_task_completed(
    agent_id='shipping-agent',
    task_id=f'ship-{order_id}',
    result=label,
    correlation_id=order_id
)

# 7. A2A: Complete order task
client.a2a.log_task_completed(
    agent_id='fulfillment-agent',
    task_id=order_id,
    result={'status': 'shipped', 'tracking': 'TRACK123'},
    correlation_id=order_id
)

# Reconstruct the complete order workflow
from aop import Analytics
analytics = Analytics(client)
trace = analytics.reconstruct_trace(correlation_id=order_id)

print(f"Order workflow:")
print(f"  Events: {trace['event_count']}")
print(f"  Duration: {trace['total_duration_ms']}ms")
print(f"  Protocols used: MCP, A2A, AP2")
```

### Querying Multi-Protocol Events

```python
# All events for the order
all_events = client.query(correlation_id=order_id)

# Filter by protocol
mcp_events = [e for e in all_events if e['protocol'] == 'mcp']
a2a_events = [e for e in all_events if e['protocol'] == 'a2a']
ap2_events = [e for e in all_events if e['protocol'] == 'ap2']

print(f"MCP events: {len(mcp_events)}")
print(f"A2A events: {len(a2a_events)}")
print(f"AP2 events: {len(ap2_events)}")
```

---

## Protocol Comparison

| Feature | MCP | A2A | AP2 |
|---------|-----|-----|-----|
| **Primary Use** | Tool/LLM interactions | Multi-agent coordination | Payment tracking |
| **Key Events** | tool.called, sampling.request | task.assigned, message.sent | payment.initiated, cost.incurred |
| **Decorator Support** | ✅ Yes (`@observe_tool`) | ❌ No | ❌ No |
| **Context Manager** | ✅ Yes | ❌ No | ❌ No |
| **Typical Volume** | High (many tool calls) | Medium (task delegation) | Low (occasional payments) |
| **Duration Tracking** | ✅ Automatic | ⚠️ Manual | ⚠️ Manual |

---

## Best Practices

### 1. Use Correlation IDs Consistently

```python
# Good: Same correlation_id across protocols
trace_id = generate_trace_id()

client.a2a.log_task_assigned(..., correlation_id=trace_id)
client.mcp.observe_tool(..., correlation_id=trace_id)
client.ap2.log_payment_initiated(..., correlation_id=trace_id)

# Bad: Different or missing correlation_ids
client.a2a.log_task_assigned(...)  # No correlation_id
client.mcp.observe_tool(..., correlation_id='different-id')
```

### 2. Choose the Right Protocol

- **MCP**: For individual agent actions (tools, LLM calls)
- **A2A**: For agent coordination and communication
- **AP2**: For financial transactions

### 3. Include Rich Context in Data Fields

```python
# Good: Rich context
client.a2a.log_task_assigned(
    task_data={
        'action': 'process',
        'priority': 'high',
        'deadline': '2025-01-15T17:00:00Z',
        'retry_count': 0,
        'dependencies': ['task-122']
    }
)

# Avoid: Minimal context
client.a2a.log_task_assigned(
    task_data={'action': 'process'}
)
```

### 4. Link Events with Parent IDs

```python
# Log parent event
task_assigned_id = client.log_event({
    'event_type': 'a2a.task.assigned',
    'correlation_id': trace_id,
    # ...
})

# Link child event
client.log_event({
    'event_type': 'a2a.task.completed',
    'parent_id': task_assigned_id,  # Links to parent
    'correlation_id': trace_id,
    # ...
})
```

---

## Next Steps

- **[API Reference](api-reference.md)** - Complete protocol adapter APIs
- **[User Guide](user-guide.md)** - General usage patterns
- **[Examples](examples/)** - Protocol-specific examples
- **[Integrations](integrations.md)** - Connect with other tools
