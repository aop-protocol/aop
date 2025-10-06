"""
AP2 Protocol Adapter - Convenience methods for Agent Payment events.
"""

from typing import Optional, Dict, Any

from .base import BaseAdapter, EventHandle


class AP2Adapter(BaseAdapter):
    """
    Adapter for AP2 (Agent Payments Protocol) events.
    
    Provides convenient methods for logging payment flow events:
    - Payment lifecycle (initiated/completed/failed)
    """
    
    def log_payment_initiated(
        self,
        agent_id: str,
        payment_id: str,
        amount: float,
        currency: str,
        payment_method: Optional[str] = None,
        merchant_id: Optional[str] = None,
        mandate_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log AP2 payment initiated event.
        
        Args:
            agent_id: Agent identifier
            payment_id: Unique payment identifier
            amount: Payment amount
            currency: Currency code (ISO 4217)
            payment_method: Payment method type (e.g., 'CARD', 'BANK_TRANSFER')
            merchant_id: Merchant identifier
            mandate_id: Payment mandate ID
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> payment = client.ap2.log_payment_initiated(
            ...     agent_id='payment-agent',
            ...     payment_id='pay-123',
            ...     amount=99.99,
            ...     currency='USD',
            ...     payment_method='CARD'
            ... )
        """
        data: Dict[str, Any] = {
            'payment_id': payment_id,
            'amount': amount,
            'currency': currency
        }
        if payment_method is not None:
            data['payment_method'] = payment_method
        if merchant_id is not None:
            data['merchant_id'] = merchant_id
        if mandate_id is not None:
            data['mandate_id'] = mandate_id
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='ap2.payment.initiated',
            data=data,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_payment_completed(
        self,
        agent_id: str,
        payment_id: str,
        transaction_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        duration_ms: Optional[int] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log AP2 payment completed event.
        
        Args:
            agent_id: Agent identifier
            payment_id: Unique payment identifier
            transaction_id: Processor transaction ID
            amount: Final processed amount
            currency: Currency code
            duration_ms: Payment processing duration in milliseconds
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from payment_initiated)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> completion = client.ap2.log_payment_completed(
            ...     agent_id='payment-agent',
            ...     payment_id='pay-123',
            ...     transaction_id='txn-456',
            ...     amount=99.99,
            ...     currency='USD',
            ...     duration_ms=2000,
            ...     parent_id=payment.id
            ... )
        """
        data: Dict[str, Any] = {'payment_id': payment_id}
        if transaction_id is not None:
            data['transaction_id'] = transaction_id
        if amount is not None:
            data['amount'] = amount
        if currency is not None:
            data['currency'] = currency
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='ap2.payment.completed',
            data=data,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)
    
    def log_payment_failed(
        self,
        agent_id: str,
        payment_id: str,
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventHandle:
        """
        Log AP2 payment failed event.
        
        Args:
            agent_id: Agent identifier
            payment_id: Unique payment identifier
            error_code: Payment error code
            error_message: Error message
            details: Additional error details
            correlation_id: Correlation ID (uses trace context if None)
            parent_id: Parent event ID (from payment_initiated)
            metadata: Event metadata
            
        Returns:
            EventHandle for the logged event
            
        Example:
            >>> failure = client.ap2.log_payment_failed(
            ...     agent_id='payment-agent',
            ...     payment_id='pay-123',
            ...     error_code='INSUFFICIENT_FUNDS',
            ...     error_message='Payment declined',
            ...     parent_id=payment.id
            ... )
        """
        error_info: Dict[str, Any] = {
            'code': error_code,
            'message': error_message
        }
        if details:
            error_info['details'] = details
        
        data: Dict[str, Any] = {'payment_id': payment_id}
        
        event = self._build_event(
            agent_id=agent_id,
            event_type='ap2.payment.failed',
            data=data,
            error=error_info,
            severity='error',
            correlation_id=correlation_id,
            parent_id=parent_id,
            metadata=metadata
        )
        
        return self._log_and_return_handle(event)