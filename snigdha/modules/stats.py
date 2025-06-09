import time
import sys
import psutil
from pyrogram import filters
from snigdha import app

start_time = time.time()

def time_formatter():
    seconds = int(time.time() - start_time)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((f"{days}d ") if days else "")
        + ((f"{hours}h ") if hours else "")
        + ((f"{minutes}m ") if minutes else "")
        + ((f"{seconds}s") if seconds else "")
    )
    return tmp.strip() or "0s"

@app.on_message(filters.command("stats") & filters.private)
async def stats(client, message):
    try:
        start = time.time()
        ping = round((time.time() - start) * 1000, 2)
        bot = await client.get_me()
        
        # Get storage stats
        disk = psutil.disk_usage('/')
        total_storage = round(disk.total / (1024 ** 3), 2)  # Convert to GB
        used_storage = round(disk.used / (1024 ** 3), 2)
        free_storage = round(disk.free / (1024 ** 3), 2)
        
        # Get memory stats
        memory = psutil.virtual_memory()
        total_memory = round(memory.total / (1024 ** 3), 2)  # Convert to GB
        used_memory = round(memory.used / (1024 ** 3), 2)
        free_memory = round(memory.free / (1024 ** 3), 2)
        
        await message.reply_text(
            f"""
💥 **Smart Tools Server Stats** 💥
✘━━━━━━━━━━━━━✘
🌐 **Server Connection:**
- 💫 **Ping**: {ping} ms ✨
- 🌟 **Bot Status**: Online 🔥
- 👀 **Server Uptime**: {time_formatter()} 🇧🇩
✘━━━━━━━━━━━━━✘
💾 **Server Storage:**
- ❄️ **Total**: {total_storage} GB ✨
- 💥 **Used**: {used_storage} GB 🌟
- 🌐 **Available**: {free_storage} GB 🔥
✘━━━━━━━━━━━━━✘
🧠 **Memory Usage:**
- 💫 **Total**: {total_memory} GB 🇧🇩
- ❄️ **Used**: {used_memory} GB ✨
- 👀 **Available**: {free_memory} GB 🌟
            """
        )
    except Exception as e:
        await message.reply_text(f"Error retrieving stats: {str(e)}")