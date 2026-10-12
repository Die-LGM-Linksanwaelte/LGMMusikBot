import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import config

RAIGBAIT_ROLE_NAME = config.RAIGBAIT_ROLE_NAME

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = bot.get_cog("StateCog")
        self._raigbait_muted = False  # Toggle-Status

    @commands.command(name="reload", hidden=True)
    @commands.has_role(config.OWNER_ROLE_NAME)
    async def reload_cog(self, ctx, extension: str=None):
        """Lädt ein Modul neu (Nur für den Bot-Besitzer)"""
        if extension is None:
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py") and filename != "state.py":
                    await self.reload_cog(ctx,filename[:-3])
            return
        try:
            # Wir bauen den Pfad zusammen (z.B. "cogs.music") und laden neu
            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"✅ Modul `cogs/{extension}.py` erfolgreich neu geladen!")

        except commands.ExtensionNotLoaded:
            await ctx.send(
                f"⚠️ Das Modul `{extension}` war gar nicht geladen.")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ Ich kann keine Datei namens `cogs/{extension}.py` finden!")
        except Exception as e:
            # Wenn du einen Syntax-Fehler im Code hast, zeigt er dir hier direkt an, wo!
            await ctx.send(f"🔥 Fehler im Code von `{extension}`:\n```py\n{e}\n```")

    @commands.command(name="sync", hidden=True)
    @commands.has_role(config.OWNER_ROLE_NAME)
    async def sync_command(self, ctx, scope: str = "local"):
        if scope == "global":
            await ctx.send("Ich synchronisiere die Slah-Befehle global!")
            synced = await self.bot.tree.sync()
            await ctx.send(f"Es wurden {len(synced)} Slah-Befehle global synchronisiert!")

        elif scope == "local":
            await ctx.send("Ich synchronisiere die Slah-Befehle lokal!")

            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)

            await ctx.send(f"Es wurden {len(synced)} Slah-Befehle lokal synchronisiert!")

            # --- NEU: DER BEREINIGUNGS-MODUS ---
        elif scope == "clear":
            await ctx.send("Lösche alle globalen Befehle zur Bereinigung...")

            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()

            await ctx.send("Globale Befehle geleert. Führe nun `!sync local` aus.")


    @commands.command(name="rebuild_cache", hidden=True)
    @commands.has_role(config.OWNER_ROLE_NAME)
    async def rebuild_cache(self, ctx):
        try:
            await self.state.build_track_cache()
            await ctx.send("Cache wurde neu gebaut!")
        except Exception as e:
            await ctx.send(f"Fehler beim rebuilden des Caches: \n {e}")
            print(f"Fehler beim rebuilden des Caches: {e}")


    @commands.command()
    @commands.has_permissions(move_members=True)
    async def move_all(self, ctx, *, target_input: str):
        # 1. Prüfen, ob der Autor in einem Voice-Channel ist
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Du musst in einem Sprachkanal sein, um diesen Befehl zu nutzen!")
            return

        source_channel = ctx.author.voice.channel
        target_channel = None

        # 2. STRATEGIE A: Ist die Eingabe eine ID? (Besteht nur aus Zahlen)
        if target_input.isdigit():
            # Umwandeln in eine echte Zahl und im Cache suchen
            possible_channel = self.bot.get_channel(int(target_input))

            # Sicherheitscheck: Ist es auch wirklich ein VOICE-Channel?
            if isinstance(possible_channel, discord.VoiceChannel):
                target_channel = possible_channel

        # 3. STRATEGIE B: Wenn es keine (gültige) ID war, suchen wir nach dem Namen
        if not target_channel:
            for vc in ctx.guild.voice_channels:
                # lower() macht die Suche unabhängig von Groß-/Kleinschreibung
                if vc.name.lower() == target_input.lower():
                    target_channel = vc
                    break

        # 4. Finaler Check, ob wir IRGENDWAS gefunden haben
        if not target_channel:
            await ctx.send(f"❌ Ich konnte keinen Sprachkanal mit dem Namen oder der ID '{target_input}' finden.")
            return

        if source_channel == target_channel:
            await ctx.send("Zielkanal entspricht aktuellem Kanal.")
            return

        moved_count = 0
        await ctx.send(f"Verschiebe alle Mitglieder aus **{source_channel.name}** nach **{target_channel.name}**...")

        for member in source_channel.members:
            try:
                await member.move_to(target_channel)
                moved_count += 1
            except discord.Forbidden:
                await ctx.send(f"Fehlende Rechte, um {member.display_name} zu verschieben.")
            except discord.HTTPException:
                pass

        await ctx.send(f"Fertig: {moved_count} Mitglieder nach {target_channel.name} verschoben.")

    @commands.command(name="debug", hidden=True)
    @commands.has_role(config.OWNER_ROLE_NAME)
    async def debug_command(self, ctx):
        await ctx.send(self.state.playback_info)
        await ctx.send(self.state.server_settings)
        await ctx.send(self.state.past_songs)
        await ctx.send(self.state.music_cue)
        await ctx.send(datetime.fromtimestamp(self.state.last_seen_erhabenheit).strftime('%H:%M:%S, %d.%m.%Y'))
        await ctx.send(self.state.is_erhabenheit)
        await ctx.send(self.state.USE_MANUAL_ERHABENHEIT_TOGGLE)
        await ctx.send(self.state.first_stop)


    # ─────────────────────────────────────────────────────────────────────────
    # RAIGBAIT FINAL BOSS – MUTE TOGGLE
    # ─────────────────────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="raigbait_mute",
        description=f"Schaltet alle Mitglieder mit der Rolle '{RAIGBAIT_ROLE_NAME}' serverweit stumm (oder hebt es auf)."
    )
    @commands.has_role(config.OWNER_ROLE_NAME)
    @app_commands.default_permissions(administrator=True)
    async def raigbait_mute(self, ctx):
        """Togglet den Server-Mute für alle 'raigbait final boss'-Mitglieder."""
        await ctx.defer()  # Verhindert Timeout bei vielen Mitgliedern

        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=RAIGBAIT_ROLE_NAME)

        if role is None:
            await ctx.send(
                f"❌ Ich konnte die Rolle **'{RAIGBAIT_ROLE_NAME}'** nicht finden. "
                f"Stimmt der Rollenname?"
            )
            return

        # Toggle: Wenn gerade gemutet → entmutet; sonst → mutet
        self._raigbait_muted = not self._raigbait_muted
        action = "stummgeschaltet" if self._raigbait_muted else "entstummt"
        emoji  = "🔇" if self._raigbait_muted else "🔊"

        affected = []
        failed   = []

        for member in role.members:
            if member.voice is None:
                # Mitglied ist gerade in keinem Voice-Channel – überspringen
                continue
            try:
                await member.edit(mute=self._raigbait_muted)
                affected.append(member.display_name)
            except discord.Forbidden:
                failed.append(member.display_name)
            except discord.HTTPException:
                failed.append(member.display_name)

        # ─── Antwort zusammenbauen ───────────────────────────────────────────
        if not affected and not failed:
            await ctx.send(
                f"{emoji} Niemand mit der Rolle **{role.name}** ist gerade in einem Voice-Channel."
            )
            return

        lines = [f"{emoji} **{len(affected)} Mitglied(er)** wurden {action}:"]
        if affected:
            lines.append(", ".join(affected))
        if failed:
            lines.append(f"\n⛔ Bei diesen hat's nicht geklappt (fehlende Rechte?): {', '.join(failed)}")

        await ctx.send("\n".join(lines))


async def setup(bot):
    await bot.add_cog(AdminCog(bot))