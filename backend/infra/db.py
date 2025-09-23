import datetime
from typing import Literal

import motor.motor_asyncio

from common.error import raise_error
from config import SETTINGS
from entities.dto import AIGCTask, TwitterTTSTask, DigitalHuman, Profile
from entities.dto import PredefinedVoice

client = motor.motor_asyncio.AsyncIOMotorClient(SETTINGS.MONGO_STR)
db = client[SETTINGS.MONGO_DB]
twitter_user_col = db["twitter_user"]
file_col = db["file"]
aigc_task_col = db["aigc_task"]
users_col = db["users"]  # Collection for user authentication data
twitter_tts_task_col = db["twitter_tts_task"]  # Collection for Twitter TTS tasks
digital_human_col = db["digital_human"]
predefined_voice_col = db["predefined_voice"]
resource_limits_col = db["resource_limits"]
resource_usage_col = db["resource_usage"]
logs_col = db["logs"]
messages_col = db["messages"]
x_oauth_col = db["x_oauth"]
profiles_col = db["profiles"]


async def add_points(
        tenant_id: str,
        points: int,
        remark: str = "",
        points_type: Literal["add", "subtract"] = "add",
):
    if points <= 0:
        raise_error("points must be positive")

    delta = points if type == "add" else -points

    detail = {
        "points": points,
        "type": points_type,
        "remark": remark,
        "created_at": datetime.datetime.now(),
    }

    await profiles_col.update_one(
        {"tenant_id": tenant_id},
        {
            "$inc": {"total_points": delta},
            "$push": {"points_details": detail},
        },
        upsert=True,
    )


async def profile_save(p: Profile):
    await profiles_col.replace_one({"tenant_id": p.tenant_id}, p.model_dump(), upsert=True)


async def get_profile_by_tenant_id(tenant_id: str) -> Profile | None:
    if not tenant_id:
        raise_error("tenant_id is required")
    ret = await profiles_col.find_one({"tenant_id": tenant_id})
    if ret:
        return Profile(**ret)
    else:
        user = await users_col.find_one({"tenant_id": tenant_id})
        p = Profile(
            tenant_id=tenant_id,
            wallet_address=user["wallet_address"],
        )
        await profile_save(p)
        return p


async def digital_human_save(digital_human: DigitalHuman):
    digital_human.updated_at = datetime.datetime.now()
    await digital_human_col.replace_one({"digital_name": digital_human.digital_name}, digital_human.model_dump(),
                                        upsert=True)


async def digital_human_get_by_digital_human(username: str) -> DigitalHuman | None:
    ret = await digital_human_col.find_one({"digital_name": username})
    if ret:
        return DigitalHuman(**ret)
    else:
        return None


async def digital_human_col_delete_by_id(id: str):
    await digital_human_col.delete_one({'id': id})


async def digital_human_get_by_id(id: str) -> DigitalHuman | None:
    ret = await digital_human_col.find_one({"id": id})
    if ret:
        return DigitalHuman(**ret)
    else:
        return None


async def aigc_task_get_by_id(task_id: str) -> AIGCTask | None:
    ret = await aigc_task_col.find_one({"task_id": task_id})
    if ret:
        return AIGCTask(**ret)
    else:
        return None


async def aigc_task_delete_by_id(task_id: str):
    await aigc_task_col.delete_one({'task_id': task_id})


async def aigc_task_count_by_tenant_id(tenant_id: str) -> int:
    return await aigc_task_col.count_documents({"tenant_id": tenant_id})


async def aigc_task_save(task: AIGCTask):
    task.updated_at = datetime.datetime.now()
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


async def twitter_tts_task_get_by_username_and_url(username: str, twitter_url: str,
                                                   tenant_id: str) -> TwitterTTSTask | None:
    """Get Twitter TTS task by username, twitter_url and tenant_id for deduplication"""
    ret = await twitter_tts_task_col.find_one({
        "username": username,
        "twitter_url": twitter_url,
        "tenant_id": tenant_id
    })
    if ret:
        return TwitterTTSTask(**ret)
    else:
        return None


async def twitter_tts_task_get_by_tenant(tenant_id: str, page: int = 1, page_size: int = 20, status: str = None,
                                         task_type: str = None, style: str = None, username: str = None) -> \
        tuple[list[TwitterTTSTask], int]:
    """Get Twitter TTS tasks by tenant with pagination"""
    skip = (page - 1) * page_size

    # Build query
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    if task_type:
        query["task_type"] = task_type
    if style:
        query["style"] = style
    if username:
        query["username"] = username

    # Get total count
    total = await twitter_tts_task_col.count_documents(query)

    # Get tasks with pagination
    cursor = twitter_tts_task_col.find(query).sort("created_at", -1).skip(skip).limit(page_size)
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


# Predefined Voice operations
async def predefined_voice_save(voice: PredefinedVoice):
    """Save or update predefined voice"""
    await predefined_voice_col.replace_one({"voice_id": voice.voice_id}, voice.model_dump(), upsert=True)


async def predefined_voice_get_all(category: str = None, is_active: bool = True) -> tuple[list[PredefinedVoice], int]:
    """Get all predefined voices with optional filtering"""
    # Build query
    query = {"is_active": is_active}
    if category:
        query["category"] = category

    # Get total count
    total = await predefined_voice_col.count_documents(query)

    # Get voices
    cursor = predefined_voice_col.find(query).sort("name", 1)
    voices = []
    async for doc in cursor:
        # Handle missing fields with defaults
        if "audio_url" not in doc:
            doc["audio_url"] = None
        if "updated_at" not in doc:
            doc["updated_at"] = doc.get("created_at")  # Use created_at as fallback

        voices.append(PredefinedVoice(**doc))

    return voices, total


async def predefined_voice_get_by_id(voice_id: str) -> PredefinedVoice | None:
    """Get predefined voice by ID"""
    ret = await predefined_voice_col.find_one({"voice_id": voice_id})
    if ret:
        # Handle missing fields with defaults
        if "audio_url" not in ret:
            ret["audio_url"] = None
        if "updated_at" not in ret:
            ret["updated_at"] = ret.get("created_at")  # Use created_at as fallback

        return PredefinedVoice(**ret)
    else:
        return None


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
        await twitter_tts_task_col.create_index("task_type")
        await twitter_tts_task_col.create_index("style")
        await twitter_tts_task_col.create_index("created_at")
        await twitter_tts_task_col.create_index("tweet_id")
        await twitter_tts_task_col.create_index("username")
        print("Twitter TTS task indexes created successfully")
    except Exception as e:
        print(f"Error creating Twitter TTS task indexes: {e}")


async def create_predefined_voice_indexes():
    """Create indexes for the predefined_voice collection"""
    try:
        await predefined_voice_col.create_index("voice_id", unique=True)
        await predefined_voice_col.create_index("name")
        await predefined_voice_col.create_index("category")
        await predefined_voice_col.create_index("is_active")
        await predefined_voice_col.create_index("created_at")
        print("Predefined voice indexes created successfully")
    except Exception as e:
        print(f"Error creating predefined voice indexes: {e}")


async def init_indexes():
    try:
        await create_user_indexes()
        await create_twitter_tts_indexes()
        await create_predefined_voice_indexes()
        print("All indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")

# asyncio.run(init_indexes())
