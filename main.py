import asyncio
import random
import re
from datetime import datetime, timedelta
from enum import StrEnum

import discord
from discord import Message, Embed, Button, Interaction, FFmpegPCMAudio
from discord.ui import View
from pydantic import BaseModel

from logger import logger
from settings import SETTINGS
from youtube_api.api import YOUTUBE_API
from youtube_api.models import Video


class Action(StrEnum):
    PLAY = "play"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    SKIP = "skip"
    QUEUE = "queue"
    CLEAR = "clear"
    DISCONNECT = "disconnect"
    HELP = "help"


COMMANDS = {
    Action.PLAY: ["play", "pone", "pon", "poneme", "ponme"],
    Action.PAUSE: [
        "pause",
        "pausa",
        "aguanta",
        "espera",
        "pera",
        "para",
        "cortala",
        "deja de joder",
        "no",
        "basta",
    ],
    Action.RESUME: ["resume", "resumir", "resumime", "segui", "dale", "mandale"],
    Action.STOP: ["stop"],
    Action.SKIP: ["skip", "saltear", "salta", "siguiente", "sig", "next"],
    Action.QUEUE: ["queue", "cola", "list"],
    Action.CLEAR: ["clear", "lavate la cola", "limpiate la cola"],
    Action.DISCONNECT: ["disconnect", "desconectar", "salir", "chau", "vete", "raja"],
    Action.HELP: ["help", "ayuda", "comandos", "commands", "halluda"],
}

COMMANDS_HELP = {
    Action.PLAY: "Reproduce una canción. Puede ser una URL de YouTube, un nombre de canción o un nombre de playlist",
    Action.PAUSE: "Pausa la canción actual",
    Action.RESUME: "Reanuda la canción pausada",
    Action.STOP: "Detiene la canción actual",
    Action.SKIP: "Salta a la siguiente canción",
    Action.QUEUE: "Muestra la cola de canciones",
    Action.CLEAR: "Limpia la cola de canciones",
    Action.DISCONNECT: "Desconecta al bot del canal de voz",
    Action.HELP: "Muestra esta ayuda",
}


class Command(BaseModel):
    action: Action
    query: str

    def is_youtube_video(self) -> bool:
        youtube_regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.*(v|e(?:mbed)?)\S+"
        return bool(re.match(youtube_regex, self.query))

    def is_youtube_playlist(self) -> bool:
        playlist_regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=[\w-]+&list=[\w-]+|playlist\?list=[\w-]+)"
        return bool(re.match(playlist_regex, self.query))


