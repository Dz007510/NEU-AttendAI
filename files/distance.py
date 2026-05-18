from math import radians, sin, cos, sqrt, atan2

CLASSROOM_LAT  = 35.1450
CLASSROOM_LON  = 33.9060
MAX_DISTANCE_M = 50


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in metres between two GPS coordinates."""
    R    = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a    = (sin(dlat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)
    c    = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 1000  # metres


def is_inside_classroom(lat: float, lon: float,
                        class_lat: float = CLASSROOM_LAT,
                        class_lon: float = CLASSROOM_LON,
                        max_dist:  float = MAX_DISTANCE_M) -> bool:
    """Returns True if the coordinate is within max_dist metres of the classroom."""
    return haversine(lat, lon, class_lat, class_lon) < max_dist
