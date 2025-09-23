import base64
import hashlib
import json
import logging
import re
import secrets
from urllib.parse import urlencode

from aiohttp import ClientSession
from fastapi import HTTPException

from clients.twitter_client import twitter_fetch_user, twitter_fetch_user_tweets
from config import SETTINGS
from entities.bo import TwitterBO, Country
from infra.db import twitter_user_col, x_oauth_col, get_profile_by_tenant_id, profile_save, add_points

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


async def twitter_callback_svc(code: str, state: str):
    logging.info(f"M Twitter callback request: {code} {state}")

    oauth2_params: dict = await x_oauth_col.find_one({"state": state})
    await x_oauth_col.delete_one({"state": state})

    if not isinstance(oauth2_params, dict):
        raise HTTPException(status_code=400, detail="invalid state")

    logging.info(f"oauth2_params: {oauth2_params}")
    basic_token = base64.b64encode(
        f"{SETTINGS.X_APP_CLIENT_ID}:{SETTINGS.X_APP_CLIENT_SECRET}".encode()
    ).decode()
    async with ClientSession() as session:
        async with session.post(
                TOKEN_URL,
                data={
                    "client_id": SETTINGS.X_APP_CLIENT_ID,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": SETTINGS.X_APP_REDIRECT_URI,
                    "code_verifier": oauth2_params["code_verifier"],
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic_token}"
                },
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

    x_username = user_data.get("data", {}).get("username")
    x_user_id = user_data.get("data", {}).get("id")

    logging.info(f"M user_data {json.dumps(user_data, ensure_ascii=False)} ")
    bo = await twitter_fetch_user_svc(x_username)

    profile = await get_profile_by_tenant_id(oauth2_params["tenant_id"])
    profile.verified_x_username = x_username
    profile.verified_x_user_id = x_user_id
    profile.verified_x_avatar_url = bo.avatar_url

    await profile_save(profile)

    await add_points(tenant_id=profile.tenant_id, points=100, remark="twitter_bind")


def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("utf-8")
    challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge).rstrip(b"=").decode("utf-8")
    return code_verifier, code_challenge


async def twitter_redirect_url(tenant_id: str) -> str:
    logging.info(f"M twitter_redirect_url: {tenant_id}")

    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_hex(8)

    params = {
        "response_type": "code",
        "client_id": SETTINGS.X_APP_CLIENT_ID,
        "redirect_uri": SETTINGS.X_APP_REDIRECT_URI,
        "scope": "tweet.read users.read offline.access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    doc = {
        "state": state,
        "code_verifier": code_verifier,
        "tenant_id": tenant_id,
    }

    logging.info(f"M doc: {json.dumps(doc, ensure_ascii=False)} params {json.dumps(params, ensure_ascii=False)}")

    await x_oauth_col.insert_one(doc)
    url = f"{AUTH_URL}?{urlencode(params)}"
    return url


async def _save(bo: TwitterBO):
    await twitter_user_col.replace_one({"id": bo.id}, bo.model_dump(), upsert=True)
