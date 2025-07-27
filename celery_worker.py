from celery import Celery
import os

from app.video_utils import generate_cool_video
from app.generate import download_images
from transitions import get_random_template

celery_app = Celery(
    "worker",
    broker="rediss://default:AWx6AAIjcDFjNGYwZDJkYzBkOWY0ZDE3OTBmZWRiZTkxYjYyYzM2MnAxMA@select-quetzal-27770.upstash.io:6379?ssl_cert_reqs=none",     # Fill this below
    backend="rediss://default:AWx6AAIjcDFjNGYwZDJkYzBkOWY0ZDE3OTBmZWRiZTkxYjYyYzM2MnAxMA@select-quetzal-27770.upstash.io:6379?ssl_cert_reqs=none"
)

celery_app.conf.task_track_started = True

from app import tasks

@celery_app.task
def generate_video_task(image_urls, job_id):
    tmp_dir = f"tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    output_path = os.path.join(tmp_dir, "output.mp4")

    transitions, template_name = get_random_template()
    image_paths = download_images(image_urls, folder=tmp_dir)
    generate_cool_video(image_paths, output=output_path, transitions=transitions)
    return {"video_path": f"/videos/{job_id}/output.mp4", "template": template_name}