from discord import Intents

from discord_api.api import Client
from settings import SETTINGS


def main():
    intents = Intents.default()
    intents.message_content = True
    client = Client(intents=intents)
    client.run(SETTINGS.DISCORD_BOT_TOKEN)


if __name__ == '__main__':
    main()


