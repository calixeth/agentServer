import datetime
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, Query
from starlette.responses import Response, JSONResponse

from common.error import raise_error
from common.response import RestResponse
from infra.db import aigc_task_col, aigc_task_get_by_id, aigc_task_count_by_tenant_id
from infra.file import s3_upload_file
from entities.bo import FileBO
from entities.dto import GenCoverImgReq, AIGCTask, AIGCTaskQuery, GenVideoReq
from middleware.auth_middleware import get_optional_current_user
from services.aigc_service import gen_cover_img_svc, gen_video_svc

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


@router.post("/api/aigc_task/gen_cover_img",
             summary="aigc_task/gen_cover_img",
             response_model=RestResponse[AIGCTask]
             )
async def gen_cover_img(req: GenCoverImgReq, background_tasks: BackgroundTasks):
    logging.info(f"gen_cover_img req: {req.model_dump_json()}")
    ret = await gen_cover_img_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/gen_scenario_video",
             summary="aigc_task/gen_scenario_video",
             response_model=RestResponse[AIGCTask]
             )
async def gen_scenario_video(req: GenVideoReq, background_tasks: BackgroundTasks):
    logging.info(f"gen_scenario_video req: {req.model_dump_json()}")
    ret = await gen_video_svc(req, background_tasks)
    return RestResponse(data=ret)


@router.post("/api/aigc_task/create",
             summary="aigc_task/create",
             response_model=RestResponse[AIGCTask]
             )
async def create_aigc_task(user: Optional[dict] = Depends(get_optional_current_user), ):
    tenant_id = user.get("tenant_id", "")
    count = await aigc_task_count_by_tenant_id(tenant_id)
    if count > 1:
        raise_error("Too many tasks")
    task = AIGCTask(
        task_id=str(uuid.uuid4()),
        tenant_id=user.get("tenant_id", ""),
        created_at=datetime.datetime.now()
    )
    await aigc_task_col.insert_one(task.model_dump())
    return RestResponse(data=task)


@router.post("/api/aigc_task/get",
             summary="aigc_task/get",
             response_model=RestResponse[AIGCTask]
             )
async def get_aigc_task(req: AIGCTaskQuery):
    task = await aigc_task_get_by_id(req.task_id)
    return RestResponse(data=task)


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
