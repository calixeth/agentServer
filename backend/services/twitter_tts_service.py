import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from agent.prompt.tts import TTS_PROMPT
from entities.bo import TwitterTTSRequestBO
from entities.dto import TwitterTTSTask, TaskStatus, TwitterTTSTaskListResponse
from infra.db import twitter_tts_task_save, twitter_tts_task_get_by_id, twitter_tts_task_get_by_tenant, twitter_tts_task_get_pending
from clients.twitter_client import get_tweet_summary
from clients.tts_client import text_to_speech_svc, call_model
from infra.file import upload_audio_file

logger = logging.getLogger(__name__)


def extract_tweet_id_from_url(twitter_url: str) -> Optional[str]:
    """
    Extract tweet ID from Twitter/X URL
    
    Args:
        twitter_url: Twitter/X post URL
        
    Returns:
        Tweet ID string or None if invalid
    """
    try:
        # Pattern for Twitter/X URLs: https://x.com/username/status/1234567890
        pattern = r'https?://(?:www\.)?(?:x\.com|twitter\.com)/\w+/status/(\d+)'
        match = re.match(pattern, twitter_url)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error extracting tweet ID from URL {twitter_url}: {e}")
        return None


async def create_twitter_tts_task(request: TwitterTTSRequestBO) -> TwitterTTSTask:
    """
    Create a new Twitter TTS task
    
    Args:
        request: Twitter TTS request business object
        
    Returns:
        Created TwitterTTSTask
    """
    try:
        # Extract tweet ID from URL
        tweet_id = extract_tweet_id_from_url(request.twitter_url)
        if not tweet_id:
            raise ValueError(f"Invalid Twitter URL: {request.twitter_url}")
        
        # Create task
        task = TwitterTTSTask(
            task_id=str(uuid.uuid4()),
            tenant_id=request.tenant_id,
            twitter_url=request.twitter_url,
            tweet_id=tweet_id,
            voice=request.voice,
            model=request.model,
            response_format=request.response_format,
            speed=request.speed,
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to database
        await twitter_tts_task_save(task)
        logger.info(f"Created Twitter TTS task {task.task_id} for tweet {tweet_id}")
        
        return task
        
    except Exception as e:
        logger.error(f"Error creating Twitter TTS task: {e}", exc_info=True)
        raise


async def process_twitter_tts_task(task: TwitterTTSTask) -> bool:
    """
    Process a Twitter TTS task
    
    Args:
        task: Twitter TTS task to process
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing Twitter TTS task {task.task_id}")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.processing_started_at = datetime.now()
        task.updated_at = datetime.now()
        await twitter_tts_task_save(task)
        
        # Step 1: Fetch tweet content using twitter_client
        tweet_summary = await get_tweet_summary(task.tweet_id)
        if not tweet_summary or 'content' not in tweet_summary:
            raise Exception(f"Failed to fetch tweet content for {task.tweet_id}")
        
        tweet_content = tweet_summary['content']
        if not tweet_content.get('full_text'):
            raise Exception("Tweet content is empty")
        
        # Extract tweet text
        tweet_text = tweet_content['full_text']
        task.tweet_content = tweet_text
        
        # Step 2: Generate prompt
        prompt = TTS_PROMPT.format(posts=tweet_text)

        message = await call_model(prompt)
        title = ""
        if message and "#" in message:
            title = message.split("#")[0]

        # Step 3: Generate TTS audio
        audio_data = await text_to_speech_svc(
            text=message,
            voice=task.voice,
            model=task.model,
            response_format=task.response_format,
            speed=task.speed
        )
        
        if not audio_data:
            raise Exception("TTS generation failed")
        
        # Step 4: Upload audio to object storage
        file_extension = task.response_format
        audio_url = await upload_audio_file(audio_data, file_extension)
        
        if not audio_url:
            raise Exception("Failed to upload audio file")
        
        # Update task with success
        task.audio_url = audio_url
        task.status = TaskStatus.DONE
        task.title = title
        task.completed_at = datetime.now()
        task.updated_at = datetime.now()
        await twitter_tts_task_save(task)
        
        logger.info(f"Successfully processed Twitter TTS task {task.task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing Twitter TTS task {task.task_id}: {e}", exc_info=True)
        
        # Update task with error
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.updated_at = datetime.now()
        await twitter_tts_task_save(task)
        
        return False


async def get_twitter_tts_task(task_id: str) -> Optional[TwitterTTSTask]:
    """
    Get Twitter TTS task by ID
    
    Args:
        task_id: Task ID
        
    Returns:
        TwitterTTSTask or None if not found
    """
    try:
        return await twitter_tts_task_get_by_id(task_id)
    except Exception as e:
        logger.error(f"Error getting Twitter TTS task {task_id}: {e}", exc_info=True)
        return None


async def get_twitter_tts_tasks_by_tenant(
    tenant_id: str, 
    page: int = 1, 
    page_size: int = 20, 
    status: Optional[str] = None
) -> TwitterTTSTaskListResponse:
    """
    Get Twitter TTS tasks by tenant with pagination
    
    Args:
        tenant_id: Tenant ID
        page: Page number
        page_size: Page size
        status: Optional status filter
        
    Returns:
        TwitterTTSTaskListResponse
    """
    try:
        tasks, total = await twitter_tts_task_get_by_tenant(tenant_id, page, page_size, status)
        
        return TwitterTTSTaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting Twitter TTS tasks for tenant {tenant_id}: {e}", exc_info=True)
        raise


async def get_pending_twitter_tts_tasks() -> list[TwitterTTSTask]:
    """
    Get all pending Twitter TTS tasks
    
    Returns:
        List of pending tasks
    """
    try:
        return await twitter_tts_task_get_pending()
    except Exception as e:
        logger.error(f"Error getting pending Twitter TTS tasks: {e}", exc_info=True)
        return []


async def retry_failed_twitter_tts_task(task_id: str) -> bool:
    """
    Retry a failed Twitter TTS task
    
    Args:
        task_id: Task ID to retry
        
    Returns:
        True if retry initiated, False otherwise
    """
    try:
        task = await twitter_tts_task_get_by_id(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if task.status != TaskStatus.FAILED:
            logger.warning(f"Task {task_id} is not in failed status: {task.status}")
            return False
        
        # Reset task for retry
        task.status = TaskStatus.IN_PROGRESS
        task.error_message = None
        task.processing_started_at = None
        task.completed_at = None
        task.updated_at = datetime.now()
        
        await twitter_tts_task_save(task)
        logger.info(f"Retry initiated for Twitter TTS task {task_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error retrying Twitter TTS task {task_id}: {e}", exc_info=True)
        return False 