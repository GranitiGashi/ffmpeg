# video_utils.py
import subprocess
import os

def generate_cool_video(image_paths, output='output.mp4', transitions=None):
    if len(image_paths) != 10:
        raise ValueError("You must provide exactly 10 images.")

    duration = 3
    transition = 1
    input_args = []

    for img in image_paths:
        input_args.extend(["-loop", "1", "-t", str(duration), "-i", img])

    filters = []
    for i in range(len(image_paths)):
        filters.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuva420p,setsar=1[v{i}]"
        )

    if transitions is None:
        transitions = ["fade"] * (len(image_paths) - 1)

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

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("FFmpeg failed")
