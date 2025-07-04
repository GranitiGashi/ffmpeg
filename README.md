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

video-generator/
├── app/
│ ├── main.py # FastAPI app and API routes
│ ├── video_utils.py # FFmpeg logic & image downloading
│ └── transitions.py # Transition template options
├── tmp/ # Stores generated video files
├── requirements.txt # Python dependencies
├── render.yaml # Render deployment config
└── README.md

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.10 or 3.11 (⚠️ not 3.13)
- `ffmpeg` installed and accessible in your system PATH

---

### 🔧 Installation

1. Clone the repo:

```bash
git clone https://github.com/your-username/video-generator.git
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
