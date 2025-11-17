"""
WebSocket handler for real-time event streaming.

Allows dashboard to receive new events as they're created.
"""

import asyncio
import json
from typing import Optional, Set
from datetime import datetime, timedelta

try:
    from fastapi import WebSocket, WebSocketDisconnect
except ImportError:
    pass

from aop import AOPClient


class EventStreamer:
    """
    Manages WebSocket connections and streams events to clients.
    """

    def __init__(self, client: AOPClient):
        self.client = client
        self.active_connections: Set[WebSocket] = set()
        self.last_event_time: Optional[datetime] = None

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)

    async def send_event(self, event: dict, websocket: WebSocket):
        """Send single event to WebSocket client."""
        try:
            await websocket.send_json(event)
        except Exception:
            # Connection closed, remove it
            self.disconnect(websocket)

    async def broadcast_event(self, event: dict):
        """Send event to all connected clients."""
        # Send to all connections concurrently
        await asyncio.gather(
            *[self.send_event(event, ws) for ws in self.active_connections],
            return_exceptions=True
        )

    async def poll_and_stream(self,
                               websocket: WebSocket,
                               agent_id: Optional[str] = None,
                               event_types: Optional[list] = None,
                               poll_interval: float = 2.0):
        """
        Poll for new events and stream to client.

        Args:
            websocket: WebSocket connection
            agent_id: Optional filter by agent ID
            event_types: Optional filter by event types
            poll_interval: How often to poll (seconds)
        """
        # Track last seen event timestamp
        last_seen = datetime.utcnow()

        while True:
            try:
                await asyncio.sleep(poll_interval)

                # Query for events since last poll
                events = self.client.query(
                    agent_id=agent_id,
                    start_time=last_seen,
                    limit=100
                )

                # Filter by event type if specified
                if event_types:
                    events = [e for e in events if e.get('event_type') in event_types]

                # Send new events
                for event in events:
                    await self.send_event(event, websocket)

                    # Update last seen timestamp
                    event_time_str = event.get('timestamp')
                    if event_time_str:
                        try:
                            event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                            if event_time > last_seen:
                                last_seen = event_time
                        except Exception:
                            pass

            except WebSocketDisconnect:
                self.disconnect(websocket)
                break
            except Exception as e:
                # Log error but keep connection alive
                print(f"Error in event stream: {e}")
                await asyncio.sleep(poll_interval)


# =============================================================================
# WEBSOCKET ENDPOINT (to be added to server.py)
# =============================================================================

"""
Add this to server.py to enable WebSocket:

from fastapi import WebSocket, WebSocketDisconnect
from .websocket import EventStreamer

# Global streamer
streamer: Optional[EventStreamer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, analytics, streamer

    client = AOPClient(storage=storage_url)
    analytics = Analytics(client)
    streamer = EventStreamer(client)

    yield

    if client:
        client.close()

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_id: Optional[str] = None
):
    '''
    WebSocket endpoint for real-time event streaming.

    Query params:
        agent_id: Optional filter by agent ID
    '''
    if not streamer:
        await websocket.close()
        return

    await streamer.connect(websocket)

    try:
        # Start streaming events
        await streamer.poll_and_stream(
            websocket,
            agent_id=agent_id,
            poll_interval=2.0
        )
    except WebSocketDisconnect:
        streamer.disconnect(websocket)
"""
