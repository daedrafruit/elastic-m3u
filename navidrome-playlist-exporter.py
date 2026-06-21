import argparse
import os
import subprocess
import requests
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--server", required=True, help="Navidrome server URL")
parser.add_argument("--user", required=True, help="Navidrome username")
parser.add_argument("--container", default="navidrome", help="Docker container name")
parser.add_argument("--volume-map", required=True,
                     help="host_path:container_path (taken from docker container directly)")
parser.add_argument("--output-map", required=True,
                     help="host_path:container_path (taken from docker container directly)")
parser.add_argument("--move-to", help="Host directory to move the finished .m3u files into")
args = parser.parse_args()

password = os.environ["NAVIDROME_PASS"]

host_path, container_path = args.volume_map.split(":")
host_output_dir, container_output_dir = args.output_map.split(":")

params = {"u": args.user, "p": password, "c": "my-script", "f": "json", "v": "1.15.0"}
resp = requests.get(f"{args.server}/rest/getPlaylists", params=params).json()
playlists = resp["subsonic-response"]["playlists"]["playlist"]

for p in playlists:
    name = p["name"].replace("/", "_")
    container_file = f"{container_output_dir}/{name}.m3u"
    host_file = f"{host_output_dir}/{name}.m3u"

    subprocess.run([
        "docker", "exec", args.container,
        "/app/navidrome", "pls",
        "-p", p["id"],
        "-o", container_file
    ])

    # rewrite the track paths inside the m3u from container paths to host paths
    with open(host_file, "r") as f:
        content = f.read()

    content = content.replace(container_path, host_path)

    with open(host_file, "w") as f:
        f.write(content)

    if args.move_to:
        os.makedirs(args.move_to, exist_ok=True)
        dest = os.path.join(args.move_to, f"{name}.m3u")
        shutil.move(host_file, dest)
        host_file = dest

    cover_id = p.get("coverArt")
    if cover_id:
        cover_dir = args.move_to if args.move_to else host_output_dir
        cover_params = {"u": args.user, "p": password, "c": "my-script", "f": "json", "v": "1.15.0", "id": cover_id}
        cover_resp = requests.get(f"{args.server}/rest/getCoverArt", params=cover_params)
        if cover_resp.ok and cover_resp.headers.get("Content-Type", "").startswith("image/"):
            ext = cover_resp.headers["Content-Type"].split("/")[-1]
            cover_path = os.path.join(cover_dir, f"{name}.{ext}")
            with open(cover_path, "wb") as f:
                f.write(cover_resp.content)
