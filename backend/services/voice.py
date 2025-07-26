import asyncio
import base64
import json
import logging
from typing import Any, assert_never

from agents import function_tool
from agents.realtime import RealtimeSession, RealtimeRunner, RealtimeSessionEvent, RealtimeAgent, RealtimeRunConfig, \
    RealtimeSessionModelSettings, RealtimeModelConfig
from fastapi import WebSocket

from config import SETTINGS

logger = logging.getLogger(__name__)


@function_tool
def action_transmission(action: str) -> str:
    """
    What action(expressions or movements) will you show?.

    class action(StrEnum):
        happy
        hello
        like
        sad
        angry
        hate
    """
    logger.info(f"action transmission: {action}")
    return action


PROMPT_WITH_TOOL = """\
You are an advanced virtual AI companion who can make expressions and movements, so you MUST to use the action_transmission tool before responding to any query.

Key elements included:
1. Mandatory use action_transmission tool
2. Replies should be natural and expressions should be colloquial
"""

PROMPT = f"""\
You are an advanced virtual AI companion.

Key elements included:
- Replies should be natural and expressions should be colloquial
{SETTINGS.PROMPT_KEY_ELEMENTS_APPEND}
"""

agent = RealtimeAgent(
    name="Assistant",
    instructions=PROMPT,
    # tools=[action_transmission],
)


class RealtimeWebSocketManager:

    def __init__(self):
        self.active_sessions: dict[str, RealtimeSession] = {}
        self.session_contexts: dict[str, Any] = {}
        self.websockets: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str, voice: str):
        await websocket.accept()
        self.websockets[session_id] = websocket

        runner = RealtimeRunner(
            starting_agent=agent,
            config=RealtimeRunConfig(model_settings=RealtimeSessionModelSettings(voice=voice)),
        )
        session_context = await runner.run(
            model_config=RealtimeModelConfig(
                initial_model_settings=RealtimeSessionModelSettings(
                    voice=voice,
                )
            )
        )
        session = await session_context.__aenter__()
        self.active_sessions[session_id] = session
        self.session_contexts[session_id] = session_context

        # Start event processing task
        asyncio.create_task(self._process_events(session_id))

    async def disconnect(self, session_id: str):
        logger.info(f"disconnect session: {session_id}")
        if session_id in self.session_contexts:
            await self.session_contexts[session_id].__aexit__(None, None, None)
            del self.session_contexts[session_id]
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.websockets:
            del self.websockets[session_id]

    async def send_audio(self, session_id: str, audio_bytes: bytes):
        logger.info(f"send audio session: {session_id}")
        if session_id in self.active_sessions:
            await self.active_sessions[session_id].send_audio(audio_bytes)

    async def _process_events(self, session_id: str):
        try:
            session = self.active_sessions[session_id]
            websocket = self.websockets[session_id]

            async for event in session:
                event_data = await self._serialize_event(event)
                event_data_json = json.dumps(event_data, ensure_ascii=False)
                logger.info(f"event_data_json: {event_data_json}")
                await websocket.send_text(event_data_json)
        except Exception as e:
            logger.error(f"Error processing events for session {session_id}: {e}")

    async def _serialize_event(self, event: RealtimeSessionEvent) -> dict[str, Any]:
        base_event: dict[str, Any] = {
            "type": event.type,
        }

        if event.type == "agent_start":
            base_event["agent"] = event.agent.name
        elif event.type == "agent_end":
            base_event["agent"] = event.agent.name
        elif event.type == "handoff":
            base_event["from"] = event.from_agent.name
            base_event["to"] = event.to_agent.name
        elif event.type == "tool_start":
            base_event["tool"] = event.tool.name
        elif event.type == "tool_end":
            base_event["tool"] = event.tool.name
            base_event["output"] = str(event.output)
        elif event.type == "audio":
            base_event["audio"] = base64.b64encode(event.audio.data).decode("utf-8")
        elif event.type == "audio_interrupted":
            pass
        elif event.type == "audio_end":
            pass
        elif event.type == "history_updated":
            base_event["history"] = [item.model_dump(mode="json") for item in event.history]
        elif event.type == "history_added":
            pass
        elif event.type == "guardrail_tripped":
            base_event["guardrail_results"] = [
                {"name": result.guardrail.name} for result in event.guardrail_results
            ]
        elif event.type == "raw_model_event":
            base_event["raw_model_event"] = {
                "type": event.data.type,
            }
        elif event.type == "error":
            base_event["error"] = str(event.error) if hasattr(event, "error") else "Unknown error"
        else:
            assert_never(event)

        return base_event
