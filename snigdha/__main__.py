import asyncio
import importlib
import gc
from pyrogram import idle
from snigdha.modules import ALL_MODULES
from snigdha.core.mongo.plans_db import check_and_remove_expired_users
from aiojobs import create_scheduler

loop = asyncio.get_event_loop()

async def schedule_expiry_check():
    scheduler = await create_scheduler()
    while True:
        await scheduler.spawn(check_and_remove_expired_users())
        await asyncio.sleep(60)  # Check every 60 seconds
        gc.collect()  # Explicit garbage collection to free memory

async def restrictdl_boot():
    # Import all modules dynamically
    for module in ALL_MODULES:
        importlib.import_module(f"snigdha.modules.{module}")
    
    # Schedule the expiry check task
    asyncio.create_task(schedule_expiry_check())
    
    # Keep the bot running
    await idle()

if __name__ == "__main__":
    loop.run_until_complete(restrictdl_boot())