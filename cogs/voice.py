from discord.ext import commands
from discord import app_commands

class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="join", description="Sorgt dafür, dass der Bot in den Voice-Channel geht, in dem du bist.")
    async def join(self, ctx):
        # Bot betritt deinen Voice Channel
        if ctx.author.voice:
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.disconnect()
            await ctx.author.voice.channel.connect()
            await ctx.send("Bin jetzt da!")
        else:
            await ctx.send("Du bist in keinem Voice-Channel!")

    @commands.hybrid_command(name="leave", description="Sorgt dafür, dass der Bot den Voice-Channel verlässt.")
    async def leave(self, ctx):
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Auf Wiedersehen, ihr Penner!")
        else:
            await ctx.send("Ich häng doch nicht mir jemandem wie DIR ab!")


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))