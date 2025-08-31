import asyncio
import datetime
import logging
import uuid

from fastapi import BackgroundTasks

from agent.prompt.aigc import V_DEFAULT_PROMPT, FIRST_FRAME_IMG_PROMPT, V_THINK_PROMPT, V_DANCE_VIDEO_PROMPT, \
    V_SING_VIDEO_PROMPT, V_SPEECH_PROMPT, V_DANCE_IMAGE_PROMPT, V_SING_IMAGE_PROMPT, V_TURN_PROMPT, \
    V_FIGURE_IMAGE_PROMPT
from clients.gen_fal_client import veo3_gen_video_svc_v3, veo3_gen_video_svc_v2
from clients.openai_gen_img import gpt_image_1_gen_imgs_svc, gemini_gen_img_svc
from common.error import raise_error
from config import SETTINGS
from entities.bo import TwitterBO, Country, TwitterTTSRequestBO
from entities.dto import GenCoverImgReq, AIGCTask, Cover, TaskStatus, GenVideoReq, Video, VideoKeyType, DigitalHuman, \
    DigitalVideo, GenCoverResp, AIGCPublishReq, Lyrics, GenerateLyricsResponse, \
    GenerateLyricsResp, GenerateLyricsReq, GenMusicReq, Music, GenerateMusicResponse, GenerateMusicResp
from infra.db import aigc_task_get_by_id, aigc_task_save, digital_human_save, digital_human_get_by_username
from infra.file import s3_upload_openai_img
from services import twitter_tts_service
from services.resource_usage_limit import check_limit_and_record
from services.twitter_service import twitter_fetch_user_svc
from services.twitter_tts_service import create_twitter_tts_task


async def gen_lyrics_svc(req: GenerateLyricsReq, background: BackgroundTasks) -> AIGCTask:
    task = await aigc_task_get_by_id(req.task_id)

    await check_limit_and_record(client=f"task-{task.task_id}", resource="gen-lyrics")

    if task.lyrics:
        task.lyrics.regenerate()
        task.lyrics.input = req
        task.lyrics.output = None
    else:
        task.lyrics = Lyrics(
            sub_task_id=str(uuid.uuid4()),
            input=req,
            output=None,
            created_at=datetime.datetime.now()
        )

    await aigc_task_save(task)

    background.add_task(_task_gen_lyrics, task)

    return task


async def gen_music_svc(req: GenMusicReq, background: BackgroundTasks) -> AIGCTask:
    task = await aigc_task_get_by_id(req.task_id)

    await check_limit_and_record(client=f"task-{task.task_id}", resource="gen_music")

    if task.music:
        task.music.regenerate()
        task.music.input = req
        task.music.output = None
    else:
        task.music = Music(
            sub_task_id=str(uuid.uuid4()),
            input=req,
            output=None,
            created_at=datetime.datetime.now()
        )

    await aigc_task_save(task)

    background.add_task(_task_gen_music, task, req)

    return task


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

    await check_limit_and_record(client=f"task-{task.task_id}", resource="gen-img")

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

    await check_limit_and_record(client=f"task-{org_task.task_id}", resource=f"gen-video-{req.key}")
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
    first_frame_imgs_task = gpt_image_1_gen_imgs_svc(img_urls=[twitter_bo.avatar_url_400x400],
                                                     prompt=FIRST_FRAME_IMG_PROMPT,
                                                     scenario="first_frame")
    dance_imgs_task = gpt_image_1_gen_imgs_svc(img_urls=[SETTINGS.GEN_T_URL_DANCE, twitter_bo.avatar_url_400x400],
                                               prompt=V_DANCE_IMAGE_PROMPT,
                                               scenario="dance")
    sing_imgs_task = gpt_image_1_gen_imgs_svc(img_urls=[SETTINGS.GEN_T_URL_SING, twitter_bo.avatar_url_400x400],
                                              prompt=V_SING_IMAGE_PROMPT,
                                              scenario="sing")
    figure_imgs_task = gemini_gen_img_svc(img_url=twitter_bo.avatar_url_400x400,
                                          prompt=V_FIGURE_IMAGE_PROMPT,
                                          scenario="figure")

    first_frame_imgs, dance_imgs, sing_imgs, figure_imgs = await asyncio.gather(
        first_frame_imgs_task,
        dance_imgs_task,
        sing_imgs_task,
        figure_imgs_task
    )

    cur_task = await aigc_task_get_by_id(task.task_id)
    first_frame_url = ""
    if first_frame_imgs and first_frame_imgs.data:
        first_frame_url = await s3_upload_openai_img(first_frame_imgs.data[0])
        if not first_frame_url:
            logging.info(f"first_frame_url upload error")

    dance_url = ""
    if dance_imgs and dance_imgs.data:
        dance_url = await s3_upload_openai_img(dance_imgs.data[0])
        if not dance_url:
            logging.info(f"dance_url upload error")

    sing_url = ""
    if sing_imgs and sing_imgs.data:
        sing_url = await s3_upload_openai_img(sing_imgs.data[0])
        if not sing_url:
            logging.info(f"sing_url upload error")

    figure_url = ""
    if figure_imgs and figure_imgs.data:
        # figure_url = await s3_upload_openai_img(figure_imgs.data[0])
        figure_url = figure_imgs.data[0].url
        if not figure_url:
            logging.info(f"figure_url upload error")

    if first_frame_url and dance_url and sing_url and figure_url:
        cur_task.cover.output = GenCoverResp(
            first_frame_img_url=first_frame_url,
            cover_img_url=first_frame_url,
            dance_first_frame_img_url=dance_url,
            sing_first_frame_img_url=sing_url,
            figure_first_frame_img_url=figure_url,
        )
        cur_task.cover.status = TaskStatus.DONE
        cur_task.cover.done_at = datetime.datetime.now()
        await aigc_task_save(cur_task)
        return

    cur_task.cover.status = TaskStatus.FAILED
    await aigc_task_save(cur_task)


