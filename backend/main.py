import json
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openai
import os
from sqlalchemy.orm import Session
from models import User, Base
from database import SessionLocal
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Placeholder for LangGraph imports and agent logic
# from langgraph import ...

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load questions from questions.json
with open("../questions.json") as f:
    QUESTIONS = json.load(f)

# Agent stubs
class QuestionAgent:
    def get_question(self, question_id=None):
        if question_id is not None:
            for q in QUESTIONS:
                if q["id"] == question_id:
                    return q
        return QUESTIONS[0]  # Default to first question

class ClarificationAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def respond(self, user_input, question):
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
        q_constraints = "\n".join(question.get("constraints", []))
        prompt = f"""
You are an interviewer for a coding interview. Given the user's input and the coding question, provide feedback as an interviewer: do NOT give out the answer, but nudge the user in the right direction with hints, questions, or suggestions. Be specific, constructive, and encourage deeper thinking.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints:
{q_constraints}

User input:
{user_input}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an interviewer for a coding interview. Never give out the answer directly. Nudge the user with hints, questions, or suggestions."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class BruteForceAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def feedback(self, user_idea, question, time_complexity=None, space_complexity=None):
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
        q_constraints = "\n".join(question.get("constraints", []))
        prompt = f"""
You are an interviewer for a coding interview. The user is describing a brute-force solution for the following coding question. ONLY consider the brute-force approach and its analysis in your feedback. Do NOT compare to or suggest optimized solutions. If the user provides a time complexity like O(n^2) and it matches the brute-force approach, accept it as correct for this section.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints:
{q_constraints}

Brute-force idea:
{user_idea}
Time Complexity: {time_complexity or 'Not provided'}
Space Complexity: {space_complexity or 'Not provided'}

Give feedback on the idea, and specifically comment on the time and space complexity provided (or lack thereof), but ONLY in the context of a brute-force solution."""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an interviewer for a coding interview. Never give out the answer directly. Nudge the user with hints, questions, or suggestions. Only consider the brute-force approach for this section."},
                      {"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class OptimizeAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def feedback(self, user_idea, question, time_complexity=None, space_complexity=None):
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
        q_constraints = "\n".join(question.get("constraints", []))
        prompt = f"""
You are an interviewer for a coding interview. The user is describing an optimized solution for the following coding question. ONLY consider the optimized approach and its analysis in your feedback. Do NOT compare to or critique the brute-force solution. Focus your feedback on the optimized idea and its time and space complexity.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints:
{q_constraints}

Optimized idea:
{user_idea}
Time Complexity: {time_complexity or 'Not provided'}
Space Complexity: {space_complexity or 'Not provided'}

Give feedback on the idea, and specifically comment on the time and space complexity provided (or lack thereof), but ONLY in the context of the optimized solution."""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an interviewer for a coding interview. Never give out the answer directly. Nudge the user with hints, questions, or suggestions. Only consider the optimized approach for this section."},
                      {"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class CodeReviewAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def review(self, clarification, brute_force, code, question, bf_time=None, bf_space=None, opt_time=None, opt_space=None):
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
        q_constraints = "\n".join(question.get("constraints", []))
        prompt = f"""
You are a senior coding interview coach. Review the user's performance for the following coding question:

Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints:
{q_constraints}

For each stage, provide a grade (1-10) and detailed feedback, including key pointers for improvement. The stages are:

1. Input Clarification: How well did the user clarify the problem and requirements?
2. Brute-force Idea: How well did the user propose and analyze a brute-force solution? Include feedback on the time and space complexity provided: Time Complexity: {bf_time or 'Not provided'}, Space Complexity: {bf_space or 'Not provided'}
3. Coding Solution: How correct, efficient, and clear is the final code? Also consider the optimized idea's time and space complexity: Time Complexity: {opt_time or 'Not provided'}, Space Complexity: {opt_space or 'Not provided'}

After grading each stage, also provide a total score out of 10 for the user's overall performance (not an average, but your holistic judgment).

Return a JSON object with this structure:
{{
  "clarification": {{"grade": int, "feedback": str}},
  "brute_force": {{"grade": int, "feedback": str}},
  "coding": {{"grade": int, "feedback": str}},
  "total": int,  // total score out of 10
  "key_pointers": str
}}

User's input clarification:
{clarification}

User's brute-force idea:
{brute_force}

User's code solution:
{code}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a senior coding interview coach."},
                      {"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3
        )
        import re, json as pyjson
        content = response['choices'][0]['message']['content']
        print('OpenAI response:', content)
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return pyjson.loads(match.group(0))
            except Exception:
                pass
        return {"clarification": {}, "brute_force": {}, "coding": {}, "total": None, "key_pointers": content}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/api/questions")
async def get_questions():
    return [{"id": q["id"], "title": q["title"]} for q in QUESTIONS]

@app.post("/api/start-session")
async def start_session(request: Request):
    data = await request.json()
    question_id = data.get("question_id")
    question = QuestionAgent().get_question(question_id)
    return {"question": question}

@app.post("/api/clarify")
async def clarify(request: Request):
    data = await request.json()
    question_id = data.get("question_id")
    question = QuestionAgent().get_question(question_id)
    response = ClarificationAgent().respond(data.get("user_input", ""), question)
    return {"agent": "ClarificationAgent", "response": response}

@app.post("/api/brute-force")
async def brute_force(request: Request):
    data = await request.json()
    question_id = data.get("question_id")
    question = QuestionAgent().get_question(question_id)
    response = BruteForceAgent().feedback(
        data.get("user_idea", ""),
        question,
        data.get("time_complexity"),
        data.get("space_complexity")
    )
    return {"agent": "BruteForceAgent", "response": response}

@app.post("/api/optimize")
async def optimize(request: Request):
    data = await request.json()
    question_id = data.get("question_id")
    question = QuestionAgent().get_question(question_id)
    response = OptimizeAgent().feedback(
        data.get("user_idea", ""),
        question,
        data.get("time_complexity"),
        data.get("space_complexity")
    )
    return {"agent": "OptimizeAgent", "response": response}

@app.post("/api/code-review")
async def code_review(request: Request):
    data = await request.json()
    question_id = data.get("question_id")
    question = QuestionAgent().get_question(question_id)
    review = CodeReviewAgent().review(
        data.get("clarification", ""),
        data.get("brute_force", ""),
        data.get("code", ""),
        question,
        data.get("brute_force_time_complexity"),
        data.get("brute_force_space_complexity"),
        data.get("optimize_time_complexity"),
        data.get("optimize_space_complexity")
    )
    return {"agent": "CodeReviewAgent", "review": review}

# User registration endpoint
@app.post("/api/register")
async def register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if db.query(User).filter((User.username == username) | (User.email == email)).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User registered successfully"}

# User login endpoint
@app.post("/api/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Utility to get current user from token
def get_current_user(token: str = Depends(lambda request: request.headers.get('Authorization', '').replace('Bearer ', '')), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user 