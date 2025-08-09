import datetime
import logging
import uuid

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from starlette.responses import Response, JSONResponse

from common.response import RestResponse
from infra.db import aigc_task_col
from infra.file import s3_upload_file
from entities.bo import FileBO
from entities.dto import GenCoverImgReq, AIGCTask, AIGCTaskQuery
from services.aigc_service import gen_cover_img_svc

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


@router.post("/api/aigc_task/create",
             summary="aigc_task/create",
             response_model=RestResponse[AIGCTask]
             )
async def create_aigc_task():
    task = AIGCTask(
        task_id=str(uuid.uuid4()),
        created_at=datetime.datetime.now()
    )
    await aigc_task_col.insert_one(task.model_dump())
    return RestResponse(data=task)


@router.post("/api/aigc_task/find",
             summary="aigc_task/find",
             response_model=RestResponse[AIGCTask]
             )
async def find_aigc_task(req: AIGCTaskQuery):
    data = await aigc_task_col.find_one({"task_id": str(req.task_id)})
    return RestResponse(data=AIGCTask(**data))
