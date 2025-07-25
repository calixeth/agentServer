import json
import logging
import struct

from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect

from services.voice_service import RealtimeWebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()

manager = RealtimeWebSocketManager()


@router.websocket("/api/voice/chat/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    voice: str = websocket.query_params.get("voice")
    if not voice:
        voice = "coral"
    logger.info(f"new session: {session_id} voice: {voice}")
    await manager.connect(websocket, session_id, voice)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "audio":
                # Convert int16 array to bytes
                int16_data = message["data"]
                audio_bytes = struct.pack(f"{len(int16_data)}h", *int16_data)
                await manager.send_audio(session_id, audio_bytes)

    except WebSocketDisconnect:
        await manager.disconnect(session_id)
    except Exception as e:
        logger.exception(f"Unexpected error in session {session_id}: {e}")
        await manager.disconnect(session_id)
