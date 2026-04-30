import asyncio
import random
import time
from discord.ext import commands

class EasterEggsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ABSTINENZ_ID = 1495885269394784317
        self.PENIS_ID = 1495869135622508615
        self.state = bot.get_cog("StateCog")


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


        if self.state is None:
            await ctx.send("@Lichtgott du hast mal wieder verkackt! Ich hab kein Musik-Modul! Wie kannst du nur!")
            return

        self.state.server_settings[ctx.guild.id] = {
            "repeat": "Single"
        }
        music_module = self.bot.get_cog("MusicCog")
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

    @commands.command()
    async def reset_timer(self, ctx):
        self.state.last_seen_erhabenheit = 0
        await ctx.send("Ok!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        LICHTGOT_ID = 771375658235461652
        LOETGOTT_ID = 861587158594093056
        SUCKYSUCKY = "ErhabeneBegruesung.mp3"
        COOLDOWN = 1200

        if member.id not in [LICHTGOT_ID, LOETGOTT_ID]:
            return

        def are_together_now(channel):
            if not channel:
                return False
            member_ids = [m.id for m in channel.members]
            return LICHTGOT_ID in member_ids and LOETGOTT_ID in member_ids

        def were_together_before(channel, member_that_moved):
            if not channel:
                return False

            member_ids = set(m.id for m in channel.members)
            member_ids.add(member_that_moved.id)
            return LOETGOTT_ID in member_ids and LICHTGOT_ID in member_ids


        together_before = were_together_before(before.channel, member)
        together_after = are_together_now(after.channel)
        print(f"Zzuvor: {together_before} - danach: {together_after}")

        #Trennung
        if together_before and not together_after:
            self.state.last_seen_erhabenheit = time.time()
            print("💔 Die Erhabenen haben sich getrennt. Cooldown-Timer startet.")
            return

        #Wiedervereinigung
        if not together_before and together_after:
            now = time.time()
            last_sep = getattr(self.state, "last_seen_erhabenheit", 0)

            if now - last_sep > COOLDOWN:
                print(f"DIE ERHABENHEIT IST DA! Letztes mal war vor {int(now - last_sep)}s!")

                self.state.last_seen_erhabenheit = now

                await self.trigger_greeting_interrupt(member.guild, after.channel, SUCKYSUCKY)

            else:
                time_left = int(COOLDOWN - (now - last_sep))
                print(f"🤫 Erhabenheit vereint, aber Cooldown läuft noch ({time_left}s übrig).")

    async def trigger_greeting_interrupt(self, guild, channel, song):
        state = self.state
        current_info = state.playback_info.get(guild.id)

        old_data_copy = None
        resume_time = 0
        #was_playing = False

        if guild.voice_client and guild.voice_client.is_playing():
            #was_playing = True

            start_time = current_info.get("start_time", time.time())
            resume_time = time.time() - start_time
            old_data_copy = current_info.copy()

            #Musik stoppen
            state.first_stop = True
            state.playback_info[guild.id]["is_interrupted"] = True
            #state.playback_info[guild.id]["interrupted_song"] = current_info
            #state.playback_info[guild.id]["resume_at"] = resume_time
            guild.voice_client.stop()

            await asyncio.sleep(0.5)

        if not guild.voice_client:
            await channel.connect()

        state.playback_info[guild.id] = {
            #"start_time": time.time(),
            #"duration": 0,
            #"name": song,
            #"file": song + ".mp3",
            #"is_paused": False,
            #"pause_start": 0,
            "is_interrupted": True,
            "interrupted_data": current_info,
            "resume_at": resume_time,
        }


        musicCog = self.bot.get_cog("MusicCog")
        await musicCog.play_song(song, guild, guild.voice_client)


async def setup(bot):
    await bot.add_cog(EasterEggsCog(bot))