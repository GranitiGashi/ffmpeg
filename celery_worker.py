from celery import Celery

celery_app = Celery(
    "worker",
    broker="rediss://default:AWx6AAIjcDFjNGYwZDJkYzBkOWY0ZDE3OTBmZWRiZTkxYjYyYzM2MnAxMA@select-quetzal-27770.upstash.io:6379?ssl_cert_reqs=none",     # Fill this below
    backend="rediss://default:AWx6AAIjcDFjNGYwZDJkYzBkOWY0ZDE3OTBmZWRiZTkxYjYyYzM2MnAxMA@select-quetzal-27770.upstash.io:6379?ssl_cert_reqs=none"
)

celery_app.conf.task_track_started = True
