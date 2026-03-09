# -------------------------------
# Import Section
# -------------------------------

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import json
from fastapi.responses import FileResponse
from typing import List, Optional

# internal LLM service
import llm_service
import database

# -------------------------------
# Load Environment Variables
# -------------------------------


load_dotenv()

# -------------------------------
# FastAPI App Instance
# -------------------------------

app = FastAPI()

# -------------------------------
# CORS Middleware
# -------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Static Files (CSS, JS, images)
# -------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js",  StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")),  name="js")

# -------------------------------
# OpenAI Client Setup
# -------------------------------



# -------------------------------
# Request Model
# -------------------------------

class GenerateRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "medium"
    number_of_questions: Optional[int] = 5


class MCQ(BaseModel):
    question: str
    options: List[str]
    answer: int


class GenerateResponse(BaseModel):
    summary: str
    mcqs: List[MCQ]


class MCQResponse(BaseModel):
    mcqs: List[MCQ]


# ── Auth Models ──
class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str


# -------------------------------
# Root Endpoint
# -------------------------------

@app.get("/")
def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/index.html")
def read_index_html():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/login.html")
def read_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/signup.html")
def read_signup():
    return FileResponse(os.path.join(FRONTEND_DIR, "signup.html"))

# -------------------------------
# AI MCQ Generator Endpoint
# -------------------------------

# -------------------------------
# AI MCQ Generator Endpoint
# -------------------------------




@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest):
    """Generate a summary and MCQs for a given topic and return combined JSON."""
    try:
        summary = llm_service.generate_summary(payload.topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

    try:
        mcqs = llm_service.generate_mcqs(payload.topic, payload.number_of_questions, payload.difficulty)
    except Exception as e:
        # If MCQ generation fails, surface the error but still return the summary
        raise HTTPException(status_code=500, detail=f"MCQ generation failed: {str(e)}")

    return {"summary": summary, "mcqs": mcqs}


@app.post("/generate-mcq", response_model=MCQResponse)
def generate_mcq(payload: GenerateRequest):
    """Generate only MCQs for a given topic."""
    try:
        mcqs = llm_service.generate_mcqs(payload.topic, payload.number_of_questions, payload.difficulty)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCQ generation failed: {str(e)}")

    return {"mcqs": mcqs}


# Friendly GET handlers to avoid Method Not Allowed when users open the URL in a browser
@app.get("/generate")
def generate_get_info():
    return {
        "detail": "This endpoint accepts POST requests with JSON body. Use POST /generate with {topic, difficulty, number_of_questions}.'",
        "example_body": {"topic": "Operating System Deadlock", "difficulty": "medium", "number_of_questions": 5},
    }


@app.get("/generate-mcq")
def generate_mqc_get_info():
    return {
        "detail": "This endpoint accepts POST requests with JSON body. Use POST /generate-mcq with {topic, difficulty, number_of_questions}.'",
        "example_body": {"topic": "Operating System Deadlock", "difficulty": "medium", "number_of_questions": 5},
    }


# -------------------------------
# Auth Endpoints
# -------------------------------

@app.post("/signup")
def signup(payload: SignupRequest):
    """Register a new user — saves to XAMPP MySQL database."""
    if len(payload.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    try:
        user = database.create_user(payload.username.strip(), payload.email.strip().lower(), payload.password)
        return {"success": True, "message": "Account created successfully!", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@app.post("/login")
def login(payload: LoginRequest):
    """Authenticate user credentials against XAMPP MySQL database."""
    try:
        user = database.authenticate_user(payload.email.strip().lower(), payload.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        return {"success": True, "message": "Login successful!", "user": user}
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok"}