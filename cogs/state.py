import os
from collections import deque
from imaplib import Commands
from discord.ext import commands
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

class StateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playback_info = {}
        self.server_settings = {}
        self.past_songs = deque()
        self.music_cue = deque()
        self.track_cache = []
        self.last_seen_erhabenheit = 0
        self.is_erhabenheit = False
        self.first_stop = False

        self.NEVER_COMING_EVENT_NAME = "Die Wahl vom Gott des Pflaumenbaums"
        self.USE_MANUAL_ERHABENHEIT_TOGGLE = True
        self.MUSIC_DIR = "/music"
        self.PLAYLIST_DIR = "/playlists"



    async def cog_load(self):
        await self.build_track_cache()




    def get_track_info(self, file_name: str):
        file_path = os.path.join(self.MUSIC_DIR, file_name)
        info = {
            "title": os.path.basename(file_path),
            "artist": "Unbekannter Künstler",
            "cover": None,
            "duration": 0
        }

        try:
            if file_path.endswith('.mp3'):
                audio = MP3(file_path)
                info["duration"] = audio.info.length

                # 2. Prüfen, ob überhaupt ID3-Tags vorhanden sind
                if audio.tags:
                    # Titel (TIT2)
                    if 'TIT2' in audio.tags:
                        info["title"] = audio.tags['TIT2'].text[0]

                    # Künstler (TPE1)
                    if 'TPE1' in audio.tags:
                        info["artist"] = audio.tags['TPE1'].text[0]

                    # Bilder (APIC)
                    # getall() ist sicherer, weil es eine leere Liste liefert, falls kein APIC da ist
                    pictures = audio.tags.getall("APIC")
                    if pictures:
                        info["cover"] = pictures[0].data
            elif file_path.endswith(".flac"):
                audio = FLAC(file_path)
                info["duration"] = audio.info.length
                info["title"] = audio.get("title", info["title"])[0]
                info["artist"] = audio.get("artist", info["artist"])[0]
                if audio.pictures:
                    info["cover"] = audio.pictures[0].data

        except Exception as e:
            print(f"Fehler beim lesen von {e}!")

        return info


    async def build_track_cache(self):
        self.track_cache = []
        for file in os.listdir(self.MUSIC_DIR):
            if file.endswith(('.mp3', '.flac')):
                meta = self.get_track_info(file)

                artist = str(meta.get("artist", "Unbekannt"))
                title = str(meta.get("title", file))

                self.track_cache.append({
                    "path": file,
                    "display": f"{title} - {artist}",
                    "search": f"{title}  {artist} {file}".lower()
                })

        print(f"✅ Cache rebuildet: {len(self.track_cache)} Tracks geladen.")

async def setup(bot):
    await bot.add_cog(StateCog(bot))