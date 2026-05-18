import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, attendance, admin

app = FastAPI(title="NEU AttendAI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/auth",       tags=["Auth"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(admin.router,      prefix="/admin",      tags=["Admin"])

STATIC = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _page(name: str) -> FileResponse:
    return FileResponse(os.path.join(STATIC, name))


@app.get("/",            include_in_schema=False)
async def root():        return _page("login.html")

@app.get("/login",       include_in_schema=False)
async def login_page():  return _page("login.html")

@app.get("/student",     include_in_schema=False)
async def student():     return _page("index.html")

@app.get("/instructor",  include_in_schema=False)
async def instructor():  return _page("instructor.html")

@app.get("/admin-panel", include_in_schema=False)
async def admin_panel(): return _page("admin.html")

@app.get("/health")
async def health():
    return {"status": "ok", "system": "NEU AttendAI v1.0"}
