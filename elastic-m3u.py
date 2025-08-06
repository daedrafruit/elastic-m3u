'''
open m3u file
read each path
if a path is not broken, write/update a comment with its metadata

if a path is broken, check if it has a metadata comment
search the library for matching metadata

if matching metadata is found, replace the path:
'''

import os
from tinytag import TinyTag
from pathlib import Path
from pathlib import Path
from collections import defaultdict
import re

library = Path("Library/")
m3u = "test.m3u"
audio_extentions = {".ogg" , ".mp3", ".acc", ".wav", ".flac", ".aiff"}

metadata_path_cache = defaultdict(list)

def build_cache():
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

def extract_m3u_metadata(line):
    pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(pattern, line)
    return {key.lower(): value for key, value in matches}

def get_comment_from_metadata(albumartist, year, album, artist, title):
    return str(f'# ALBUMARTIST="{albumartist}" YEAR="{year}" ARTIST="{artist}" ALBUM="{album}" TITLE="{title}"\n')

def main():
    f_in = open(m3u)

    lines = f_in.readlines()
    if os.path.isfile("tmp_m3u"): os.remove("tmp_m3u")

    f_out = open("tmp_m3u", "x")
    cache_built = False

    prevline = ""
    for line in lines:
        if line.startswith("#"):
            prevline = line
            continue

        path = line.rstrip('\n')
        if not os.path.isfile(path):
            tags = extract_m3u_metadata(prevline)

            if not cache_built: 
                build_cache()
                cache_built = True

            search_path = search_cache(tags["albumartist"], tags["year"], tags["album"], tags["artist"], tags["title"])
            f_out.write(get_comment_from_metadata(tags["albumartist"], tags["year"], tags["artist"], tags["album"], tags["title"]))
            f_out.write(str(search_path[0]) + "\n")

            prevline = line
            continue

        tag: TinyTag = TinyTag.get(path)
        f_out.write(get_comment_from_metadata(tag.albumartist, tag.year, tag.artist, tag.album, tag.title))
        f_out.write(line)
        prevline = line

    f_out = open("tmp_m3u", "r")
    lines = f_out.readlines()
    f_in = open(m3u, "w")
    for line in lines:
        f_in.write(line)
    os.remove("tmp_m3u")

main()
