import re

line = '# ALBUMARTIST=Bossfight YEAR=2017 ARTIST=Nock Em ALBUM=Bossfight TITLE=Nock Em\n'
albumartist = line.split(" ALBUMARTIST=")[1].split(" YEAR=")[0]
year = line.split(" YEAR=")[1].split(" ARTIST=")[0]
artist = line.split(" ARTIST=")[1].split(" ALBUM=")[0]
album = line.split(" ALBUM=")[1].split(" TITLE=")[0]
title = line.split(" TITLE=")[1].rstrip("\n")
print(albumartist)
print(year)
print(artist)
print(album)
print(title)
