# Note if you are trying to deploy on vps then directly fill values in ("")

from os import getenv

# VPS --- FILL COOKIES 🍪 in """ ... """ 

INST_COOKIES = """
# wtite up here insta cookies
"""

YTUB_COOKIES = """
#Write Cookies Here
"""

API_ID = int(getenv("API_ID", "2820"))
API_HASH = getenv("API_HASH", "7fc5b3569245497ab5eca3")
BOT_TOKEN = getenv("BOT_TOKEN", "8019809817:AAHNHK9inNi04DQx8hk0uE4")
OWNER_ID = list(map(int, getenv("OWNER_ID", "7303810912").split()))
MONGO_DB = getenv("MONGO_DB", "mongodb+srv://ytpremium4434360:zxx1VPDzGW96Nrites=true&w=majority&appName=ItsSmartToolBot")
LOG_GROUP = getenv("LOG_GROUP", "-10017356")
CHANNEL_ID = int(getenv("CHANNEL_ID", "-1002183077"))
FREEMIUM_LIMIT = int(getenv("FREEMIUM_LIMIT", "0"))
PREMIUM_LIMIT = int(getenv("PREMIUM_LIMIT", "500"))
WEBSITE_URL = getenv("WEBSITE_URL", "upshrink.com")
AD_API = getenv("AD_API", "52b4a2cf4687d81e7d3f8f8e78cb")
STRING = getenv("STRING", None)
YT_COOKIES = getenv("YT_COOKIES", YTUB_COOKIES)
DEFAULT_SESSION = getenv("DEFAUL_SESSION", None)  # added old method of invite link joining
INSTA_COOKIES = getenv("INSTA_COOKIES", INST_COOKIES)
