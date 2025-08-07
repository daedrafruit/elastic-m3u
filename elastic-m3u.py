import os
from tinytag import TinyTag
from pathlib import Path
from collections import defaultdict
import argparse

audio_extentions = {".ogg" , ".mp3", ".acc", ".wav", ".flac", ".aiff"}

metadata_path_cache = defaultdict(list)
global cache_built

def build_cache(libraries):
    global cache_built
    if cache_built: return
    cached_files = 0

    for library in libraries:
        print("Caching: " + str(Path(library)))
        paths = (path for path in Path(library).glob(r'**/*') if path.suffix in audio_extentions and os.path.isfile(path))
        for path in paths:

            tag: TinyTag = TinyTag.get(path)

            metadata_path_cache[tag.albumartist].append(path)
            metadata_path_cache[tag.year].append(path)
            metadata_path_cache[tag.album].append(path)
            metadata_path_cache[tag.artist].append(path)
            metadata_path_cache[tag.title].append(path)

            cached_files += 1
            if cached_files % 100 == 0: print(f"Files cached: {cached_files}")

    cache_built = True

def search_cache(albumartist, year, album, artist, title):
    result = list(set(metadata_path_cache[albumartist]) & set(metadata_path_cache[year]) & set(metadata_path_cache[artist]) & set(metadata_path_cache[album]) & set(metadata_path_cache[title]))
    if not result:
        print(f"ERROR: could not find: ALBUMARTIST={albumartist}, YEAR={year}, ALBUM={album}, ARTIST={artist}, TITLE={title}")
    return result

def get_metadata(line):
    dict = defaultdict(list)
    dict["albumartist"] = line.split(" ALBUMARTIST=")[1].split(" YEAR=")[0]
    dict["year"] = line.split(" YEAR=")[1].split(" ARTIST=")[0]
    dict["artist"] = line.split(" ARTIST=")[1].split(" ALBUM=")[0]
    dict["album"] = line.split(" ALBUM=")[1].split(" TITLE=")[0]
    dict["title"] = line.split(" TITLE=")[1].rstrip("\n")
    return dict

def get_comment(albumartist, year, album, artist, title):
    return str(f'# ALBUMARTIST={albumartist} YEAR={year} ARTIST={artist} ALBUM={album} TITLE={title}\n')

def process_m3u(m3u_path, libraries, relative):
    tmp_path = ".tmp_m3u"
    if os.path.isfile(tmp_path): os.remove(tmp_path)
    tmp = open(tmp_path, "x")
    m3u = open(m3u_path)

    prevline = ""

    lines = m3u.readlines()
    for line in lines:
        path = line.rstrip('\n')
        fixed_path = os.path.abspath(os.path.join(Path(m3u_path).parent, path))
        is_metadata_comment = line.startswith("# ALBUMARTIST=")
        prev_is_metadata_comment = prevline.startswith("# ALBUMARTIST=")
        is_comment_or_blank = line.startswith("#") or line.isspace()

        is_unbroken_path = os.path.isfile(fixed_path)

        if is_metadata_comment:
            prevline = line
            continue

        if is_comment_or_blank:
            tmp.write(line)
            prevline = line
            continue

        if is_unbroken_path:
            tag: TinyTag = TinyTag.get(fixed_path)
            new_comment = get_comment(tag.albumartist, tag.year, tag.artist, tag.album, tag.title)

            tmp.write(new_comment)
            tmp.write(line)
            prevline = line
            continue

        if not prev_is_metadata_comment:
            print("No metadata comment found for: " + line, end='')
            tmp.write(line)
            prevline = line
            continue

        build_cache(libraries)

        tags = get_metadata(prevline)
        found_paths = search_cache(tags["albumartist"], tags["year"], tags["album"], tags["artist"], tags["title"])

        if not found_paths:
            tmp.write(prevline)
            tmp.write(line)
            prevline = line
            continue

        found_path = found_paths[0]

        rel_path = os.path.relpath(found_path, Path(m3u_path).parent) + '\n'
        abs_path = os.path.abspath(rel_path)
        new_comment = (get_comment(tags["albumartist"], tags["year"], tags["artist"], tags["album"], tags["title"]))

        tmp.write(new_comment)

        if relative:
            tmp.write(rel_path)
        else:
            tmp.write(abs_path)

        prevline = line

    os.remove(m3u_path)
    os.rename(tmp_path, m3u_path)


parser = argparse.ArgumentParser(prog='elastic-m3u')
parser.add_argument('-l', '--libraries', required=True, nargs='*')
parser.add_argument('-p', '--playlists', required=True, nargs='*')
parser.add_argument('-r', '--relative', action="store_true")
args = parser.parse_args()

cache_built = False
for playlist_arg in args.playlists:
    if os.path.isfile(playlist_arg) and Path(playlist_arg).suffix == ".m3u":
        print("Processing: " + Path(playlist_arg).name)
        process_m3u(playlist_arg, args.libraries, args.relative)

    else:
        playlists = (path for path in Path(playlist_arg).glob(r'**/*') if path.suffix == ".m3u" and os.path.isfile(path))

        for m3u in playlists:
            print("Processing: " + m3u.name)
            process_m3u(m3u, args.libraries, args.relative)
