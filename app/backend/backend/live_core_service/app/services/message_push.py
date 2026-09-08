"""Message WebSocket real-time push"""

import json
import logging
from typing import Any, Dict, Set
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MessagePushManager:
    """Manage WebSocket connections per room and broadcast new messages"""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        key = str(room_id)
        if key not in self._connections:
            self._connections[key] = set()
        self._connections[key].add(websocket)
        logger.info("WebSocket connected: room=%s, total=%d", key, len(self._connections[key]))

    def disconnect(self, room_id: UUID, websocket: WebSocket) -> None:
        key = str(room_id)
        conns = self._connections.get(key)
        if conns and websocket in conns:
            conns.discard(websocket)
            if not conns:
                del self._connections[key]

    async def broadcast_new_message(self, room_id: UUID, message_data: Dict[str, Any]) -> None:
        key = str(room_id)
        conns = self._connections.get(key)
        if not conns:
            return
        payload = json.dumps(
            {"type": "new_message", "data": message_data},
            default=str,
        )
        dead: Set[WebSocket] = set()
        for ws in list(conns):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning("WebSocket send failed: %s", e)
                dead.add(ws)
        for ws in dead:
            self.disconnect(room_id, ws)


message_push_manager = MessagePushManager()
