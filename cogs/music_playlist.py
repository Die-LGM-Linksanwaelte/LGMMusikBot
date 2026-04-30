import difflib
import random
import discord
from discord.app_commands import describe

from cogs.music import is_playing_or_paused
from discord.ext import commands
from discord import app_commands
import os


class MusicPlaylistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = bot.get_cog("StateCog")
        self.PLAYLIST_DIR = self.state.PLAYLIST_DIR


    def get_cue(self):
        if not self.state:
            return None
        return self.state.music_cue


    def create_playlist(self, name:str, playlist:list[str], overwrite=False):
        filepath = os.path.join(self.PLAYLIST_DIR, f"{name}.playlist")
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(playlist))


    def fetch_playlist(self, name):
        available_files = [f for f in os.listdir(self.PLAYLIST_DIR) if f.endswith('.playlist')]
        files_without_ext = {os.path.splitext(f)[0]: f for f in available_files}
        matches = difflib.get_close_matches(name, files_without_ext.keys(), n=1, cutoff=0.4)

        if not matches:
            return []

        best_match = matches[0]
        best_match_file = files_without_ext[best_match]

        full_path = os.path.join(self.PLAYLIST_DIR, best_match_file)

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                playlist = [line.strip() for line in f if line.strip()]
                return playlist


        except FileNotFoundError:
            print(f"❌ Fehler: Die Playlist '{full_path}' existiert gar nicht.")
            return []

        except PermissionError:
            print(f"⛔ Fehler: Du hast keine Leserechte für '{full_path}' (chmod/chown checken!).")
            return []

        except UnicodeDecodeError:
            print(f"🔣 Fehler: Die Datei {full_path} ist kein sauberer UTF-8 Text.")
            return []

        except Exception as e:
            # Der "Catch-All" für jeden anderen, unerwarteten Fehler (z.B. Festplatte voll)
            print(f"🔥 Ein wilder Fehler ist aufgetreten beim öffnen von {full_path}: {e}")
            return []

    async def playlist_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            # Sucht nach .playlist Dateien im Ordner
            available_files = [f for f in os.listdir(self.PLAYLIST_DIR) if f.endswith('.playlist')]
            files_without_ext = [os.path.splitext(f)[0] for f in available_files]
            matches = [f for f in files_without_ext if current.lower() in f.lower()]

            return [app_commands.Choice(name=match, value=match) for match in matches[:25]]
        except FileNotFoundError:
            return []

    async def track_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        music_module = self.bot.get_cog("MusicCog")
        return await music_module.play_autocomplete(interaction, current)



    @commands.hybrid_command(name="shuffle", description="Mischt die Cue zufällig")
    async def shuffle(self, ctx):
        music_cue = self.get_cue()
        if music_cue:
            random.shuffle(music_cue)
            await ctx.send("Ok, hab in Absenz der Ute geshuffled. ")
        else:
            await ctx.send("DUMM!! DUMM!!!! ES GIBT KEINE LIEDER DIE DU SCHUFFLEN KÖNNTEST!!!!")


    @commands.hybrid_group(name="playlist", description="Verwaltet die Playlists")
    async def playlist_group(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = self.bot.command_prefix
            await ctx.send(f"Bitte nutze `{prefix}playlist play`, `{prefix}playlist save` oder `{prefix}playlist add`.")


    @playlist_group.command(name="play", description="Spielt eine gespeicherte Playlist ab.")
    @app_commands.autocomplete(name=playlist_autocomplete)
    async def playlist_play(self, ctx, name):
        playlist = self.fetch_playlist(name)
        music_module = self.bot.get_cog("MusicCog")
        if playlist:
            await ctx.send("Playlist geladen")
            self.state.music_cue.extend(playlist)

            if not is_playing_or_paused(ctx):
                await music_module.handle_song_end(ctx)
        else:
            await ctx.send("Die Playlist kenne ich nicht, du Bastard!")

    @playlist_group.command(name="save", description="Speichert die aktuelle Queue als Playlist")
    async def playlist_save(self, ctx, name):
        music_module = self.bot.get_cog("MusicCog")
        if not self.state.music_cue:
            await ctx.send("Ich kann keine leere Playlist erstellen!")
            return
        try:
            self.create_playlist(name, self.state.music_cue)
            await ctx.send(f"Playlist '{name}' wurde erstellt!")
        except FileExistsError as e:
            await ctx.send(f"Es existiert bereits eine Playlist mit dem Namen:  \"{name}\"")

    @playlist_group.command(name="add", description="Fügt ein Lied an das Ende einer Playlist an")
    @app_commands.autocomplete(name=playlist_autocomplete)
    @app_commands.autocomplete(track=track_autocomplete)
    async def playlist_add(self, ctx, name: str, *, track:str):
        music_module = self.bot.get_cog("MusicCog")
        playlist = self.fetch_playlist(name)
        _, song = music_module.fetch_song(name)
        if song is None:
            await ctx.send("Ich bin zu blöd, dieses Lied zu finden")
            return
        if playlist:
            playlist.append(song)
            self.create_playlist(name, playlist, overwrite=True)
            await ctx.send(f"Ich habe das Lied {song} zur Playlist hinzugefügt")

    @playlist_group.command(name="delete", description="Löscht eine Playlist")
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.has_role("Eigentümer")
    async def playlist_delete(self, ctx, name):
        # 1. Pfad zur Datei erstellen
        pfad = os.path.join(self.PLAYLIST_DIR, f"{name}.playlist")

        # 2. Prüfen, ob die Datei existiert
        if not os.path.exists(pfad):
            await ctx.send(f"❌ Die Playlist **{name}** wurde nicht gefunden.")
            return

        # 3. Datei löschen
        try:
            # os.remove ist der Standardbefehl unter Linux/Python zum Löschen
            os.remove(pfad)
            await ctx.send(f"🗑️ Die Playlist **{name}** wurde erfolgreich gelöscht.")

        except Exception as e:
            await ctx.send(f"🔥 Ein Fehler ist beim Löschen aufgetreten: {e}")





async def setup(bot):
    await bot.add_cog(MusicPlaylistCog(bot))