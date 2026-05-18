import os
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.models.models import LoginRequest, RegisterRequest, TokenResponse
from app.db.mongo import users_collection

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "neu-attend-ai-secret-2026")
ALGORITHM  = os.getenv("ALGORITHM",  "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer(auto_error=False)
router  = APIRouter()

# Fixed staff credentials (demo/pilot)
STAFF = {
    "instructor1": {"password": "instructor123", "role": "instructor", "name": "PROF. DR. DUYGU ÇELİK"},
    "instructor2": {"password": "instructor123", "role": "instructor", "name": "ASSOC. PROF. DR. YILTAN BİTİRİM"},
    "admin":       {"password": "admin123",       "role": "admin",      "name": "System Administrator"},
}


def _valid_neu_id(sid: str) -> bool:
    """NEU student IDs: all digits, 6-10 characters."""
    return bool(re.fullmatch(r"\d{6,10}", sid))


def _make_token(data: dict) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _decode(creds.credentials)


# ── Register (students only) ───────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    sid = req.student_id.strip()

    if not _valid_neu_id(sid):
        raise HTTPException(
            status_code=400,
            detail="Invalid student ID. Must be all-numeric (6-10 digits), e.g. 24700035",
        )
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await users_collection.find_one({"user_id": sid, "role": "student"})
    if existing:
        raise HTTPException(status_code=409, detail="This ID is already registered. Please sign in.")

    await users_collection.insert_one({
        "user_id":         sid,
        "hashed_password": pwd_ctx.hash(req.password),
        "role":            "student",
        "full_name":       req.full_name.strip() if req.full_name else "",
        "registered_at":   datetime.now(),
    })

    token = _make_token({"sub": sid, "role": "student", "name": req.full_name or ""})
    return TokenResponse(access_token=token, role="student",
                         user_id=sid, full_name=req.full_name or "")


# ── Login ──────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    uid  = req.user_id.strip()
    role = req.role.strip().lower()

    # Staff login
    if role in ("instructor", "admin"):
        acc = STAFF.get(uid)
        if not acc or acc["password"] != req.password or acc["role"] != role:
            raise HTTPException(status_code=401, detail="Invalid staff credentials")
        token = _make_token({"sub": uid, "role": role, "name": acc["name"]})
        return TokenResponse(access_token=token, role=role,
                             user_id=uid, full_name=acc["name"])

    # Student login
    if role == "student":
        if not _valid_neu_id(uid):
            raise HTTPException(status_code=400, detail="Invalid student ID format")

        user = await users_collection.find_one({"user_id": uid, "role": "student"})
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Student ID not registered. Please create an account first.",
            )
        if not pwd_ctx.verify(req.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect password")

        name  = user.get("full_name", "")
        token = _make_token({"sub": uid, "role": "student", "name": name})
        return TokenResponse(access_token=token, role="student",
                             user_id=uid, full_name=name)

    raise HTTPException(status_code=400, detail="Role must be student, instructor, or admin")


# ── Helpers ────────────────────────────────────────────────────────────────
@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@router.get("/check-registered/{student_id}")
async def check_registered(student_id: str):
    if not _valid_neu_id(student_id.strip()):
        return {"registered": False, "valid_id": False}
    doc = await users_collection.find_one(
        {"user_id": student_id.strip(), "role": "student"}, {"_id": 0, "user_id": 1}
    )
    return {"registered": bool(doc), "valid_id": True}
