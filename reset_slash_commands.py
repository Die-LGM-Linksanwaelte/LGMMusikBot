import os
import discord
from discord.ext import commands
import config


class CommandWiper(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("Lösche globale Befehle...")
        self.tree.clear_commands(guild=None)
        await self.tree.sync()

        print("Bereinige Server-spezifische Befehle...")
        for guild in self.guilds:
            try:
                print(f" -> Bereinige Befehle auf Server: {guild.name} ({guild.id})")
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)
            except discord.Forbidden:
                print(f" -> Fehlende Rechte auf Server: {guild.name}")
            except discord.HTTPException as e:
                print(f" -> API-Fehler auf Server {guild.name}: {e}")

        print("Befehle erfolgreich synchronisiert und bereinigt.")
        await self.close()


if __name__ == "__main__":
    bot = CommandWiper()

    token = config.DISCORD_TOKEN

    if not token:
        print("DISCORD_TOKEN nicht gefunden.")
        exit(1)

    bot.run(token)