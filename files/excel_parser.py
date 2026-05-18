import io
import openpyxl
from typing import List

DAYS  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SLOTS = [
    "08:30-09:30", "09:30-10:30", "10:30-11:30", "11:30-12:30",
    "12:30-13:30", "13:30-14:30", "14:30-15:30", "15:30-16:30",
    "16:30-17:30", "17:30-18:30",
]
SKIP = {"", "none", "x", "nan"}


def parse_neu_excel(content: bytes) -> List[dict]:
    """
    Parse the official NEU timetable Excel file.
    Rows 0-1: headers. Row 2+: room data.
    Cols: SALON | CAPACITY | BOARD | PROJECTOR | [6 days x 10 slots]
    """
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    sessions = []

    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        if idx < 2:
            continue
        room = str(row[0] or "").strip()
        if not room or room.lower() in SKIP:
            continue

        for di, day in enumerate(DAYS):
            for si, slot in enumerate(SLOTS):
                col = 4 + di * 10 + si
                if col >= len(row):
                    break
                val = str(row[col] or "").strip()
                if not val or val.lower() in SKIP:
                    continue
                parts = val.split()
                code  = parts[0] if parts else val
                instr = parts[-1] if len(parts) > 1 else ""
                sessions.append({
                    "room":        room,
                    "day":         day,
                    "time_slot":   slot,
                    "course_code": code,
                    "instructor":  instr,
                    "source":      "official_excel",
                })

    return sessions
