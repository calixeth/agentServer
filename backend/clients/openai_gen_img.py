import io
import logging

import aiohttp
import openai
from openai.types import ImagesResponse

from config import SETTINGS


async def gemini_gen_img_svc(img_url: str, prompt: str, scenario: str = "") -> ImagesResponse | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                img_bytes = await resp.read()

        image_file = io.BytesIO(img_bytes)
        image_file.name = "template.png"
        logging.info(f"gemini_gen_img_svc: {img_url} {scenario}")

        ret = await openai.AsyncClient(api_key=SETTINGS.PROXY_OPENAI_API_KEY,
                                       base_url=SETTINGS.PROXY_OPENAI_BASE_URL).images.edit(
            image=image_file,
            prompt=prompt,
            model="gemini-2.5-flash-image"
        )

        if ret and ret.data[0].url:
            logging.info(f"gemini_gen_img_svc success {img_url} {scenario}")
            return ret
        else:
            logging.info(f"gemini_gen_img_svc error {img_url} {scenario} {ret}")
            return None
    except Exception as e:
        logging.error(f"{scenario} gemini_gen_img_svc url={img_url} prompt={prompt} error: {e}", exc_info=True)
    return None


async def gpt_image_1_gen_imgs_svc(img_urls: list[str], prompt: str, scenario: str = "") -> ImagesResponse | None:
    try:
        image_files = []
        for img_url in img_urls:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as resp:
                    img_bytes = await resp.read()
            image_file = io.BytesIO(img_bytes)
            image_file.name = "template.png"
            logging.info(f"gpt_image_1_gen_imgs_svc: {img_url} {scenario}")
            image_files.append(image_file)
        ret = await openai.AsyncClient(api_key=SETTINGS.PROXY_OPENAI_API_KEY,
                                       base_url=SETTINGS.PROXY_OPENAI_BASE_URL).images.edit(
            image=image_files,
            prompt=prompt,
            model="gpt-image-1"
        )

        if ret and ret.data[0] and (ret.data[0].url or ret.data[0].b64_json):
            logging.info(f"gpt_image_1_gen_imgs_svc success {img_urls} {scenario}")
            return ret
        else:
            logging.info(f"gpt_image_1_gen_imgs_svc error {img_urls} {scenario} {ret}")
            return None
    except Exception as e:
        logging.error(f"{scenario} gpt_image_1_gen_imgs_svc error {img_urls} {prompt}: {e}", exc_info=True)
    return None
