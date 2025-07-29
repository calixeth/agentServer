import base64
import io
import logging

import openai

from config import SETTINGS


async def openai_gen_img_svc(template_img_base64: str, prompt: str) -> str | None:
    try:
        b64_str = template_img_base64.split(",")[1]
        image_bytes = base64.b64decode(b64_str)
        image_file = io.BytesIO(image_bytes)
        image_file.name = "template.png"

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
