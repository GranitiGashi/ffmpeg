import os
import subprocess
import requests
import random

def download_images(urls, folder='images'):
    os.makedirs(folder, exist_ok=True)
    paths = []
    for i, url in enumerate(urls):
        filename = os.path.join(folder, f'image{i+1}.jpg')
        if not os.path.exists(filename):
            print(f"Downloading {url} -> {filename}")
            resp = requests.get(url)
            resp.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(resp.content)
        paths.append(filename)
    return paths

def generate_cool_video(image_paths, output='output.mp4', transitions=None):
    if len(image_paths) != 10:
        raise ValueError("You must provide exactly 10 images.")

    duration = 3       # seconds each image is fully visible
    transition = 1     # seconds for each transition effect
    input_args = []

    # Prepare ffmpeg input args (loop images for 'duration' seconds)
    for img in image_paths:
        input_args.extend(["-loop", "1", "-t", str(duration), "-i", img])

    # Prepare filter chains to scale and pad images to 1080x1920, keep aspect ratio
    filters = []
    for i in range(len(image_paths)):
        filters.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuva420p,setsar=1[v{i}]"
        )

    if transitions is None:
        transitions = [
            "fade", "slideleft", "slideright", "circlecrop", "rectcrop",
            "distance", "slideup", "slidedown", "smoothleft"
        ]

    # Build xfade filters chaining each transition
    for i in range(len(image_paths) - 1):
        trans = transitions[i % len(transitions)]
        offset = (duration - transition) * i + duration - transition
        if i == 0:
            filters.append(f"[v0][v1]xfade=transition={trans}:duration={transition}:offset={offset}[x0]")
        else:
            filters.append(f"[x{i-1}][v{i+1}]xfade=transition={trans}:duration={transition}:offset={offset}[x{i}]")

    last_output = f"[x{len(image_paths) - 2}]"
    filter_chain = ";".join(filters) + f";{last_output}format=yuv420p[v]"

    total_duration = duration + (duration - transition) * (len(image_paths) - 2)

    cmd = [
        "ffmpeg",
        "-y",
        *input_args,
        "-filter_complex", filter_chain,
        "-map", "[v]",
        "-t", str(total_duration),
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        output
    ]

    print("🌀 Generating video with cool transitions...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg error:")
        print(result.stderr)
        raise RuntimeError("FFmpeg failed")
    print(f"✅ Done! Video saved to {output}")

if __name__ == "__main__":
    image_urls = [
        "https://img.classistatic.de/api/v1/mo-prod/images/5c/5cca08a8-4aec-401c-9015-44c3ee89ee55?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/8c/8c8ce39a-8a20-402e-aa46-2a6f6be15e60?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/0f/0f559ab1-1f69-44f8-8fe3-7b02daa9ca8c?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/88/889bda73-d184-4bb5-88fc-46398a596b52?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/55/5508123f-c9aa-4272-8d67-2ea68d904a33?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/69/69912411-775b-4bbf-bf15-1bd59a9be822?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/a6/a6318ddf-eaa5-4144-be6c-caadd4921281?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/8a/8a5fdfa0-7fb5-4f09-8bb3-2acc6b631199?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/98/987ad68c-de32-47d1-b98a-003b1852ea39?rule=mo-1600.jpg",
        "https://img.classistatic.de/api/v1/mo-prod/images/50/506d1a7f-477e-4323-a5f4-206d1bf95c2b?rule=mo-1600.jpg"
    ]

    # Download images
    images = download_images(image_urls)

    # Define multiple transition templates
    transition_templates = {
        "classic": ["fade"] * 9,
        "slide": ["slideleft", "slideright", "slideup", "slidedown", "slideleft", "slideright", "slideup", "slidedown", "slideleft"],
        "mix": ["fade", "slideleft", "circlecrop", "rectcrop", "distance", "slideup", "slidedown", "smoothleft", "slideright"],
        "random": ["fade", "slideleft", "slideright", "circlecrop", "rectcrop", "distance", "slideup", "slidedown", "smoothleft"],
    }

    # Randomly select one template
    chosen_template_name = random.choice(list(transition_templates.keys()))
    chosen_transitions = transition_templates[chosen_template_name]
    print(f"Using transition template: {chosen_template_name}")

    # Generate video with chosen transitions
    generate_cool_video(images, transitions=chosen_transitions)
