# 🎬 Video Generator API (FastAPI + FFmpeg)

A FastAPI-based microservice that creates vertical videos (1080x1920) from exactly 10 image URLs, applying smooth transitions using `ffmpeg`. Ideal for social content generation and integration with tools like `n8n`.

---

## 📦 Features

- 🔟 Accepts exactly 10 image URLs
- 🎨 Multiple transition styles (fade, slide, crop, etc.)
- ⚡️ Fast API response
- 🧰 Easily deployable on Render
- 📂 Temporary video storage with direct access endpoint

---

## 🧱 Project Structure

```bash
video-generator/
├── app/
│ ├── main.py # FastAPI app and API routes
│ ├── video_utils.py # FFmpeg logic & image downloading
│ └── transitions.py # Transition template options
├── tmp/ # Stores generated video files
├── requirements.txt # Python dependencies
├── render.yaml # Render deployment config
└── README.md
```
---

```app```
### auth.py – User Authentication Routes (Sign Up, Login, Logout)

Handles basic authentication via Supabase for a FastAPI app using HTML forms.

📄 Routes Included:
─────────────────────
1. GET  /signup   – Show sign-up form (admin only)
2. POST /signup   – Create new user (Supabase + hashed password)
3. GET  /login    – Show login form
4. POST /login    – Validate user credentials and start session
5. GET  /logout   – Clear session and log user out

🛠️ Features:
- Uses Jinja2 templates for forms
- Passwords are hashed using bcrypt
- Session stores authenticated user info

----------

### client_config.py – Client Webhook Configuration

Stores a list of known clients and their corresponding n8n webhook URLs.

🔧 Structure:
Each client is identified by:
- email: unique identifier
- n8n_webhook: URL to post Facebook access tokens

🔍 Function:
get_n8n_webhook_by_email(email: str) -> str | None
    Looks up a client's webhook URL based on their email.
    Returns the webhook URL if found, otherwise returns None.

----------


### fb_oauth.py – Facebook OAuth Login & Page Access Token Handling

Enables users to log in with Facebook and connect their Facebook Page and Instagram Business Account.

🔐 Endpoints:
────────────────────────────────────────────
1. GET /fb/login
   - Redirects authenticated users to Facebook OAuth dialog.
   - Requests permissions: `pages_show_list`, `pages_manage_posts`.

2. GET /fb/callback
   - Handles Facebook’s redirect with auth code.
   - Exchanges for long-lived access token.
   - Fetches Facebook Page + Instagram Business ID.
   - Saves data to Supabase using upsert_social_record().

🧠 Key Logic:
- Uses Facebook Graph API v19.0
- Tokens are exchanged securely via `client_secret`
- Page access token and IG ID are saved for later use
- Only the first FB page is selected by default

🛠️ Env Variables:
- FACEBOOK_APP_ID
- FACEBOOK_APP_SECRET
- BASE_DOMAIN

📦 Dependencies:
- `requests` for external API calls
- `uuid` to generate unique state values
- `dotenv` for env loading

----------


### video_utils.py – Image Downloader & Resizer (for Video Generation)

Downloads images from URLs and resizes them using FFmpeg to fit within 720x1280 dimensions,
while preserving aspect ratio – ideal for vertical video creation.

🔧 Function:
────────────────────────────────────────────
download_images(urls: list[str], folder: str) -> list[str]
    - Downloads images from given URLs to the specified folder.
    - Uses FFmpeg to resize each image to max 720x1280 (vertical format).
    - Returns a list of local image file paths.

🛠️ Dependencies:
- `requests` – fetches image data from the web.
- `os` and `subprocess` – handles filesystem and runs FFmpeg commands.
- `ffmpeg` must be installed and available in system PATH.

📦 Used In:
- Video generation pipeline (before passing images to FFmpeg to make a video)

----------

### main.py – FastAPI Application Entry Point

This is the main setup file for the app, handling routing, middleware, templating,
static files, and core page views.

📌 Features:
────────────────────────────────────────────
- Sets up the FastAPI app with session support
- Adds routers for:
  • Authentication (`/login`, `/signup`, `/logout`)
  • Facebook OAuth (`/fb/login`, `/fb/callback`)
- Serves static files (CSS, JS, images)
- Renders HTML pages with Jinja2 templates
- Includes health check for deployment (e.g., Render)

