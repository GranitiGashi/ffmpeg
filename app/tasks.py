import os
import uuid
import shutil
import boto3
from botocore.config import Config
from app.generate import download_images
from app.video_utils import generate_cool_video
from celery_worker import celery_app

# Environment variables
R2_BUCKET = os.getenv("R2_BUCKET")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")  # Example: https://cdn.yourdomain.com

# Setup boto3 client for R2 (Cloudflare R2 or other S3-compatible storage)
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
    tmp_dir = os.path.join("tmp", job_id)
    output_filename = "output.mp4"
    output_path = os.path.join(tmp_dir, output_filename)

    try:
        os.makedirs(tmp_dir, exist_ok=True)

        # 1. Download images
        image_paths = download_images(image_urls, folder=tmp_dir)

        # 2. Generate video
        generate_cool_video(image_paths, output=output_path)

        # 3. Upload video to R2
        key = f"videos/{job_id}.mp4"
        with open(output_path, "rb") as f:
            s3.upload_fileobj(f, R2_BUCKET, key, ExtraArgs={"ACL": "public-read"})

        # 4. Return video URL
        video_url = f"{R2_PUBLIC_URL}/{key}"

        return {
            "status": "completed",
            "video_url": video_url
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        # 5. Clean up temporary files
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
