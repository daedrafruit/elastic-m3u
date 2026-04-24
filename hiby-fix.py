from pathlib import Path
import argparse
import os

def fix(m3u_path, base):
    tmp_path = ".tmp_m3u"
    if os.path.isfile(tmp_path): os.remove(tmp_path)
    tmp = open(tmp_path, "x")
    m3u = open(m3u_path)

    lines = m3u.readlines()
    for line in lines:

        is_comment_or_blank = line.startswith("#") or line.isspace()
        if is_comment_or_blank:
            tmp.write(line)
            continue

        new_line = "a:/" + base + line.split(base)[1]
        tmp.write(new_line.replace('/', '\\'))
    os.remove(m3u_path)
    os.rename(tmp_path, m3u_path)
                


parser = argparse.ArgumentParser(prog='elastic-m3u')
parser.add_argument('-p', '--playlists', required=True, nargs='*')
parser.add_argument('-b', '--base', required=True)
args = parser.parse_args()

for playlist_arg in args.playlists:
    if os.path.isfile(playlist_arg) and Path(playlist_arg).suffix == ".m3u":
        print("Processing: " + Path(playlist_arg).name)
        fix(playlist_arg, args.base)

    else:
        playlists = (path for path in Path(playlist_arg).glob(r'**/*') if path.suffix == ".m3u" and os.path.isfile(path))

        for m3u in playlists:
            print("Processing: " + m3u.name)
            fix(m3u, args.base)

