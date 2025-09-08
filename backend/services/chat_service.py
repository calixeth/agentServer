import json
from datetime import datetime

from clients.llm_client import proxy_client
from infra.db import messages_col


async def save_message(conversation_id: str, role: str, content: str):
    doc = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "ts": datetime.utcnow()
    }
    await messages_col.insert_one(doc)


async def build_history(conversation_id: str, user_message: str):
    cursor = messages_col.find(
        {"conversation_id": conversation_id}
    ).sort("ts", -1).limit(10)

    history = await cursor.to_list(length=10)
    history = history[::-1]

    messages = [{"role": "system", "content": "You are a helpful assistant"}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    return messages


async def event_generator(conversation_id: str, user_message: str):
    await save_message(conversation_id, "user", user_message)

    messages = await build_history(conversation_id, user_message)

    stream = await proxy_client.chat.completions.create(
        model="grok-3",
        messages=messages,
        stream=True,
    )

    full_content = ""
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            full_content += delta
            yield f"event: message\ndata: {json.dumps({'type': 'markdown', 'text': delta}, ensure_ascii=False)}\n\n"

    await save_message(conversation_id, "assistant", full_content)
