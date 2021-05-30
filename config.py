import os

from dotenv import load_dotenv

if os.path.exists("local.env"):
    load_dotenv("local.env")
   

class Config(object):
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", None)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
    CHAT_ID = int(os.environ.get("CHAT_ID", 0))
    PORT = int(os.environ.get("PORT", "8443"))
    HOST = os.environ.get("HOST", "0.0.0.0")
    HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", None)
    PING_TIME = int(os.environ.get("PING_TIME", 10))
