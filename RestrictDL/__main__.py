import asyncio
import importlib
import gc
from pyrogram import idle
from RestrictDL.modules import ALL_MODULES
from RestrictDL.core.mongo.plans_db import check_and_remove_expired_users
from aiojobs import create_scheduler

# ----------------------------Bot-Start---------------------------- #

loop = asyncio.get_event_loop()

# Function to schedule expiry checks
async def schedule_expiry_check():
    scheduler = await create_scheduler()
    while True:
        await scheduler.spawn(check_and_remove_expired_users())
        await asyncio.sleep(60)  # Check every hour
        gc.collect()

async def devggn_boot():
    for all_module in ALL_MODULES:
        importlib.import_module("RestrictDL.modules." + all_module)
    print("""
---------------------------------------------------
📂 Bot Deployed successfully ...
📝 Description: A Pyrogram bot for downloading files from Telegram channels or groups 
                and uploading them back to Telegram.

👨‍💻 Main Author: Devgagan
👨‍💻 Update Author: Abir Arafat Chawdhury
🌐 GitHub: https://github.com/abirxdhack
📬 Telegram: https://t.me/abirxdhackz
▶️ YouTube: https://youtube.com/@abirxdhackz
🗓️ Created: 2025-01-11
🔄 Last Modified: 2025-29-3
🛠️ Version: 5.0 HexaDLBot
📜 License: MIT License
---------------------------------------------------
""")

    asyncio.create_task(schedule_expiry_check())
    print("Auto removal started ...")
    await idle()
    print("Bot stopped...")


if __name__ == "__main__":
    loop.run_until_complete(devggn_boot())

# ------------------------------------------------------------------ #
