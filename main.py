import os
import discord
from discord.ext import commands
import config


class LgmMusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        print("Lade Erweiterungen...")
        await self.load_extension("cogs.state")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "state.py":
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Erweiterung {filename[:-3]} erfolgreich geladen.")


    async def on_ready(self):
        print(f"Bot erfolgreich eingeloggt als {self.user}")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=config.BOT_ACTIVITY)
        )


if __name__ == "__main__":
    bot = LgmMusicBot()

    token = config.DISCORD_TOKEN

    if not token:
        print("DISCORD_TOKEN environment variable not found")
        exit(1)

    bot.run(token)
