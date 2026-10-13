"""
CarbonKheti Real-time Event Backbone & SSE Broadcaster.
Implements Section 3 & Section 7:
- Server-Sent Events (SSE) stream at /v1/stream
- Real-time distribution across the link matrix
- Transactional outbox logging
"""

import asyncio
import json
import time
from typing import Dict, Set, AsyncGenerator, Any

class EventBroadcaster:
    def __init__(self):
        # Set of active asyncio Queues for connected SSE clients
        self._subscribers: Set[asyncio.Queue] = set()
        self._history: list = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    async def publish(self, event_type: str, payload: Dict[str, Any], aggregate_type: str = "SYSTEM", aggregate_id: str = "GLOBAL", is_sandbox: bool = True):
        event_data = {
            "id": f"evt_{int(time.time() * 1000)}",
            "type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "payload": payload,
            "is_sandbox": is_sandbox,
            "timestamp": time.time()
        }
        self._history.append(event_data)
        if len(self._history) > 200:
            self._history.pop(0)

        # Broadcast to all live SSE queues
        dead_queues = set()
        for q in self._subscribers:
            try:
                q.put_nowait(event_data)
            except Exception:
                dead_queues.add(q)
        for q in dead_queues:
            self.unsubscribe(q)

    def get_recent_events(self, limit: int = 50):
        return self._history[-limit:]

# Global singleton broadcaster
broadcaster = EventBroadcaster()
