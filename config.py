

from os import getenv

# VPS --- FILL COOKIES 🍪 in """ ... """ 

INST_COOKIES = """
# wtite up here insta cookies
"""

YTUB_COOKIES = """
# write here yt cookies
"""

API_ID = int(getenv("API_ID", "28735699"))
API_HASH = getenv("API_HASH", "2e19c326d8cb322df7c15d7b7e84d1f3")
BOT_TOKEN = getenv("BOT_TOKEN", "8419506999:AAGHxYoprCCZIc1Cam2bk0ecHRiwLl9gkJw")
OWNER_ID = list(map(int, getenv("OWNER_ID", "6573328336 7852142757").split()))
MONGO_DB = getenv("MONGO_DB", "mongodb+srv://ridhatlog:RcZ4EVi6hzwSaarZ@cluster0.dxj0ntg.mongodb.net/?retryWrites=true&w=majority")
#LOG_GROUP = getenv("LOG_GROUP", "-1002879768901")
CHANNEL_ID = int(getenv("CHANNEL_ID", "-1002504099057"))
FREEMIUM_LIMIT = int(getenv("FREEMIUM_LIMIT", "500"))
PREMIUM_LIMIT = int(getenv("PREMIUM_LIMIT", "500"))
WEBSITE_URL = getenv("WEBSITE_URL", "")
AD_API = getenv("AD_API", "")
STRING = getenv("STRING", None)
YT_COOKIES = getenv("YT_COOKIES", YTUB_COOKIES)
DEFAULT_SESSION = getenv("DEFAUL_SESSION", None)  # added old method of invite link joining
INSTA_COOKIES = getenv("INSTA_COOKIES", INST_COOKIES)
