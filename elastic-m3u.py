'''
open m3u file
read each path
if a path is not broken, write/update a comment with its metadata

if a path is broken, check if it has a metadata comment
search the library for matching metadata

if matching metadata is found, replace the path:
'''

import os
import glob
from tinytag import TinyTag
from pathlib import Path

library = Path("Library/")
audio_extentions = {".ogg"}

paths = (path for path in library.glob(r'**/*') if path.suffix in audio_extentions)
for path in paths:
    print(path)
    tag: TinyTag = TinyTag.get(path)
    print(f"# ALBUMARTIST={tag.albumartist} YEAR={tag.year} ALBUM={tag.album} TITLE={tag.title}\n")



f_in = open("test.m3u")

lines = f_in.readlines()

f_out = open("out.m3u", "x")

for line in lines:
    if line.startswith("#"):
        continue

    path = line.rstrip('\n')
    if not os.path.isfile(path):
        continue

    tag: TinyTag = TinyTag.get(path)
    f_out.write(f"# ALBUMARTIST={tag.albumartist} YEAR={tag.year} ALBUM={tag.album} TITLE={tag.title}\n")
    f_out.write(line)

f_out = open("out.m3u", "r")
lines = f_out.readlines()
for line in lines:
    print(line)

os.remove("out.m3u")

