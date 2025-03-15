import discord
from discord import Message, Interaction, Button
from discord.ui import View

from logger import logger
from youtube_api.models import Video


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
        await interaction.delete_original_response()
        await interaction.message.delete()
        await self.client.add_to_queue(video=video, message=self.source_message)
