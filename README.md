# NEU AttendAI

A smart, web-based attendance system for Near East University (NEU). Students check in using a rotating QR code that refreshes every 2 minutes, while GPS geo-fencing confirms physical presence inside the classroom. Built-in fraud detection catches impossible travel and GPS spoofing.

> **Pilot project — 2026.** Demo mode is on by default so you can run and test everything locally without a real GPS device.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Running the App](#running-the-app)
6. [Project Structure](#project-structure)
7. [How to Use Each Role](#how-to-use-each-role)
8. [API Endpoints](#api-endpoints)
9. [Configuration](#configuration)
10. [Demo Mode vs Live Mode](#demo-mode-vs-live-mode)
11. [Attendance Policy Rules](#attendance-policy-rules)
12. [Troubleshooting](#troubleshooting)

---

## What It Does

| Feature | Description |
|---|---|
| **Dynamic QR Tokens** | Each course gets a unique QR code that rotates every 2 minutes. Sharing a screenshot won't work. |
| **GPS Geo-Fencing** | Check-in is blocked if the student is more than 50 metres from the classroom. |
| **Fraud Detection** | Flags impossible travel (teleporting between rooms) and mock/simulated GPS signals. |
| **Attendance Policy** | Automatically tracks warnings (Warning 1 → 3) and deprivation status based on NEU's 70 % / 75 % / 85 % thresholds. |
| **Three Portals** | Separate dashboards for students, instructors, and administrators. |
| **Timetable Import** | Admins upload the official NEU timetable `.xlsx` file and the system parses every room/day/slot automatically. |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| **Server** | [Uvicorn](https://www.uvicorn.org/) (ASGI) |
| **Database** | [MongoDB](https://www.mongodb.com/) via [Motor](https://motor.readthedocs.io/) (async) |
| **Auth** | JWT tokens ([python-jose](https://python-jose.readthedocs.io/)) + bcrypt passwords |
| **Frontend** | Plain HTML + CSS + vanilla JavaScript (no framework needed) |
| **Excel parsing** | [openpyxl](https://openpyxl.readthedocs.io/) |

---

## Prerequisites

Before you start, make sure you have these installed on your computer.

### 1 — Python 3.10 or newer
Check your version:
```bash
python --version
```
Download from [python.org](https://www.python.org/downloads/) if needed.

### 2 — MongoDB Community Edition
The app stores all data (users, attendance records, timetable) in MongoDB.

- **Windows / macOS / Linux:** [Download MongoDB Community](https://www.mongodb.com/try/download/community)
- After installing, start the MongoDB service:
  ```bash
  # macOS (with Homebrew)
  brew services start mongodb-community

  # Linux (systemd)
  sudo systemctl start mongod

  # Windows — open Services and start "MongoDB"
  ```
- Verify it is running:
  ```bash
  mongosh
  # You should see a shell prompt like: test>
  # Type exit to quit
  ```

### 3 — Git
Download from [git-scm.com](https://git-scm.com/) if you do not have it.

---

## Installation

### Step 1 — Clone the repository
```bash
git clone https://github.com/Dz007510/NEU-AttendAI.git

#then write: cd NEU-AttendAI
```

### Step 2 — Create a virtual environment
A virtual environment keeps the project's packages separate from your system Python.
```bash
# Create the environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```
You will see `(venv)` at the start of your terminal prompt when it is active.

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```
This installs FastAPI, Uvicorn, Motor, and all other packages the project needs.

### Step 4 — Set up environment variables
Copy the example file and edit it if needed:
```bash
# macOS / Linux
cp .env.example .env

# Windows
copy .env.example .env
```
The default values work for a local MongoDB install. You only need to change them if your MongoDB is on a different host or port (see [Configuration](#configuration)).

---

## Running the App

```bash
python run.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Open your browser and go to:
```
http://localhost:8000
```

You will land on the **Sign In** page. Use the demo credentials below to log in.

---

## Project Structure

```
F.M/
│
├── run.py                  ← Start the server (entry point)
├── requirements.txt        ← Python package list
├── .env                    ← Your local config (not committed to git)
├── .env.example            ← Template for .env
│
└── app/
    ├── main.py             ← FastAPI app, routes wired up here
    │
    ├── static/             ← HTML pages served to the browser
    │   ├── login.html      ← Sign-in page (all roles)
    │   ├── index.html      ← Student dashboard
    │   ├── instructor.html ← Instructor dashboard
    │   └── admin.html      ← Admin panel
    │
    ├── routes/             ← API endpoint handlers
    │   ├── auth.py         ← /auth  — login, register, token check
    │   ├── attendance.py   ← /attendance — check-in, QR tokens, reports
    │   └── admin.py        ← /admin — timetable upload, stats
    │
    ├── db/
    │   └── mongo.py        ← MongoDB connection and collection handles
    │
    ├── models/
    │   └── models.py       ← Pydantic data models (request/response shapes)
    │
    └── logic/              ← Business logic (pure Python, no HTTP)
        ├── distance.py     ← Haversine formula, geo-fence check
        ├── token_logic.py  ← In-memory QR token store (generate / verify)
        ├── fraud_detection.py ← Impossible travel + GPS spoofing checks
        ├── policy_engine.py   ← Warning levels and deprivation calculation
        └── excel_parser.py    ← Parses the official NEU timetable .xlsx
```

---

## How to Use Each Role

### Student

**Demo credentials:** any 6–10 digit number as the student ID, any password.

1. Open `http://localhost:8000` — the **Student** tab is selected by default.
2. Enter your NEU student ID (e.g. `24700035`).
   - The system auto-detects whether you are already registered.
   - If not registered, it switches to **New Account** mode automatically.
3. After logging in you reach the **Student Dashboard** where you can:
   - Enter a course code and the QR token shown on the instructor's screen to check in.
   - View your attendance percentage and warning level for each course.

### Instructor

**Demo credentials:**

| Username | Password | Name |
|---|---|---|
| `instructor1` | `instructor123` | PROF. DR. DUYGU ÇELİK |
| `instructor2` | `instructor123` | ASSOC. PROF. DR. YILTAN BİTİRİM |

1. On the Sign In page click the **Instructor** tab.
2. After logging in you reach the **Instructor Dashboard** where you can:
   - Activate a session for a course (sets it as the active class).
   - Generate a rotating QR token — show this on your projector screen.
   - View today's attendance report (present / absent / late-registered).
   - Check the policy status (warning levels) for all students in a course.

### Admin

**Demo credentials:**

| Username | Password |
|---|---|
| `admin` | `admin123` |

1. On the Sign In page click the **Admin** tab.
2. After logging in you reach the **Admin Panel** where you can:
   - See system statistics (total sessions, unique courses, rooms, check-ins).
   - Upload the official NEU timetable `.xlsx` file.
   - Search the timetable by course code.
   - Delete all timetable data.

---

## API Endpoints

The interactive API documentation is available at:
```
http://localhost:8000/docs
```

Here is a quick reference:

### Auth — `/auth`
| Method | Path | What it does |
|---|---|---|
| `POST` | `/auth/register` | Register a new student account |
| `POST` | `/auth/login` | Log in (student, instructor, or admin) |
| `GET` | `/auth/me` | Return the current user's info from their token |
| `GET` | `/auth/check-registered/{student_id}` | Check if a student ID already has an account |

### Attendance — `/attendance`
| Method | Path | What it does |
|---|---|---|
| `POST` | `/attendance/generate-token/{course_id}` | Generate a new QR token for a course (instructor only) |
| `GET` | `/attendance/active-token/{course_id}` | Get the current active token |
| `POST` | `/attendance/activate-session` | Mark a course session as active (instructor only) |
| `POST` | `/attendance/deactivate-session/{course_id}` | Deactivate a session |
| `POST` | `/attendance/check-in` | Student check-in (validates QR + GPS) |
| `GET` | `/attendance/session-report/{course_id}` | Today's attendance list for a course |
| `GET` | `/attendance/policy-status/{student_id}/{course_id}` | One student's warning level |
| `GET` | `/attendance/policy-report/{course_id}` | All students' warning levels for a course |

### Admin — `/admin`
| Method | Path | What it does |
|---|---|---|
| `POST` | `/admin/upload-timetable` | Upload the NEU `.xlsx` timetable file |
| `DELETE` | `/admin/delete-timetable` | Wipe all timetable data |
| `GET` | `/admin/timetable` | List all timetable entries |
| `GET` | `/admin/timetable/search?q=CMPE301` | Search timetable by course code |
| `GET` | `/admin/stats` | System-wide statistics |

---

## Configuration

All configuration is stored in the `.env` file. Here are all the available options:

```env
# MongoDB connection string
# Default works for a standard local MongoDB install
MONGO_URL=mongodb://localhost:27017

# Name of the database (created automatically on first use)
DB_NAME=neu_attendance

# Secret key used to sign JWT tokens
# Change this to a long random string in any non-demo environment
SECRET_KEY=neu-attend-ai-secret-2026

# JWT signing algorithm (do not change unless you know what this means)
ALGORITHM=HS256

# How long a login token stays valid, in minutes (480 = 8 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

**Using a remote or Atlas MongoDB:**
```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net
DB_NAME=neu_attendance
```

---

## Demo Mode vs Live Mode

The file `app/routes/attendance.py` has a flag at the top:

```python
DEMO_MODE = True
```

| Setting | Behaviour |
|---|---|
| `True` (default) | GPS checks, QR token validation, and geo-fencing are **skipped**. Any coordinates work. Great for local testing. |
| `False` | Full enforcement — student must be within 50 m of the classroom, QR token must match and be less than 2 minutes old, GPS spoofing and impossible travel are blocked. |

To switch to live mode, change the line to:
```python
DEMO_MODE = False
```
and update the classroom coordinates in `app/logic/distance.py` to match your actual building:
```python
CLASSROOM_LAT = 35.1450   # ← replace with real latitude
CLASSROOM_LON = 33.9060   # ← replace with real longitude
MAX_DISTANCE_M = 50       # ← metres, adjust as needed
```

---

## Attendance Policy Rules

The policy engine follows NEU's official thresholds:

| Attendance % | Status | Colour |
|---|---|---|
| 90 % and above | Good Standing | Green |
| 85 % – 90 % | Warning 1 | Yellow |
| 75 % – 85 % | Warning 2 | Orange |
| 70 % – 75 % | Warning 3 | Red |
| 70 % and below | **Deprived** — barred from final exam | Red |

The system also calculates how many consecutive sessions a student must attend to return to safe standing (85 %).

---

## Troubleshooting

**`ModuleNotFoundError` when starting the server**
Make sure your virtual environment is activated and you have run `pip install -r requirements.txt`.

**`Connection refused` or MongoDB errors**
MongoDB is not running. Start it with:
```bash
# macOS
brew services start mongodb-community
# Linux
sudo systemctl start mongod
```

**The page loads but login does nothing**
Open the browser console (F12 → Console tab) to see the error. The most common cause is that the server crashed on startup — check the terminal where you ran `python run.py`.

**`Invalid student ID` error**
Student IDs must be **all digits, 6 to 10 characters long** (e.g. `24700035`). Letters and special characters are not accepted.

**I uploaded a timetable but search returns nothing**
Make sure the Excel file follows the NEU format: row 1–2 are headers, column A is the room name, and course data starts at column E. The parser expects 6 days × 10 time slots starting at column index 4.

---

## License

This project is a university pilot and is provided for educational purposes.
