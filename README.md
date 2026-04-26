# 🤖 AI Study Assistant

An AI-powered study tool that generates **summaries** and **multiple-choice questions (MCQs)** for any topic using **FastAPI + Gemini API**.

---

## 🚀 Features

* 📚 Generate concise study summaries
* ❓ Create MCQs automatically
* 🧠 AI-powered content generation (Google Gemini)
* 📄 Export content as PDF
* 🔐 User authentication (Login/Signup with MySQL)

---

## 🛠️ Tech Stack

### Backend

* FastAPI
* Python
* Gemini API (Google AI)
* MySQL (XAMPP)
* bcrypt (password hashing)

### Frontend

* HTML
* CSS
* JavaScript

---

## 📂 Project Structure

```
study-assistant-ai/
│
├── backend/
│   ├── main.py
│   ├── llm_service.py
│   ├── database.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── css/
│   └── js/
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/study-assistant-ai.git
cd study-assistant-ai/backend
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3️⃣ Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

### 4️⃣ Setup `.env`

Create a `.env` file in `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=2.5-flash-lite
```

---

### 5️⃣ Run the server

```bash
fastapi dev main.py
```

Or:

```bash
python -m uvicorn main:app --reload
```

---

### 6️⃣ Open in browser

```
http://127.0.0.1:8000
```

---

## 🧪 API Endpoints

### 🔹 Generate Summary + MCQs

```
POST /generate
```

**Request:**

```json
{
  "topic": "Operating System",
  "difficulty": "easy",
  "number_of_questions": 4
}
```

---

### 🔹 Generate Only MCQs

```
POST /generate-mcq
```

---

### 🔹 Debug LLM

```
GET /debug/llm
```

---

## 🔐 Authentication

* Signup → `/signup`
* Login → `/login`

Uses MySQL database (XAMPP).

---

## 📸 Screenshots

*Add screenshots of your UI here*

---

## ⚠️ Important Notes

* Never expose API keys publicly
* Use `.env` file for secrets
* If Gemini না কাজ করে → API key check করো

---

## 👨‍💻 Author

**Sakib Foysal & Noyon S**
CSE Student, Northern University of Business and Technology Khulna

---

## ⭐ Contribute

Feel free to fork this repo and improve it!

---

## 📜 License

This project is for educational purposes.
