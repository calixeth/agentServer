import json
import logging
import re

from aiohttp import ClientSession
from fastapi import HTTPException

from clients.twitter_client import twitter_fetch_user, twitter_fetch_user_tweets
from config import SETTINGS
from entities.bo import TwitterBO, Country
from infra.db import twitter_user_col

AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
USERINFO_URL = "https://api.twitter.com/2/users/me"


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


async def twitter_callback_svc(code: str):
    logging.info(f"M Twitter callback request: {code}")

    async with ClientSession() as session:
        async with session.post(
                TOKEN_URL,
                data={
                    "client_id": SETTINGS.X_APP_CLIENT_ID,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": SETTINGS.X_APP_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            token_data = await resp.json()
            logging.info(f"M Token response: {token_data}")

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"token empty: {token_data}")

    async with ClientSession() as session:
        async with session.get(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
        ) as user_resp:
            user_data = await user_resp.json()

    username = user_data.get("data", {}).get("username")
    user_id = user_data.get("data", {}).get("id")

    logging.info(f"M user_data {json.dumps(user_data, ensure_ascii=False)} ")

    return "OK"


async def _save(bo: TwitterBO):
    await twitter_user_col.replace_one({"id": bo.id}, bo.model_dump(), upsert=True)
