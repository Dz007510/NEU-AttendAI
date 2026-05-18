import re
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.db.mongo import timetable_collection, attendance_collection
from app.logic.excel_parser import parse_neu_excel
from app.routes.auth import get_current_user

router = APIRouter()


async def _admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


@router.post("/upload-timetable")
async def upload_timetable(file: UploadFile = File(...),
                            user: dict = Depends(_admin)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx / .xls files accepted")

    content  = await file.read()
    sessions = parse_neu_excel(content)
    if not sessions:
        raise HTTPException(status_code=400, detail="No sessions found in the file")

    await timetable_collection.delete_many({})
    await timetable_collection.insert_many(sessions)
    return {"status": "success", "sessions_imported": len(sessions), "filename": file.filename}


@router.delete("/delete-timetable")
async def delete_timetable(user: dict = Depends(_admin)):
    await timetable_collection.delete_many({})
    return {"status": "deleted"}


@router.get("/timetable")
async def get_timetable(user: dict = Depends(get_current_user)):
    docs = await timetable_collection.find({}, {"_id": 0}).to_list(10000)
    return docs


@router.get("/timetable/search")
async def search_timetable(q: str, user: dict = Depends(get_current_user)):
    pattern = re.compile(re.escape(q), re.IGNORECASE)
    docs = await timetable_collection.find(
        {"course_code": {"$regex": pattern}}, {"_id": 0}
    ).to_list(50)
    return docs


@router.get("/stats")
async def stats(user: dict = Depends(_admin)):
    total    = await timetable_collection.count_documents({})
    courses  = len(await timetable_collection.distinct("course_code"))
    rooms    = len(await timetable_collection.distinct("room"))
    att      = await attendance_collection.count_documents({})
    return {"total_sessions": total, "unique_courses": courses,
            "unique_rooms": rooms, "attendance_records": att}
