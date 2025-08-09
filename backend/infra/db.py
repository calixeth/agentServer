import asyncio

import motor.motor_asyncio

from config import SETTINGS
from entities.dto import AIGCTask

client = motor.motor_asyncio.AsyncIOMotorClient(SETTINGS.MONGO_STR)
db = client[SETTINGS.MONGO_DB]
twitter_user_col = db["twitter_user"]
file_col = db["file"]
aigc_task_col = db["aigc_task"]
users_col = db["users"]  # Collection for user authentication data


async def aigc_task_get_by_id(task_id: str) -> AIGCTask | None:
    ret = await aigc_task_col.find_one({"task_id": task_id})
    if ret:
        return AIGCTask(**ret)
    else:
        return None


async def aigc_task_save(task: AIGCTask):
    await aigc_task_col.replace_one({"task_id": task.task_id}, task.model_dump(), upsert=True)


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


def init_indexes():
    try:
        asyncio.run(create_user_indexes())
    except RuntimeError:
        # Already in an event loop (e.g. FastAPI, Jupyter)
        loop = asyncio.get_event_loop()
        loop.create_task(create_user_indexes())
        print("create_user_indexes scheduled in existing event loop")

# Only call this explicitly (optional)
# init_indexes()
