import time
import discord
from discord.ext import commands
from discord import app_commands

class MusicInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    def get_music_data(self):
        music_module = self.bot.get_cog("MusicCog")
        if not music_module:
            return None, None
        return music_module.playback_info, music_module.music_cue

    @commands.hybrid_command(name="now", description="Gibt Infos über das aktuelle Lied aus")
    async def now(self, ctx):
        playback_info, _ = self.get_music_data()

        is_playing = ctx.guild.voice_client.is_paused() or ctx.guild.voice_client.is_playing()


        if not playback_info or not ctx.guild.voice_client or not is_playing:
            await ctx.send("Zurzeit läuft hier nichts.")
            return

        info = playback_info.get(ctx.guild.id)

        # Ausrechnen, wie lange es schon läuft
        if info.get("is_paused"):
            elapsed = info["pause_start"] - info["start_time"]
            status_emoji = "⏸️"
        else:
            elapsed = time.time() - info["start_time"]
            status_emoji = "▶️"

        duration = info["duration"]
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

        await ctx.send(
            f"{status_emoji} **{info['name']}**\n"
            f"`{el_m}:{el_s:02d} {bar} {dur_m}:{dur_s:02d}`\n"
            f"⏳ Noch **{rem_m}:{rem_s:02d}** bis zum Ende."
        )

    @commands.hybrid_command(name="cue", description="Gibt Infos über die Lieder in der Warteschlange aus")
    async def cue(self, ctx):
        playback_info, music_cue = self.get_music_data()

        # 1. Ein leeres, schickes Embed erstellen (blurple ist das Standard-Discord-Blau)
        embed = discord.Embed(
            title="🎶 Musik-Warteschlange",
            color=discord.Color.blurple()
        )

        # 2. Was läuft gerade? (Wir greifen auf unser Gedächtnis von vorhin zurück)
        info = playback_info.get(ctx.guild.id)
        voice_client = ctx.guild.voice_client

        if info and voice_client and voice_client.is_playing():
            embed.add_field(name="▶️ Läuft gerade:", value=f"**{info['name']}**", inline=False)
        else:
            embed.add_field(name="▶️ Läuft gerade:", value="*Stille.*", inline=False)

        # 3. Die Warteschlange (Queue) auslesen
        if not music_cue:
            # Wenn die Queue leer ist
            embed.description = "Die Warteschlange ist aktuell leer. Pack was rein!"
        else:
            # Wir wandeln die Deque kurz in eine Liste um und schneiden die ersten 10 Elemente ab
            upcoming_songs = list(music_cue)[:10]

            # Wir bauen den Text für die Anzeige zusammen
            queue_text = ""
            for index, song in enumerate(upcoming_songs, start=1):
                queue_text += f"**{index}.** {song}\n"

            # Falls es MEHR als 10 Lieder sind, hängen wir einen kleinen Hinweis an
            if len(music_cue) > 10:
                queue_text += f"\n*... und {len(music_cue) - 10} weitere Lieder*"

            # Den Text als Block ins Embed einfügen
            embed.add_field(name="⏳ Als Nächstes:", value=queue_text, inline=False)

        # 4. Das fertige Embed abschicken!
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MusicInfoCog(bot))