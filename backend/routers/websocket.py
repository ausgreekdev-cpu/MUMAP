from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..services.auth import decode_token
from ..services.websocket import manager
from ..database import get_db
from ..models.user import User

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            # For now, just keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/auth")
async def websocket_auth_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get token from query params
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        
        # Validate token
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Connect with user ID
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected",
            "user_id": user_id
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id if 'user_id' in locals() else None)
    except Exception as e:
        await websocket.close(code=4002, reason=str(e))
