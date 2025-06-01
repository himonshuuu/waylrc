#!/usr/bin/env python3

import sys
import json
import re
import time
import urllib.request
import urllib.parse
from urllib.error import URLError

# === LYRIC CLASS ===
class Lyric:
    def __init__(self, text: str, minutes: int, seconds: int, milliseconds: int):
        self.text = text
        self.timestamp = (minutes * 60 * 1000) + (seconds * 1000) + milliseconds

    @classmethod
    def from_lyric_line(cls, line: str):
        match = re.match(r"\[(\d+):(\d+)\.(\d+)\] (.+)", line)
        if match:
            m, s, ms, txt = match.groups()
            return cls(txt, int(m), int(s), int(ms))
        return None

# === LYRICS FETCHER ===
def fetch_lyrics(title: str, artist: str):
    print(f"Fetching lyrics for: {title} by {artist}")
    try:
        base_url = "https://lrclib.net/api/search" 
        params = {'q': f"{title} {artist}"}
        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                results = json.loads(response.read().decode())
                print(f"Results: {url}")
                if results:
                    synced_lyrics = results[0].get("syncedLyrics")
                    if synced_lyrics:
                        lines = synced_lyrics.split("\n")
                        lyrics = []
                        for line in lines:
                            lyric = Lyric.from_lyric_line(line)
                            if lyric:
                                lyrics.append(lyric)
                        return sorted(lyrics, key=lambda x: x.timestamp)
    except (URLError, json.JSONDecodeError) as e:
        print(f"Error fetching lyrics: {e}")
    return []

# === MEDIA INFO PARSER ===
def get_media_info():
    try:
        import subprocess

        # Get status
        status = subprocess.run(['playerctl', 'status'],
                               capture_output=True, text=True).stdout.strip()
        if status not in ["Playing", "Paused"]:
            return None

        title = subprocess.run(['playerctl', 'metadata', 'title'],
                              capture_output=True, text=True).stdout.strip()
        artist = subprocess.run(['playerctl', 'metadata', 'artist'],
                               capture_output=True, text=True).stdout.strip()
        position_ms = int(float(subprocess.run(['playerctl', 'position'],
                                              capture_output=True, text=True).stdout.strip()) * 1000)

        return {
            'title': title,
            'artist': artist,
            'position': position_ms,
            'status': status
        }
    except Exception as e:
        print(f"Error getting media info: {e}", file=sys.stderr)
        return None

# === MAIN LOOP ===
def main():
    last_title = ""
    last_artist = ""
    lyrics = []
    index = 0
    last_line = ""

    while True:
        info = get_media_info()

        if not info:
            print(json.dumps({"text": ""}))
            sys.stdout.flush()
            time.sleep(1)
            continue

        current_title = info['title']
        current_artist = info['artist']
        current_status = info['status']

        # Track change detection
        if current_title != last_title or current_artist != last_artist:
            print(f"Song changed: {current_title} - {current_artist}")
            lyrics = fetch_lyrics(current_title, current_artist)
            index = 0
            last_title = current_title
            last_artist = current_artist
            last_line = ""

        position = info['position']
        current_line = ""

        # Only update if playing
        if current_status == "Playing":
            for i in range(index, len(lyrics)):
                if lyrics[i].timestamp <= position:
                    current_line = lyrics[i].text
                    index = i
                    last_line = current_line
                else:
                    break
        else:
            current_line = last_line

        output = {"text": current_line}
        print(json.dumps(output))
        sys.stdout.flush()

        time.sleep(0.5)

if __name__ == "__main__":
    main()