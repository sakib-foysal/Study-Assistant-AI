# -------------------------------
# Import Section
# -------------------------------

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from fastapi.responses import FileResponse

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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------
# Request Model
# -------------------------------

class MCQRequest(BaseModel):
    topic: str
    difficulty: str
    number_of_questions: int


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
