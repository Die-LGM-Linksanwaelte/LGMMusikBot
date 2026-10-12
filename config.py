import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei (falls vorhanden)
load_dotenv()


def format_msg(template: str, **kwargs) -> str:
    """Formatiert Template-Strings sicher mit Keyword-Argumenten."""
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError, IndexError):
        return template


# ─── Bot-Grundeinstellungen & Verzeichnisse ──────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_ACTIVITY = os.getenv("BOT_ACTIVITY", "Musik & Audio")
MUSIC_DIR = os.getenv("MUSIC_DIR", "/home/lichtgott/Music/BotMusik")
PLAYLIST_DIR = os.getenv("PLAYLIST_DIR", "/home/lichtgott/Music/BotPlaylists")

# ─── Musik-Wiedergabe Nachrichten ────────────────────────────────────────────
MSG_NO_VOICE = os.getenv("MSG_NO_VOICE", "Du musst in einem Sprachkanal sein!")
MSG_UNKNOWN_SONG = os.getenv("MSG_UNKNOWN_SONG", "Ich konnte dieses Lied leider nicht finden.")
MSG_SONG_QUEUED = os.getenv("MSG_SONG_QUEUED", "{song} wurde zur Warteschlange hinzugefügt.")
MSG_NOW_PLAYING = os.getenv("MSG_NOW_PLAYING", "Ich spiele jetzt: {song} ({mins}:{secs:02d})")
MSG_PAUSE_NOT_PLAYING = os.getenv("MSG_PAUSE_NOT_PLAYING", "Es wird zurzeit nichts abgespielt.")
MSG_PAUSE = os.getenv("MSG_PAUSE", "Wiedergabe pausiert.")
MSG_RESUME_NOT_PAUSED = os.getenv(
    "MSG_RESUME_NOT_PAUSED",
    "Wiedergabe ist nicht pausiert oder läuft bereits."
)
MSG_RESUME = os.getenv("MSG_RESUME", "Wiedergabe wird fortgesetzt.")
MSG_STOP_NOT_PLAYING = os.getenv("MSG_STOP_NOT_PLAYING", "Es läuft keine Wiedergabe zum Stoppen.")
MSG_SKIP_NOT_PLAYING = os.getenv("MSG_SKIP_NOT_PLAYING", "Es läuft kein Song zum Überspringen.")
MSG_STOP = os.getenv("MSG_STOP", "Wiedergabe beendet und Warteschlange geleert.")
MSG_REPEAT_SPECIAL = os.getenv("MSG_REPEAT_SPECIAL", "Wiederhole diesen Titel.")
MSG_REPEAT_RANDOM = os.getenv("MSG_REPEAT_RANDOM", "Wiederhole Titel.")

# ─── Playlist & Voice Nachrichten ────────────────────────────────────────────
MSG_SHUFFLE_EMPTY = os.getenv("MSG_SHUFFLE_EMPTY", "Die Warteschlange ist leer. Es gibt nichts zu mischen.")
MSG_SHUFFLE_SUCCESS = os.getenv("MSG_SHUFFLE_SUCCESS", "Warteschlange gemischt.")
MSG_PLAYLIST_NOT_FOUND = os.getenv("MSG_PLAYLIST_NOT_FOUND", "Diese Playlist wurde nicht gefunden.")
MSG_CANNOT_FIND_SONG = os.getenv("MSG_CANNOT_FIND_SONG", "Song konnte nicht gefunden werden.")
MSG_LEAVE = os.getenv("MSG_LEAVE", "Auf Wiedersehen!")
MSG_LEAVE_NOT_CONNECTED = os.getenv("MSG_LEAVE_NOT_CONNECTED", "Ich bin in keinem Sprachkanal verbunden.")

# ─── Events & Geplante Aktionen ──────────────────────────────────────────────
SCHEDULED_EVENT_NAME = os.getenv("EVENT_NAME", "Die Wahl vom Gott des Pflaumenbaums")
EVENT_DESCRIPTION = os.getenv("EVENT_DESCRIPTION", "Geplantes Community Event")
EVENT_REASON = os.getenv("EVENT_REASON", "Verschiebung des Termins")
EVENT_LOCATION = os.getenv("EVENT_LOCATION", "Unter dem großen Pflaumenbaum")

# ─── Easter Eggs, Audio & Zitate ─────────────────────────────────────────────
QUOTE_CHANNEL_ID = int(os.getenv("QUOTE_CHANNEL_ID", "1495869135622508615"))
QUOTE_CMD_NAME = os.getenv("QUOTE_CMD_NAME", "quote")
QUOTE_CMD_ALIASES = [a.strip() for a in os.getenv("QUOTE_CMD_ALIASES", "").split(",") if a.strip()]
QUOTE_FALLBACK_MSG = os.getenv("QUOTE_FALLBACK_MSG", "Keine Zitate gefunden!")
MSG_NO_MUSIC_MODULE = os.getenv("MSG_NO_MUSIC_MODULE", "Musik-Modul ist derzeit nicht verfügbar.")

ABSTINENZ_SONG = os.getenv("ABSTINENZ_SONG", "AbstinenzDerUte.mp3")
GREETING_SONG = os.getenv("GREETING_SONG", "ErhabeneBegruesung.mp3")
FAREWELL_SONG = os.getenv("FAREWELL_SONG", "Glue.mp3")
MSG_FAREWELL = os.getenv("MSG_FAREWELL", "Auf Wiedersehen bis zum nächsten Mal!")
MSG_CHAOS_SUCCESS = os.getenv("MSG_CHAOS_SUCCESS", "Nicknames wurden geändert ({count} Mitglieder).")
MSG_HEAL_SUCCESS = os.getenv("MSG_HEAL_SUCCESS", "Nicknames wurden wiederhergestellt ({count} Mitglieder).")

# ─── Rollen, IDs & Berechtigungen ────────────────────────────────────────────
OWNER_ROLE_NAME = os.getenv("OWNER_ROLE_NAME", "Eigentümer")
OUTLAW_ROLE_NAME = os.getenv("OUTLAW_ROLE_NAME", "Geächteter")
RAIGBAIT_ROLE_NAME = os.getenv("RAIGBAIT_ROLE_NAME", "raigbait final boss")
RAIGBAIT_GUILD_ID = os.getenv("RAIGBAIT_GUILD_ID", "1262550330969948261")
RAIGBAIT_ROLE_ID = os.getenv("RAIGBAIT_ROLE_ID", "1557476559051559094")

ABSTINENZ_CHANNEL_ID = int(os.getenv("ABSTINENZ_CHANNEL_ID", "1495885269394784317"))
USER_ID_1 = int(os.getenv("USER_ID_1", "771375658235461652"))
USER_ID_2 = int(os.getenv("USER_ID_2", "1262796633431609427"))
