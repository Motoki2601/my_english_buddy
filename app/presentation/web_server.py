import asyncio
import base64
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.application.conversation_service import ConversationService
from app.application.errors import ExternalServiceError
from app.infrastructure.web.speech_to_text import WebSpeechToText
from app.infrastructure.web.text_to_speech import WebTextToSpeech
from app.utils.logger import Logger

_STATIC_DIR = Path(__file__).parent / "static"
_executor = ThreadPoolExecutor(max_workers=4)


def create_app(
    *,
    conversation_service: ConversationService,
    stt: WebSpeechToText,
    tts: WebTextToSpeech,
    logger: Logger,
) -> FastAPI:
    app = FastAPI(title="My English Buddy")

    @app.get("/")
    async def index() -> HTMLResponse:
        return HTMLResponse((_STATIC_DIR / "index.html").read_text(encoding="utf-8"))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        logger.log("Web client connected.")
        loop = asyncio.get_running_loop()

        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)

                if msg.get("type") != "audio":
                    continue

                audio_bytes = base64.b64decode(msg["data"])
                mime_type = msg.get("mime_type", "audio/webm")

                await websocket.send_json({"type": "status", "message": "transcribing"})
                try:
                    user_text = await loop.run_in_executor(
                        _executor, stt.transcribe_bytes, audio_bytes, mime_type
                    )
                except ExternalServiceError as e:
                    logger.log(f"STT error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})
                    continue

                if not user_text:
                    await websocket.send_json({"type": "status", "message": "no_speech"})
                    continue

                logger.log(f"You: {user_text}")
                await websocket.send_json({"type": "transcript", "text": user_text})
                await websocket.send_json({"type": "status", "message": "thinking"})

                try:
                    reply = await loop.run_in_executor(
                        _executor, conversation_service.reply, user_text
                    )
                except ExternalServiceError as e:
                    logger.log(f"Chat error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})
                    continue

                if not reply:
                    continue

                logger.log(f"Buddy: {reply}")
                await websocket.send_json({"type": "status", "message": "synthesizing"})

                try:
                    audio_response = await loop.run_in_executor(
                        _executor, tts.synthesize_to_bytes, reply
                    )
                except ExternalServiceError as e:
                    logger.log(f"TTS error: {e}")
                    await websocket.send_json({"type": "reply", "text": reply})
                    await websocket.send_json({"type": "status", "message": "ready"})
                    continue

                audio_b64 = base64.b64encode(audio_response).decode()
                await websocket.send_json({"type": "reply", "text": reply, "audio": audio_b64})
                await websocket.send_json({"type": "status", "message": "ready"})

        except WebSocketDisconnect:
            logger.log("Web client disconnected.")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.log(f"WebSocket protocol error: {e}")

    return app
