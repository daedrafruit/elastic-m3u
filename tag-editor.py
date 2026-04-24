import os
import music_tag
from pathlib import Path

audio_extentions = {".ogg" , ".mp3", ".acc", ".wav", ".flac", ".aiff"}
downloads = "/home/daedr/Music/Downloads"
    
paths = (path for path in Path(downloads).glob(r'**/*') if path.suffix in audio_extentions and os.path.isfile(path))
for path in paths:
    file = music_tag.load_file(path)
    print(file['title'])
    if str(file["title"]) == "test":
        file['title'] = "Pest"
        file.save()
        print(file['title'])
