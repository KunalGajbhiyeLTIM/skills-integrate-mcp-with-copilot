"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Load teacher credentials from data/teachers.json (simple JSON file)
import json

data_dir = current_dir / ".." / "data"
data_dir = data_dir.resolve()
teachers_file = data_dir / "teachers.json"

if not data_dir.exists():
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best effort; if running in an environment without write access we'll continue
        pass

teachers = []
try:
    if teachers_file.exists():
        with open(teachers_file, "r", encoding="utf-8") as f:
            teachers = json.load(f).get("teachers", [])
except Exception:
    teachers = []

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(request: Request, activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Only a logged-in teacher may sign up students
    teacher_user = request.cookies.get("teacher_user")
    if not teacher_user or not any(t.get("username") == teacher_user for t in teachers):
        raise HTTPException(status_code=401, detail="Teacher login required to sign up students")
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(request: Request, activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Only a logged-in teacher may unregister students
    teacher_user = request.cookies.get("teacher_user")
    if not teacher_user or not any(t.get("username") == teacher_user for t in teachers):
        raise HTTPException(status_code=401, detail="Teacher login required to unregister students")
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/login")
def login(response: Response, username: str = Form(...), password: str = Form(...)):
    """Very small / insecure login: checks `data/teachers.json` for username/password and sets a cookie.

    This is intentionally simple for the exercise. For production, use secure session management.
    """
    if any(t.get("username") == username and t.get("password") == password for t in teachers):
        # Set a simple cookie to indicate teacher is logged in
        response.set_cookie(key="teacher_user", value=username, httponly=True, path="/")
        return {"message": "ok", "username": username}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("teacher_user", path="/")
    return {"message": "logged out"}


@app.get("/auth/status")
def auth_status(request: Request):
    teacher_user = request.cookies.get("teacher_user")
    is_teacher = bool(teacher_user and any(t.get("username") == teacher_user for t in teachers))
    return {"is_teacher": is_teacher}
