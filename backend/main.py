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

class FunctionDefinitionAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def generate(self, question, language):
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        
        prompt = f"""
Based on the coding question below, generate a function definition for the language "{language}".

Question Title: {q_title}
Question Description: {q_desc}

Provide only the function signature or a simple stub. Do not include any explanations, comments, or example usage.
For example, for "Two Sum" in Python, a good response would be:
def two_sum(nums, target):
    pass

For Java:
class Solution {{
    public int[] twoSum(int[] nums, int target) {{
        // Your code here
    }}
}}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": f"You are a code generator. You output only raw code for the {language} language."},
                      {"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.0
        )
        return response['choices'][0]['message']['content'].strip()

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
You are an interviewer for a coding interview. The user is asking clarifying questions about the problem. Your role is to guide them with subtle hints and questions that help them think deeper, but NEVER give away the solution or approach.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints (for your reference only, don't mention these to the user):
{q_constraints}

User's clarifying question:
{user_input}

Respond with:
1. Acknowledge their question
2. Ask a follow-up question that nudges them toward the right direction
3. Suggest what additional information they might want to consider
4. Keep your response under 100 words

Remember: Don't solve the problem for them. Just guide their thinking.
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful but subtle coding interview coach. Never give direct answers or solutions."},
                      {"role": "user", "content": prompt}],
            max_tokens=150,
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
You are an interviewer evaluating a brute-force solution. The user is describing their initial approach. Provide gentle guidance without revealing the optimal solution.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints (for your reference only):
{q_constraints}

User's brute-force idea:
{user_idea}
Time Complexity: {time_complexity or 'Not provided'}
Space Complexity: {space_complexity or 'Not provided'}

Provide feedback that:
1. Acknowledges their approach
2. Asks questions about edge cases they might have missed
3. Gently suggests areas they could think about more
4. Comments on their complexity analysis (if provided)
5. Keeps response under 120 words

Remember: Don't suggest better algorithms. Just help them think through their current approach.
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a coding interview coach. Guide gently without revealing solutions."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
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
You are an interviewer evaluating an optimized solution. The user is describing their improved approach. Provide subtle guidance without revealing the best solution.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints (for your reference only):
{q_constraints}

User's optimized idea:
{user_idea}
Time Complexity: {time_complexity or 'Not provided'}
Space Complexity: {space_complexity or 'Not provided'}

Provide feedback that:
1. Acknowledges their optimization attempt
2. Asks about trade-offs they considered
3. Gently questions if there are other approaches they could explore
4. Comments on their complexity analysis
5. Keeps response under 120 words

Remember: Don't give away the optimal solution. Just guide their thinking about optimization.
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a coding interview coach. Guide optimization thinking without revealing the best approach."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class CodeReviewAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def review(self, clarification, brute_force, code, question, language, bf_time=None, bf_space=None, opt_time=None, opt_space=None):
        q_title = question.get("title", "")
        q_desc = question.get("description", "")
        q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
        q_constraints = "\n".join(question.get("constraints", []))
        prompt = f"""
You are a senior coding interview coach providing a comprehensive review. Analyze the user's performance and provide detailed, line-by-line code feedback.

Question:
Title: {q_title}
Description: {q_desc}
Examples:
{q_examples}
Constraints (for your reference only):
{q_constraints}

Programming Language: {language}

User's responses:
Clarification: {clarification}
Brute-force idea: {brute_force}
Code solution: {code}
Brute-force complexity: Time={bf_time}, Space={bf_space}
Optimized complexity: Time={opt_time}, Space={opt_space}

Provide a detailed review with:

1. Overall grades (1-10) for each section
2. Line-by-line code analysis pointing out specific issues, considering {language} best practices
3. Language-specific suggestions for improvement
4. Total score out of 10

Return a JSON object with this structure:
{{
  "clarification": {{"grade": int, "feedback": str}},
  "brute_force": {{"grade": int, "feedback": str}},
  "coding": {{
    "grade": int, 
    "feedback": str,
    "line_by_line": [
      {{"line": int, "issue": str, "suggestion": str}}
    ]
  }},
  "total": int,
  "key_pointers": str
}}

For the line-by-line analysis, identify specific lines with issues and provide concrete suggestions for each, considering {language} syntax, conventions, and best practices.
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": f"You are a senior coding interview coach providing detailed, constructive feedback for {language} code."},
                      {"role": "user", "content": prompt}],
            max_tokens=800,
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

question_agent = QuestionAgent()
function_definition_agent = FunctionDefinitionAgent()

@app.post("/api/function-definition")
async def get_function_definition(request: Request):
    data = await request.json()
    question_id = data.get("question_id")
    language = data.get("language")

    if not question_id or not language:
        raise HTTPException(status_code=400, detail="question_id and language are required")

    question = question_agent.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    function_definition = function_definition_agent.generate(question, language)
    return {"function_definition": function_definition}

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
        data.get("language"),
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