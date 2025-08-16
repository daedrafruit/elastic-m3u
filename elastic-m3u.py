import os
from tinytag import TinyTag
from pathlib import Path
from collections import defaultdict
import argparse

audio_extentions = {".ogg" , ".mp3", ".acc", ".wav", ".flac", ".aiff"}
metadata_path_cache = defaultdict(lambda: defaultdict(list))
tag_types = ['albumartist', 'year', 'album', 'artist', 'title']


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
            metadata: dict = tag.as_dict()

            for tag_type in tag_types:
                try:
                    metadata_path_cache[tag_type][metadata[tag_type][0]].append(path)
                except:
                    metadata_path_cache[tag_type]['None'].append(path)

            cached_files += 1
            if cached_files % 100 == 0: print(f"Files cached: {cached_files}")

    print(f"Total files cached: {cached_files}")
    cache_built = True



def search_cache(song_tags):

    perfect_match = set(metadata_path_cache['albumartist'][song_tags['albumartist']])
    for tag_type in tag_types:
        tag = song_tags[tag_type]
        perfect_match = set(perfect_match) & set(metadata_path_cache[tag_type][tag])

    if perfect_match: return list(perfect_match)

    match_scores = defaultdict(int) 
    max = ""
    for tag_type in tag_types:
        tag = song_tags[tag_type]
        for match in metadata_path_cache[tag_type][tag]:

            match_scores[match] += 1

            if tag_type != 'year':
                match_scores[match] += 1

            if match_scores[match] > match_scores[max] : max = match

    print(f"\nCould not find perfect match for:")
    print(get_comment(song_tags), end="")
    print("\n    Is '" + str(max) + "' OK? (y/n)")
    print(get_comment(get_tags_from(max)), end="")

    response = input()
    if response.lower() == "y":
        return list({max})

    sorted_matches = dict(sorted(match_scores.items(), key=lambda item: item[1], reverse=True))
    for i, match in enumerate(sorted_matches): 
        if sorted_matches[match] > 1:
            print(str(i) + ": " + str(match) + " (Confidence: " + str(sorted_matches[match]) + ")")

    print("\n    Select a value or (s)kip:")
    response = input()

    if response.lower() == "s":
        print(get_comment(song_tags), end="")
        return list({})
    
    return list({list(sorted_matches)[int(response)]})


def get_tags_from(path):
    tag: TinyTag = TinyTag.get(path)
    metadata: dict = tag.as_dict()
    song_tags = {}
    for tag_type in tag_types:
        try:
            song_tags[tag_type] = metadata[tag_type][0]
        except:
            song_tags[tag_type] = 'None'

    return song_tags

def read_comment(line):
    dict = {}
    dict["albumartist"] = line.split(" ALBUMARTIST=")[1].split(" YEAR=")[0]
    dict["year"] = line.split(" YEAR=")[1].split(" ALBUM=")[0]
    dict["album"] = line.split(" ALBUM=")[1].split(" ARTIST=")[0]
    dict["artist"] = line.split(" ARTIST=")[1].split(" TITLE=")[0]
    dict["title"] = line.split(" TITLE=")[1].rstrip("\n")
    return dict

def get_comment(song_tags):
    comment = '# '
    for tag_type in tag_types:
        comment += str(tag_type.upper()) + "="
        comment += str(song_tags[tag_type]) + " " 
    return comment.rstrip() + "\n"


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
            song_tags = get_tags_from(fixed_path)

            new_comment = get_comment(song_tags)

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

        tags = read_comment(prevline)
        found_paths = search_cache(tags)

        if not found_paths:
            tmp.write(prevline)
            tmp.write(line)
            prevline = line
            continue

        found_path = found_paths[0]

        rel_path = os.path.relpath(found_path, Path(m3u_path).parent) + '\n'

        song_tags = get_tags_from(found_path)
        new_comment = (get_comment(song_tags))

        tmp.write(new_comment)

        if relative:
            tmp.write(rel_path)
        else:
            tmp.write(str(found_path) + "\n")

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
