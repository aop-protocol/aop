"""
A2A Protocol Adapter - Convenience methods for Agent-to-Agent events.
"""

from typing import Optional, Dict, Any

from .base import BaseAdapter, EventHandle


class A2AAdapter(BaseAdapter):
    """
    Adapter for A2A (Agent-to-Agent) protocol events.
    
    Provides convenient methods for logging common A2A events:
    - Task lifecycle (assigned/completed)
    - Agent messaging (sent/received)
    """
    
    def log_task_assigned(
        self,
        agent_id: str,
        task_id: str,
        assignee: str,
        task_type: Optional[str] = None,
        description: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log A2A task assigned event.
        
        Args:
            agent_id: Agent identifier (orchestrator)
            task_id: Unique task identifier
            assignee: Agent ID receiving the task
            task_type: Type of task
            description: Task description
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> task = client.a2a.log_task_assigned(
            ...     agent_id='orchestrator',
            ...     task_id='task-123',
            ...     assignee='worker-1',
            ...     task_type='research',
            ...     description='Research market trends'
            ... )
        """
        data: Dict[str, Any] = {
            'task_id': task_id,
            'assignee': assignee
        }
        if task_type is not None:
            data['task_type'] = task_type
        if description is not None:
            data['description'] = description
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='a2a.task.assigned',
            data=data,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_task_completed(
        self,
        agent_id: str,
        task_id: str,
        result: Any,
        duration_ms: Optional[int] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log A2A task completed event.
        
        Args:
            agent_id: Agent identifier
            task_id: Unique task identifier
            result: Task result
            duration_ms: Task duration in milliseconds
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from task_assigned)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> completion = client.a2a.log_task_completed(
            ...     agent_id='worker-1',
            ...     task_id='task-123',
            ...     result={'status': 'success', 'data': {...}},
            ...     duration_ms=5000,
            ...     parent_id=task.id
            ... )
        """
        data: Dict[str, Any] = {
            'task_id': task_id,
            'result': result
        }
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='a2a.task.completed',
            data=data,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_message_sent(
        self,
        agent_id: str,
        recipient: str,
        content: Any,
        message_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log A2A message sent event.
        
        Args:
            agent_id: Agent identifier (sender)
            recipient: Recipient agent ID
            content: Message content
            message_type: Type of message
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> msg = client.a2a.log_message_sent(
            ...     agent_id='agent-1',
            ...     recipient='agent-2',
            ...     content={'action': 'start', 'params': {...}},
            ...     message_type='command'
            ... )
        """
        data: Dict[str, Any] = {
            'recipient': recipient,
            'content': content
        }
        if message_type is not None:
            data['message_type'] = message_type
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='a2a.message.sent',
            data=data,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_message_received(
        self,
        agent_id: str,
        sender: str,
        content: Any,
        message_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log A2A message received event.
        
        Args:
            agent_id: Agent identifier (receiver)
            sender: Sender agent ID
            content: Message content
            message_type: Type of message
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from message_sent)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> received = client.a2a.log_message_received(
            ...     agent_id='agent-2',
            ...     sender='agent-1',
            ...     content={'action': 'start', 'params': {...}},
            ...     message_type='command',
            ...     parent_id=msg.id
            ... )
        """
        data: Dict[str, Any] = {
            'sender': sender,
            'content': content
        }
        if message_type is not None:
            data['message_type'] = message_type
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='a2a.message.received',
            data=data,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)