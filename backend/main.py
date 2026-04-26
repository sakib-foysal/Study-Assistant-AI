from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from typing import List, Optional
from datetime import datetime
import os
import logging

import llm_service
import database

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


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


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


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


@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest):
    try:
        summary = llm_service.generate_summary(payload.topic)
        mcqs = llm_service.generate_mcqs(
            payload.topic,
            payload.number_of_questions,
            payload.difficulty
        )

        return {
            "summary": summary,
            "mcqs": mcqs
        }

    except Exception as e:
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "llm_errors.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.utcnow().isoformat()} GENERATE ERROR: {str(e)}\n")
        except Exception:
            pass

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-mcq", response_model=MCQResponse)
def generate_mcq(payload: GenerateRequest):
    try:
        mcqs = llm_service.generate_mcqs(
            payload.topic,
            payload.number_of_questions,
            payload.difficulty
        )

        return {"mcqs": mcqs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate")
def generate_get_info():
    return {
        "detail": "Use POST /generate with JSON body.",
        "example_body": {
            "topic": "Operating System",
            "difficulty": "easy",
            "number_of_questions": 2
        }
    }


@app.get("/generate-mcq")
def generate_mcq_get_info():
    return {
        "detail": "Use POST /generate-mcq with JSON body.",
        "example_body": {
            "topic": "Operating System",
            "difficulty": "easy",
            "number_of_questions": 2
        }
    }


@app.post("/signup")
def signup(payload: SignupRequest):
    if len(payload.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")

    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    try:
        user = database.create_user(
            payload.username.strip(),
            payload.email.strip().lower(),
            payload.password
        )

        return {
            "success": True,
            "message": "Account created successfully!",
            "user": user
        }

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@app.post("/login")
def login(payload: LoginRequest):
    try:
        user = database.authenticate_user(
            payload.email.strip().lower(),
            payload.password
        )

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "success": True,
            "message": "Login successful!",
            "user": user
        }

    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/llm")
def debug_llm():
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    try:
        import requests
        requests_ok = True
    except Exception:
        requests_ok = False

    return {
        "gemini_key_set": bool(gemini_key),
        "requests_installed": requests_ok,
        "gemini_model_env": os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    }