from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME",   "neu_attendance")

client = AsyncIOMotorClient(MONGO_URL)
db     = client[DB_NAME]

users_collection      = db["users"]
attendance_collection = db["attendance"]
roster_collection     = db["roster"]
timetable_collection  = db["timetable"]
sessions_collection   = db["active_sessions"]
