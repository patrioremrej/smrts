from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import ChannelInvalid, ChannelPrivate, PeerIdInvalid
from pyrogram.enums import ParseMode
import re
import asyncio
import aiofiles
from config import COMMAND_PREFIXES
from utils import LOGGER
from core.mongo import get_db

@Client.on_message(filters.command("dl", prefixes=COMMAND_PREFIXES))
async def download_content(client: Client, message: Message):
    LOGGER.info(f"Received /dl command from user {message.from_user.id} with URL: {message.command[1] if len(message.command) > 1 else 'None'}")
    
    if len(message.command) < 2:
        LOGGER.warning("No URL provided in /dl command")
        await client.send_message(
            message.chat.id,
            "**Please Provide A Valid URL**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    url = message.command[1]
    
    # Extract chat_id and message_id from URL
    try:
        # Handle both t.me and telegram.me URLs, including private links (t.me/c/)
        match = re.match(r"(?:https?://)?(?:t\.me|telegram\.me)/(?:c/)?([^/]+)/(\d+)", url)
        if not match:
            LOGGER.warning(f"Invalid URL format: {url}")
            await client.send_message(
                message.chat.id,
                "**Invalid URL Provided Bro**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        chat_id = match.group(1)
        message_id = int(match.group(2))

        # Check if it's a private link (t.me/c/)
        is_private = "c/" in url
        if is_private:
            chat_id = f"-100{chat_id[2:]}"
            # Check if user is logged in
            db = get_db()
            user_data = db.users.find_one({"user_id": message.from_user.id})
            if not user_data:
                LOGGER.warning(f"User {message.from_user.id} not logged in for private /dl command")
                await client.send_message(
                    message.chat.id,
                    "**Bro Please Login First /login**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            # Private links are handled by /d command
            await client.send_message(
                message.chat.id,
                "**Please use /d for private links!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Handle public links
        if not chat_id.startswith("@"):
            chat_id = f"@{chat_id}"

        LOGGER.info(f"Processing public download from chat {chat_id}, message ID {message_id}")
        
        # Send processing message
        processing_msg = await client.send_message(
            message.chat.id,
            "**Downloading Restricted Media**",
            parse_mode=ParseMode.MARKDOWN
        )

        # Small delay to prevent rate-limiting
        await asyncio.sleep(0.1)

        # Try to copy the message
        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            LOGGER.info(f"Successfully copied message {message_id} from {chat_id} to user {message.from_user.id}")
            # Edit the processing message to success
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**Media Downloaded Successfully!**",
                parse_mode=ParseMode.MARKDOWN
            )
        except ChannelInvalid:
            LOGGER.error(f"Invalid channel or group: {chat_id}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**Invalid channel or group! Please ensure it's public and accessible.**",
                parse_mode=ParseMode.MARKDOWN
            )
        except ChannelPrivate:
            LOGGER.error(f"Private channel or group: {chat_id}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**This is a private channel or group! Please use /d after logging in with /login.**",
                parse_mode=ParseMode.MARKDOWN
            )
        except PeerIdInvalid:
            LOGGER.error(f"Invalid chat ID: {chat_id}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**Invalid chat ID! Please check the URL and try again.**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            LOGGER.error(f"Error copying message from {chat_id}: {str(e)}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text=f"**An error occurred: {str(e)}**",
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        LOGGER.error(f"Failed to process URL {url}: {str(e)}")
        await client.send_message(
            message.chat.id,
            f"**Failed to process the URL: {str(e)}**",
            parse_mode=ParseMode.MARKDOWN
        )