import json
import logging
import re

from clients.twitter_client import twitter_fetch_user, twitter_fetch_user_tweets
from entities.bo import TwitterBO, Country
from infra.db import twitter_user_col


async def twitter_fetch_user_svc(username: str) -> TwitterBO | None:
    ret = await twitter_user_col.find_one({"username": username})
    if ret:
        logging.info(f"Cached user {username}")
        return await _fill(TwitterBO(**ret))

    user = None
    try:
        user = await twitter_fetch_user(username)
    except Exception as ex:
        logging.error(f"Failed to fetch user {username}: {ex}")
    if not isinstance(user, dict):
        logging.info(f"User {username} not found")
        return None

    data = user.get("result", {}).get("data", {}).get("user", {}).get("result", {})
    if not data:
        return None

    bo = TwitterBO(
        id=data["id"],
        username=username,
        data=data,
    )
    bo = await _fill(bo)

    return bo


def convert_twitter_avatar_to_400(url: str) -> str:
    return re.sub(r'_(normal|bigger|mini)\.(jpg|png|jpeg|gif)$', r'_400x400.\2', url)


async def _fill(bo: TwitterBO) -> TwitterBO:
    changed = False
    if not bo.avatar_url:
        bo.avatar_url = bo.data.get("avatar").get("image_url")
        changed = True
    if not bo.avatar_url_400x400:
        if bo.avatar_url:
            bo.avatar_url_400x400 = convert_twitter_avatar_to_400(bo.avatar_url)
            changed = True

    if not bo.description:
        bo.description = bo.data.get("legacy", {}).get("description", "")
        changed = True
    if not bo.country:
        text = bo.description

        try:
            ret = await twitter_fetch_user_tweets(bo.data.get("rest_id"))
            text += json.dumps(ret, ensure_ascii=False)
        except Exception as ex:
            pass
        match = re.search(r'[\u4e00-\u9fff]', text)
        if match:
            bo.country = Country.CN
        else:
            bo.country = Country.USA

    if changed:
        await _save(bo)

    logging.info(f"TwitterBO {bo.model_dump_json()}")
    return bo


async def _save(bo: TwitterBO):
    await twitter_user_col.replace_one({"id": bo.id}, bo.model_dump(), upsert=True)
