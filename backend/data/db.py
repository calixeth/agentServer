import motor.motor_asyncio

from config import SETTINGS

client = motor.motor_asyncio.AsyncIOMotorClient(SETTINGS.MONGO_STR)
db = client[SETTINGS.MONGO_DB]
twitter_user_col = db["twitter_user"]
file_col = db["file"]
aigc_task_col = db["aigc_task"]