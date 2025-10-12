import json
import logging

import aiohttp

from config import SETTINGS

host = SETTINGS.XAPI_IO_HOST
headers = {
    f"X-API-Key": SETTINGS.XAPI_IO_API_KEY,
}


async def x_get_user_info_by_username(username: str):
    url = f"{host}/twitter/user/info?userName={username}"
    logging.info(f"Fetching {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                if response.status == 200:
                    res = await response.json()
                    if "status" in res and "success" == res["status"]:
                        logging.info(f"fetched {json.dumps(res["data"], ensure_ascii=False)}")
                        return res["data"]
    except Exception as ex:
        logging.error("Failed to fetch user info", exc_info=True)
    return None


async def x_get_user_last_tweets_by_username(username: str):
    url = f"{host}/twitter/user/last_tweets?userName={username}"
    logging.info(f"Fetching {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                if response.status == 200:
                    res = await response.json()
                    if "status" in res and "success" == res["status"]:
                        logging.info(f"fetched {json.dumps(res["data"]["tweets"], ensure_ascii=False)}")
                        return res["data"]["tweets"]
    except Exception as ex:
        logging.error("Failed x_get_user_last_tweets_by_username", exc_info=True)
    return None
