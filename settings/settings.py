from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    DISCORD_CODE: str
    DISCORD_GUILD_ID: int
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    DISCORD_REDIRECT_URI: str
    DISCORD_BOT_TOKEN: str
    # DISCORD_REFRESH_TOKEN: str

    YOUTUBE_CHANNEL_ID: str
    YOUTUBE_API_KEY: str
    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str
    YOUTUBE_REFRESH_TOKEN: str


SETTINGS = Settings()
