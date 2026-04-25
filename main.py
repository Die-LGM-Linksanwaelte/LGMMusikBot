import discord
from discord.ext import commands
import os


class LgmMusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix='§', intents=intents)

    async def setup_hook(self):
        print("Lade die erhabenen Module...")
        await self.load_extension("cogs.state")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "state.py":
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Erhabenes Modul {filename[:-3]} geladen!")


    async def on_ready(self):
        print(f"Ich bin der erhabene {self.user}!!!")
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="mit seinem Penis"))


if __name__ == "__main__":
    bot = LgmMusicBot()

    token = os.getenv("DISCORD_TOKEN")
    token = "MTMyNzk5ODc0Mjg1MDMwNjA5MA.GKIoax.4_q2wtBKoA4-OSjtqGiQH1kTj_J9_o35hNrWIo"
    if not token:
        print("DISCORD_TOKEN environment variable not found")
        exit(1)

    bot.run(token)