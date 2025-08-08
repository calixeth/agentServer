import motor.motor_asyncio

from config import SETTINGS

client = motor.motor_asyncio.AsyncIOMotorClient(SETTINGS.MONGO_STR)
db = client[SETTINGS.MONGO_DB]
twitter_user_col = db["twitter_user"]
file_col = db["file"]
aigc_task_col = db["aigc_task"]
users_col = db["users"]  # Collection for user authentication data

# Create indexes for users collection
async def create_user_indexes():
    """Create indexes for the users collection"""
    try:
        # Create unique indexes for username, email, and wallet_address
        await users_col.create_index("username", unique=True)
        await users_col.create_index("email", unique=True, sparse=True)  # sparse for optional email
        await users_col.create_index("wallet_address", unique=True)
        await users_col.create_index("tenant_id")
        print("User indexes created successfully")
    except Exception as e:
        print(f"Error creating user indexes: {e}")

# Initialize indexes when module is imported
import asyncio
try:
    asyncio.run(create_user_indexes())
except RuntimeError:
    print("Error creating user indexes")