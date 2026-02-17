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

@app.post("/generate-mcq")
def generate_mcq(request: MCQRequest):

    topic = request.topic
    difficulty = request.difficulty
    number = request.number_of_questions

    # 🔥 Structured Prompt
    prompt = f"""
    Generate {number} multiple choice questions on the topic "{topic}".
    Difficulty level: {difficulty}.

    Each question must contain:
    - question
    - 4 options labeled A, B, C, D
    - correct answer (A/B/C/D)
    - short explanation

    Return strictly in valid JSON format like this:

    [
      {{
        "question": "Question text",
        "options": {{
          "A": "Option A",
          "B": "Option B",
          "C": "Option C",
          "D": "Option D"
        }},
        "answer": "A",
        "explanation": "Short explanation"
      }}
    ]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate structured academic MCQs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        ai_output = response.choices[0].message.content

        # Convert AI output string → JSON
        mcq_data = json.loads(ai_output)

        return {
            "status": "success",
            "topic": topic,
            "difficulty": difficulty,
            "mcqs": mcq_data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
