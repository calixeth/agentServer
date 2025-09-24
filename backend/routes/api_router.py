import datetime
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from starlette.responses import Response, RedirectResponse

from clients.twitter_client import twitter_fetch_user_tweets
from common.error import raise_error
from common.response import RestResponse
from config import SETTINGS
from entities.bo import FileBO, TwitterDTO
from entities.dto import GenCoverImgReq, AIGCTask, AIGCTaskID, GenVideoReq, DigitalHuman, ID, Username, AIGCPublishReq, \
    GenerateLyricsReq, GenMusicReq, BasicInfoReq, GenXAudioReq, Username1, Profile
from infra.db import aigc_task_col, aigc_task_get_by_id, aigc_task_count_by_tenant_id, digital_human_col, \
    digital_human_get_by_id, digital_human_get_by_digital_human, aigc_task_delete_by_id, digital_human_col_delete_by_id, \
    get_profile_by_tenant_id, add_points
from infra.file import s3_upload_file
from middleware.auth_middleware import get_optional_current_user
from services.aigc_service import gen_cover_img_svc, gen_video_svc, aigc_task_publish_by_id, gen_lyrics_svc, \
    gen_music_svc, save_basic_info, gen_twitter_audio_svc
from services.chat_service import event_generator
from services.twitter_service import twitter_fetch_user_svc, twitter_callback_svc, twitter_redirect_url

logger = logging.getLogger(__name__)

router = APIRouter()


@router.options("/{full_path:path}", include_in_schema=False)
async def preflight_handler(full_path: str):
    return Response(status_code=204)  # 204 No Content


@router.get("/", include_in_schema=False)
async def root():
    """Root endpoint that returns service status"""
    return "UP"


@router.get("/api/health", include_in_schema=False)
async def health():
    """Health check endpoint"""
    return "UP"


@router.post("/api/upload_file", summary="upload_file", response_model=RestResponse[FileBO])
async def upload_file(
        file: UploadFile = File(...),
):
    if not file:
        return RestResponse(code=400, msg="no file", )

    bo = await s3_upload_file(file)
    return RestResponse(data=bo)


@router.post("/api/aigc_task/create",
             summary="aigc_task/create",
             response_model=RestResponse[AIGCTask]
             )
async def create_aigc_task(user: Optional[dict] = Depends(get_optional_current_user), ):
    logging.info("M create aigc_task")
    tenant_id = user.get("tenant_id", "")
    count = await aigc_task_count_by_tenant_id(tenant_id)
    if count > 0:
        raise_error("Too many tasks")
    task = AIGCTask(
        task_id=str(uuid.uuid4()),
        tenant_id=user.get("tenant_id", ""),
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    await aigc_task_col.insert_one(task.model_dump())
    return RestResponse(data=task)


@router.post("/api/aigc_task/gen_cover_img",
             summary="aigc_task/gen_cover_img",
             response_model=RestResponse[AIGCTask]
             )
async def gen_cover_img(req: GenCoverImgReq, background_tasks: BackgroundTasks):
    logging.info(f"M gen_cover_img req: {req.model_dump_json()}")
    ret = await gen_cover_img_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/save_base_info",
             summary="aigc_task/save_base_info",
             response_model=RestResponse[AIGCTask]
             )
async def save_base_info(req: BasicInfoReq, background_tasks: BackgroundTasks):
    logging.info(f"M save_base_info req: {req.model_dump_json()}")
    ret = await save_basic_info(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/gen_scenario_video",
             summary="aigc_task/gen_scenario_video",
             response_model=RestResponse[AIGCTask]
             )
async def gen_scenario_video(req: GenVideoReq, background_tasks: BackgroundTasks):
    logging.info(f"M gen_scenario_video req: {req.model_dump_json()}")
    ret = await gen_video_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/gen_lyrics",
             summary="aigc_task/gen_lyrics",
             response_model=RestResponse[AIGCTask]
             )
async def gen_lyrics(req: GenerateLyricsReq, background_tasks: BackgroundTasks):
    logging.info(f"M gen_lyrics req: {req.model_dump_json()}")
    ret = await gen_lyrics_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/gen_music",
             summary="aigc_task/gen_music",
             response_model=RestResponse[AIGCTask]
             )
async def gen_music(req: GenMusicReq, background_tasks: BackgroundTasks):
    logging.info(f"M gen_music req: {req.model_dump_json()}")
    ret = await gen_music_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/gen_twitter_audio",
             summary="aigc_task/gen_twitter_audio",
             response_model=RestResponse[AIGCTask]
             )
async def gen_twitter_audio(req: GenXAudioReq, background_tasks: BackgroundTasks):
    logging.info(f"M gen_twitter_audio req: {req.model_dump_json()}")
    ret = await gen_twitter_audio_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/get",
             summary="aigc_task/get",
             response_model=RestResponse[AIGCTask]
             )
async def get_aigc_task(req: AIGCTaskID):
    task = await aigc_task_get_by_id(req.task_id)
    return RestResponse(data=task)


@router.post("/api/aigc_task/delete",
             summary="aigc_task/delete",
             response_model=RestResponse
             )
