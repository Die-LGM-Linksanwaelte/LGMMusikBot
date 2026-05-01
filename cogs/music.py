import random
import discord
from discord.ext import commands
from collections import deque
import os
import time
import subprocess
import asyncio
import difflib
from discord import app_commands


def is_playing_or_paused(target):
    guild = target.guild if hasattr(target, "guild") else target
    voice_client = guild.voice_client
    return voice_client.is_playing() or voice_client.is_paused()


async def safe_send(target, message):
    """Sendet eine Nachricht bevorzugt in den Text-Chat des aktuellen Sprachkanals."""

    # 1. Fall: target ist bereits ein Context (Slash Command)
    if hasattr(target, "send") and not isinstance(target, discord.Guild):
        try:
            return await target.send(message)
        except:
            pass

    # 2. Fall: Wir haben nur eine Guild (vom Event)
    guild = target.guild if hasattr(target, "guild") else target
    voice_client = guild.voice_client

    # Wir versuchen in den Text-Chat des Sprachkanals zu schreiben, in dem der Bot ist
    if voice_client and voice_client.channel:
        try:
            # Ja, man kann auf einem VoiceChannel-Objekt .send() aufrufen!
            return await voice_client.channel.send(message)
        except discord.Forbidden:
            # Falls wir dort keine Rechte haben, Fallback auf Standard-Kanal
            pass

    # 3. Fallback: Erster schreibbarer Textkanal (wie zuvor)
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return await channel.send(message)
    return None


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.state = bot.get_cog("StateCog")
        self.MUSIC_DIR = self.state.MUSIC_DIR

    async def play_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        matches = [
            app_commands.Choice(name=t["display"][:100], value=t["path"])
            for t in self.state.track_cache if current.lower() in t["search"]
        ]

        return matches[:25]


    def fetch_song(self, track):
        available_files = [f for f in os.listdir(self.MUSIC_DIR) if f.endswith(('.mp3', '.flac', '.wav', '.ogg'))]
        files_without_ext = {os.path.splitext(f)[0]: f for f in available_files}

        matches = difflib.get_close_matches(track, files_without_ext.keys(), n=1, cutoff=0.1)

        if not matches:
            return None, None

        best_match = matches[0]
        best_match_file = files_without_ext[best_match]


        return best_match, best_match_file



    def song_finished(self, error, target):
        guild = target.guild if hasattr(target, "guild") else target
        if error:
            print(f"Fehler beim Abspielen: {error}")

        past_song = self.state.playback_info[guild.id]["file"]

        # Hier löschen wir die gespeicherte Zeit für diesen Server
        if self.state.playback_info[guild.id]["is_interrupted"]:
            if self.state.first_stop:
                self.state.first_stop = False
                return
        #elif guild.id in self.state.playback_info:
        #    del self.state.playback_info[guild.id]

        coro = self.handle_song_end(target, past_song)
        asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def handle_song_end(self, target, past_song: str):
        guild = target.guild if hasattr(target, "guild") else target
        guild_id = guild.id
        info = self.state.playback_info.get(guild_id)

        if info and info.get("is_interrupted"):

            self.state.playback_info[guild.id]["is_interrupted"] = False
            old_data = info.get("interrupted_data")
            resume_time = info.get("resume_at")

            self.state.playback_info[guild_id]["interrupted_data"] = {}
            self.state.playback_info[guild_id]["resume_at"] = 0

            if old_data:
                await self.play_song(old_data["file"], target, guild.voice_client, resume_at=resume_time)
                # Laut GPLUS DAS WICHTIGSTE WORT DES TAGES:
                return

        repeat = self.state.server_settings[guild.id]["repeat"]

        if repeat == "Single":
            await self.play_song(past_song, target, guild.voice_client)
            if random.randint(0, 20) == 0 and past_song != "AbstinenzDerUte.mp3":
                if "Smalltown Boy" in past_song:
                    await safe_send(target, "Ist mal wieder typisch, Hohlmann")
                else:
                    await safe_send(target, "Wird dir nicht langweilig?")
        else:
            if repeat in ["All", "Shuffle"]:
                self.state.past_songs.append(past_song)

            if self.state.music_cue:
                await self.play_song(self.state.music_cue.popleft(), target, guild.voice_client)
            else:
                if repeat == "None":
                    await safe_send(target, "🛑 Die Wiedergabe ist zu Ende!")
                    if guild_id in self.state.playback_info:
                        del self.state.playback_info[guild_id]
                elif repeat in ["All","Shuffle"]:
                    self.state.music_cue = self.state.past_songs
                    self.state.past_songs = deque()
                    await safe_send(target, "Wir wiederholen alles nochmal!")
                    if repeat == "Shuffle":
                        random.shuffle(self.state.music_cue)
                        await safe_send(target, "Zufällig!")
                    await self.play_song(self.state.music_cue.popleft(), target, guild.voice_client)
                else:
                    message = f"Error: Ungültiger Repeat-Modus: {repeat}"
                    await safe_send(target, message)
                    print(message)





    @commands.hybrid_command(name="play", description="Spiel ein Lied ab, das ich hier irgendwo liegen habe")
    @app_commands.autocomplete(track=play_autocomplete)
    async def play_command(self, ctx, *, track: str):
        # Spielt die lokale Datei per FFmpeg ab
        voice_client = ctx.guild.voice_client
        if not voice_client:
            await ctx.send("wo soll ich das den abspielen, bist du dumm?!?!")
            return

        best_match, best_match_file = self.fetch_song(track)

        song_name = self.state.get_track_info(best_match_file)["title"]
        song_artist = self.state.get_track_info(best_match_file)["artist"]

        song_data = f"{song_name} von {song_artist}"


        if best_match is None:
            await ctx.send("Was soll denn das für ein Lied sein?!?!")
            return

        if is_playing_or_paused(ctx):
            self.state.music_cue.append(best_match_file)
            await ctx.send(f"{song_data} ist in der Cue! Freu dich du HS")
            return

        #Weil ja dieser Teil nur drankommt, wenn bisher noch nichts gespielt wurde (aka es ist eine neue Session), muss
        # hier repeat zurückgesetzt werden.
        self.state.server_settings[ctx.guild.id] = {
            "repeat": "None"
        }

        mins, secs = await self.play_song(best_match_file, ctx, voice_client)
        await ctx.send(f"PENIS! Ich spiele jetzt: {song_data} ({mins}:{secs:02d})")

    async def play_song(self, best_match_file: str, ctx_or_guild, voice_client, resume_at=0):
        guild = ctx_or_guild.guild if hasattr(ctx_or_guild, "guild") else ctx_or_guild


        if is_playing_or_paused(guild):
            voice_client.stop()

        before_args = f"-ss {resume_at}"

        ffmpeg_options = {
            'before_options': before_args,
            'options': '-vn'
        }

        full_path = os.path.join(self.MUSIC_DIR, best_match_file)

        song_info = self.state.get_track_info(best_match_file)

        duration = song_info["duration"]

        old_data = self.state.playback_info.get(guild.id, {})

        # 2. Die Daten im "Gedächtnis" des Bots ablegen
        new_data = {
            "start_time": time.time() - resume_at,
            "duration": duration,
            "name": song_info["title"],
            "file": best_match_file,
            "is_paused": False,
            "pause_start": 0,
            "is_interrupted": old_data.get("is_interrupted", False),
            "interrupted_data": old_data.get("interrupted_data", {}),
            "resume_at": old_data.get("resume_at", 0),
        }

        self.state.playback_info[guild.id] = new_data

        # 3. Das Lied starten und das 'after' Callback übergeben!
        # Wichtig: Wir nutzen lambda, um das 'ctx' an die Funktion mitzugeben
        source = discord.FFmpegPCMAudio(full_path, **ffmpeg_options)
        voice_client.play(source, after=lambda e: self.song_finished(e, ctx_or_guild))

        # Dauer hübsch formatieren (z.B. "3:45")
        mins, secs = divmod(int(duration), 60)
        return mins, secs

    @commands.hybrid_command(name="pause",description="Pausiert die Wiedergabe")
    async def pause(self, ctx):
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.send("Es läuft nichts du Bastard!")
            return

        voice_client.pause()

        if ctx.guild.id in self.state.playback_info:
            info = self.state.playback_info[ctx.guild.id]
            info["is_paused"] = True
            info["pause_start"] = time.time()

        await ctx.send("Penis! Äh ne warte, Pause, ja stimmt, Pause mein ich...")

    @commands.hybrid_command(name="resume", description="Startet die Wiedergabe wieder nach einer Pause")
    async def resume(self, ctx):
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_paused():
            await ctx.send(
                "Geht doch grad nicht, entweder es läuft noch nicht oder es ist überhaupt nicht pausiert, was weiß ich")

        voice_client.resume()

        if ctx.guild.id in self.state.playback_info:
            info = self.state.playback_info[ctx.guild.id]
            if info["is_paused"]:
                paused_duration = time.time() - info["pause_start"]
                info["start_time"] += paused_duration
                info["is_paused"] = False

        await ctx.send("Penis! Ne warte, das ergibt überhaupt keinen Sinn, niemand glaubt mir doch, dass ich \"Penis\" und \"Weiter gehts\" verwechselt hab...")

    @commands.hybrid_command(name="stop",description="Stoppt die Wiedergabe und löscht alle Lieder aus der Warteschlange")
    async def stop(self, ctx):
        voice_client = ctx.guild.voice_client
        if not voice_client or not is_playing_or_paused(ctx):
            await ctx.send("Was soll ich den hier stoppen?")
            return
        self.state.music_cue.clear()
        self.state.server_settings[ctx.guild.id]["repeat"] = "None"
        self.state.past_songs.clear()
        voice_client.stop()
        await ctx.send("RUHE IM GERICHTSAAL!")

    @commands.hybrid_command(name="skip",description="Überspringt das aktuell spielende Lied und geht direkt zum nächsten")
    async def skip(self, ctx):
        voice_client = ctx.guild.voice_client
        if not voice_client or not is_playing_or_paused(ctx):
            await ctx.send("Was soll ich den hier skippen?")
            return

        await ctx.send(f"Ich überspringe jetzt {self.state.playback_info[ctx.guild.id]['name']}!")
        voice_client.stop()


    @commands.hybrid_group(name="repeat", description="Ändert das Verhalten was nach dem ablaufen eines Song/der gesammten Queue passieren soll")
    async def repeat_group(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = self.bot.command_prefix
            await ctx.send(f"Bitte nutze `{prefix}repeat none`, `{prefix}repeat all`, `{prefix}repeat shuffle` oder `{prefix}repeat single`.")


    @repeat_group.command(name="none", description="Beendet die Wiedergabe wenn die Queue leer ist.")
    async def repeat_none(self, ctx):
        if ctx.guild.id in self.state.server_settings:
            self.state.server_settings[ctx.guild.id]["repeat"] = "None"
            self.state.past_songs.clear()
            await ctx.send("Es wiederholt sich nichts")
        else:
            await ctx.send("Es gibt keine Session, zu der der Repeat-modus geändert werden könnte.")

    @repeat_group.command(name="all", description="Wiederholt alle mit diesem Modus gehörten Lieder, wenn die Queue leer ist.")
    async def repeat_none(self, ctx):
        if ctx.guild.id in self.state.server_settings:
            self.state.server_settings[ctx.guild.id]["repeat"] = "All"
            await ctx.send("Es wiederholt sich alles")
        else:
            await ctx.send("Es gibt keine Session, zu der der Repeat-modus geändert werden könnte.")

    @repeat_group.command(name="shuffle", description="Wiederholt alle mit diesem Modus gehörten Lieder in zufälliger Reihenfolge, wenn die Queue leer ist.")
    async def repeat_none(self, ctx):
        if ctx.guild.id in self.state.server_settings:
            self.state.server_settings[ctx.guild.id]["repeat"] = "Shuffle"
            random.shuffle(self.state.music_cue) #Kann theoretisch auskommentiert werden, falls sich rausstellt, das man das nicht will
            await ctx.send("Es wiederholt sich alles zufällig")
        else:
            await ctx.send("Es gibt keine Session, zu der der Repeat-modus geändert werden könnte.")

    @repeat_group.command(name="single", description="Wiederholt das aktuelle Lied für immer.")
    async def repeat_none(self, ctx):
        if ctx.guild.id in self.state.server_settings:
            self.state.server_settings[ctx.guild.id]["repeat"] = "Single"
            self.state.past_songs.clear()
            await ctx.send(f"Es wiederholt sich {self.state.playback_info[ctx.guild.id]['name']}")
        else:
            await ctx.send("Es gibt keine Session, zu der der Repeat-modus geändert werden könnte.")



async def setup(bot):
    await bot.add_cog(MusicCog(bot))
