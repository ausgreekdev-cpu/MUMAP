from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
import logging

from ...services.websocket import manager
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=None),
):
    connected = await manager.connect(websocket, token)
    if not connected:
        return

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    agent_id: int,
    token: str = Query(default=None),
):
    connected = await manager.connect(websocket, token)
    if not connected:
        return

    try:
        await websocket.send_json({
            "type": "connected",
            "data": {"agent_id": agent_id},
            "message": f"Connected to agent {agent_id} updates",
        })

        while True:
            data = await websocket.receive_text()
            logger.debug(f"Agent WebSocket received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/task/{task_id}")
async def websocket_task_endpoint(
    websocket: WebSocket,
    task_id: int,
    token: str = Query(default=None),
):
    connected = await manager.connect(websocket, token)
    if not connected:
        return

    try:
        await websocket.send_json({
            "type": "connected",
            "data": {"task_id": task_id},
            "message": f"Connected to task {task_id} updates",
        })

        while True:
            data = await websocket.receive_text()
            logger.debug(f"Task WebSocket received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Task WebSocket error: {e}")
        manager.disconnect(websocket)
