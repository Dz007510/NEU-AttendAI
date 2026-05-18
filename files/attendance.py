from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.db.mongo import attendance_collection, roster_collection, sessions_collection
from app.logic.distance import is_inside_classroom
from app.logic.token_logic import verify_token, generate_token, get_active_token
from app.logic.fraud_detection import check_impossible_travel, check_gps_spoofing
from app.logic.policy_engine import calculate_status
from app.routes.auth import get_current_user
from app.models.models import AttendanceCheck, SessionActivate

router = APIRouter()

# Set True for demo — disables GPS/token checks so you can test locally
DEMO_MODE = True


# ── QR Token ───────────────────────────────────────────────────────────────
@router.post("/generate-token/{course_id}")
async def gen_token(course_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructors only")
    return generate_token(course_id)


@router.get("/active-token/{course_id}")
async def active_token(course_id: str, user: dict = Depends(get_current_user)):
    t = get_active_token(course_id)
    if not t:
        raise HTTPException(status_code=404, detail="No active token")
    return {"token": t}


# ── Session ────────────────────────────────────────────────────────────────
@router.post("/activate-session")
async def activate_session(data: SessionActivate, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructors only")
    doc = {
        "course_code":  data.course_code,
        "room":         data.room,
        "day":          data.day,
        "time_slot":    data.time_slot,
        "instructor":   data.instructor,
        "source":       data.source,
        "activated_by": user.get("sub"),
        "activated_at": datetime.now(),
        "is_active":    True,
    }
    await sessions_collection.update_one(
        {"course_code": data.course_code}, {"$set": doc}, upsert=True
    )
    return {"status": "activated", "token_info": generate_token(data.course_code)}


@router.post("/deactivate-session/{course_id}")
async def deactivate_session(course_id: str, user: dict = Depends(get_current_user)):
    await sessions_collection.update_one(
        {"course_code": course_id}, {"$set": {"is_active": False}}
    )
    return {"status": "deactivated"}


# ── Check-in ───────────────────────────────────────────────────────────────
@router.post("/check-in")
async def check_in(data: AttendanceCheck):
    flags = []

    # 1. QR Token
    if not DEMO_MODE:
        if not verify_token(data.course_id, data.token):
            raise HTTPException(status_code=401, detail="Invalid or expired QR token")

    # 2. GPS Spoofing
    spoof = check_gps_spoofing(
        latitude=data.latitude, longitude=data.longitude,
        accuracy_m=data.accuracy_m, is_mock=data.is_mock or False,
        altitude_zero=data.altitude_zero or False,
    )
    if spoof["flagged"]:
        flags.append({"type": "gps_spoofing", **spoof})
        if not DEMO_MODE and spoof["risk_level"] == "high":
            raise HTTPException(status_code=403, detail="GPS spoofing detected")

    # 3. Geo-Fencing
    if not DEMO_MODE:
        if not is_inside_classroom(data.latitude, data.longitude):
            raise HTTPException(status_code=403, detail="Outside classroom range (>50m)")

    # 4. Impossible Travel
    last = await attendance_collection.find_one(
        {"student_id": data.student_id}, sort=[("timestamp", -1)]
    )
    if last and not DEMO_MODE:
        travel = check_impossible_travel(
            lat1=last.get("latitude", data.latitude),
            lon1=last.get("longitude", data.longitude),
            lat2=data.latitude, lon2=data.longitude,
            last_time=last["timestamp"],
        )
        if travel["flagged"]:
            flags.append({"type": "impossible_travel", **travel})
            raise HTTPException(status_code=403, detail=travel["reason"])

    # 5. Duplicate check
    today = datetime.now().strftime("%Y-%m-%d")
    if await attendance_collection.find_one({
        "student_id": data.student_id,
        "course_id":  data.course_id,
        "date":       today,
    }):
        raise HTTPException(status_code=409, detail="Already checked in today")

    # 6. Registration status
    roster = await roster_collection.find_one({
        "course_id": data.course_id, "official_ids": data.student_id
    })
    reg_status = "official" if roster else "late_registration"

    # 7. Save
    await attendance_collection.insert_one({
        "student_id": data.student_id,
        "course_id":  data.course_id,
        "timestamp":  datetime.now(),
        "date":       today,
        "status":     "Present",
        "reg_status": reg_status,
        "latitude":   data.latitude,
        "longitude":  data.longitude,
        "flags":      flags,
    })
    return {"status": "success", "type": reg_status, "flags": flags}


# ── Session report ─────────────────────────────────────────────────────────
@router.get("/session-report/{course_id}")
async def session_report(course_id: str, user: dict = Depends(get_current_user)):
    today   = datetime.now().strftime("%Y-%m-%d")
    roster  = await roster_collection.find_one({"course_id": course_id})
    off_ids = roster.get("official_ids", []) if roster else []

    logs     = await attendance_collection.find(
        {"course_id": course_id, "date": today}
    ).to_list(1000)
    attended = {l["student_id"]: l for l in logs}

    report = []
    for sid in off_ids:
        if sid in attended:
            ts = attended[sid]["timestamp"]
            t  = ts.strftime("%H:%M") if hasattr(ts, "strftime") else ""
            report.append({"id": sid, "status": "Present", "color": "green",  "type": "Official",          "time": t})
        else:
            report.append({"id": sid, "status": "Absent",  "color": "red",    "type": "Official",          "time": "—"})

    for sid, log in attended.items():
        if sid not in off_ids:
            ts = log["timestamp"]
            t  = ts.strftime("%H:%M") if hasattr(ts, "strftime") else ""
            report.append({"id": sid, "status": "Present", "color": "orange", "type": "Late Registration", "time": t})

    return report


# ── Policy status ──────────────────────────────────────────────────────────
@router.get("/policy-status/{student_id}/{course_id}")
async def policy_status(student_id: str, course_id: str,
                         user: dict = Depends(get_current_user)):
    all_logs = await attendance_collection.find(
        {"course_id": course_id}, {"date": 1}
    ).to_list(10000)
    total = len(set(l["date"] for l in all_logs))
    attended = await attendance_collection.count_documents({
        "student_id": student_id, "course_id": course_id, "status": "Present"
    })
    return calculate_status(student_id, course_id, total, attended)


# ── Policy report (all students in course) ────────────────────────────────
@router.get("/policy-report/{course_id}")
async def policy_report(course_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructors only")

    roster = await roster_collection.find_one({"course_id": course_id})
    if not roster:
        return []

    all_logs = await attendance_collection.find(
        {"course_id": course_id}, {"date": 1}
    ).to_list(10000)
    total = len(set(l["date"] for l in all_logs))

    results = []
    for sid in roster.get("official_ids", []):
        attended = await attendance_collection.count_documents({
            "student_id": sid, "course_id": course_id, "status": "Present"
        })
        results.append(calculate_status(sid, course_id, total, attended))

    results.sort(key=lambda x: x["pct"])
    return results
