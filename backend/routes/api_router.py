import logging

from fastapi import APIRouter, UploadFile, File
from starlette.responses import Response

from common.response import RestResponse
from data.file import s3_upload_file
from entities.bo import FileBO
from entities.dto import GenCoverImgReq, GenCoverImgResp
from services.aigc_service import gen_cover_img_svc

logger = logging.getLogger(__name__)

router = APIRouter()


@router.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return Response(status_code=204)  # 204 No Content


@router.get("/")
async def root():
    """Root endpoint that returns service status"""
    return "UP"


@router.get("/api/health")
async def health():
    """Health check endpoint"""
    return "UP"


@router.post("/api/upload/file", summary="Upload File", response_model=RestResponse[FileBO])
async def upload_file(
        file: UploadFile = File(...),
):
    if not file:
        return RestResponse(code=400, msg="no file", )

    bo = await s3_upload_file(file)
    return RestResponse(data=bo)


@router.post("/api/gen_cover_img",
             summary="gen_cover_img",
             response_model=RestResponse[GenCoverImgResp]
             )
async def gen_cover_img(req: GenCoverImgReq):
    ret = await gen_cover_img_svc(req)
    return RestResponse(data=ret)
