import os
from os.path import isdir
from tinytag import TinyTag
from pathlib import Path
from collections import defaultdict
import re
import argparse

audio_extentions = {".ogg" , ".mp3", ".acc", ".wav", ".flac", ".aiff"}

metadata_path_cache = defaultdict(list)

def build_cache(library):
    cached_files = 0

    paths = (path for path in library.glob(r'**/*') if path.suffix in audio_extentions and os.path.isfile(path))
    for path in paths:

        tag: TinyTag = TinyTag.get(path)

        metadata_path_cache[tag.albumartist].append(path)
        metadata_path_cache[tag.year].append(path)
        metadata_path_cache[tag.album].append(path)
        metadata_path_cache[tag.artist].append(path)
        metadata_path_cache[tag.title].append(path)

        cached_files += 1
        if cached_files % 100 == 0: print(f"Files cached: {cached_files}")

def search_cache(albumartist, year, album, artist, title):
    return list(set(metadata_path_cache[albumartist]) & set(metadata_path_cache[year]) & set(metadata_path_cache[artist]) & set(metadata_path_cache[album]) & set(metadata_path_cache[title]))

def get_metadata(line):
    pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(pattern, line)
    return {key.lower(): value for key, value in matches}

def get_comment(albumartist, year, album, artist, title):
    return str(f'# ALBUMARTIST="{albumartist}" YEAR="{year}" ARTIST="{artist}" ALBUM="{album}" TITLE="{title}"\n')

def process_m3u(m3u_path, library):
    tmp_path = ".tmp_m3u"
    if os.path.isfile(tmp_path): os.remove(tmp_path)
    tmp = open(tmp_path, "x")
    m3u = open(m3u_path)

    cache_built = False

    prevline = ""

    lines = m3u.readlines()
    for line in lines:

        
        if line.startswith("#") or line.isspace():
            prevline = line
            continue

        path = line.rstrip('\n')
        if os.path.isfile(path):
            tag: TinyTag = TinyTag.get(path)
            tmp.write(get_comment(tag.albumartist, tag.year, tag.artist, tag.album, tag.title))
            tmp.write(line)
            prevline = line
            continue

        tags = get_metadata(prevline)

        if not cache_built: 
            build_cache(library)
            cache_built = True

        matches = search_cache(tags["albumartist"], tags["year"], tags["album"], tags["artist"], tags["title"])
        tmp.write(get_comment(tags["albumartist"], tags["year"], tags["artist"], tags["album"], tags["title"]))
        tmp.write(str(matches[0]) + "\n")

        prevline = line

    os.remove(m3u_path)
    os.rename(tmp_path, m3u_path)


parser = argparse.ArgumentParser(prog='elastic-m3u')
parser.add_argument('-l', '--library', required=True)
parser.add_argument('-p', '--playlists', required=True, nargs='*')
args = parser.parse_args()

for playlist_arg in args.playlists:
    if os.path.isfile(playlist_arg) and Path(playlist_arg).suffix == ".m3u":
        process_m3u(playlist_arg, Path(args.library))

    else:
        playlists = (path for path in Path(playlist_arg).glob(r'**/*') if path.suffix == ".m3u" and os.path.isfile(path))

        for m3u in playlists:
            print(str(m3u))
