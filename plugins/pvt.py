from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from pyrogram.errors import ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid, ChannelInvalid, ChannelPrivate, PeerIdInvalid
from pyrogram.enums import ParseMode
from pyrogram.utils import get_channel_id
from pyrogram.parser import Parser
from pyleaves import Leaves
import re
import asyncio
import aiofiles
import aiofiles.os
from time import time
from PIL import Image
from config import COMMAND_PREFIXES
from utils import LOGGER
from core.mongo import get_db
import json
import subprocess

# Constants for timeouts
TIMEOUT_OTP = 600  # 10 minutes
TIMEOUT_2FA = 300  # 5 minutes

# Store user sessions temporarily during login
temp_sessions = {}

# Progress bar template
PROGRESS_BAR = """
Percentage: {percentage:.2f}% | {current}/{total}
Speed: {speed}/s
Estimated Time Left: {est_time} seconds
"""

def getChatMsgID(link: str):
    """Parse Telegram URL to extract chat_id and message_id."""
    linkps = link.split("/")
    chat_id, message_thread_id, message_id = None, None, None
    
    try:
        if len(linkps) == 7 and linkps[3] == "c":
            # https://t.me/c/1192302355/322/487
            chat_id = get_channel_id(int(linkps[4]))
            message_thread_id = int(linkps[5])
            message_id = int(linkps[6])
        elif len(linkps) == 6:
            if linkps[3] == "c":
                # https://t.me/c/1387666944/609282
                chat_id = get_channel_id(int(linkps[4]))
                message_id = int(linkps[5])
            else:
                # https://t.me/TheForum/322/487
                chat_id = f"@{linkps[3]}"
                message_thread_id = int(linkps[4])
                message_id = int(linkps[5])
        elif len(linkps) == 5:
            # https://t.me/pyrogramchat/609282
            chat_id = f"@{linkps[3]}"
            if chat_id == "@m":
                raise ValueError("Invalid ClientType used to parse this message link")
            message_id = int(linkps[4])
    except (ValueError, TypeError):
        raise ValueError("Invalid post URL. Must end with a numeric ID.")

    if not chat_id or not message_id:
        raise ValueError("Please send a valid Telegram post URL.")

    return chat_id, message_id

async def get_parsed_msg(text, entities):
    """Unparse message text with entities."""
    return Parser.unparse(text, entities or [], is_html=False)

async def get_media_info(path):
    """Get media duration, artist, and title using ffprobe."""
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", "-hide_banner", "-loglevel", "error", "-print_format", "json",
            "-show_format", path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0 and stdout:
            fields = json.loads(stdout.decode()).get("format", {})
            duration = round(float(fields.get("duration", 0)))
            tags = fields.get("tags", {})
            artist = tags.get("artist") or tags.get("ARTIST") or tags.get("Artist")
            title = tags.get("title") or tags.get("TITLE") or tags.get("Title")
            return duration, artist, title
        LOGGER.error(f"ffprobe failed for {path}: {stderr.decode()}")
        return 0, None, None
    except Exception as e:
        LOGGER.error(f"Get Media Info failed for {path}: {str(e)}")
        return 0, None, None

async def get_video_thumbnail(video_file, duration):
    """Generate a thumbnail for a video using ffmpeg."""
    output = os.path.join("Assets", f"video_thumb_{int(time())}.jpg")
    if duration is None:
        duration = (await get_media_info(video_file))[0]
    if duration == 0:
        duration = 3
    duration = duration // 2
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-ss", f"{duration}", "-i", video_file,
        "-vf", "thumbnail", "-q:v", "1", "-frames:v", "1",
        "-threads", f"{os.cpu_count() // 2}", output
    ]
    try:
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        if process.returncode != 0 or not await aiofiles.os.path.exists(output):
            LOGGER.error(f"Thumbnail extraction failed for {video_file}: {stderr.decode()}")
            return None
        return output
    except asyncio.TimeoutError:
        LOGGER.error(f"Thumbnail extraction timed out for {video_file}")
        return None
    except Exception as e:
        LOGGER.error(f"Thumbnail extraction failed for {video_file}: {str(e)}")
        return None

