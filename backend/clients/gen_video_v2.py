import json
import logging
import re

import aiohttp
import fal_client
import requests

from config import SETTINGS
from entities.dto import GenVideoResp
from infra.file import download_and_upload_image, img_url_to_base64


async def veo3_gen_video_svc_v2(img_url: str, prompt: str) -> GenVideoResp | None:
    try:
        handler = await fal_client.submit_async(
            SETTINGS.IMAGE_TO_VIDEO_V2,
            arguments={
                "prompt": prompt,
                "image_url": img_url,
                "negative_prompt": "blur, distort, and low quality",
                "cfg_scale": 0.5
            },
        )

        result = await handler.get()
        logging.debug(f"result: {result}")
        if result and isinstance(result, dict):
            if "video" in result and result["video"] and isinstance(result["video"], dict):
                if "url" in result["video"] and result["video"]["url"]:
                    return GenVideoResp(
                        out_id="",
                        view_url=result["video"]["url"],
                        download_url=""
                    )
    except Exception as e:
        logging.error(f"veo3_gen_video_svc_v2 error: {e}", exc_info=True)
    return None
