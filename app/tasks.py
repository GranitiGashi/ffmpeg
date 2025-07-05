import os
import uuid
import boto3
from botocore.config import Config
from app.generate import download_images
from app.video_utils import generate_cool_video
from celery_worker import celery_app

R2_BUCKET = os.getenv("R2_BUCKET")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")

# Setup R2 client (S3-compatible)
s3 = boto3.client(
    "s3",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    endpoint_url=R2_ENDPOINT,
    config=Config(signature_version="s3v4"),
    region_name="auto"
)

@celery_app.task(bind=True)
def generate_video_task(self, image_urls: list):
    job_id = str(uuid.uuid4())
    tmp_dir = f"tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    output_path = os.path.join(tmp_dir, "output.mp4")

    try:
        image_paths = download_images(image_urls, folder=tmp_dir)
        generate_cool_video(image_paths, output=output_path)

        # Upload to R2
        with open(output_path, "rb") as f:
            s3.upload_fileobj(f, R2_BUCKET, f"videos/{job_id}.mp4",  ExtraArgs={"ACL": "public-read"})

        # Clean up
        for path in image_paths:
            os.remove(path)
        os.remove(output_path)
        os.rmdir(tmp_dir)

        return {
            "status": "completed",
            "video_url": f"{R2_ENDPOINT}/{R2_BUCKET}/videos/{job_id}.mp4"
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}
