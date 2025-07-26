import logging

import aiohttp

from config import SETTINGS

logger = logging.getLogger('twitter_client')

host = f"https://{SETTINGS.TWITTER241_HOST}"

headers = {
    f"x-{SETTINGS.TWITTER241}-host": SETTINGS.TWITTER241_HOST,
    f"x-{SETTINGS.TWITTER241}-key": SETTINGS.TWITTER241_KEY
}


async def twitter_fetch_user(username: str):
    url = f"{host}/user?username={username}"
    logger.info(f"Fetching {url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()

    return None
