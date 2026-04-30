import io
import time
import discord
from discord.ext import commands

class MusicInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = bot.get_cog("StateCog")


    def get_music_data(self):
        if not self.state:
            return None, None
        return self.state.playback_info, self.state.music_cue

    @commands.hybrid_command(name="now", description="Gibt Infos über das aktuelle Lied aus")
    async def now(self, ctx):
        playback_info, _ = self.get_music_data()

        is_playing = ctx.guild.voice_client.is_paused() or ctx.guild.voice_client.is_playing()


        if not playback_info or not ctx.guild.voice_client or not is_playing:
            await ctx.send("Zurzeit läuft hier nichts.")
            return

        info = playback_info.get(ctx.guild.id)
        current_file = info["file"]
        meta = self.state.get_track_info(current_file)

        # Ausrechnen, wie lange es schon läuft
        if info.get("is_paused"):
            elapsed = info["pause_start"] - info["start_time"]
            status_emoji = "⏸️"
        else:
            elapsed = time.time() - info["start_time"]
            status_emoji = "▶️"

        duration = meta["duration"]
        remaining = duration - elapsed

        if remaining < 0:
            remaining = 0

        # Alles hübsch in Minuten und Sekunden umrechnen
        el_m, el_s = divmod(int(elapsed), 60)
        dur_m, dur_s = divmod(int(duration), 60)
        rem_m, rem_s = divmod(int(remaining), 60)

        # Einen kleinen Fortschrittsbalken basteln (10 Blöcke lang)
        progress = int((elapsed / duration) * 10) if duration > 0 else 0
        bar = "▬" * progress + "🔘" + "▬" * (10 - progress)

        embed = discord.Embed(
            title=f"{status_emoji} **{str(meta['title'])}**",
            description=f"von {meta['artist']}\n Geladen von {current_file}\n {el_m}:{el_s:02d} {bar} {dur_m}:{dur_s:02d}`\n⏳ Noch **{rem_m}:{rem_s:02d}** bis zum Ende.",
            color=discord.Color.red()
        )

        if meta["cover"]:
            # Cover aus Bytes in ein Discord-File umwandeln
            file = discord.File(io.BytesIO(meta["cover"]), filename="cover.png")
            embed.set_thumbnail(url="attachment://cover.png")
            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="cue", description="Gibt Infos über die Lieder in der Warteschlange aus")
    async def cue(self, ctx):
        # Daten abrufen
        playback_info, music_cue = self.get_music_data()

        embed = discord.Embed(
            title="🎶 Musik-Warteschlange",
            color=discord.Color.blurple()
        )

        # 1. Aktueller Song (mit Metadaten-Check)
        info = playback_info.get(ctx.guild.id)
        voice_client = ctx.guild.voice_client

        if info and voice_client and voice_client.is_playing():
            current_file = info['name']
            # Wir suchen im Cache nach dem hübschen Namen
            cache_hit = next((t for t in self.state.track_cache if t["path"] == current_file), None)
            display_name = cache_hit["display"] if cache_hit else current_file

            embed.add_field(name="▶️ Läuft gerade:", value=f"**{display_name}**", inline=False)
        else:
            embed.add_field(name="▶️ Läuft gerade:", value="*Stille.*", inline=False)

        # 2. Die Warteschlange
        if not music_cue:
            embed.description = "Die Warteschlange ist aktuell leer. Pack was rein!"
        else:
            upcoming_songs = list(music_cue)[:10]
            queue_text = ""

            for index, song_file in enumerate(upcoming_songs, start=1):
                # Auch hier: Metadaten aus dem Cache ziehen für die Anzeige
                cache_hit = next((t for t in self.state.track_cache if t["path"] == song_file), None)
                display_name = cache_hit["display"] if cache_hit else song_file

                queue_text += f"**{index}.** {display_name}\n"

            if len(music_cue) > 10:
                queue_text += f"\n*... und {len(music_cue) - 10} weitere Lieder*"

            embed.add_field(name="⏳ Als Nächstes:", value=queue_text, inline=False)

        # 3. Kleiner Bonus: Den aktuellen Loop-Modus anzeigen
        settings = self.state.server_settings.get(ctx.guild.id, {"repeat": "None"})
        loop_status = settings["repeat"]
        emoji = "🔁" if loop_status != "None" else "➡️"
        embed.set_footer(text=f"Modus: {loop_status} {emoji} | {len(music_cue)} Lieder in der Queue")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MusicInfoCog(bot))