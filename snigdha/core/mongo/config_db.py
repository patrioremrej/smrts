from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB

mongo = AsyncIOMotorClient(MONGO_DB)
db = mongo.bot_config
log_config = db.log_config  # New collection for log group info

async def set_log_group(log_group_id):
    await log_config.update_one({'_id': 'LOG_GROUP'}, {'$set': {'value': log_group_id}}, upsert=True)

async def get_log_group():
    doc = await log_config.find_one({'_id': 'LOG_GROUP'})
    return doc['value'] if doc else None

async def delete_log_group():
    await log_config.delete_one({'_id': 'LOG_GROUP'})