async def send_media(client, message, media_path, media_type, caption, progress_message, start_time):
    """Send media to the user with progress tracking."""
    progress_args = ("📥 Uploading Progress", progress_message, start_time, PROGRESS_BAR, "▓", "░")
    try:
        if not await aiofiles.os.path.exists(media_path):
            LOGGER.error(f"Media file {media_path} does not exist")
            return
        if media_type == "photo":
            await client.send_photo(
                chat_id=message.chat.id,
                photo=media_path,
                caption=caption or "",
                progress=Leaves.progress_for_pyrogram,
                progress_args=progress_args,
            )
        elif media_type == "video":
            duration = (await get_media_info(media_path))[0]
            thumb = await get_video_thumbnail(media_path, duration)
            width, height = (480, 320) if not thumb else Image.open(thumb).size
            await client.send_video(
                chat_id=message.chat.id,
                video=media_path,
                duration=duration,
                width=width,
                height=height,
                thumb=thumb,
                caption=caption or "",
                progress=Leaves.progress_for_pyrogram,
                progress_args=progress_args,
            )
            if thumb and await aiofiles.os.path.exists(thumb):
                await aiofiles.os.remove(thumb)
        elif media_type == "audio":
            duration, artist, title = await get_media_info(media_path)
            await client.send_audio(
                chat_id=message.chat.id,
                audio=media_path,
                duration=duration,
                performer=artist,
                title=title,
                caption=caption or "",
                progress=Leaves.progress_for_pyrogram,
                progress_args=progress_args,
            )
        elif media_type == "document":
            await client.send_document(
                chat_id=message.chat.id,
                document=media_path,
                caption=caption or "",
                progress=Leaves.progress_for_pyrogram,
                progress_args=progress_args,
            )
    finally:
        if await aiofiles.os.path.exists(media_path):
            await aiofiles.os.remove(media_path)

async def processMediaGroup(chat_message, bot, message):
    """Process and send a media group."""
    media_group_messages = await chat_message.get_media_group()
    valid_media = []
    temp_paths = []
    invalid_paths = []

    start_time = time()
    progress_message = await message.reply("📥 Downloading media group...")
    LOGGER.info(f"Downloading media group with {len(media_group_messages)} items...")

    for msg in media_group_messages:
        if msg.photo or msg.video or msg.document or msg.audio:
            try:
                media_path = await msg.download(
                    progress=Leaves.progress_for_pyrogram,
                    progress_args=(
                        "📥 Downloading Progress",
                        progress_message,
                        start_time,
                        PROGRESS_BAR,
                        "▓",
                        "░"
                    ),
                )
                if media_path and await aiofiles.os.path.exists(media_path):
                    temp_paths.append(media_path)
                else:
                    LOGGER.error(f"Failed to download media for message {msg.id}")
                    continue

                if msg.photo:
                    valid_media.append(
                        InputMediaPhoto(
                            media=media_path,
                            caption=await get_parsed_msg(
                                msg.caption or "", msg.caption_entities
                            ),
                        )
                    )
                elif msg.video:
                    valid_media.append(
                        InputMediaVideo(
                            media=media_path,
                            caption=await get_parsed_msg(
                                msg.caption or "", msg.caption_entities
                            ),
                        )
                    )
                elif msg.document:
                    valid_media.append(
                        InputMediaDocument(
                            media=media_path,
                            caption=await get_parsed_msg(
                                msg.caption or "", msg.caption_entities
                            ),
                        )
                    )
                elif msg.audio:
                    valid_media.append(
                        InputMediaAudio(
                            media=media_path,
                            caption=await get_parsed_msg(
                                msg.caption or "", msg.caption_entities
                            ),
                        )
                    )

            except Exception as e:
                LOGGER.info(f"Error downloading media: {e}")
                if media_path and await aiofiles.os.path.exists(media_path):
                    invalid_paths.append(media_path)
                continue

    LOGGER.info(f"Valid media count: {len(valid_media)}")

    if valid_media:
        try:
            await bot.send_media_group(chat_id=message.chat.id, media=valid_media)
            await progress_message.delete()
        except Exception:
            await message.reply("**❌ Failed to send media group, trying individual uploads**")
            for media in valid_media:
                try:
                    if isinstance(media, InputMediaPhoto):
                        await bot.send_photo(
                            chat_id=message.chat.id,
                            photo=media.media,
                            caption=media.caption,
                        )
                    elif isinstance(media, InputMediaVideo):
                        await bot.send_video(
                            chat_id=message.chat.id,
                            video=media.media,
                            caption=media.caption,
                        )
                    elif isinstance(media, InputMediaDocument):
                        await bot.send_document(
                            chat_id=message.chat.id,
                            document=media.media,
                            caption=media.caption,
                        )
                    elif isinstance(media, InputMediaAudio):
                        await bot.send_audio(
                            chat_id=message.chat.id,
                            audio=media.media,
                            caption=media.caption,
                        )
                except Exception as individual_e:
                    await message.reply(f"Failed to upload individual media: {individual_e}")
            await progress_message.delete()

        for path in temp_paths:
            if await aiofiles.os.path.exists(path):
                await aiofiles.os.remove(path)
        for path in invalid_paths:
            if await aiofiles.os.path.exists(path):
                await aiofiles.os.remove(path)

        return True

    await progress_message.delete()
    await message.reply("❌ No valid media found in the media group.")
    for path in invalid_paths:
        if await aiofiles.os.path.exists(path):
            await aiofiles.os.remove(path)
    return False

