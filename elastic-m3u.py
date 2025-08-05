#!/usr/bin/python

'''
open m3u file
read each path
if a path is not broken, write/update a comment with its metadata

if a path is broken, check if it has a metadata comment
search the library for matching metadata

if matching metadata is found, replace the path
'''


import os

f_in = open("test.m3u")

lines = f_in.readlines()
for line in lines:
    print(line)

f_out = open("out.m3u", "x")
for line in lines:
    if not line.startswith("# ALBUMARTIST="):
        f_out.write(line)

f_out = open("out.m3u", "r")
lines = f_out.readlines()
for line in lines:
    print(line)

os.remove("out.m3u")
