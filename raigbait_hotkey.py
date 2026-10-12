#!/usr/bin/env python3
"""
raigbait_hotkey.py  (Wayland-kompatibel via evdev)
───────────────────────────────────────────────────
Drücke Ctrl+Alt+R um alle "raigbait final boss"-Mitglieder
serverweit stumm zu schalten – oder die Stummschaltung aufzuheben.

Starten:  .venv/bin/python raigbait_hotkey.py
Beenden:  Ctrl+C
"""

import os
import sys
import time
import threading
import asyncio
import requests
import evdev
from evdev import ecodes
from dotenv import dotenv_values

# ─── Konfiguration & Token laden ──────────────────────────────────────────────
ENV_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
env = dotenv_values(ENV_FILE)
TOKEN = env.get("DISCORD_TOKEN")
GUILD_ID  = env.get("RAIGBAIT_GUILD_ID", "1262550330969948261")
ROLE_ID   = env.get("RAIGBAIT_ROLE_ID", "1557476559051559094")
BASE_URL  = "https://discord.com/api/v10"

# Hotkey: Ctrl + Alt + R
TRIGGER_KEY  = ecodes.KEY_R
NEED_CTRL    = True
NEED_ALT     = True

if not TOKEN:
    print("❌  DISCORD_TOKEN nicht in .env gefunden!")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json",
}

# ─── Toggle-State ─────────────────────────────────────────────────────────────
_muted = False
_busy  = False   # verhindert Doppelauslösung bei schnellem Drücken

# ─── Discord-Helfer ───────────────────────────────────────────────────────────

def get_members_with_role() -> list[str]:
    ids, after = [], 0
    while True:
        r = requests.get(
            f"{BASE_URL}/guilds/{GUILD_ID}/members",
            headers=HEADERS,
            params={"limit": 1000, "after": after},
        )
        if r.status_code != 200:
            print(f"  ⚠️  Fehler {r.status_code}: {r.text[:120]}")
            break
        batch = r.json()
        if not batch:
            break
        for m in batch:
            if ROLE_ID in m.get("roles", []):
                ids.append(m["user"]["id"])
        if len(batch) < 1000:
            break
        after = batch[-1]["user"]["id"]
    return ids


def set_server_mute(user_id: str, mute: bool) -> int:
    r = requests.patch(
        f"{BASE_URL}/guilds/{GUILD_ID}/members/{user_id}",
        headers=HEADERS,
        json={"mute": mute},
    )
    return r.status_code


def toggle_mute():
    global _muted, _busy
    if _busy:
        return
    _busy = True
    try:
        _muted = not _muted
        label = "STUMMSCHALTEN" if _muted else "ENTSTUMMEN"
        print(f"\n{'─'*54}")
        print(f"  {label}  (Ctrl+Alt+R)")
        print(f"{'─'*54}")
        print("  Lade Mitglieder mit konfigurierter Rolle...")

        member_ids = get_members_with_role()
        if not member_ids:
            print("  Niemand mit dieser Rolle gefunden.")
            return

        print(f"  {len(member_ids)} Mitglied(er) – verarbeite...\n")
        ok, skip, fail = 0, 0, 0

        for uid in member_ids:
            status = set_server_mute(uid, _muted)
            if status == 204:
                ok += 1
            elif status == 400:
                skip += 1   # nicht in Voice
            else:
                print(f"  User {uid}: HTTP {status}")
                fail += 1
            time.sleep(0.05)   # Rate-Limit schonen

        word = "stummgeschaltet" if _muted else "entstummt"
        print(f"\n  {ok} {word}")
        if skip: print(f"  {skip} nicht in Voice (übersprungen)")
        if fail: print(f"  {fail} Fehler")
        print()
    finally:
        _busy = False


# ─── Keyboard-Listener per evdev (Wayland-kompatibel) ────────────────────────

def find_keyboards() -> list[evdev.InputDevice]:
    """Gibt alle Geräte zurück, die echte Tastatur-Tasten haben."""
    keyboards = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            keys = caps.get(ecodes.EV_KEY, [])
            # Hat es Alpha-Tasten? → echte Tastatur
            if ecodes.KEY_A in keys and ecodes.KEY_R in keys:
                keyboards.append(dev)
        except Exception:
            pass
    return keyboards


def listen_keyboard(device: evdev.InputDevice):
    """Lauscht auf einem einzelnen Gerät nach dem Hotkey."""
    held = set()
    try:
        for event in device.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            key_event = evdev.categorize(event)
            code = key_event.scancode

            if key_event.keystate == evdev.KeyEvent.key_down:
                held.add(code)
            elif key_event.keystate == evdev.KeyEvent.key_up:
                held.discard(code)

            # Prüfen ob Ctrl+Alt+R gedrückt
            ctrl_held = ecodes.KEY_LEFTCTRL  in held or ecodes.KEY_RIGHTCTRL in held
            alt_held  = ecodes.KEY_LEFTALT   in held or ecodes.KEY_RIGHTALT  in held
            r_down    = key_event.scancode == TRIGGER_KEY and key_event.keystate == evdev.KeyEvent.key_down

            if ctrl_held and alt_held and r_down:
                threading.Thread(target=toggle_mute, daemon=True).start()

    except OSError:
        pass   # Gerät getrennt – Thread stirbt leise


# ─── Start ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║      Raigbait Final Boss – Mute Hotkey               ║")
    print("║      (Wayland-kompatibel via evdev)                  ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Hotkey  :  Ctrl + Alt + R                           ║")
    print(f"║  Guild   :  {GUILD_ID}          ║")
    print(f"║  Rolle   :  {ROLE_ID}   ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Wartet auf Tastendruck ...  Ctrl+C zum Beenden.     ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    keyboards = find_keyboards()
    if not keyboards:
        print("Fehler: Keine Tastatur-Geräte gefunden!")
        print("   Bist du in der 'input'-Gruppe? (Prüfe mit: groups $USER)")
        sys.exit(1)

    print(f"Lausche auf {len(keyboards)} Tastatur-Gerät(e):")
    for kb in keyboards:
        print(f"    {kb.path}  →  {kb.name}")
    print()

    threads = []
    for kb in keyboards:
        t = threading.Thread(target=listen_keyboard, args=(kb,), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBeendet.")
