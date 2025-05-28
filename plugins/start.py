from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import UpdatesChannel, DEV_USER_ID, COMMAND_PREFIXES

@Client.on_message(filters.command("start", prefixes=COMMAND_PREFIXES))
async def start_command(client, message):
    start_text = (
        "**👋 Welcome to SataBot! 🚀**\n\n"
        "I'm here to **help you download restricted content** from **public Telegram channels and groups**! 🎉\n"
        "Use **/dl <URL>** to download content from public channels.\n\n"
        "**Stay updated** with our channel and feel free to **contact the developer**! 😎"
    )
    
    buttons = [
        [
            InlineKeyboardButton("Updates Channel 📢", url=UpdatesChannel),
            InlineKeyboardButton("Dev 👨‍💻", user_id=DEV_USER_ID)
        ]
    ]
    
    await client.send_photo(
        chat_id=message.chat.id,
        photo="resources/start.jpg",
        caption=start_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )