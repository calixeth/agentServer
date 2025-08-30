import json
import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from agent.prompt.tts import TTS_PROMPT, SONG_PROMPT, LYRICS_PROMPT
from clients.gen_img import gen_text
from config import SETTINGS
from entities.bo import TwitterTTSRequestBO
from entities.dto import TwitterTTSTask, TaskStatus, TaskType, TwitterTTSTaskListResponse
from infra.db import twitter_tts_task_save, twitter_tts_task_get_by_id, twitter_tts_task_get_by_tenant, twitter_tts_task_get_pending
from infra.db import predefined_voice_get_all, predefined_voice_get_by_id, twitter_tts_task_get_by_username_and_url
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
        Created TwitterTTSTask or existing one if duplicate
    """
    try:
        # Check if task already exists for the same username + twitter_url + tenant_id
        if request.username:
            existing_task = await twitter_tts_task_get_by_username_and_url(
                username=request.username,
                twitter_url=request.twitter_url,
                tenant_id=request.tenant_id
            )
            if existing_task:
                logger.info(f"Task already exists for username {request.username} and URL {request.twitter_url}, returning existing task {existing_task.task_id}")
                return existing_task
        
        # Extract tweet ID from URL
        tweet_id = extract_tweet_id_from_url(request.twitter_url) or ""
        # if not tweet_id:
        #     raise ValueError(f"Invalid Twitter URL: {request.twitter_url}")
        
        # Create task
        task = TwitterTTSTask(
            task_id=str(uuid.uuid4()),
            tenant_id=request.tenant_id,
            twitter_url=request.twitter_url,
            tweet_id=tweet_id,
            task_type=TaskType(request.task_type) if request.task_type else TaskType.TTS,
            voice=request.voice,
            model=request.model,
            response_format=request.response_format,
            speed=request.speed,
            voice_id=request.voice_id,
            audio_url_input=request.audio_url,
            username=request.username,
            style=request.style,
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
    Process a Twitter TTS task using strategy pattern
    
    Args:
        task: Twitter TTS task to process
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing Twitter TTS task {task.task_id} with type {task.task_type}")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.processing_started_at = datetime.now()
        task.updated_at = datetime.now()
        await twitter_tts_task_save(task)
        
        # Use strategy pattern to process based on task type
        if task.task_type == TaskType.TTS:
            return await _process_tts_task(task)
        elif task.task_type == TaskType.VOICE_CLONE:
            return await _process_voice_clone_task(task)
        elif task.task_type == TaskType.MUSIC_GEN:
            return await _process_music_gen_task(task)
        else:
            logger.error(f"Unknown task type: {task.task_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing Twitter TTS task {task.task_id}: {e}", exc_info=True)
        
        # Update task with error
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.updated_at = datetime.now()
        await twitter_tts_task_save(task)
        
        return False


async def _process_tts_task(task: TwitterTTSTask) -> bool:
    """
    Process a standard TTS task (original logic)
    
    Args:
        task: Twitter TTS task to process
        
    Returns:
        True if successful, False otherwise
    """
    try:
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

        # Step 3: Generate TTS audio with optional parameters
        tts_kwargs = {
            "text": message,
            "voice": task.voice,
            "model": task.model,
            "response_format": task.response_format,
            "speed": task.speed
        }
        
        # Add optional parameters if they exist
        if task.voice_id:
            tts_kwargs["voice_id"] = task.voice_id
        if task.audio_url_input:
            tts_kwargs["audio_url"] = task.audio_url_input
            
        audio_data = await text_to_speech_svc(**tts_kwargs)
        
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
        
        logger.info(f"Successfully processed TTS task {task.task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing TTS task {task.task_id}: {e}", exc_info=True)
        raise


async def _process_voice_clone_task(task: TwitterTTSTask) -> bool:
    """
    Process a voice cloning task
    
    Args:
        task: Twitter TTS task to process
        
    Returns:
        True if successful, False otherwise
    """
    try:
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
        
        # Step 2: Generate prompt for voice cloning
        prompt = TTS_PROMPT.format(posts=tweet_text)
        message = await call_model(prompt)
        title = ""
        if message and "#" in message:
            title = message.split("#")[0]

        # Step 3: Generate voice cloned audio
        if not task.audio_url_input:
            raise Exception("Audio URL is required for voice cloning")
        
        voice_clone_kwargs = {
            "text": message,
            "model": "speech-02-hd",  # Voice clone specific model
            "response_format": task.response_format or "mp3",
            "speed": task.speed or 1.0,
            "audio_url": task.audio_url_input,
            "voice_application": SETTINGS.VOICE_APPLICATION_CLONE
        }
            
        audio_data = await text_to_speech_svc(**voice_clone_kwargs)
        
        if not audio_data:
            raise Exception("Voice clone generation failed")
        
        # Step 4: Upload audio to object storage
        file_extension = task.response_format or "mp3"
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
        
        logger.info(f"Successfully processed voice clone task {task.task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing voice clone task {task.task_id}: {e}", exc_info=True)
        raise


async def _process_music_gen_task(task: TwitterTTSTask) -> bool:
    """
    Process a music generation task
    
    Args:
        task: Twitter TTS task to process
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Step 1: Extract username from tweet URL
        import re
        url_match = re.search(r'https?://(?:www\.)?(?:x\.com|twitter\.com)/([^/]+)', task.twitter_url)
        if url_match:
            username = url_match.group(1)
        else:
            raise Exception("Username not provided and cannot be extracted from Twitter URL")
        
        # Step 2: Get user context for music generation
        from clients.twitter_client import get_user_music_generation_context, generate_music_prompt_from_context
        
        logger.info(f"Getting user context for music generation: {username}")
        user_context = await get_user_music_generation_context(username)
        
        if not user_context:
            raise Exception(f"Failed to get user context for {username}, falling back to tweet-based generation")
        
        # Step 3: Generate music prompt based on user context and style
        style, profile_summary, tweets_summary = await generate_music_prompt_from_context(user_context, task.style)
        music_prompt = SONG_PROMPT.format(style=style, content=profile_summary+ '\n' + tweets_summary)
        logger.info(f"Generated music prompt for user {username} with style '{task.style}': {len(music_prompt)} characters")
        
        # Step 4: Generate music using the enhanced prompt
        # For now, we'll use TTS as a placeholder, but this would be replaced with actual music generation
        logger.info(f"Music generation for task {task.task_id} with enhanced user context - using placeholder TTS generation")

        message = await call_model(music_prompt)
        # Use the enhanced prompt for TTS generation
        tts_kwargs = {
            "text": None,
            "prompt": message,
            "voice": task.voice or "alloy",
            "model": task.model or "tts-1",
            "response_format": task.response_format or "mp3",
            "speed": task.speed or 1.0,
            "reference_audio_url": task.audio_url_input,
            "voice_application": SETTINGS.VOICE_APPLICATION_MUSIC
        }
        
        audio_data = await text_to_speech_svc(**tts_kwargs)
        
        if not audio_data:
            raise Exception("Music generation failed")
        
        # Step 5: Upload audio to object storage
        file_extension = task.response_format or "mp3"
        audio_url = await upload_audio_file(audio_data, file_extension)
        
        if not audio_url:
            raise Exception("Failed to upload audio file")
        
        # Update task with success
        task.audio_url = audio_url
        task.status = TaskStatus.DONE
        task.title = f"Music for @{username}"  # Set title based on username
        task.completed_at = datetime.now()
        task.updated_at = datetime.now()
        await twitter_tts_task_save(task)
        
        logger.info(f"Successfully processed music generation task {task.task_id} for user {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing music generation task {task.task_id}: {e}", exc_info=True)
        raise


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
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    style: Optional[str] = None,
    username: Optional[str] = None
) -> TwitterTTSTaskListResponse:
    """
    Get Twitter TTS tasks by tenant with pagination
    
    Args:
        tenant_id: Tenant ID
        page: Page number
        page_size: Page size
        status: Optional status filter
        task_type: Optional task type filter
        style: Optional music style filter
        username: Optional username filter
        
    Returns:
        TwitterTTSTaskListResponse
    """
    try:
        tasks, total = await twitter_tts_task_get_by_tenant(tenant_id, page, page_size, status, task_type, style, username)
        
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


