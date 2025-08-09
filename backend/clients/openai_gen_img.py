import base64
import io
import logging

import aiohttp
import openai

from config import SETTINGS


async def openai_gen_img_svc(img_url: str, prompt: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                img_bytes = await resp.read()

        image_file = io.BytesIO(img_bytes)
        image_file.name = "template.png"
        logging.info(f"openai generating image: {img_url}")

        ret = await openai.AsyncClient(api_key=SETTINGS.PROXY_OPENAI_API_KEY,
                                       base_url=SETTINGS.PROXY_OPENAI_BASE_URL).images.edit(
            image=image_file,
            prompt=prompt,
            model="gpt-image-1"
        )

        logging.info(f"openai_gen_img_svc: {ret}")
    except Exception as e:
        logging.error(f"openai_gen_img_svc error: {e}", exc_info=True)
    return None