@Client.on_message(filters.command("login", prefixes=COMMAND_PREFIXES) & filters.private)
async def login_command(client: Client, message: Message):
    user_id = message.from_user.id
    LOGGER.info(f"Received /login command from user {user_id}")

    # Check if user is already logged in
    db = get_db()
    user_data = db.users.find_one({"user_id": user_id})
    if user_data:
        await client.send_message(
            message.chat.id,
            "**You're already logged in! Use /logout to clear your session.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Initialize session data
    temp_sessions[user_id] = {"type": "Pyrogram"}
    await client.send_message(
        message.chat.id,
        "**💥 Welcome to the login setup!**\n"
        "**━━━━━━━━━━━━━━━━━**\n"
        "**This is a safe process. We store your session securely in our database to access private media.**\n\n"
        "**Note: Don't share your OTP or credentials publicly.**",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Start", callback_data="session_start_pyrogram"),
            InlineKeyboardButton("Close", callback_data="session_close")
        ]]),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^session_"))
async def callback_query_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if data == "session_close":
        await callback_query.message.edit_text(
            "**❌ Cancelled. You can start by sending /login.**",
            parse_mode=ParseMode.MARKDOWN
        )
        if user_id in temp_sessions:
            if "client" in temp_sessions[user_id]:
                await temp_sessions[user_id]["client"].stop()
            del temp_sessions[user_id]
        LOGGER.info(f"Login cancelled for user {user_id}")
        return

    if data == "session_start_pyrogram":
        temp_sessions[user_id] = {"type": "Pyrogram", "stage": "api_id"}
        await callback_query.message.edit_text(
            "**Send Your API ID**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                InlineKeyboardButton("Close", callback_data="session_close")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Login started for user {user_id}")

    if data == "session_restart_pyrogram":
        if user_id in temp_sessions and "client" in temp_sessions[user_id]:
            await temp_sessions[user_id]["client"].stop()
        temp_sessions[user_id] = {"type": "Pyrogram"}
        await callback_query.message.edit_text(
            "**💥 Welcome to the login setup!**\n"
            "**━━━━━━━━━━━━━━━━━**\n"
            "**This is a safe process. We store your session securely in our database to access private media.**\n\n"
            "**Note: Don't share your OTP or credentials publicly.**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Start", callback_data="session_start_pyrogram"),
                InlineKeyboardButton("Close", callback_data="session_close")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Login restarted for user {user_id}")

