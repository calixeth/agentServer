import logging

import aiohttp

from config import SETTINGS
from data.file import download_and_upload_image
from entities.bo import GenImgTaskBO


async def gen_img_svc(task: GenImgTaskBO):
    try:
        content = [
            {"type": "text", "text": task.prompt},
            {"type": "image_url", "image_url": {"url": task.template_img_base64}}
        ]

        data = {
            "model": "gpt-4o-image",
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }

        headers = {
            "Authorization": f"Bearer {SETTINGS.TZ_API_KEY}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SETTINGS.TZ_URL}/v1/chat/completions", json=data, headers=headers,
                                    timeout=1200) as response:
                if response.status != 200:
                    logging.warning(f'gen_img: http status: {response.status}')
                    return None
                result = await response.json()
                if "error" in result:
                    return None
                if "choices" in result and isinstance(result["choices"], list):
                    for choice in result["choices"]:
                        if "message" in choice and "content" in choice["message"]:
                            content = choice["message"]["content"]
                            import re
                            matches = re.findall(r"!\[.*?\]\((https?://[^\s]+)\)", content)
                            for image_url in matches:
                                if image_url:
                                    ret_img = await download_and_upload_image(image_url, "deepweb3")
                                    if ret_img:
                                        logging.info(f"gen_img {task.task_id} successful!")
                                        return ret_img
    except Exception as e:
        logging.error(f"gen_img {task.task_id} error: {e}", exc_info=True)
    return None
