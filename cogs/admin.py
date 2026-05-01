import os
import discord
from discord.ext import commands
from datetime import datetime

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = bot.get_cog("StateCog")

    @commands.command(name="reload", hidden=True)
    @commands.has_role("Eigentümer")  # <-- GANZ WICHTIG! Nur DU darfst das.
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
    @commands.has_role("Eigentümer")
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
            await ctx.send("🧹 Lösche alle globalen Befehle, um Duplikate zu vernichten...")

            # 1. Leert die globale Warteschlange im Bot
            self.bot.tree.clear_commands(guild=None)

            # 2. Schickt diese "leere" Liste an Discord (löscht die alten)
            await self.bot.tree.sync()

            await ctx.send(
                "✅ Globale Schublade geleert! Mache jetzt einen `!sync local` und lade Discord mit Strg+R neu.")


    @commands.command(name="rebuild_cache", hidden=True)
    @commands.has_role("Eigentümer")
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
            await ctx.send("Ihr seid doch schon in diesem Kanal! 🤨")
            return

        # 5. Alle verschieben
        moved_count = 0
        await ctx.send(f"🔄 Verschiebe alle aus **{source_channel.name}** nach **{target_channel.name}**...")

        for member in source_channel.members:
            try:
                await member.move_to(target_channel)
                moved_count += 1
            except discord.Forbidden:
                await ctx.send(f"⛔ Mir fehlen die Rechte, um {member.display_name} zu verschieben!")
            except discord.HTTPException:
                pass

        await ctx.send(f"✅ Erledigt! {moved_count} Leute nach {target_channel.name} verschoben.")

    @commands.command(name="debug", hidden=True)
    @commands.has_role("Eigentümer")
    async def debug_command(self, ctx):
        await ctx.send(self.state.playback_info)
        await ctx.send(self.state.server_settings)
        await ctx.send(self.state.past_songs)
        await ctx.send(self.state.music_cue)
        await ctx.send(datetime.fromtimestamp(self.state.last_seen_erhabenheit).strftime('%H:%M:%S, %d.%m.%Y'))
        await ctx.send(self.state.is_erhabenheit)
        await ctx.send(self.state.USE_MANUAL_ERHABENHEIT_TOGGLE)
        await ctx.send(self.state.first_stop)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))