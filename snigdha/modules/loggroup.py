from pyrogram import filters
from snigdha import app
from config import OWNER_ID
from snigdha.core.mongo.config_db import set_log_group, get_log_group, delete_log_group

@app.on_message(filters.command("addlog") & filters.user(OWNER_ID))
async def add_log_group(client, message):
    if len(message.command) < 2:
        await message.reply("Usage: `/addlog -100xxxxxxxxx`")
        return
    log_group_id = message.command[1]
    await set_log_group(log_group_id)
    await message.reply(f"✅ Log group set to `{log_group_id}`.")

@app.on_message(filters.command("dellog") & filters.user(OWNER_ID))
async def del_log_group(client, message):
    await delete_log_group()
    await message.reply("✅ Log group deleted.")

@app.on_message(filters.command("logch") & filters.user(OWNER_ID))
async def show_log_group(client, message):
    log_group_id = await get_log_group()
    if log_group_id:
        try:
            chat = await client.get_chat(int(log_group_id))
            title = chat.title if hasattr(chat, "title") else "<No Title>"
            await message.reply(
                f"Current log group:\n\n"
                f"**Title:** {title}\n"
                f"**ID:** `{log_group_id}`"
            )
        except Exception as e:
            await message.reply(
                f"Current log group ID: `{log_group_id}`\n\n"
                f"Could not fetch channel info: `{e}`"
            )
    else:
        await message.reply("No log group is currently set.")