class PlaySelector(View):
    def __init__(self, message: Message, videos: list[Video], client: "MyClient"):
        super().__init__()
        self.source_message = message
        self.videos = videos
        self.client = client

    @discord.ui.button(label="▶ 1", style=discord.ButtonStyle.success)
    async def video_play_0(self, interaction: Interaction, button: Button):
        await self.handle_button_click(
            interaction=interaction, button=button, video=self.videos[0]
        )

    @discord.ui.button(label="▶ 2", style=discord.ButtonStyle.success)
    async def video_play_1(self, interaction: Interaction, button: Button):
        await self.handle_button_click(
            interaction=interaction, button=button, video=self.videos[1]
        )

    @discord.ui.button(label="▶ 3", style=discord.ButtonStyle.success)
    async def video_play_2(self, interaction: Interaction, button: Button):
        await self.handle_button_click(
            interaction=interaction, button=button, video=self.videos[2]
        )

    @discord.ui.button(label="▶ 4", style=discord.ButtonStyle.success)
    async def video_play_3(self, interaction: Interaction, button: Button):
        await self.handle_button_click(
            interaction=interaction, button=button, video=self.videos[3]
        )

    @discord.ui.button(label="▶ 5", style=discord.ButtonStyle.success)
    async def video_play_4(self, interaction: Interaction, button: Button):
        await self.handle_button_click(
            interaction=interaction, button=button, video=self.videos[4]
        )

    async def handle_button_click(
        self, button: Button, interaction: Interaction, video: Video
    ):
        logger.info(f"Button {button.label} clicked by {interaction.user}. Video selected: {video}")
        await interaction.response.send_message(f"Video seleccionado: {video.label}", ephemeral=True)
        await self.client.add_to_queue(video=video, message=self.source_message)
        await interaction.delete_original_response()
        await interaction.message.delete()


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_keywords = ["faka ", "f "]
        self.queue = []
        self.current_video = None
        self.voice_client = None
        self.channel = None
        self.handlers = {
            Action.PLAY: self.handle_play,
            Action.PAUSE: self.handle_pause,
            Action.RESUME: self.handle_resume,
            Action.STOP: self.handle_stop,
            Action.SKIP: self.handle_skip,
            Action.QUEUE: self.handle_queue,
            Action.CLEAR: self.handle_clear,
            Action.DISCONNECT: self.handle_disconnect,
            Action.HELP: self.handle_help,
        }
        self.last_playing = None

    async def on_ready(self):
        logger.info(f"Logged on as {self.user}!")
        self.channel = discord.utils.get(self.get_all_channels(), name="faka-dj")
        # one time delete all messages that happened after 20 pm of yesterday
        # yesterday = (datetime.now() - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
        # async for message in self.channel.history(after=yesterday):
        #     logger.info(f"Deleting message. Created at: '{message.created_at}'. Author: '{message.author}'. Content: '{message.content}'")
        #     await message.delete()
        #     await asyncio.sleep(1)

    async def on_message(self, message: Message):
        command = await self.get_command(message=message)
        await self.handle_command(message=message, command=command)

    async def on_voice_state_update(self, member, before, after):
        # Check if the bot itself disconnected from a voice channel
        if member == self.user and before.channel is not None and after.channel is None:
            logger.warning(
                f"The bot disconnected from voice channel: {before.channel.name}"
            )
            self.voice_client = None

    async def get_command(self, message: Message) -> Command | None:
        if message.author == self.user:
            return None

        content = message.content.strip()
        start_keyword = None
        for keyword in self.start_keywords:
            if content.casefold().startswith(keyword):
                start_keyword = keyword
                break
        if start_keyword is None:
            return None

        if message.author.voice is None:
            await message.channel.send("Unite a un canal de voz primero")
            return None
        for command, options in COMMANDS.items():
            for option in options:
                if content.casefold().startswith(f"{start_keyword}{option}"):
                    return Command(
                        action=command,
                        query=content[len(start_keyword) + len(option) :].strip(),
                    )
        return None

    async def handle_command(self, message: Message, command: Command | None):
        if command is None:
            return
        logger.info(f"Received command: {command}")
        handler = self.handlers.get(command.action)
        if handler is None:
            return
        await handler(message=message, command=command)

    async def handle_play(self, message: Message, command: Command):
        if command.is_youtube_playlist():
            videos = YOUTUBE_API.get_playlist_videos_from_url(url=command.query)
            for video in videos:
                await self.add_to_queue(video=video, message=message)
            return
        elif command.is_youtube_video():
            video = YOUTUBE_API.get_video_from_url(url=command.query)
            await self.add_to_queue(video=video, message=message)
            return
        elif command.query != "":
            videos: list[Video] = YOUTUBE_API.search(query=command.query)
            embed = Embed(title="Encontré estas canciones:")
            embed.set_thumbnail(url=videos[0].thumbnail_url)
            for index, video in enumerate(videos, start=1):
                embed.add_field(name="", value=f"{index}) {video.label}", inline=False)
            await message.channel.send(
                embed=embed,
                view=PlaySelector(message=message, videos=videos, client=self),
            )
            return
        await self.handle_resume(message=message, command=command)

    async def handle_pause(self, message: Message, command: Command):
        embed = Embed(title="Pausando canción")
        embed.add_field(name="", value=self.current_video.label, inline=False)
        await message.channel.send(embed=embed)
        if self.voice_client is None and message.author.voice is not None:
            self.voice_client = await message.author.voice.channel.connect()
        self.voice_client.pause()

    async def handle_resume(self, message: Message, command: Command):
        embed = Embed(title="Resumiendo canción")

        if self.current_video:
            embed.add_field(name="", value=self.current_video.label, inline=False)
            await message.channel.send(embed=embed)
            if self.voice_client is None and message.author.voice is not None:
                self.voice_client = await message.author.voice.channel.connect()
            self.voice_client.resume()

        if (self.voice_client is None or not self.voice_client.is_playing()) and self.queue:
            if self.voice_client is None and message.author.voice is not None:
                self.voice_client = await message.author.voice.channel.connect()
            await self.play_next_in_queue()

    async def handle_stop(self, message: Message, command: Command):
        embed = Embed(title="Parando canción")
        embed.add_field(name="", value=self.current_video.label, inline=False)
        await message.channel.send(embed=embed)
        if self.voice_client is None and message.author.voice is not None:
            self.voice_client = await message.author.voice.channel.connect()
        self.voice_client.stop()
        self.current_video = None

    async def handle_skip(self, message: Message, command: Command):
        embed = Embed(title="Saltando canción")
        embed.add_field(name="", value=self.current_video.label, inline=False)
        await message.channel.send(embed=embed)
        if self.voice_client is None and message.author.voice is not None:
            self.voice_client = await message.author.voice.channel.connect()
        self.voice_client.stop()
        await self.play_next_in_queue()

    async def handle_queue(self, message: Message, command: Command):
        embed = Embed(title="Cola de canciones")
        queue = [self.current_video] + self.queue
        if not queue:
            embed.add_field(name="", value="No hay canciones en cola", inline=False)
        for index, video in enumerate(queue, start=1):
            embed.add_field(name="", value=f"{index}) {video.label}", inline=False)
            if index == 10:
                embed.add_field(name="", value="...", inline=False)
                break
        await message.channel.send(embed=embed)

    async def handle_clear(self, message: Message, command: Command):
        self.queue = []
        self.current_video = None
        if self.voice_client is not None:
            self.voice_client.stop()
        await message.channel.send("Cola de canciones limpiada")

    async def handle_disconnect(self, **kwargs):
        if self.voice_client is not None:
            await self.voice_client.disconnect()
            self.voice_client = None
            self.current_video = None
            self.last_playing = None
        goodbye_messages = [
            "Chau!",
            "Nos vemos!",
            "Hasta luego!",
            "Adiós!",
            "Bye.-",
            "gg wp",
            "gg ez",
            "nv",
        ]
        await self.channel.send(random.choice(goodbye_messages))

    async def handle_help(self, message: Message, command: Command):
        embed = Embed(title="Comandos disponibles")
        for action, description in COMMANDS_HELP.items():
            embed.add_field(name=action, value=description, inline=False)
        await message.channel.send(embed=embed)

    async def add_to_queue(self, video: Video, message: Message):
        if self.voice_client is None:
            if message.author is None or message.author.voice is None:
                return
            self.voice_client = await message.author.voice.channel.connect()
        self.queue.append(video)
        if len(self.queue) == 1:
            await self.play_next_in_queue()

    async def play_next_in_queue(self, *args, **kwargs):
        if self.voice_client is None:
            return
        if self.voice_client.is_playing():
            return
        if not self.queue:
            self.current_video = None
            return
        self.current_video = self.queue.pop(0)
        audio_source = FFmpegPCMAudio(YOUTUBE_API.get_video_file(video=self.current_video))
        self.voice_client.play(audio_source, after=self._audio_finish_callback)
        embed = Embed(title="Reproduciendo canción")
        embed.add_field(name="", value=self.current_video.label, inline=False)
        await self.channel.send(embed=embed)
        if self.last_playing is None:
            self.last_playing = datetime.now()
            asyncio.create_task(self.inactivity_check())

    async def inactivity_check(self):
        while True:
            await asyncio.sleep(60)
            if self.voice_client is not None and not self.voice_client.is_playing():
                await self.handle_disconnect()

    def _audio_finish_callback(self, error):
        if error:
            logger.error(f"Error occurred: {error}")
        asyncio.run(self.play_next_in_queue())


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run(SETTINGS.DISCORD_BOT_TOKEN)

    # videos = YOUTUBE_API.search(query='chulo')
    # for video in videos:
    #     print(video)
    # video = videos[1]
    # # download video
    # print(YOUTUBE_API.get_video_file(video=video))


if __name__ == '__main__':
    main()


