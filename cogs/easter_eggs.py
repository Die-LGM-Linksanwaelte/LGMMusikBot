import random
from discord.ext import commands

class EasterEggsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ABSTINENZ_ID = 1495885269394784317
        self.PENIS_ID = 1495869135622508615


    @commands.command()
    async def Abstinenz(self, ctx):
        channel = self.bot.get_channel(self.ABSTINENZ_ID)
        voice_client = ctx.guild.voice_client

        if voice_client:
            # Wenn er schon in einem Voice-Channel ist, zieht er einfach um
            await voice_client.move_to(channel)
        else:
            # Wenn er noch nirgends ist, tritt er frisch bei
            await channel.connect()

        music_module = self.bot.get_cog("MusicCog")

        if music_module is None:
            await ctx.send("@Lichtgott du hast mal wieder verkackt! Ich hab kein Musik-Modul! Wie kannst du nur!")
            return

        await music_module.play_song("AbstinenzDerUte.mp3", ctx, ctx.guild.voice_client)

    @commands.command()
    async def penis(self, ctx):
        channel = self.bot.get_channel(self.PENIS_ID)
        async with ctx.typing():
            # Lade die letzten 200 Nachrichten herunter
            messages = [msg async for msg in channel.history(limit=200)]

            # Filtere Nachrichten heraus, die leer sind (z.B. nur ein Bild)
            # oder von anderen Bots stammen
            valid_texts = [
                msg.content for msg in messages
                if msg.content.strip() != "" and not msg.author.bot
            ]

            # Sicherheitscheck, falls der Channel leer ist
            if not valid_texts:
                await ctx.send("DER PENIS IST TOT! LANG LEBE DER PENIS!")
                return

            # Eine zufällige Nachricht auswählen und senden
            random_text = random.choice(valid_texts)
            await ctx.send(random_text)

async def setup(bot):
    await bot.add_cog(EasterEggsCog(bot))