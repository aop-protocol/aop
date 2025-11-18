"""
Analytics and query engine for AOP events.

Provides advanced querying capabilities:
- Trace reconstruction (parent-child trees)
- Aggregations (count, average, percentiles)
- Time-series analysis
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class Analytics:
    """
    Analytics engine for AOP events.

    Provides methods for analyzing and aggregating events beyond basic filtering.
    """

    def __init__(self, client):
        """
        Initialize analytics with an AOPClient.

        Args:
            client: AOPClient instance to query events from
        """
        self.client = client

    def reconstruct_trace(
        self,
        correlation_id: Optional[str] = None,
        root_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reconstruct a complete trace as a tree structure.

        Args:
            correlation_id: Correlation ID to reconstruct trace for
            root_event_id: Alternative: root event ID to start from

        Returns:
            Dictionary with trace tree structure:
            {
                'root_event': {...},
                'children': [
                    {
                        'event': {...},
                        'children': [...]
                    }
                ],
                'total_duration_ms': 150,
                'event_count': 5,
                'error_count': 1
            }

        Example:
            >>> analytics = Analytics(client)
            >>> trace = analytics.reconstruct_trace(correlation_id='trace-123')
            >>> print(f"Total events: {trace['event_count']}")
            >>> print(f"Total duration: {trace['total_duration_ms']}ms")
        """
        # Get all events for this trace
        if correlation_id:
            events = self.client.query(correlation_id=correlation_id)
        elif root_event_id:
            # Get root event and all descendants
            root = self.client.get_event(root_event_id)
            if not root:
                return {
                    'root_event': None,
                    'children': [],
                    'total_duration_ms': 0,
                    'event_count': 0,
                    'error_count': 0
                }
            # Find all events that reference this root
            events = self._find_descendants(root_event_id)
            events.insert(0, root)
        else:
            raise ValueError("Must provide either correlation_id or root_event_id")

        if not events:
            return {
                'root_event': None,
                'children': [],
                'total_duration_ms': 0,
                'event_count': 0,
                'error_count': 0
            }

        # Build parent-child map
        events_by_id = {e['id']: e for e in events}
        children_map = defaultdict(list)

        for event in events:
            parent_id = event.get('parent_id')
            if parent_id:
                children_map[parent_id].append(event)

        # Find root event (no parent or parent not in trace)
        root_event = None
        for event in events:
            parent_id = event.get('parent_id')
            if not parent_id or parent_id not in events_by_id:
                root_event = event
                break

        if not root_event:
            # If no clear root, use first event
            root_event = events[0]

        # Build tree recursively
        def build_tree(event: Dict[str, Any]) -> Dict[str, Any]:
            children = []
            for child_event in children_map.get(event['id'], []):
                children.append(build_tree(child_event))

            return {
                'event': event,
                'children': children
            }

        tree = build_tree(root_event)

        # Calculate statistics
        total_duration = sum(e.get('duration_ms', 0) for e in events if e.get('duration_ms'))
        error_count = sum(1 for e in events if e['event_type'].endswith('.error'))

        return {
            'root_event': root_event,
            'children': tree['children'],
            'total_duration_ms': total_duration,
            'event_count': len(events),
            'error_count': error_count
        }
    
    def reconstruct_trace_from_event(self, event_id: str) -> Dict[str, Any]:
        """
        Reconstruct trace starting from any event ID.
        
        Walks up parent chain to find root, then reconstructs full trace.
        
        Args:
            event_id: Any event ID in the trace
            
        Returns:
            Same structure as reconstruct_trace()
        """
        # Get the starting event
        event = self.client.get_event(event_id)
        if not event:
            return {
                'root_event': None,
                'children': [],
                'total_duration_ms': 0,
                'event_count': 0,
                'error_count': 0
            }
        
        # If event has correlation_id, use the normal trace reconstruction
        if event.get('correlation_id'):
            return self.reconstruct_trace(correlation_id=event['correlation_id'])
        
        # Walk up parent chain to find root
        root_event = self._find_root_event(event)
        
        # Collect all events in this trace (root + all descendants)
        all_events = [root_event]
        all_events.extend(self._collect_all_descendants_recursive(root_event['id']))
        
        # Build tree structure
        return self._build_trace_tree_from_events(all_events, root_event)
    
    def _find_root_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Walk up parent chain to find root event."""
        current = event
        visited = {event['id']}  # Prevent infinite loops
        max_depth = 100  # Safety limit
        depth = 0
        
        while current.get('parent_id') and depth < max_depth:
            parent_id = current['parent_id']
            
            # Avoid infinite loops
            if parent_id in visited:
                break
            
            # Try to get parent
            parent = self.client.get_event(parent_id)
            if not parent:
                # Parent not found, current is root
                break
            
            visited.add(parent_id)
            current = parent
            depth += 1
        
        return current
    
    def _collect_all_descendants_recursive(self, parent_id: str) -> List[Dict[str, Any]]:
        """Recursively collect all descendant events."""
        descendants = []
        
        # Query all events - we'll filter by parent_id
        all_events = self.client.query(limit=10000)
        
        # Build parent->children map
        children_by_parent = defaultdict(list)
        for event in all_events:
            if event.get('parent_id'):
                children_by_parent[event['parent_id']].append(event)
        
        # Recursive collection
        def collect_children(pid: str):
            for child in children_by_parent.get(pid, []):
                if child not in descendants:
                    descendants.append(child)
                    collect_children(child['id'])
        
        collect_children(parent_id)
        return descendants
    
    def _build_trace_tree_from_events(
        self, 
        events: List[Dict[str, Any]], 
        root_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build trace tree structure from list of events."""
        
        # Build lookup maps
        events_by_id = {e['id']: e for e in events}
        children_map = defaultdict(list)
        
        for event in events:
            parent_id = event.get('parent_id')
            if parent_id and parent_id in events_by_id:
                children_map[parent_id].append(event)
        
        # Recursive tree builder
        def build_tree(event: Dict[str, Any]) -> Dict[str, Any]:
            children = []
            for child_event in children_map.get(event['id'], []):
                children.append(build_tree(child_event))
            return {
                'event': event,
                'children': children
            }
        
        tree = build_tree(root_event)
        
        # Calculate statistics
        total_duration = sum(e.get('duration_ms', 0) for e in events if e.get('duration_ms'))
        error_count = sum(1 for e in events if '.error' in e.get('event_type', ''))
        
        return {
            'root_event': root_event,
            'children': tree['children'],
            'total_duration_ms': total_duration,
            'event_count': len(events),
            'error_count': error_count
        }

    def _find_descendants(self, parent_id: str) -> List[Dict[str, Any]]:
        """Find all events that are descendants of the given parent."""
        # Query all events that have this as parent
        # This is a simplified version - in production you'd want recursive search
        all_events = self.client.query()
        descendants = []

        def find_children(pid: str):
            for event in all_events:
                if event.get('parent_id') == pid and event not in descendants:
                    descendants.append(event)
                    find_children(event['id'])

        find_children(parent_id)
        return descendants

    def count_by_tool(self, agent_id: str) -> Dict[str, int]:
        """
        Count events grouped by tool name.

        Args:
            agent_id: Agent to analyze

        Returns:
            Dictionary mapping tool names to event counts

        Example:
            >>> counts = analytics.count_by_tool('mcp-memory')
            >>> # {'recall_memory': 150, 'store_memory': 45}
        """
        events = self.client.query(agent_id=agent_id, event_type='mcp.tool.called')
        counts: Dict[str, int] = defaultdict(int)

        for event in events:
            tool_name = event.get('data', {}).get('tool_name')
            if tool_name:
                counts[tool_name] += 1

        return dict(counts)

    def count_by_event_type(self, agent_id: str) -> Dict[str, int]:
        """
        Count events grouped by event type.

        Args:
            agent_id: Agent to analyze

        Returns:
            Dictionary mapping event types to counts
        """
        events = self.client.query(agent_id=agent_id)
        counts: Dict[str, int] = defaultdict(int)

        for event in events:
            counts[event['event_type']] += 1

        return dict(counts)

    def avg_duration_by_tool(self, agent_id: str) -> Dict[str, float]:
        """
        Calculate average duration grouped by tool name.

        Args:
            agent_id: Agent to analyze

        Returns:
            Dictionary mapping tool names to average duration in ms

        Example:
            >>> avgs = analytics.avg_duration_by_tool('mcp-memory')
            >>> # {'recall_memory': 18.5, 'store_memory': 125.3}
        """
        events = self.client.query(agent_id=agent_id, event_type='mcp.tool.completed')
        durations: Dict[str, List[int]] = defaultdict(list)

        for event in events:
            tool_name = event.get('data', {}).get('tool_name')
            duration = event.get('duration_ms')
            if tool_name and duration is not None:
                durations[tool_name].append(duration)

        return {
            tool: statistics.mean(vals) if vals else 0.0
            for tool, vals in durations.items()
        }

    def percentile_duration(
        self,
        agent_id: str,
        tool_name: Optional[str] = None,
        percentile: int = 95
    ) -> float:
        """
        Calculate percentile duration for tool executions.

        Args:
            agent_id: Agent to analyze
            tool_name: Specific tool (None for all tools)
            percentile: Percentile to calculate (50, 95, 99, etc.)

        Returns:
            Duration at specified percentile in milliseconds

        Example:
            >>> p95 = analytics.percentile_duration('mcp-memory', 'recall_memory', 95)
            >>> # 45.2 (95% of calls finish under 45.2ms)
        """
        events = self.client.query(agent_id=agent_id, event_type='mcp.tool.completed')
        durations = []

        for event in events:
            if tool_name:
                event_tool = event.get('data', {}).get('tool_name')
                if event_tool != tool_name:
                    continue

            duration = event.get('duration_ms')
            if duration is not None:
                durations.append(duration)

        if not durations:
            return 0.0

        # Calculate percentile using quantiles
        durations.sort()
        index = int((percentile / 100.0) * len(durations))
        index = min(index, len(durations) - 1)
        return float(durations[index])

    def events_over_time(
        self,
        agent_id: str,
        bucket_size: str = '1h',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Group events by time buckets.

        Args:
            agent_id: Agent to analyze
            bucket_size: Time bucket size ('1h', '1d', '1w')
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of dicts with time bucket and event count:
            [
                {'time': '2025-11-01T08:00:00Z', 'count': 23},
                {'time': '2025-11-01T09:00:00Z', 'count': 45},
                ...
            ]

        Example:
            >>> timeline = analytics.events_over_time('mcp-memory', bucket_size='1h')
        """
        # Parse bucket size
        bucket_delta = self._parse_bucket_size(bucket_size)

        # Query events
        events = self.client.query(
            agent_id=agent_id,
            start_time=start_time,
            end_time=end_time
        )

        if not events:
            return []

        # Group by time buckets
        buckets: Dict[str, int] = defaultdict(int)

        for event in events:
            timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            # Round down to bucket
            bucket_time = self._round_to_bucket(timestamp, bucket_delta)
            bucket_key = bucket_time.isoformat().replace('+00:00', 'Z')
            buckets[bucket_key] += 1

        # Convert to sorted list
        result = [
            {'time': time_str, 'count': count}
            for time_str, count in sorted(buckets.items())
        ]

        return result

    def event_rate(
        self,
        agent_id: str,
        window_minutes: int = 60
    ) -> float:
        """
        Calculate event rate (events per minute) over time window.

        Args:
            agent_id: Agent to analyze
            window_minutes: Time window in minutes

        Returns:
            Events per minute

        Example:
            >>> rate = analytics.event_rate('mcp-memory', window_minutes=60)
            >>> # 12.5 events/minute
        """
        from datetime import timezone
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=window_minutes)

        events = self.client.query(
            agent_id=agent_id,
            start_time=start_time,
            end_time=end_time
        )

        if not events:
            return 0.0

        return len(events) / window_minutes

    def _parse_bucket_size(self, bucket_size: str) -> timedelta:
        """Parse bucket size string to timedelta."""
        if bucket_size == '1h':
            return timedelta(hours=1)
        elif bucket_size == '1d':
            return timedelta(days=1)
        elif bucket_size == '1w':
            return timedelta(weeks=1)
        else:
            raise ValueError(f"Unsupported bucket size: {bucket_size}")

    def _round_to_bucket(self, dt: datetime, delta: timedelta) -> datetime:
        """Round datetime down to nearest bucket."""
        timestamp = dt.timestamp()
        bucket_seconds = delta.total_seconds()
        rounded = (timestamp // bucket_seconds) * bucket_seconds
        return datetime.fromtimestamp(rounded, tz=dt.tzinfo)