async def get_all_predefined_voices(category: str = None, is_active: bool = True) -> tuple[list, int]:
    """
    Get all predefined voices with optional filtering
    
    Args:
        category: Optional category filter
        is_active: Filter by active status (default: True)
        
    Returns:
        Tuple of (voices_list, total_count)
    """
    try:
        return await predefined_voice_get_all(category, is_active)
    except Exception as e:
        logger.error(f"Error getting predefined voices: {e}", exc_info=True)
        return [], 0


async def get_predefined_voice_by_id(voice_id: str):
    """
    Get predefined voice by ID
    
    Args:
        voice_id: Voice ID to retrieve
        
    Returns:
        PredefinedVoice or None if not found
    """
    try:
        return await predefined_voice_get_by_id(voice_id)
    except Exception as e:
        logger.error(f"Error getting predefined voice {voice_id}: {e}", exc_info=True)
        return None


async def generate_lyrics_from_twitter_url(twitter_url: str, tenant_id: str) -> dict:
    """
    Generate lyrics from Twitter URL by analyzing user profile and recent tweets
    
    Args:
        twitter_url: Twitter/X post URL
        tenant_id: Tenant ID for the request
        
    Returns:
        Dictionary containing generated lyrics and metadata
    """
    try:

        prompt = LYRICS_PROMPT.replace("{twitter_url}", twitter_url)
        text = await gen_text(prompt)
        data = text.split("##")

        if not data or len(data) < 2:
            return {}

        return {
            "lyrics": data[0].lstrip(),
            "title": data[1].lstrip(),
            "twitter_url": twitter_url,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating lyrics from Twitter URL: {e}", exc_info=True)
        raise

async def generate_music_from_lyrics(lyrics: str, style: str, tenant_id: str, 
                                   voice: str = "alloy", model: str = "tts-1", 
                                   response_format: str = "mp3", speed: float = 1.0,
                                    reference_audio_url: str="") -> dict:
    """
    Generate music from lyrics and style using TTS service
    
    Args:
        lyrics: Generated lyrics text
        style: Music style (pop, rock, jazz, classical, electronic, folk, blues, country, hip_hop, ambient, custom)
        tenant_id: Tenant ID for the request
        voice: TTS voice to use
        model: TTS model to use
        response_format: Audio format
        speed: Speech speed
        
    Returns:
        Dictionary containing generated music URL and metadata
    """
    try:
        logger.info(f"Generating music from lyrics with style: {style}")
        
        # Generate music using TTS service with music application
        tts_kwargs = {
            "text": None,
            "prompt": lyrics,
            "voice": voice,
            "model": model,
            "response_format": response_format,
            "reference_audio_url": reference_audio_url,
            "speed": speed,
            "voice_application": SETTINGS.VOICE_APPLICATION_MUSIC
        }
        
        audio_data = await text_to_speech_svc(**tts_kwargs)
        if not audio_data:
            raise Exception("Music generation failed")
        
        # Upload audio to object storage
        file_extension = response_format
        audio_url = await upload_audio_file(audio_data, file_extension)
        if not audio_url:
            raise Exception("Failed to upload audio file")
        
        return {
            "audio_url": audio_url,
            "lyrics": lyrics,
            "style": style,
            "voice": voice,
            "model": model,
            "response_format": response_format,
            "speed": speed,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating music from lyrics: {e}", exc_info=True)
        raise 