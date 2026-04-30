from datetime import datetime, timedelta, timezone

import discord
from discord.ext import tasks
import asyncio
import random
import time
from discord.ext import commands

class EasterEggsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ABSTINENZ_ID = 1495885269394784317
        self.PENIS_ID = 1495869135622508615
        self.LICHTGOT_ID = 771375658235461652
        self.LOETGOTT_ID = 861587158594093056
        self.state = bot.get_cog("StateCog")
        self.EVENT_NAME = self.state.NEVER_COMING_EVENT_NAME
        self.USE_MANUAL_TOGGLE = self.state.USE_MANUAL_ERHABENHEIT_TOGGLE
        self.pflaumenbaum_loop.start()


    def cog_unload(self):
        self.pflaumenbaum_loop.cancel()

    @tasks.loop(minutes=1)
    async def pflaumenbaum_loop(self):

        await self.bot.wait_until_ready()

        new_start = datetime.now(timezone.utc) + timedelta(days=7)
        new_end = new_start + timedelta(seconds=42)

        for guild in self.bot.guilds:

            existing_event = discord.utils.get(guild.scheduled_events, name=self.EVENT_NAME)

            if existing_event:
                try:
                    await existing_event.edit(
                        start_time=new_start,
                        end_time=new_end,
                        reason="Wir brauchen noch ein bisschen Vorberietungszeit, diesesmal wirklich das letzte Mal"
                    )
                    print(f"[{guild.name}] Pflaumenbaum-Wahl erfolgreich um eine Woche verschoben!")

                except discord.Forbidden:
                    print(f"[{guild.name}] Mir fehlen die Rechte, um Events zu bearbeiten!")
                except discord.HTTPException as e:
                    print(f"[{guild.name}] API Fehler beim Verschieben: {e}")

            else:
                try:
                    await guild.create_scheduled_event(
                        name=self.EVENT_NAME,
                        description="WIR MACHENS! Endlich wählen wir den Gott des Pflaumenbaums",
                        start_time=new_start,
                        end_time=new_end,
                        entity_type=discord.EntityType.external,
                        location="Unter dem großen Pflaumenbaum",
                        privacy_level=discord.PrivacyLevel.guild_only
                    )
                    print(f"[{guild.name}] Pflaumenbaum-Event wurde neu erschaffen!")
                except Exception as e:
                    print(f"[{guild.name}] Fehler beim Erstellen des Events: {e}")





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
        SUCKYSUCKY = "ErhabeneBegruesung.mp3"
        COOLDOWN = 1200

        if member.id not in [self.LICHTGOT_ID, self.LOETGOTT_ID]:
            return

        def are_together_now(channel):
            if not channel:
                return False
            member_ids = [m.id for m in channel.members]
            return self.LICHTGOT_ID in member_ids and self.LOETGOTT_ID in member_ids

        def were_together_before(channel, member_that_moved):
            if not channel:
                return False

            member_ids = set(m.id for m in channel.members)
            member_ids.add(member_that_moved.id)
            return self.LOETGOTT_ID in member_ids and self.LICHTGOT_ID in member_ids


        together_before = were_together_before(before.channel, member)
        together_after = are_together_now(after.channel)
        print(f"Zzuvor: {together_before} - danach: {together_after}")

        # ==========================================
        # NEUE LOGIK: Manueller Toggle (!glue)
        # ==========================================
        if self.USE_MANUAL_TOGGLE:  # (Oder einfach nur USE_MANUAL_TOGGLE, je nachdem wo du es definiert hast)

            # Sicherheits-Check: Falls der Bot neustartet und die Variable noch nicht da ist
            if not hasattr(self.state, "is_erhabenheit"):
                self.state.is_erhabenheit = False

            # Ihr seid jetzt zusammen
            if not together_before and together_after:
                # Ist die Erhabenheit inaktiv? Dann los!
                if not self.state.is_erhabenheit:
                    print("🎤 Erhabenheit vereint (Toggle-Modus)! Starte Begrüßung.")

                    # Status auf aktiv setzen, damit es nicht nochmal triggert
                    self.state.is_erhabenheit = True

                    await self.trigger_greeting_interrupt(member.guild, after.channel, SUCKYSUCKY)
                else:
                    print("🤫 Erhabenheit ist schon aktiv. Warte auf !glue.")

        # ==========================================
        # ALTE LOGIK: Cooldown Timer
        # ==========================================
        else:
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

    @commands.command(name="glue")
    @commands.has_role("Eigentümer")
    async def glue_command(self, ctx):
        FAREWELL_SONG = "I Glued My Balls to My Butthole Again.mp3"

        # Nur ihr beide dürft den Befehl nutzen
        if ctx.author.id not in [self.LICHTGOT_ID, self.LOETGOTT_ID]:
            return

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Du musst in einem Sprachkanal sein, um dich zu verabschieden!")
            return

        # 1. Status auf inaktiv setzen
        self.state.is_erhabenheit = False
        await ctx.send("👋 Die Erhabenheit verabschiedet sich... bis zum nächsten Mal!")

        # 2. VL abspielen (Wir nutzen einfach unseren perfekten Interrupt-Mechanismus!)
        await self.trigger_greeting_interrupt(ctx.guild, ctx.author.voice.channel, FAREWELL_SONG)



async def setup(bot):
    await bot.add_cog(EasterEggsCog(bot))