import asyncio

import motor.motor_asyncio

from config import SETTINGS
from entities.dto import AIGCTask, TwitterTTSTask

client = motor.motor_asyncio.AsyncIOMotorClient(SETTINGS.MONGO_STR)
db = client[SETTINGS.MONGO_DB]
twitter_user_col = db["twitter_user"]
file_col = db["file"]
aigc_task_col = db["aigc_task"]
users_col = db["users"]  # Collection for user authentication data
twitter_tts_task_col = db["twitter_tts_task"]  # Collection for Twitter TTS tasks


async def aigc_task_get_by_id(task_id: str) -> AIGCTask | None:
    ret = await aigc_task_col.find_one({"task_id": task_id})
    if ret:
        return AIGCTask(**ret)
    else:
        return None


async def aigc_task_count_by_tenant_id(tenant_id: str) -> int:
    return await aigc_task_col.count_documents({"tenant_id": tenant_id})


async def aigc_task_save(task: AIGCTask):
    await aigc_task_col.replace_one({"task_id": task.task_id}, task.model_dump(), upsert=True)


# Twitter TTS Task operations
async def twitter_tts_task_save(task: TwitterTTSTask):
    """Save or update Twitter TTS task"""
    await twitter_tts_task_col.replace_one({"task_id": task.task_id}, task.model_dump(), upsert=True)


async def twitter_tts_task_get_by_id(task_id: str) -> TwitterTTSTask | None:
    """Get Twitter TTS task by ID"""
    ret = await twitter_tts_task_col.find_one({"task_id": task_id})
    if ret:
        return TwitterTTSTask(**ret)
    else:
        return None


async def twitter_tts_task_get_by_tenant(tenant_id: str, page: int = 1, page_size: int = 20, status: str = None) -> tuple[list[TwitterTTSTask], int]:
    """Get Twitter TTS tasks by tenant with pagination and optional status filter"""
    skip = (page - 1) * page_size
    
    # Build filter
    filter_query = {"tenant_id": tenant_id}
    if status:
        filter_query["status"] = status
    
    # Get total count
    total = await twitter_tts_task_col.count_documents(filter_query)
    
    # Get tasks with pagination
    cursor = twitter_tts_task_col.find(filter_query).sort("created_at", -1).skip(skip).limit(page_size)
    tasks = []
    async for doc in cursor:
        tasks.append(TwitterTTSTask(**doc))
    
    return tasks, total


async def twitter_tts_task_get_pending() -> list[TwitterTTSTask]:
    """Get all pending Twitter TTS tasks"""
    cursor = twitter_tts_task_col.find({"status": "in_progress"}).sort("created_at", 1)
    tasks = []
    async for doc in cursor:
        tasks.append(TwitterTTSTask(**doc))
    
    return tasks


async def create_user_indexes():
    """Create indexes for the users collection"""
    try:
        await users_col.create_index("username", unique=True)
        await users_col.create_index("email", unique=True, sparse=True)
        await users_col.create_index("wallet_address", unique=True)
        await users_col.create_index("tenant_id")
        print("User indexes created successfully")
    except Exception as e:
        print(f"Error creating user indexes: {e}")


async def create_twitter_tts_indexes():
    """Create indexes for the twitter_tts_task collection"""
    try:
        await twitter_tts_task_col.create_index("task_id", unique=True)
        await twitter_tts_task_col.create_index("tenant_id")
        await twitter_tts_task_col.create_index("status")
        await twitter_tts_task_col.create_index("created_at")
        await twitter_tts_task_col.create_index("tweet_id")
        print("Twitter TTS task indexes created successfully")
    except Exception as e:
        print(f"Error creating Twitter TTS task indexes: {e}")


def init_indexes():
    try:
        asyncio.run(create_user_indexes())
        asyncio.run(create_twitter_tts_indexes())
    except RuntimeError:
        # Already in an event loop (e.g. FastAPI, Jupyter)
        loop = asyncio.get_event_loop()
        loop.create_task(create_user_indexes())
        loop.create_task(create_twitter_tts_indexes())
        print("create_indexes scheduled in existing event loop")

# Only call this explicitly (optional)
# init_indexes()
