from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    user_id:  str
    password: str
    role:     str


class RegisterRequest(BaseModel):
    student_id: str
    password:   str
    full_name:  Optional[str] = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    role:         str
    user_id:      str
    full_name:    Optional[str] = ""


class AttendanceCheck(BaseModel):
    student_id:    str
    course_id:     str
    latitude:      float
    longitude:     float
    token:         str
    accuracy_m:    Optional[float] = None
    is_mock:       Optional[bool]  = False
    altitude_zero: Optional[bool]  = False


class SessionActivate(BaseModel):
    course_code: str
    room:        str
    day:         str
    time_slot:   str
    instructor:  Optional[str] = ""
    source:      Optional[str] = "manual_input"
