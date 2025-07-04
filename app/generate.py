import os
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
        paths.append(filename)
    return paths