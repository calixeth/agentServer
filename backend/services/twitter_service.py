import logging

from infra.db import twitter_user_col
from infra.file import img_url_to_base64
from clients.twitter_client import twitter_fetch_user
from entities.bo import TwitterBO


async def twitter_fetch_user_svc(username: str) -> TwitterBO | None:
    ret = await twitter_user_col.find_one({"username": username})
    if ret:
        logging.info(f"Cached user {username}")
        return await _fill(TwitterBO(**ret))

    user = await twitter_fetch_user(username)
    if not isinstance(user, dict):
        return None

    data = user.get("result", {}).get("infra", {}).get("user", {}).get("result", {})
    if not data:
        return None

    bo = TwitterBO(
        id=data["id"],
        username=username,
        data=data,
    )
    bo = await _fill(bo)
    await twitter_user_col.replace_one({"id": data["id"]}, bo.model_dump(), upsert=True)

    return bo


async def _fill(bo: TwitterBO) -> TwitterBO:
    changed = False
    if not bo.avatar_url:
        bo.avatar_url = bo.data.get("avatar").get("image_url")
        changed = True

    if not bo.avatar_base64:
        bo.avatar_base64 = await img_url_to_base64(bo.avatar_url)
        changed = True

    if changed:
        await _save(bo)
    return bo


async def _save(bo: TwitterBO):
    await twitter_user_col.replace_one({"id": bo.id}, bo.model_dump(), upsert=True)
