from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME",   "neu_attendance")

# Use in-memory MongoDB when a real instance isn't available
try:
    import socket
    host = MONGO_URL.split("//")[-1].split(":")[0]
    port = int(MONGO_URL.split(":")[-1].split("/")[0]) if ":" in MONGO_URL.split("//")[-1] else 27017
    s = socket.create_connection((host, port), timeout=1)
    s.close()
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(MONGO_URL)
    print(f"[db] Connected to MongoDB at {MONGO_URL}")
except Exception:
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
    print("[db] MongoDB unavailable — using in-memory mongomock")
db     = client[DB_NAME]

users_collection      = db["users"]
attendance_collection = db["attendance"]
roster_collection     = db["roster"]
timetable_collection  = db["timetable"]
sessions_collection   = db["active_sessions"]
