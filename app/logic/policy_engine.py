from typing import Dict

# NEU attendance thresholds
WARN1    = 85.0
WARN2    = 75.0
WARN3    = 70.0
DEPRIVED = 70.0


def calculate_status(student_id: str, course_id: str,
                     total_sessions: int, attended: int) -> Dict:
    """
    Calculate attendance percentage, warning level, and deprivation status.

    Warning levels:
        0 = OK (>=85%)
        1 = Warning 1 (80-85%)
        2 = Warning 2 (75-80%)
        3 = Warning 3 / Deprived (<=70%)
    """
    if total_sessions == 0:
        return {
            "student_id": student_id, "course_id": course_id,
            "total": 0, "attended": 0, "pct": 100.0,
            "warning": 0, "deprived": False, "color": "green",
            "message": "No sessions recorded yet.", "sessions_to_safe": 0,
        }

    pct = (attended / total_sessions) * 100.0

    if pct <= DEPRIVED:
        level, deprived, color = 3, True, "red"
        msg = f"DEPRIVED — {pct:.1f}% attendance. Barred from final exam."
    elif pct < WARN2:
        level, deprived, color = 3, False, "red"
        msg = f"WARNING 3 — {pct:.1f}% is critically low. Risk of deprivation."
    elif pct < WARN1:
        level, deprived, color = 2, False, "orange"
        msg = f"WARNING 2 — {pct:.1f}% is below 75%. Improve immediately."
    elif pct < 90.0:
        level, deprived, color = 1, False, "yellow"
        msg = f"WARNING 1 — {pct:.1f}% is approaching the danger zone."
    else:
        level, deprived, color = 0, False, "green"
        msg = f"Good Standing — {pct:.1f}% attendance."

    # Sessions needed to reach safe zone (85%)
    safe_sessions = 0
    if pct < WARN1:
        x = 0
        while x < 200:
            if ((attended + x) / (total_sessions + x)) * 100 >= WARN1:
                break
            x += 1
        safe_sessions = x

    return {
        "student_id":      student_id,
        "course_id":       course_id,
        "total":           total_sessions,
        "attended":        attended,
        "pct":             round(pct, 1),
        "warning":         level,
        "deprived":        deprived,
        "color":           color,
        "message":         msg,
        "sessions_to_safe": safe_sessions,
    }
