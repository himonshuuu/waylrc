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

# === MPRIS HELPER ===
def get_media_info():
    try:
        import subprocess
        
        # Get playback status
        status = subprocess.run(['playerctl', 'status'], 
                              capture_output=True, text=True).stdout.strip()
        
        if status != "Playing":
            return {
                'playing': False,
                'title': None,
                'artist': None,
                'position': 0
            }

        # Get metadata
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
            'playing': status == 'Playing'
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
            # If we can't get any media info at all
            print(json.dumps({"text": "..." }))
            sys.stdout.flush()
            time.sleep(0.5)
            continue

        if info['playing']:
            if info['title'] != last_title or info['artist'] != last_artist:
                lyrics = fetch_lyrics(info['title'], info['artist'])
                last_title = info['title']
                last_artist = info['artist']
                index = 0

            position = info['position']

            for i in range(index, len(lyrics)):
                if lyrics[i].timestamp <= position:
                    last_line = lyrics[i].text
                    index = i
                else:
                    break

        # Output the current or last known line
        output_text = last_line if info and info['playing'] else f"Paused: {last_line or '...'}"
        print(json.dumps({"text": output_text}))
        sys.stdout.flush()

        time.sleep(0.5)

if __name__ == "__main__":
    main()