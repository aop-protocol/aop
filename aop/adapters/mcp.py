"""
MCP Protocol Adapter - Convenience methods for MCP events.
"""

from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager

from .base import BaseAdapter, EventHandle


class MCPAdapter(BaseAdapter):
    """
    Adapter for MCP (Model Context Protocol) events.
    
    Provides convenient methods for logging common MCP events:
    - Tool execution (call/result)
    - LLM sampling (request/response)
    - Error handling
    """
    
    def log_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log MCP tool call event.
        
        Args:
            agent_id: Agent identifier
            tool_name: Name of the tool being called
            params: Tool parameters
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> call = client.mcp.log_tool_call(
            ...     agent_id='agent-1',
            ...     tool_name='web_search',
            ...     params={'query': 'AOP protocol'}
            ... )
        """
        data: Dict[str, Any] = {'tool_name': tool_name}
        if params is not None:
            data['params'] = params
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='mcp.tool.called',
            data=data,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_tool_result(
        self,
        agent_id: str,
        tool_name: str,
        result: Any,
        duration_ms: Optional[int] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log MCP tool result event.
        
        Args:
            agent_id: Agent identifier
            tool_name: Name of the tool that was called
            result: Tool execution result
            duration_ms: Execution duration in milliseconds
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from tool_call)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> result = client.mcp.log_tool_result(
            ...     agent_id='agent-1',
            ...     tool_name='web_search',
            ...     result={'count': 10, 'items': [...]},
            ...     duration_ms=150,
            ...     parent_id=call.id
            ... )
        """
        data: Dict[str, Any] = {
            'tool_name': tool_name,
            'result': result
        }
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='mcp.tool.completed',
            data=data,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_sampling_request(
        self,
        agent_id: str,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log MCP sampling request event (LLM call).
        
        Args:
            agent_id: Agent identifier
            prompt: LLM prompt text
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
        """
        data: Dict[str, Any] = {'prompt': prompt}
        if model is not None:
            data['model'] = model
        if max_tokens is not None:
            data['max_tokens'] = max_tokens
        if temperature is not None:
            data['temperature'] = temperature
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='mcp.sampling.requested',
            data=data,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_sampling_response(
        self,
        agent_id: str,
        completion: str,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        duration_ms: Optional[int] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log MCP sampling response event (LLM response).
        
        Args:
            agent_id: Agent identifier
            completion: LLM completion text
            model: Model name
            tokens_used: Number of tokens used
            duration_ms: Response time in milliseconds
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from sampling_request)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
        """
        data: Dict[str, Any] = {'completion': completion}
        if model is not None:
            data['model'] = model
        if tokens_used is not None:
            data['tokens_used'] = tokens_used
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='mcp.sampling.completed',
            data=data,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_tool_error(
        self,
        agent_id: str,
        tool_name: str,
        error_message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log MCP tool error event.
        
        Args:
            agent_id: Agent identifier
            tool_name: Name of the tool that failed
            error_message: Error message
            error_code: Error code
            details: Additional error details
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from tool_call)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> client.mcp.log_tool_error(
            ...     agent_id='agent-1',
            ...     tool_name='web_search',
            ...     error_message='Connection timeout',
            ...     error_code='TIMEOUT',
            ...     parent_id=call.id
            ... )
        """
        error_info: Dict[str, Any] = {
            'code': error_code or 'TOOL_ERROR',
            'message': error_message
        }
        if details:
            error_info['details'] = details
        
        data: Dict[str, Any] = {'tool_name': tool_name}
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='mcp.tool.error',
            data=data,
            error=error_info,
            severity='error',
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    @contextmanager
    def tool_execution(
        self,
        agent_id: str,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Generator[EventHandle, None, None]:
        """
        Context manager for tool execution with automatic result/error logging.
        
        Args:
            agent_id: Agent identifier
            tool_name: Tool name
            params: Tool parameters
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID
            
        Yields:
            EventHandle for the tool call
            
        Example:
            >>> with client.mcp.tool_execution('agent-1', 'web_search', {'query': 'test'}) as call:
            ...     result = perform_search()
            ...     call.set_result(result, duration_ms=150)
        """
        # Log tool call
        call_handle = self.log_tool_call(
            agent_id=agent_id,
            tool_name=tool_name,
            params=params,
            correlation_id=correlation_id,
            parent_id=parent_id
        ) 
        
        # Add helper method to set result
        def set_result(result: Any, duration_ms: Optional[int] = None) -> EventHandle:
            return self.log_tool_result(
                agent_id=agent_id,
                tool_name=tool_name,
                result=result,
                duration_ms=duration_ms,
                correlation_id=self._get_correlation_id(correlation_id),
                parent_id=call_handle.id
            )
        
        # Attach helper to handle
        call_handle.set_result = set_result  # type: ignore
        
        try:
            yield call_handle
        except Exception as e:
            # Auto-log error
            self.log_tool_error(
                agent_id=agent_id,
                tool_name=tool_name,
                error_message=str(e),
                error_code=type(e).__name__,
                correlation_id=self._get_correlation_id(correlation_id),
                parent_id=call_handle.id
            )
            raise