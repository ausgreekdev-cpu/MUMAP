import json
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, user_id: int = None):
        await websocket.accept()
        self.all_connections.add(websocket)
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int = None):
        self.all_connections.discard(websocket)
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.all_connections.discard(conn)
    
    async def notify_agent_update(self, agent_data: dict):
        await self.broadcast({
            "type": "agent_update",
            "data": agent_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_task_update(self, task_data: dict):
        await self.broadcast({
            "type": "task_update",
            "data": task_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_log(self, log_data: dict):
        await self.broadcast({
            "type": "log",
            "data": log_data,
            "timestamp": datetime.utcnow().isoformat()
        })


manager = ConnectionManager()
