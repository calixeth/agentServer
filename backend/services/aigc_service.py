import datetime
import logging
import uuid

from fastapi import BackgroundTasks

from agent.prompt.aigc import GEN_COVER_IMG_PROMPT
from common.error import raise_error, raise_biz
from infra.db import aigc_task_col
from infra.file import img_url_to_base64
from clients.openai_gen_img import openai_gen_img_svc
from entities.dto import GenCoverImgReq, AIGCTask, Cover
from services.twitter_service import twitter_fetch_user_svc


async def gen_cover_img_svc(req: GenCoverImgReq, tasks: BackgroundTasks) -> AIGCTask:
    username = req.x_link.replace("https://x.com/", "")

    twitter_bo = await twitter_fetch_user_svc(username)
    if not twitter_bo:
        raise_error("twitter user not found")

    if not req.img_url:
        logging.info(f"use {twitter_bo.avatar_url}")
        img_base64 = twitter_bo.avatar_base64
    else:
        logging.info(f"use {req.img_url}")
        img_base64 = await img_url_to_base64(req.img_url)

    # url = await openai_gen_img_svc(template_img_base64=img_base64, prompt=GEN_COVER_IMG_PROMPT)
    # if not url:
    #     raise_biz()

    data = await aigc_task_col.find_one({"task_id": req.task_id})
    task = AIGCTask(**data)
    task.cover = Cover(
        sub_task_id=str(uuid.uuid4()),
        input=req,
        output=None,
        created_at=datetime.datetime.now()

    )
    await aigc_task_col.replace_one({"task_id": task.task_id}, task.model_dump(), upsert=True)

    return task
