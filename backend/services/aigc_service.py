import logging
import uuid

from common.error import raise_error, raise_biz
from common.temp_prompt import GEN_COVER_IMG_PROMPT
from data.db import aigc_task_col
from data.file import img_url_to_base64
from data.gen_img import gen_img_svc
from data.openai_gen_img import openai_gen_img_svc
from entities.dto import GenCoverImgReq, GenCoverImgResp
from services.twitter_service import twitter_fetch_user_svc


async def gen_cover_img_svc(req: GenCoverImgReq) -> GenCoverImgResp:
    username = req.x_link.replace("https://x.com/", "")

    bo = await twitter_fetch_user_svc(username)
    if not bo:
        raise_error("twitter user not found")

    if not req.img_url:
        logging.info(f"use {bo.avatar_url}")
        img_base64 = bo.avatar_base64
    else:
        logging.info(f"use {req.img_url}")
        img_base64 = await img_url_to_base64(req.img_url)

    url = await openai_gen_img_svc(template_img_base64=img_base64, prompt=GEN_COVER_IMG_PROMPT)
    if not url:
        raise_biz()

    task_id = str(uuid.uuid4())

    resp = GenCoverImgResp(
        task_id=task_id,
        img_url=url,
    )

    aigc_task_col.insert_one(resp.model_dump())

    return resp
