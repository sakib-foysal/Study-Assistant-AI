# -------------------------------
# Import Section
# -------------------------------

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
from fastapi.responses import FileResponse
from typing import List, Optional

# internal LLM service
import llm_service

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


# -------------------------------
# Root Endpoint
# -------------------------------

@app.get("/")
def read_index():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    )

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


@app.get("/health")
def health():
    return {"status": "ok"}