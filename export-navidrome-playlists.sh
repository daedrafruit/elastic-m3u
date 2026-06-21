#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -a
source "$SCRIPT_DIR/.env"
set +a

SERVER="https://navidrome.daedrafruit.com"
USER="daedra"
CONTAINER="navidrome"
VOLUME_MAP="/zfs/mnt/media/music/Library:/music/Library"
OUTPUT_MAP="/home/daedr/docker/navidrome:/data"
MOVE_TO="/zfs/mnt/media/music/Navidrome-export"
LIBRARY="/home/daedr/Music/zfs/Library/"
ELASTIC_M3U="/home/daedr/Music/zfs/Tools/elastic-m3u/elastic-m3u.py"

# clear out old playlist files
mkdir -p "$MOVE_TO"
find "$MOVE_TO" -maxdepth 1 -name "*.m3u" -delete

python3 navidrome-playlist-exporter.py \
  --server "$SERVER" \
  --user "$USER" \
  --container "$CONTAINER" \
  --volume-map "$VOLUME_MAP" \
  --output-map "$OUTPUT_MAP" \
  --move-to "$MOVE_TO"

python3 "$ELASTIC_M3U" -p "$MOVE_TO" -l "$LIBRARY" -r

git -C "$MOVE_TO" add -A
git -C "$MOVE_TO" commit -m "Playlist export $(date '+%Y-%m-%d %H:%M:%S')" --quiet
