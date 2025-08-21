import asyncio
import datetime
import logging
import uuid

from fastapi import BackgroundTasks

from agent.prompt.aigc import GEN_COVER_IMG_PROMPT, VIDEO_DANCE_PROMPY, VIDEO_GOGO_PROMPY, VIDEO_TURN_PROMPY, \
    VIDEO_ANGRY_PROMPY, VIDEO_SAYING_PROMPY, VIDEO_DEFAULT_PROMPY, GEN_FRAME_IMG_PROMPT, VIDEO_THINK_PROMPY
from clients.gen_video_v2 import veo3_gen_video_svc_v2
from clients.openai_gen_img import openai_gen_img_svc
from common.error import raise_error
from entities.bo import TwitterBO, Country, TwitterTTSRequestBO
from entities.dto import GenCoverImgReq, AIGCTask, Cover, TaskStatus, GenVideoReq, Video, VideoKeyType, DigitalHuman, \
    DigitalVideo, GenCoverResp, AIGCPublishReq
from infra.db import aigc_task_get_by_id, aigc_task_save, digital_human_save, digital_human_get_by_username
from infra.file import s3_upload_openai_img
from services.twitter_service import twitter_fetch_user_svc
from services.twitter_tts_service import create_twitter_tts_task


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
    first_frame_imgs_task = openai_gen_img_svc(img_url=twitter_bo.avatar_url_400x400,
                                               prompt=GEN_FRAME_IMG_PROMPT)
    cover_imgs_task = openai_gen_img_svc(img_url=twitter_bo.avatar_url_400x400,
                                         prompt=GEN_COVER_IMG_PROMPT)

    first_frame_imgs, cover_imgs = await asyncio.gather(
        first_frame_imgs_task,
        cover_imgs_task
    )

    cur_task = await aigc_task_get_by_id(task.task_id)
    first_frame_url = ""
    if first_frame_imgs and first_frame_imgs.data:
        ai_img = first_frame_imgs.data[0]
        first_frame_url = await s3_upload_openai_img(ai_img)

    cover_url = ""
    if cover_imgs and cover_imgs.data:
        ai_img = cover_imgs.data[0]
        cover_url = await s3_upload_openai_img(ai_img)

    if first_frame_url and cover_url:
        cur_task.cover.output = GenCoverResp(
            first_frame_img_url=first_frame_url,
            cover_img_url=cover_url,
        )
        cur_task.cover.status = TaskStatus.DONE
        cur_task.cover.done_at = datetime.datetime.now()
        await aigc_task_save(cur_task)
        return

    cur_task.cover.status = TaskStatus.FAILED
    await aigc_task_save(cur_task)


async def _task_video_svc(task: AIGCTask, req: GenVideoReq):
    logging.info(f"_task_video_svc req: {req.model_dump_json()}")

    prompt = ""
    if VideoKeyType.DANCE == req.key:
        prompt = VIDEO_DANCE_PROMPY
    elif VideoKeyType.GOGO == req.key:
        prompt = VIDEO_GOGO_PROMPY
    elif VideoKeyType.TURN == req.key:
        prompt = VIDEO_TURN_PROMPY
    elif VideoKeyType.ANGRY == req.key:
        prompt = VIDEO_ANGRY_PROMPY
    elif VideoKeyType.SAYING == req.key:
        prompt = VIDEO_SAYING_PROMPY
    elif VideoKeyType.THINK == req.key:
        prompt = VIDEO_THINK_PROMPY
    else:
        prompt = VIDEO_DEFAULT_PROMPY

    data = await veo3_gen_video_svc_v2(task.cover.output.first_frame_img_url, prompt)
    cur_task = await aigc_task_get_by_id(task.task_id)
    if data:
        for v in cur_task.videos:
            if v.input.key == req.key:
                v.output = data
                v.status = TaskStatus.DONE
                v.done_at = datetime.datetime.now()
                break

        await aigc_task_save(cur_task)


async def aigc_task_publish_by_id(req: AIGCPublishReq, user_dict: dict, background: BackgroundTasks) -> DigitalHuman:
    task: AIGCTask = await aigc_task_get_by_id(req.task_id)
    if not task:
        raise_error("task not found")

    task.check_cover()
    x_link = task.cover.input.x_link
    username = x_link.replace("https://x.com/", "")

    org = await digital_human_get_by_username(username)
    update = False
    if org:
        if org.from_task_id != task.task_id:
            raise_error("username is repeated")
        else:
            update = True

    videos: list[DigitalVideo] = []
    for v in task.videos:
        if v.status == TaskStatus.DONE and v.output.view_url:
            videos.append(DigitalVideo(
                key=v.input.key,
                view_url=v.output.view_url,
            ))

    if not videos:
        raise_error("video not found")

    if update:
        id = org.id
    else:
        id = str(uuid.uuid4())

    if not update:
        created_at = datetime.datetime.now()
    else:
        created_at = org.created_at

    description = ""
    country = Country.USA
    if req.description:
        description = req.description
    elif org and org.description:
        description = org.description
    else:
        try:
            user = await twitter_fetch_user_svc(username)
            if user:
                description = user.data.get("legacy", {}).get("description")
                country = user.country
        except Exception:
            pass

    bo = DigitalHuman(
        id=id,
        from_task_id=task.task_id,
        from_tenant_id=task.tenant_id,
        username=username,
        cover_img=task.cover.output.cover_img_url,
        videos=videos,
        updated_at=datetime.datetime.now(),
        created_at=created_at,
        mp3_url=req.mp3_url,
        x_tts_urls=req.x_tts_urls,
        gender=req.gender,
        description=description,
        country=country,
    )

    await digital_human_save(bo)

    background.add_task(voice_ttl_task, req, user_dict, username)
    return bo


async def voice_ttl_task(req: AIGCPublishReq, user: dict, username: str):
    tenant_id = user.get("tenant_id")
    voice_id = req.voice_id or "Abbess"

    for twitter_url in req.x_tts_urls:
        request_bo = TwitterTTSRequestBO(
            twitter_url=twitter_url,
            voice_id=voice_id,
            username=username,
            tenant_id=tenant_id,
            audio_url=None
        )
        await create_twitter_tts_task(request_bo)
