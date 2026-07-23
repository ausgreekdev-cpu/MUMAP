import json
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging
from jose import JWTError, jwt

from ..config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.all_connections: Set[WebSocket] = set()
        self._authenticated: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> bool:
        if settings.ENVIRONMENT == "production" and not token:
            await websocket.close(code=4001, reason="Authentication required")
            return False

        if token:
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user_id = payload.get("sub")
                if user_id is None:
                    await websocket.close(code=4001, reason="Invalid token")
                    return False
                user_id = int(user_id)
            except JWTError:
                await websocket.close(code=4001, reason="Invalid token")
                return False
        else:
            user_id = None

        await websocket.accept()
        self.all_connections.add(websocket)
        self._authenticated.add(websocket)

        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)

        logger.info(f"WebSocket connected (user_id={user_id})")
        return True

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        self.all_connections.discard(websocket)
        self._authenticated.discard(websocket)

        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"WebSocket disconnected (user_id={user_id})")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.active_connections[user_id].discard(conn)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self._authenticated:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.all_connections.discard(conn)
            self._authenticated.discard(conn)

    async def notify_agent_update(self, agent_data: dict):
        await self.broadcast({
            "type": "agent_update",
            "data": agent_data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_task_update(self, task_data: dict):
        await self.broadcast({
            "type": "task_update",
            "data": task_data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def notify_log(self, log_data: dict):
        await self.broadcast({
            "type": "log",
            "data": log_data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    @property
    def connection_count(self) -> int:
        return len(self._authenticated)

    def get_user_connections(self, user_id: int) -> int:
        return len(self.active_connections.get(user_id, set()))


manager = ConnectionManager()
