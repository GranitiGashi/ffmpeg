from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import router as auth_router
from app.fb_oauth import router as fb_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret")  # use a secure key

app.include_router(auth_router)
app.include_router(fb_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
