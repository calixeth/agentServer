import datetime
import logging
import uuid
from typing import List

from fastapi import BackgroundTasks
from opentelemetry.trace import Status

from agent.prompt.aigc import GEN_COVER_IMG_PROMPT, VIDEO_HAPPY_PROMPY, VIDEO_SAD_PROMPY, VIDEO_DANCE_PROMPY
from clients.gen_video import veo3_gen_video_svc
from common.error import raise_error, raise_biz
from entities.bo import TwitterBO
from infra.db import aigc_task_col, aigc_task_get_by_id, aigc_task_save
from infra.file import img_url_to_base64, s3_upload_openai_img
from clients.openai_gen_img import openai_gen_img_svc
from entities.dto import GenCoverImgReq, AIGCTask, Cover, TaskStatus, GenVideoReq, Video, VideoKeyType, GenVideoResp
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
    if task.cover:
        task.cover.regenerate()
        task.cover.input = req
        task.cover.output = None
    else:
        task.cover = Cover(
            sub_task_id=str(uuid.uuid4()),
            input=req,
            output=None,
            created_at=datetime.datetime.now()
        )

    await aigc_task_save(task)

    background.add_task(_task_gen_cover_img_svc, task, twitter_bo)

    return task


async def gen_video_svc(req: GenVideoReq, background: BackgroundTasks) -> AIGCTask:
    org_task = await aigc_task_get_by_id(req.task_id)
    if not org_task.cover or not org_task.cover.output:
        raise_error("cover img not found")

    regenerate: bool = False
    for v in org_task.videos:
        if v.input.key == req.key:
            v.regenerate()
            v.input = req
            v.output = None
            regenerate = True
            break
    if not regenerate:
        org_task.videos.append(
            Video(
                sub_task_id=str(uuid.uuid4()),
                input=req,
                output=None,
                status=TaskStatus.IN_PROGRESS,
                created_at=datetime.datetime.now()
            )
        )

    await aigc_task_save(org_task)
    background.add_task(_task_video_svc, org_task, req)
    return org_task


async def _task_gen_cover_img_svc(task: AIGCTask, twitter_bo: TwitterBO):
    cur_task = await aigc_task_get_by_id(task.task_id)
    ai_imgs = await openai_gen_img_svc(img_url=twitter_bo.avatar_url_400x400, prompt=GEN_COVER_IMG_PROMPT)
    if ai_imgs and ai_imgs.data:
        ai_img = ai_imgs.data[0]
        url = await s3_upload_openai_img(ai_img)
        if url:
            cur_task.cover.output = url
            cur_task.cover.status = TaskStatus.DONE
            cur_task.cover.done_at = datetime.datetime.now()
            await aigc_task_save(cur_task)
            return

    cur_task.cover.status = TaskStatus.FAILED
    await aigc_task_save(cur_task)


async def _task_video_svc(task: AIGCTask, req: GenVideoReq):
    logging.info(f"_task_video_svc req: {req.model_dump_json()}")
    cur_task = await aigc_task_get_by_id(task.task_id)
    prompt = ""
    if VideoKeyType.HAPPY == req.key:
        prompt = VIDEO_HAPPY_PROMPY
    elif VideoKeyType.SAD == req.key:
        prompt = VIDEO_SAD_PROMPY
    elif VideoKeyType.DANCE == req.key:
        prompt = VIDEO_DANCE_PROMPY
    elif VideoKeyType.HELLO == req.key:
        prompt = VIDEO_HAPPY_PROMPY

    data = await veo3_gen_video_svc(task.cover.output, prompt)
    if data:
        for v in cur_task.videos:
            if v.input.key == req.key:
                v.output = data
                v.status = TaskStatus.DONE
                v.done_at = datetime.datetime.now()
                break

        await aigc_task_save(cur_task)
