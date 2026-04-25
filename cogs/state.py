from collections import deque
import discord
from discord.ext import commands

class StateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playback_info = {}
        self.server_settings = {}
        self.past_songs = deque()
        self.music_cue = deque()


async def setup(bot):
    await bot.add_cog(StateCog(bot))