async def _task_video_svc(task: AIGCTask, req: GenVideoReq):
    logging.info(f"_task_video_svc req: {req.model_dump_json()}")

    if VideoKeyType.DANCE == req.key:
        prompt = V_DANCE_VIDEO_PROMPT
    # elif VideoKeyType.GOGO == req.key:
    #     prompt = V_GOGO_PROMPT
    elif VideoKeyType.TURN == req.key:
        prompt = V_TURN_PROMPT
    # elif VideoKeyType.ANGRY == req.key:
    #     prompt = V_ANGRY_PROMPT
    # elif VideoKeyType.SAYING == req.key:
    #     prompt = V_SAYING_PROMPT
    elif VideoKeyType.SPEECH == req.key:
        prompt = V_SPEECH_PROMPT
    elif VideoKeyType.THINK == req.key:
        prompt = V_THINK_PROMPT
    elif VideoKeyType.SING == req.key:
        prompt = V_SING_VIDEO_PROMPT
    elif VideoKeyType.FIGURE == req.key:
        prompt = V_FIGURE_IMAGE_PROMPT
    else:
        prompt = V_DEFAULT_PROMPT

    if VideoKeyType.DANCE == req.key:
        first_frame_img_url = task.cover.output.dance_first_frame_img_url
    elif VideoKeyType.SING == req.key:
        first_frame_img_url = task.cover.output.sing_first_frame_img_url
    elif VideoKeyType.FIGURE == req.key:
        first_frame_img_url = task.cover.output.figure_first_frame_img_url
    else:
        first_frame_img_url = task.cover.output.first_frame_img_url

    if VideoKeyType.DANCE == req.key:
        data = await veo3_gen_video_svc_v3(first_frame_img_url, prompt)
    elif VideoKeyType.SING == req.key:
        data = await veo3_gen_video_svc_v2(first_frame_img_url, prompt)
    elif VideoKeyType.FIGURE == req.key:
        data = await veo3_gen_video_svc_v2(first_frame_img_url, prompt)
    else:
        data = await veo3_gen_video_svc_v2(first_frame_img_url, prompt)

    cur_task = await aigc_task_get_by_id(task.task_id)
    if data:
        for v in cur_task.videos:
            if v.input.key == req.key:
                v.output = data
                v.status = TaskStatus.DONE
                v.done_at = datetime.datetime.now()
                break
        await aigc_task_save(cur_task)
    else:
        for v in cur_task.videos:
            if v.input.key == req.key:
                v.status = TaskStatus.FAILED
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
    if not task.lyrics.output:
        raise_error("lyrics not found")
    if not task.music.output:
        raise_error("music not found")

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
        sing_image=task.cover.output.sing_first_frame_img_url,
        figure_image=task.cover.output.figure_first_frame_img_url,
        dance_image=task.cover.output.dance_first_frame_img_url,
        lyrics=task.lyrics.output.lyrics,
        lyrics_title=task.lyrics.output.title,
        music_audio_url=task.music.output.audio_url,
        music_style=task.music.output.style,
        music_model=task.music.output.model,
        music_voice=task.music.output.voice,
        music_response_format=task.music.output.response_format,
        music_speed=task.music.output.speed,
    )

    await digital_human_save(bo)

    background.add_task(voice_ttl_task, req, user_dict, username, id)
    return bo


async def voice_ttl_task(req: AIGCPublishReq, user: dict, username: str, digital_human_id: str):
    tenant_id = user.get("tenant_id")
    voice_id = req.voice_id or "Abbess"

    for twitter_url in req.x_tts_urls:
        request_bo = TwitterTTSRequestBO(
            twitter_url=twitter_url,
            voice_id=voice_id,
            username=username,
            tenant_id=tenant_id,
            audio_url=None,
            digital_human_id=digital_human_id,
        )
        await create_twitter_tts_task(request_bo)


async def _task_gen_lyrics(task: AIGCTask):
    result = await twitter_tts_service.generate_lyrics_from_twitter_url(
        twitter_url=task.cover.input.x_link,
        tenant_id=task.tenant_id,
    )
    response = GenerateLyricsResponse(**result)

    cur_task = await aigc_task_get_by_id(task.task_id)
    if response:
        cur_task.lyrics.output = GenerateLyricsResp(
            lyrics=response.lyrics,
            title=response.title,
        )
        cur_task.lyrics.status = TaskStatus.DONE
        cur_task.lyrics.done_at = datetime.datetime.now()
        await aigc_task_save(cur_task)
        return

    cur_task.lyrics.status = TaskStatus.FAILED
    await aigc_task_save(cur_task)


async def _task_gen_music(task: AIGCTask, req: GenMusicReq):
    lyrics = req.lyrics
    if len(lyrics) > 550:
        lyrics = lyrics[:550]

    result = await twitter_tts_service.generate_music_from_lyrics(
        lyrics=lyrics,
        style=req.style,
        tenant_id=task.tenant_id,
        voice=req.voice,
        model=req.model,
        response_format=req.response_format,
        speed=req.speed,
        reference_audio_url=req.reference_audio_url
    )

    response = GenerateMusicResponse(**result)

    cur_task = await aigc_task_get_by_id(task.task_id)
    if response:
        cur_task.music.output = GenerateMusicResp(**result)
        cur_task.music.status = TaskStatus.DONE
        cur_task.music.done_at = datetime.datetime.now()
        await aigc_task_save(cur_task)
        return

    cur_task.music.status = TaskStatus.FAILED
    await aigc_task_save(cur_task)
