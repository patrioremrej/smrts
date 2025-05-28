# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client
from utils import LOGGER
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN
)

# Log the creation of the bot client
LOGGER.info("Creating Bot Client From BOT_TOKEN")

# Initialize the Pyrogram Client with plugins
app = Client(
    "SmartTools",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000,
    plugins={"root": "plugins"}  # Specify the plugins folder
)

# Log successful creation of the bot client
LOGGER.info("Bot Client Created Successfully!")