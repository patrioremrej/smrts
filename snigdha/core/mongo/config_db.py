from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB

mongo = AsyncIOMotorClient(MONGO_DB)
db = mongo.bot_config

async def set_log_group(log_group_id):
    await db.update_one({'_id': 'LOG_GROUP'}, {'$set': {'value': log_group_id}}, upsert=True)

async def get_log_group():
    doc = await db.find_one({'_id': 'LOG_GROUP'})
    return doc['value'] if doc else None

async def delete_log_group():
    await db.delete_one({'_id': 'LOG_GROUP'})
