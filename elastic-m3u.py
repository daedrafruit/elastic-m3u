import os
from tinytag import TinyTag
from pathlib import Path
from collections import defaultdict
import argparse

audio_extentions = {".ogg" , ".mp3", ".acc", ".wav", ".flac", ".aiff"}
tag_types = ['albumartist', 'year', 'album', 'track', 'artist', 'title']

metadata_path_cache = defaultdict(lambda: defaultdict(list))

def clean_tag(song_tags, tag_type):
    try:
        tag = song_tags[tag_type]
        if isinstance(tag, list):
            return str(tag[0])
        else:
            return str(tag)
    except:
        return 'None' 

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
            song_tags: dict = tag.as_dict()

            for tag_type in tag_types:
                tag_dict = metadata_path_cache[tag_type]
                tag = clean_tag(song_tags, tag_type)

                tag_dict[tag].append(path)

            cached_files += 1
            if cached_files % 100 == 0: print(f"Files cached: {cached_files}")

    print(f"Total files cached: {cached_files}")
    cache_built = True

def search_cache(song_tags):
    perfect_match = {""}
    for index, tag_type in enumerate(tag_types):
        tag = song_tags[tag_type]
        this_tag_set = set(metadata_path_cache[tag_type][tag])

        if index == 0:
            perfect_match = this_tag_set

        perfect_match = perfect_match & this_tag_set

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
    return metadata 

def read_comment(line):
    dict = {}
    end = len(tag_types) - 1
    for index, tag_type in enumerate(tag_types):
        if index == end:

            dict[tag_type] = line.split(" " + tag_type.upper() + "=")[1].rstrip("\n")

        else:
            dict[tag_type] = line.split(" " + tag_type.upper() + "=")[1].split(" " + tag_types[index+1].upper() + "=")[0]

    return dict

def get_comment(song_tags):
    comment = '# '
    for tag_type in tag_types:
        comment += str(tag_type.upper()) + "="
        comment += clean_tag(song_tags, tag_type) + " " 
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
        is_metadata_comment = line.startswith("# " + tag_types[0].upper())
        prev_is_metadata_comment = prevline.startswith("# " + tag_types[0].upper())
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
