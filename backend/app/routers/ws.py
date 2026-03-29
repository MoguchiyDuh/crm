from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.database import AsyncSessionLocal
from app.redis import get_redis
from app.services.auth import decode_access_token, get_user_by_id
from app.services.ws import manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    redis = await get_redis()
    try:
        user_id = await decode_access_token(token, redis)
    except Exception:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        user = await get_user_by_id(db, user_id)

    if not user or not user.is_active:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # absorb keep-alive pings
    except WebSocketDisconnect:
        manager.disconnect(websocket)