🛠️ Routes:
────────────────────────────────────────────
- GET /health      – Health check (returns {status: "ok"})
- GET /            – Home page (redirects to /login if not authenticated)
- GET /connect     – Friendly alias to start Facebook OAuth
- /static/*        – Serves static assets from `/static` folder

🔐 Middleware:
- SessionMiddleware for user sessions (change the default secret key!)

📦 Dependencies:
- `Jinja2Templates` for rendering HTML
- `SessionMiddleware` for tracking login sessions
- `StaticFiles` for public assets

💡 Tip:
Replace `"super-secret"` with a secure random key in production!

----------

### supabase_client.py – Supabase Integration Helpers

Handles all interactions with Supabase for:
- User authentication (create user, verify password)
- Managing user records in `users_app` table
- Managing Facebook/Instagram data in `social_accounts` table

📌 Features:
────────────────────────────────────────────
- 🔑 `create_supabase_user(email, password)`  
    Creates a user via Supabase Auth and returns the UUID.

- 🔒 `verify_password(plain, hashed)`  
    Compares a plain password with a hashed one using bcrypt.

- 🔐 `hash_pw(plain)`  
    Returns a securely hashed password using bcrypt.

- 📥 `insert_user_record(uid, email, hashed_pw)`  
    Inserts a new user into the `users_app` table.

- 🔄 `upsert_social_record(uid, page_id, page_tok, ig_id)`  
    Adds or updates the user's connected FB/IG data.

- 📤 `get_user_record(email)`  
    Fetches user row by email from `users_app`.

- 📦 `get_social_by_uid(uid)`  
    Returns the stored Facebook page token and Instagram ID.

🛠️ Notes:
- Uses `supabase-py` client
- Requires `.env` file with `SUPABASE_URL` and `SUPABASE_KEY` (but hardcoded here — ⚠️ avoid in production!)

📂 Tables Involved:
- `users_app` → custom table storing user emails + hashed passwords
- `social_accounts` → stores Facebook Page ID, token, and IG Business Account ID

----------

### generate_video_task.py – Async Video Generation & R2 Upload (Celery Task)

Defines a background Celery task that:
1. Downloads images
2. Generates a video using transitions
3. Uploads the final video to Cloudflare R2 (S3-compatible)
4. Cleans up temporary files

🌀 Task:
────────────────────────────────────────────
generate_video_task(image_urls: list[str]) -> dict
    - Downloads 10 image URLs
    - Generates vertical video with transitions
    - Uploads video to R2 storage (public)
    - Returns a dictionary with:
        { "status": "completed", "video_url": "..." }
      or
        { "status": "failed", "error": "..." }

🛠️ Cloudflare R2 Configuration:
- `R2_BUCKET` – Bucket name
- `R2_ACCESS_KEY` – Access key
- `R2_SECRET_KEY` – Secret key
- `R2_ENDPOINT` – R2-compatible S3 endpoint
- `R2_PUBLIC_URL` – Base URL to access uploaded videos

🔧 Dependencies:
- `boto3` – for R2 upload (S3 protocol)
- `celery` – to run the task asynchronously
- `uuid`, `os` – for job IDs and file handling

📂 Output Path:
- Videos are temporarily stored in `tmp/{job_id}/output.mp4`

💡 Tip:
Ensure your `.env` file contains the required R2 keys before running this task.

----------


### generate_cool_video.py – Generate a Vertical Video with Transitions using FFmpeg

Creates a smooth, fullscreen (1080x1920) video from exactly 10 images, applying
custom transitions (e.g. `fade`, `slide`) using FFmpeg’s `xfade` filter.

📸 Function:
────────────────────────────────────────────
generate_cool_video(
    image_paths: list[str],
    output: str = 'output.mp4',
    transitions: list[str] = None
)

🔁 Process:
1. Loops over 10 input images (each shown for 3 seconds)
2. Applies scaling, padding, and formatting to fit 1080x1920 (black background)
3. Uses `xfade` for smooth transitions between clips
4. Compiles everything into a 30fps H.264 `.mp4` video

🎛️ Parameters:
- image_paths: List of 10 local image paths (required)
- output: Output filename (default: `output.mp4`)
- transitions: List of 9 transitions (default: all `"fade"`)

📦 Requirements:
- FFmpeg must be installed and available in system PATH

❌ Raises:
- `ValueError` if the number of images is not exactly 10
- `RuntimeError` if FFmpeg fails to generate the video

💡 Example:
Use with `download_images()` and pass the result to this function
to generate a vertical video ready for Reels, Shorts, or TikTok.

----------

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.10 or 3.11 (⚠️ not 3.13)
- `ffmpeg` installed and accessible in your system PATH

---

### 🔧 Installation

1. Clone the repo:

```bash
git clone https://github.com/GranitiGashi/ffmpeg.git
cd video-generator
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Run the API locally:
```bash
uvicorn app.main:app --reload
```

### 🧪 API Usage
```bash
POST /generate-video/
```
### Generate a video from exactly 10 image URLs.
```bash
{
  "image_urls": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "...",
    "https://example.com/image10.jpg"
  ]
}
```
### ✅ Response:
```bash

{
  "status": "success",
  "video_path": "/videos/<job_id>/output.mp4",
  "template_used": "mix"
}
```

### Returns the video file generated using the job ID from the response.
```bash
GET /videos/{job_id}/output.mp4
```
