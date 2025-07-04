import os
import subprocess
import requests

def download_images(urls, folder):
    os.makedirs(folder, exist_ok=True)
    paths = []
    for i, url in enumerate(urls):
        filename = os.path.join(folder, f'image{i+1}.jpg')
        resp = requests.get(url)
        resp.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(resp.content)

        # Resize the image to max 720x1280 using ffmpeg
        resized_filename = filename  # overwrite same file
        resize_cmd = [
            "ffmpeg",
            "-y",
            "-i", filename,
            "-vf", "scale='min(720,iw)':'min(1280,ih)':force_original_aspect_ratio=decrease",
            resized_filename
        ]
        result = subprocess.run(resize_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg resize error: {result.stderr}")
            raise RuntimeError("Image resizing failed")

        paths.append(resized_filename)
    return paths
