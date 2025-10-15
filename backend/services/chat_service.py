import json
from datetime import datetime

from clients.llm_client import proxy_client
from infra.db import messages_col

PROMPT = """\
You are "{twitter_account} Digital", a digital clone of Twitter/X account @{twitter_account}'s persona. Respond in first person as the owner of @{twitter_account}. Prioritize @{twitter_account}'s actual tweets, views, and style for all answers—reference their posts, tone, and signature elements from their timeline first. If insufficient, supplement with general web knowledge, but always align with their persona and style.
Rules:

Style: Mirror @{twitter_account}'s unique tone, phrasing, emojis, humor, and boldness. Use short sentences and their typical expressions. Do not add interactive questions—directly answer the user's query.
Content: Quote/paraphrase real tweets from @{twitter_account} as primary source. Stay faithful to their views; use web knowledge only as secondary support.
Structure: Provide a direct, complete answer without engaging follow-ups or questions.
Limits: Simulate personal views only; update via latest tweets from @{twitter_account}.
"""


async def save_message(conversation_id: str, role: str, content: str):
    doc = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "ts": datetime.utcnow()
    }
    await messages_col.insert_one(doc)


async def build_history(conversation_id: str, twitter_account: str):
    cursor = messages_col.find(
        {"conversation_id": conversation_id}
    ).sort("ts", -1).limit(10)

    history = await cursor.to_list(length=10)
    history = history[::-1]

    if twitter_account:
        messages = [{"role": "system", "content": PROMPT.format(twitter_account=twitter_account)}]
    else:
        messages = [{"role": "system", "content": "You are a helpful assistant"}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    return messages


async def event_generator(conversation_id: str, user_message: str, twitter_account: str):
    await save_message(conversation_id, "user", user_message)

    messages = await build_history(conversation_id, twitter_account)

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
