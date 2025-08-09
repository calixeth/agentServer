import datetime
import logging
import uuid

from fastapi import BackgroundTasks
from opentelemetry.trace import Status

from agent.prompt.aigc import GEN_COVER_IMG_PROMPT
from common.error import raise_error, raise_biz
from entities.bo import TwitterBO
from infra.db import aigc_task_col, aigc_task_get_by_id, aigc_task_save
from infra.file import img_url_to_base64
from clients.openai_gen_img import openai_gen_img_svc
from entities.dto import GenCoverImgReq, AIGCTask, Cover, TaskStatus
from services.twitter_service import twitter_fetch_user_svc


async def gen_cover_img_svc(req: GenCoverImgReq, background: BackgroundTasks) -> AIGCTask:
    username = req.x_link.replace("https://x.com/", "")

    twitter_bo = await twitter_fetch_user_svc(username)
    if not twitter_bo:
        raise_error("twitter user not found")

    # if not req.img_url:
    #     logging.info(f"use {twitter_bo.avatar_url}")
    #     img_base64 = twitter_bo.avatar_base64
    # else:
    #     logging.info(f"use {req.img_url}")
    #     img_base64 = await img_url_to_base64(req.img_url)

    task = await aigc_task_get_by_id(req.task_id)
    task.cover = Cover(
        sub_task_id=str(uuid.uuid4()),
        input=req,
        output=None,
        created_at=datetime.datetime.now()

    )
    await aigc_task_col.replace_one({"task_id": task.task_id}, task.model_dump(), upsert=True)

    background.add_task(_task_gen_cover_img_svc, task, twitter_bo)

    return task


async def _task_gen_cover_img_svc(task: AIGCTask, twitter_bo: TwitterBO):
    url = await openai_gen_img_svc(img_url=twitter_bo.avatar_url_400x400, prompt=GEN_COVER_IMG_PROMPT)
    # TODO
    cur_task = await aigc_task_get_by_id(task.task_id)
    if task.cover.sub_task_id != cur_task.cover.sub_task_id:
        return

    cur_task.cover.output = url
    cur_task.cover.status = TaskStatus.DONE

    await aigc_task_save(cur_task)
