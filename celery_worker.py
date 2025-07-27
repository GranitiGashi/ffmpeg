from celery import Celery
from app import tasks  # import tasks to register them with celery

# Use environment variables or config file to avoid hardcoding sensitive info
broker_url = "rediss://default:AWx6AAIjcDFjNGYwZDJkYzBkOWY0ZDE3OTBmZWRiZTkxYjYyYzM2MnAxMA@select-quetzal-27770.upstash.io:6379?ssl_cert_reqs=none"
backend_url = broker_url  # using same Redis for backend

celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=backend_url,
)

celery_app.conf.task_track_started = True

# This import registers your tasks with Celery
import app.tasks