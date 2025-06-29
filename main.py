from discord import Intents

from discord_api.api import Client
from settings import SETTINGS
from youtube_api.api import YOUTUBE_API


def main():
    intents = Intents.default()
    intents.message_content = True
    client = Client(intents=intents)
    client.run(SETTINGS.DISCORD_BOT_TOKEN)
    # print(YOUTUBE_API.refresh_token)
    # YOUTUBE_API.refresh_access_token()


if __name__ == '__main__':
    main()


