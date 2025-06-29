import asyncio
import functools
import random
from datetime import datetime

import discord
from discord import Message, Client as DiscordClient, Embed, FFmpegPCMAudio

from discord_api.models import Action, Command, COMMANDS, COMMANDS_HELP
from discord_api.src import PlaySelector
from logger import logger
from youtube_api.api import YOUTUBE_API
from youtube_api.models import Video


class Client(DiscordClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_keywords = ["faka ", "f "]
        self.queue = []
        self.current_video = None
        self.voice_client = None
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

    async def on_message(self, message: Message):
        command = await self.get_command(message=message)
        await self.handle_command(message=message, command=command)

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
            logger.info(f"Command is a playlist: {command.query}")
            videos = YOUTUBE_API.get_playlist_videos_from_url(url=command.query)
            for video in videos:
                await self.add_to_queue(video=video, message=message)
            return
        elif command.is_youtube_video():
            logger.info(f"Command is a video: {command.query}")
            video = YOUTUBE_API.get_video_from_id(video_id=command.get_youtube_video_id())
            await self.add_to_queue(video=video, message=message)
            return
        elif command.query != "":
            logger.info(f"Command is a search: {command.query}")
            videos: list[Video] = YOUTUBE_API.search(query=command.query)
            embed = Embed(title="Encontré estas canciones:")
            embed.set_thumbnail(url=videos[0].thumbnail_url)
            for index, video in enumerate(videos, start=1):
                embed.add_field(name="", value=f"{index}) {video.label}", inline=False)
            response = await message.channel.send(
                embed=embed,
                view=PlaySelector(message=message, videos=videos, client=self),
            )
            await response.delete(delay=10)
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
            await self.play_next_in_queue(message=message)

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
        await self.play_next_in_queue(message=message)

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

    async def handle_disconnect(self, message: Message, command: Command = None):
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
        await message.channel.send(random.choice(goodbye_messages))

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
            await self.play_next_in_queue(message=message)

    def _audio_finish_callback(self, error):
        if error:
            logger.error(f"Error occurred: {error}")
        asyncio.run(self.play_next_in_queue())

    async def play_next_in_queue(self, message: Message):
        if self.voice_client is None:
            return
        if self.voice_client.is_playing():
            return
        if not self.queue:
            self.current_video = None
            return
        self.current_video = self.queue.pop(0)
        audio_source = FFmpegPCMAudio(YOUTUBE_API.get_video_file(video=self.current_video))
        self.voice_client.play(audio_source, after=functools.partial(self._audio_finish_callback, message=message))
        embed = Embed(title="Reproduciendo canción")
        embed.add_field(name="", value=self.current_video.label, inline=False)
        await message.channel.send(embed=embed)
        if self.last_playing is None:
            self.last_playing = datetime.now()
            asyncio.create_task(self.inactivity_check(message=message))

    async def inactivity_check(self, message: Message):
        while True:
            await asyncio.sleep(300)
            if self.voice_client is not None and not self.voice_client.is_playing():
                await self.handle_disconnect(message=message)