async def delete_aigc_task(req: AIGCTaskID):
    await aigc_task_delete_by_id(req.task_id)
    return RestResponse()


@router.post("/api/aigc_task/list",
             summary="aigc_task/list",
             response_model=RestResponse[list[AIGCTask]]
             )
async def list_aigc_task(
        page: int = Query(1, ge=1),
        pagesize: int = Query(10, ge=1, le=1000),
        user: Optional[dict] = Depends(get_optional_current_user), ):
    tenant_id = user.get("tenant_id", "")
    skip = (page - 1) * pagesize
    cursor = aigc_task_col.find({"tenant_id": tenant_id}) \
        .sort("created_at", -1) \
        .skip(skip) \
        .limit(pagesize)
    data_list = await cursor.to_list(length=pagesize)
    tasks = [AIGCTask(**doc) for doc in data_list]
    return RestResponse(data=tasks)


@router.post("/api/aigc_task/publish_digital_human",
             summary="aigc_task/publish_digital_human",
             response_model=RestResponse[DigitalHuman]
             )
async def get_aigc_publish(req: AIGCPublishReq,
                           background_tasks: BackgroundTasks,
                           user: Optional[dict] = Depends(get_optional_current_user),
                           ):
    ret = await aigc_task_publish_by_id(req, user, background_tasks)

    tenant_id = user.get("tenant_id", "")
    await add_points(tenant_id=tenant_id, points=100, remark="publish_digital_human")
    return RestResponse(data=ret)


@router.post("/api/digital_human/list",
             summary="digital_human/list",
             response_model=RestResponse[list[DigitalHuman]]
             )
async def list_digital_human(
        page: int = Query(1, ge=1),
        pagesize: int = Query(10, ge=1, le=1000),
        user: Optional[dict] = Depends(get_optional_current_user), ):
    skip = (page - 1) * pagesize
    cursor = digital_human_col.find({}) \
        .sort("created_at", -1) \
        .skip(skip) \
        .limit(pagesize)
    data_list = await cursor.to_list(length=pagesize)
    tasks = [DigitalHuman(**doc) for doc in data_list]
    return RestResponse(data=tasks)


@router.post("/api/digital_human/get_by_id",
             summary="digital_human/get_by_id",
             response_model=RestResponse[DigitalHuman]
             )
async def get_digital_human(req: ID):
    task = await digital_human_get_by_id(req.id)
    return RestResponse(data=task)


@router.post("/api/digital_human/get_by_digital_name",
             summary="digital_human/get_by_digital_name",
             response_model=RestResponse[DigitalHuman]
             )
async def get_digital_human_username(req: Username):
    task = await digital_human_get_by_digital_human(req.digital_name)
    return RestResponse(data=task)


@router.post("/api/digital_human/delete",
             summary="digital_human/delete",
             response_model=RestResponse[AIGCTask]
             )
async def delete_digital_human(req: ID):
    await digital_human_col_delete_by_id(req.id)
    return RestResponse()


@router.post("/api/x/user",
             summary="x/user",
             response_model=RestResponse[TwitterDTO]
             )
async def get_x_user(req: Username1):
    username = req.username.replace("https://x.com/", "")
    user = await twitter_fetch_user_svc(username)
    if not user:
        raise_error(f"User {username} not found")
    timeline = {}
    try:
        ret = await twitter_fetch_user_tweets(user.data.get("rest_id"))
        if ret.get("result", {}).get("timeline", {}):
            timeline = ret["result"]["timeline"]
    except Exception as err:
        logger.error(err)
    return RestResponse(data=TwitterDTO(
        name=user.data.get("core", {}).get("name"),
        screen_name=user.data.get("core", {}).get("screen_name"),
        profile_banner_url=user.data.get("legacy", {}).get("profile_banner_url"),
        description=user.data.get("legacy", {}).get("description"),
        profile_image_url_https=user.avatar_url,
        followers_count=user.data.get("legacy", {}).get("followers_count"),
        friends_count=user.data.get("legacy", {}).get("friends_count"),
        timeline=timeline
    ))


@router.get("/api/chat",
            summary="chat")
async def chat(query: str = Query(..., description="query"),
               conversation_id: str = Query(..., description="conversation_id")):
    return StreamingResponse(
        event_generator(conversation_id, query),
        media_type="text/event-stream"
    )


@router.get("/api/callback",
            summary="x callback")
async def twitter_callback(code: str, state: str):
    try:
        await twitter_callback_svc(code, state)
    except Exception as err:
        logger.error(err)
    return RedirectResponse(SETTINGS.APP_HOME_URI)


@router.get("/api/x/bind",
            summary="x bind")
async def twitter_bind(user: Optional[dict] = Depends(get_optional_current_user), ):
    """"""
    tenant_id = user.get("tenant_id", "")
    url = await twitter_redirect_url(tenant_id)
    return url


@router.get("/api/profile",
            summary="profile",
            response_model=RestResponse[Profile])
async def profile(user: Optional[dict] = Depends(get_optional_current_user), ):
    tenant_id = user.get("tenant_id", "")
    p = await get_profile_by_tenant_id(tenant_id)
    return RestResponse(data=p)