@Client.on_message(filters.text & filters.private & filters.create(lambda _, __, message: message.from_user.id in temp_sessions))
async def handle_login_input(client: Client, message: Message):
    user_id = message.from_user.id
    session = temp_sessions[user_id]
    stage = session.get("stage")
    chat_id = message.chat.id

    if stage == "api_id":
        try:
            api_id = int(message.text)
            session["api_id"] = api_id
            session["stage"] = "api_hash"
            LOGGER.info(f"Received API ID for user {user_id}")
            await client.send_message(
                chat_id,
                "**Send Your API Hash**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            LOGGER.error(f"Invalid API ID format for user {user_id}: {message.text}")
            await client.send_message(
                chat_id,
                "**❌ Invalid API ID. Please enter a valid integer.**",
                parse_mode=ParseMode.MARKDOWN
            )

    elif stage == "api_hash":
        session["api_hash"] = message.text
        session["stage"] = "phone_number"
        LOGGER.info(f"Received API Hash for user {user_id}")
        await client.send_message(
            chat_id,
            "**Send Your Phone Number (e.g., +1234567890)**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                InlineKeyboardButton("Close", callback_data="session_close")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )

    elif stage == "phone_number":
        phone_number = message.text
        session["phone_number"] = phone_number
        LOGGER.info(f"Received Phone Number for user {user_id}: {phone_number}")

        otp_message = await client.send_message(
            chat_id,
            "**💥 Sending OTP...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Create temporary client
            temp_client = Client(
                f"temp_{user_id}",
                api_id=session["api_id"],
                api_hash=session["api_hash"],
                in_memory=True
            )
            await temp_client.start()

            # Send OTP request
            sent_code = await temp_client.send_code(phone_number)
            session["client"] = temp_client
            session["phone_code_hash"] = sent_code.phone_code_hash
            session["stage"] = "otp"

            # Start OTP timeout task
            asyncio.create_task(handle_otp_timeout(client, message))

            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**✅ Send The OTP as text. Please send a text message embedding the OTP like: 'AB5 CD0 EF3 GH7 IJ6'**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )

        except ApiIdInvalid:
            LOGGER.error(f"Invalid API ID/Hash for user {user_id}")
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**❌ Invalid API ID or API Hash. Please try /login again.**",
                parse_mode=ParseMode.MARKDOWN
            )
            del temp_sessions[user_id]
        except PhoneNumberInvalid:
            LOGGER.error(f"Invalid phone number for user {user_id}: {phone_number}")
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**❌ Invalid phone number. Please try /login again.**",
                parse_mode=ParseMode.MARKDOWN
            )
            del temp_sessions[user_id]
        except Exception as e:
            LOGGER.error(f"Error sending OTP for user {user_id}: {str(e)}")
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                f"**❌ Error: {str(e)}. Please try /login again.**",
                parse_mode=ParseMode.MARKDOWN
            )
            del temp_sessions[user_id]
        finally:
            if "client" in session and session["client"].is_initialized:
                await session["client"].stop()

    elif stage == "otp":
        # Extract digits in sequence from the input
        otp = ''.join([char for char in message.text if char.isdigit()])[:5]  # Limit to 5 digits
        session["otp"] = otp
        LOGGER.info(f"Received OTP for user {user_id}: {otp}")

        otp_message = await client.send_message(
            chat_id,
            "**💥 Validating OTP...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            temp_client = session["client"]
            phone_number = session["phone_number"]
            phone_code_hash = session["phone_code_hash"]

            # Sign in
            await temp_client.start()
            await temp_client.sign_in(phone_number, phone_code_hash, otp)

            # Get session string
            session_string = await temp_client.export_session_string()

            # Save to MongoDB
            db = get_db()
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "api_id": session["api_id"],
                    "api_hash": session["api_hash"],
                    "phone_number": phone_number,
                    "session_string": session_string
                }},
                upsert=True
            )
            LOGGER.info(f"User {user_id} logged in successfully and data saved to MongoDB")

            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**✅ Login successful! You can now use /d to scrape private messages.**",
                parse_mode=ParseMode.MARKDOWN
            )

            await temp_client.stop()
            del temp_sessions[user_id]

        except SessionPasswordNeeded:
            session["stage"] = "2fa"
            LOGGER.info(f"2FA required for user {user_id}")
            asyncio.create_task(handle_2fa_timeout(client, message))
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**❌ 2FA is required. Please provide your 2FA password.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
        except PhoneCodeInvalid:
            LOGGER.error(f"Invalid OTP for user {user_id}")
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**❌ OTP is wrong! Please try /login again.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await temp_client.stop()
            del temp_sessions[user_id]
        except PhoneCodeExpired:
            LOGGER.error(f"Expired OTP for user {user_id}")
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                "**❌ OTP has expired! Please try /login again.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await temp_client.stop()
            del temp_sessions[user_id]
        except Exception as e:
            LOGGER.error(f"Login failed for user {user_id}: {str(e)}")
            await client.edit_message_text(
                chat_id,
                otp_message.id,
                f"**❌ Failed: {str(e)}. Please try /login again.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await temp_client.stop()
            del temp_sessions[user_id]

    elif stage == "2fa":
        password = message.text
        LOGGER.info(f"Received 2FA password for user {user_id}")

        try:
            temp_client = session["client"]
            await temp_client.start()
            await temp_client.check_password(password)
            session_string = await temp_client.export_session_string()

            # Save to MongoDB
            db = get_db()
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "api_id": session["api_id"],
                    "api_hash": session["api_hash"],
                    "phone_number": session["phone_number"],
                    "session_string": session_string
                }},
                upsert=True
            )
            LOGGER.info(f"User {user_id} logged in with 2FA and data saved to MongoDB")

            await client.send_message(
                chat_id,
                "**✅ Login successful! You can now use /d to scrape private messages.**",
                parse_mode=ParseMode.MARKDOWN
            )

            await temp_client.stop()
            del temp_sessions[user_id]

        except PasswordHashInvalid:
            LOGGER.error(f"Invalid 2FA password for user {user_id}")
            await client.send_message(
                chat_id,
                "**❌ Invalid password provided! Please try /login again.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await temp_client.stop()
            del temp_sessions[user_id]
        except Exception as e:
            LOGGER.error(f"2FA login failed for user {user_id}: {str(e)}")
            await client.send_message(
                chat_id,
                f"**❌ Failed: {str(e)}. Please try /login again.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data="session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await temp_client.stop()
            del temp_sessions[user_id]

async def handle_otp_timeout(client, message):
    user_id = message.from_user.id
    await asyncio.sleep(TIMEOUT_OTP)
    if user_id in temp_sessions and temp_sessions[user_id].get("stage") == "otp":
        await client.send_message(
            message.chat.id,
            "**❌ OTP input has expired! Please try /login again.**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"OTP timed out for user {user_id}")
        if "client" in temp_sessions[user_id]:
            await temp_sessions[user_id]["client"].stop()
        del temp_sessions[user_id]

async def handle_2fa_timeout(client, message):
    user_id = message.from_user.id
    await asyncio.sleep(TIMEOUT_2FA)
    if user_id in temp_sessions and temp_sessions[user_id].get("stage") == "2fa":
        await client.send_message(
            message.chat.id,
            "**❌ 2FA input has expired! Please try /login again.**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"2FA timed out for user {user_id}")
        if "client" in temp_sessions[user_id]:
            await temp_sessions[user_id]["client"].stop()
        del temp_sessions[user_id]

@Client.on_message(filters.command("logout", prefixes=COMMAND_PREFIXES) & filters.private)
async def logout_command(client: Client, message: Message):
    user_id = message.from_user.id
    LOGGER.info(f"Received /logout command from user {user_id}")

    db = get_db()
    result = db.users.delete_one({"user_id": user_id})
    if result.deleted_count > 0:
        LOGGER.info(f"User {user_id} logged out and data removed from MongoDB")
        await client.send_message(
            message.chat.id,
            "**✅ Successfully logged out! Your data has been cleared.**",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        LOGGER.info(f"User {user_id} attempted logout but no data found")
        await client.send_message(
            message.chat.id,
            "**❌ You are not logged in!**",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command("d", prefixes=COMMAND_PREFIXES) & filters.private)
async def download_private_content(client: Client, message: Message):
    user_id = message.from_user.id
    LOGGER.info(f"Received /d command from user {user_id} with URL: {message.command[1] if len(message.command) > 1 else 'None'}")

    # Check if user is logged in
    db = get_db()
    user_data = db.users.find_one({"user_id": user_id})
    if not user_data:
        LOGGER.warning(f"User {user_id} not logged in for /d command")
        await client.send_message(
            message.chat.id,
            "**Bro Please Login First /login**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if len(message.command) < 2:
        LOGGER.warning("No URL provided in /d command")
        await client.send_message(
            message.chat.id,
            "**Please Provide A Valid URL**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    url = message.command[1]

    # Extract chat_id and message_id from URL
    try:
        chat_id, message_id = getChatMsgID(url)
        LOGGER.info(f"Processing private download from chat {chat_id}, message ID {message_id}")

        # Send processing message
        processing_msg = await client.send_message(
            message.chat.id,
            "**Downloading Restricted Media...**",
            parse_mode=ParseMode.MARKDOWN
        )

        # Small delay to prevent rate-limiting
        await asyncio.sleep(0.1)

        # Create user client from stored session
        user_client = Client(
            f"user_{user_id}_{int(time())}",  # Unique session name
            session_string=user_data["session_string"],
            in_memory=True
        )

        try:
            await user_client.start()

            # Verify chat access
            try:
                chat = await user_client.get_chat(chat_id)
                LOGGER.info(f"User {user_id} has access to chat {chat_id} (Title: {chat.title})")
            except PeerIdInvalid:
                LOGGER.error(f"Invalid chat ID {chat_id} for user {user_id}")
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=processing_msg.id,
                    text="**Invalid chat ID! Please check the URL or ensure you have access.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            except ChannelPrivate:
                LOGGER.error(f"Private channel access denied: {chat_id}")
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=processing_msg.id,
                    text="**You don't have access to this private channel or group!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            finally:
                if user_client.is_initialized:
                    await user_client.stop()

            # Check if the message exists
            async with Client(
                f"user_{user_id}_{int(time())}",
                session_string=user_data["session_string"],
                in_memory=True
            ) as msg_client:
                chat_message = await msg_client.get_messages(chat_id, message_id)
                if not chat_message:
                    LOGGER.warning(f"No message found for ID {message_id} in chat {chat_id}")
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=processing_msg.id,
                        text="**No message found for the given ID!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return

                # Handle media group
                if chat_message.media_group_id:
                    success = await processMediaGroup(chat_message, client, message)
                    if not success:
                        await client.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=processing_msg.id,
                            text="**Failed to process media group!**",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    return

                # Handle single media message
                if not (chat_message.photo or chat_message.video or chat_message.document or chat_message.audio):
                    LOGGER.warning(f"No media found in message {message_id} from {chat_id}")
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=processing_msg.id,
                        text="**No media found in this message!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return

                # Download and send media
                start_time = time()
                caption = await get_parsed_msg(chat_message.caption or "", chat_message.caption_entities)
                media_type = (
                    "photo" if chat_message.photo else
                    "video" if chat_message.video else
                    "audio" if chat_message.audio else
                    "document"
                )
                media_path = await chat_message.download(
                    progress=Leaves.progress_for_pyrogram,
                    progress_args=(
                        "📥 Downloading Progress",
                        processing_msg,
                        start_time,
                        PROGRESS_BAR,
                        "▓",
                        "░"
                    ),
                )
                if not media_path or not await aiofiles.os.path.exists(media_path):
                    LOGGER.error(f"Failed to download media for message {message_id} from {chat_id}")
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=processing_msg.id,
                        text="**Failed to download media!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return

                await send_media(client, message, media_path, media_type, caption, processing_msg, start_time)
                LOGGER.info(f"Successfully sent media from message {message_id} in chat {chat_id} to user {user_id}")

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
                text="**Invalid channel or group! Please ensure you have access.**",
                parse_mode=ParseMode.MARKDOWN
            )
        except ChannelPrivate:
            LOGGER.error(f"Private channel or group access denied: {chat_id}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**You don't have access to this private channel or group!**",
                parse_mode=ParseMode.MARKDOWN
            )
        except PeerIdInvalid:
            LOGGER.error(f"Invalid chat ID: {chat_id}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**Invalid chat ID! Please check the URL or ensure you have access.**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            LOGGER.error(f"Error processing media from {chat_id}: {str(e)}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text=f"**An error occurred: {str(e)}**",
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            if user_client.is_initialized:
                await user_client.stop()

    except ValueError as e:
        LOGGER.error(f"Failed to process URL {url}: {str(e)}")
        await client.send_message(
            message.chat.id,
            f"**Failed to process the URL: {str(e)}**",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        LOGGER.error(f"Unexpected error processing URL {url}: {str(e)}")
        await client.send_message(
            message.chat.id,
            f"**Unexpected error: {str(e)}**",
            parse_mode=ParseMode.MARKDOWN
        )
