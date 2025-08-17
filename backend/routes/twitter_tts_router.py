import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from common.error_messages import get_error_message
from common.exceptions import CustomAgentException, ErrorCode
from common.response import RestResponse
from entities.bo import TwitterTTSRequestBO
from entities.dto import TwitterTTSRequest, TwitterTTSResponse, TwitterTTSTask, TwitterTTSTaskListResponse, TwitterTTSTaskQuery
from entities.dto import PredefinedVoice, PredefinedVoiceListResponse
from services import twitter_tts_service
from middleware.auth_middleware import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/api/twitter-tts/create", response_model=RestResponse[TwitterTTSResponse], summary="Create Twitter TTS task")
async def create_twitter_tts_task(
    request: TwitterTTSRequest,
    user: dict = Depends(get_current_user)
):
    """
    Create a new Twitter TTS task
    
    - **twitter_url**: Twitter/X post URL (e.g., https://x.com/username/status/1234567890)
    - **voice**: TTS voice to use (alloy, echo, fable, onyx, nova, shimmer)
    - **model**: TTS model to use (tts-1, tts-1-hd)
    - **response_format**: Audio format (mp3, opus, aac, flac)
    - **speed**: Speech speed (0.25 to 4.0)
    - **voice_id**: Optional voice ID for TTS (optional)
    - **audio_url**: Optional audio URL for TTS (optional)
    
    Note: Tenant ID is automatically extracted from authenticated user
    """
    try:
        # Get tenant_id from authenticated user
        tenant_id = user.get("tenant_id")
        if not tenant_id:
            return RestResponse(
                code=ErrorCode.INVALID_PARAMETERS,
                msg="User does not have a valid tenant ID"
            )
        
        # Convert to business object
        request_bo = TwitterTTSRequestBO(
            twitter_url=request.twitter_url,
            voice=request.voice,
            model=request.model,
            response_format=request.response_format,
            speed=request.speed,
            voice_id=request.voice_id,
            audio_url=request.audio_url,
            tenant_id=tenant_id
        )
        
        # Create task
        task = await twitter_tts_service.create_twitter_tts_task(request_bo)
        
        response = TwitterTTSResponse(
            task_id=task.task_id,
            status=task.status,
            message="Twitter TTS task created successfully"
        )
        
        return RestResponse(data=response)
        
    except ValueError as e:
        logger.error(f"Validation error in Twitter TTS task creation: {str(e)}")
        return RestResponse(
            code=ErrorCode.INVALID_PARAMETERS,
            msg=str(e)
        )
    except CustomAgentException as e:
        logger.error(f"Error in Twitter TTS task creation: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in Twitter TTS task creation: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.get("/api/twitter-tts/task/{task_id}", response_model=RestResponse[TwitterTTSTask], summary="Get Twitter TTS task by ID")
async def get_twitter_tts_task(
    task_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get Twitter TTS task details by task ID
    
    - **task_id**: Unique task identifier
    
    Note: Only tasks belonging to the authenticated user's tenant can be accessed
    """
    try:
        task = await twitter_tts_service.get_twitter_tts_task(task_id)
        if not task:
            return RestResponse(
                code=ErrorCode.NOT_FOUND,
                msg="Task not found"
            )
        
        # Check if user has access to this task
        tenant_id = user.get("tenant_id")
        if task.tenant_id != tenant_id:
            return RestResponse(
                code=ErrorCode.FORBIDDEN,
                msg="Access denied: Task belongs to different tenant"
            )
        
        return RestResponse(data=task)
        
    except CustomAgentException as e:
        logger.error(f"Error getting Twitter TTS task: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting Twitter TTS task: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.get("/api/twitter-tts/tasks", response_model=RestResponse[TwitterTTSTaskListResponse], summary="Get Twitter TTS tasks by tenant")
async def get_twitter_tts_tasks(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status (in_progress, done, failed)")
):
    """
    Get Twitter TTS tasks for the authenticated user's tenant with pagination
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of tasks per page (1-100)
    - **status**: Optional status filter
    
    Note: Tenant ID is automatically extracted from authenticated user
    """
    try:
        # Get tenant_id from authenticated user
        tenant_id = user.get("tenant_id")
        if not tenant_id:
            return RestResponse(
                code=ErrorCode.BAD_REQUEST,
                msg="User does not have a valid tenant ID"
            )
        
        result = await twitter_tts_service.get_twitter_tts_tasks_by_tenant(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            status=status
        )
        
        return RestResponse(data=result)
        
    except CustomAgentException as e:
        logger.error(f"Error getting Twitter TTS tasks: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting Twitter TTS tasks: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.post("/api/twitter-tts/task/{task_id}/retry", response_model=RestResponse[dict], summary="Retry failed Twitter TTS task")
async def retry_twitter_tts_task(
    task_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Retry a failed Twitter TTS task
    
    - **task_id**: Task ID to retry
    
    Note: Only tasks belonging to the authenticated user's tenant can be retried
    """
    try:
        # First check if user has access to this task
        task = await twitter_tts_service.get_twitter_tts_task(task_id)
        if not task:
            return RestResponse(
                code=ErrorCode.NOT_FOUND,
                msg="Task not found"
            )
        
        tenant_id = user.get("tenant_id")
        if task.tenant_id != tenant_id:
            return RestResponse(
                code=ErrorCode.FORBIDDEN,
                msg="Access denied: Task belongs to different tenant"
            )
        
        success = await twitter_tts_service.retry_failed_twitter_tts_task(task_id)
        
        if success:
            return RestResponse(
                data={"message": "Task retry initiated successfully"},
                msg="Task retry initiated successfully"
            )
        else:
            return RestResponse(
                code=ErrorCode.BAD_REQUEST,
                msg="Failed to retry task. Task may not exist or not in failed status."
            )
            
    except CustomAgentException as e:
        logger.error(f"Error retrying Twitter TTS task: {str(e)}", exc_info=True)
        return RestResponse(code=e.error_code, msg=e.message)
    except Exception as e:
        logger.error(f"Unexpected error retrying Twitter TTS task: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.delete("/api/twitter-tts/task/{task_id}", response_model=RestResponse[dict], summary="Delete Twitter TTS task")
async def delete_twitter_tts_task(
    task_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete a Twitter TTS task (soft delete by marking as deleted)
    
    - **task_id**: Task ID to delete
    
    Note: Only tasks belonging to the authenticated user's tenant can be deleted
    """
    try:
        # First check if user has access to this task
        task = await twitter_tts_service.get_twitter_tts_task(task_id)
        if not task:
            return RestResponse(
                code=ErrorCode.NOT_FOUND,
                msg="Task not found"
            )
        
        tenant_id = user.get("tenant_id")
        if task.tenant_id != tenant_id:
            return RestResponse(
                code=ErrorCode.FORBIDDEN,
                msg="Access denied: Task belongs to different tenant"
            )
        
        # For now, we'll just return a success message
        # In a real implementation, you might want to add a 'deleted' field to the task
        # or move it to a separate collection
        return RestResponse(
            data={"message": "Task deletion not implemented yet"},
            msg="Task deletion not implemented yet"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error deleting Twitter TTS task: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.get("/api/twitter-tts/voices", response_model=RestResponse[PredefinedVoiceListResponse], summary="Get all predefined voices")
async def get_all_predefined_voices(
    category: Optional[str] = Query(None, description="Filter by voice category"),
    is_active: bool = Query(True, description="Filter by active status")
):
    """
    Get all predefined voices with optional filtering
    
    - **category**: Optional category filter (e.g., "male", "female", "child")
    - **is_active**: Filter by active status (default: true)
    
    Returns a list of available voices with their names, IDs, and sample audio URLs
    """
    try:
        voices, total = await twitter_tts_service.get_all_predefined_voices(category, is_active)
        
        response = PredefinedVoiceListResponse(
            voices=voices,
            total=total
        )
        
        return RestResponse(data=response)
        
    except Exception as e:
        logger.error(f"Unexpected error getting predefined voices: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        )


@router.get("/api/twitter-tts/voices/{voice_id}", response_model=RestResponse[PredefinedVoice], summary="Get predefined voice by ID")
async def get_predefined_voice_by_id(voice_id: str):
    """
    Get predefined voice details by voice ID
    
    - **voice_id**: Unique voice identifier
    
    Returns detailed information about a specific voice
    """
    try:
        voice = await twitter_tts_service.get_predefined_voice_by_id(voice_id)
        
        if not voice:
            return RestResponse(
                code=ErrorCode.INVALID_PARAMETERS,
                msg="Voice not found"
            )
        
        return RestResponse(data=voice)
        
    except Exception as e:
        logger.error(f"Unexpected error getting predefined voice: {str(e)}", exc_info=True)
        return RestResponse(
            code=ErrorCode.INTERNAL_ERROR,
            msg=get_error_message(ErrorCode.INTERNAL_ERROR)
        ) 