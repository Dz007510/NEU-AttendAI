from datetime import datetime
from app.logic.distance import haversine

MAX_SPEED_MPS  = 10.0   # max realistic campus speed m/s
MIN_ACCURACY_M = 500    # above this = untrusted GPS


def check_impossible_travel(lat1: float, lon1: float,
                            lat2: float, lon2: float,
                            last_time: datetime) -> dict:
    """Detect if student moved impossibly fast since last check-in."""
    elapsed = max((datetime.now() - last_time).total_seconds(), 1)
    dist    = haversine(lat1, lon1, lat2, lon2)
    speed   = dist / elapsed
    flagged = speed > MAX_SPEED_MPS
    return {
        "flagged":     flagged,
        "distance_m":  round(dist, 2),
        "elapsed_sec": round(elapsed, 2),
        "speed_mps":   round(speed, 2),
        "reason":      (
            f"Travelled {dist:.0f}m in {elapsed:.0f}s ({speed:.1f} m/s)"
            if flagged else "OK"
        ),
    }


def check_gps_spoofing(latitude: float, longitude: float,
                       accuracy_m: float = None,
                       is_mock: bool = False,
                       altitude_zero: bool = False) -> dict:
    """Detect common GPS spoofing signals."""
    reasons = []

    if is_mock:
        reasons.append("Device reports mock/simulated location.")

    if accuracy_m is not None and accuracy_m > MIN_ACCURACY_M:
        reasons.append(f"GPS accuracy too low ({accuracy_m}m).")

    if altitude_zero:
        reasons.append("Altitude is exactly 0.0 — possible mock location.")

    lat_dec = len(str(latitude).split(".")[-1])  if "." in str(latitude)  else 0
    lon_dec = len(str(longitude).split(".")[-1]) if "." in str(longitude) else 0
    if lat_dec < 3 or lon_dec < 3:
        reasons.append("Coordinate precision too low — possible spoofing.")

    risk = "low"
    if len(reasons) >= 2:
        risk = "medium"
    if is_mock or len(reasons) >= 3:
        risk = "high"

    return {"flagged": bool(reasons), "reasons": reasons, "risk_level": risk}
