import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import openai
import os

# Import our production-ready modules
from config import settings
from models import (
    User, Base, ClarifyRequest, BruteForceRequest, OptimizeRequest, 
    FunctionDefinitionRequest, CodeReviewRequest, StartSessionRequest,
    ClarifyResponse, BruteForceResponse, OptimizeResponse,
    FunctionDefinitionResponse, CodeReviewResponse
)
from database import SessionLocal, engine
from exceptions import (
    LeetCoachException, ValidationError, AuthenticationError,
    NotFoundError, OpenAIError, handle_leetcoach_exception
)
from middleware import setup_middleware
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="LeetCoach API",
    description="AI-powered coding interview simulator",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Setup middleware
setup_middleware(app)

# Load questions from questions.json
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    QUESTIONS_PATH = os.path.join(BASE_DIR, "questions.json")
    with open(QUESTIONS_PATH) as f:
        QUESTIONS = json.load(f)
    logger.info(f"Loaded {len(QUESTIONS)} questions")
except Exception as e:
    logger.error(f"Failed to load questions: {e}")
    QUESTIONS = []

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

# Global exception handler
@app.exception_handler(LeetCoachException)
async def leetcoach_exception_handler(request: Request, exc: LeetCoachException):
    logger.error(f"LeetCoach exception: {exc.message}")
    return handle_leetcoach_exception(exc)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Something went wrong"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Agent classes with improved error handling
class QuestionAgent:
    def get_question(self, question_id=None):
        if not QUESTIONS:
            raise NotFoundError("No questions available")
        
        if question_id is not None:
            for q in QUESTIONS:
                if q["id"] == question_id:
                    return q
            raise NotFoundError(f"Question with ID {question_id} not found")
        return QUESTIONS[0]

class FunctionDefinitionAgent:
    def __init__(self):
        if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
            logger.warning("OpenAI API key not set. Function definition generation will be limited.")
        openai.api_key = settings.openai_api_key

    def generate(self, question, language):
        try:
            if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
                # Return a basic function stub when OpenAI is not available
                if language == "python":
                    return f"def {question.get('title', '').lower().replace(' ', '_')}():\n    pass"
                elif language == "javascript":
                    title = question.get('title', '').lower().replace(' ', '')
                    return f"function {title}() {{\n    // Your code here\n}}"
                else:
                    return f"// {language} function stub for {question.get('title', '')}"
            
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
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"Failed to generate function definition: {str(e)}")

class ClarificationAgent:
    def __init__(self):
        if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
            logger.warning("OpenAI API key not set. Clarification responses will be limited.")
        openai.api_key = settings.openai_api_key

    def respond(self, user_input, question):
        try:
            if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
                return "I'm here to help clarify the problem. What specific aspect would you like me to explain further?"
            
            q_title = question.get("title", "")
            q_desc = question.get("description", "")
            q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
            q_constraints = "\n".join(question.get("constraints", []))
            
            prompt = f"""
You are an expert coding interview coach. The user is asking clarifying questions about a specific coding problem. Your role is to provide targeted, helpful guidance based on their specific question and the problem requirements.

PROBLEM DETAILS:
Title: {q_title}
Description: {q_desc}
Examples: {q_examples}
Constraints: {q_constraints}

USER'S QUESTION: {user_input}

ANALYZE their question and provide feedback that:
1. Directly addresses their specific question about this problem
2. Points out any misconceptions they might have about the problem requirements
3. Suggests what additional information they should consider for THIS specific problem
4. References the actual examples and constraints when relevant
5. Keeps response under 100 words and focused on THIS problem

IMPORTANT: Be specific to this problem. Don't give generic advice. If they're asking about edge cases, mention the actual constraints. If they're confused about the output format, reference the examples.
"""
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a precise coding interview coach who provides problem-specific guidance."},
                          {"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"Failed to generate clarification response: {str(e)}")

class BruteForceAgent:
    def __init__(self):
        if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
            logger.warning("OpenAI API key not set. Brute force feedback will be limited.")
        openai.api_key = settings.openai_api_key

    def feedback(self, user_idea, question, time_complexity=None, space_complexity=None):
        try:
            if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
                return "That's a good starting approach. Have you considered edge cases and the time complexity of your solution?"
            
            q_title = question.get("title", "")
            q_desc = question.get("description", "")
            q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
            q_constraints = "\n".join(question.get("constraints", []))
            
            prompt = f"""
You are an expert coding interview coach evaluating a brute-force solution for a specific problem. Your job is to assess if their approach is a valid brute force solution, NOT whether it's optimal.

PROBLEM DETAILS:
Title: {q_title}
Description: {q_desc}
Examples: {q_examples}
Constraints: {q_constraints}

USER'S BRUTE-FORCE APPROACH: {user_idea}
Time Complexity: {time_complexity or 'Not provided'}
Space Complexity: {space_complexity or 'Not provided'}

ANALYZE their approach as a BRUTE FORCE solution:
1. Is their approach a valid brute force solution for THIS problem? (Does it try all possible combinations/iterations?)
2. Will their brute force approach handle the given examples correctly?
3. Does their brute force approach consider the actual constraints of this problem?
4. Is their complexity analysis accurate for their brute force approach?
5. What edge cases specific to this problem might their brute force approach miss?

IMPORTANT: 
- Only evaluate if it's a valid brute force solution, NOT if it's optimal
- Don't suggest optimizations or better approaches
- Focus on whether their brute force approach would work, even if inefficient
- If their approach isn't actually brute force, explain why
"""
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a precise coding interview coach who evaluates solutions against specific problem requirements."},
                          {"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.2
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"Failed to generate brute force feedback: {str(e)}")

class OptimizeAgent:
    def __init__(self):
        if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
            logger.warning("OpenAI API key not set. Optimization feedback will be limited.")
        openai.api_key = settings.openai_api_key

    def feedback(self, user_idea, question, time_complexity=None, space_complexity=None):
        try:
            if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
                return "Good optimization attempt! Consider the trade-offs between time and space complexity."
            
            q_title = question.get("title", "")
            q_desc = question.get("description", "")
            q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
            q_constraints = "\n".join(question.get("constraints", []))
            
            prompt = f"""
You are an expert coding interview coach evaluating an optimization approach for a specific problem. Analyze the user's optimization against the actual problem requirements.

PROBLEM DETAILS:
Title: {q_title}
Description: {q_desc}
Examples: {q_examples}
Constraints: {q_constraints}

USER'S OPTIMIZATION APPROACH: {user_idea}
Time Complexity: {time_complexity or 'Not provided'}
Space Complexity: {space_complexity or 'Not provided'}

ANALYZE their optimization and provide specific feedback:
1. Is their optimization actually better than a brute-force approach for THIS problem?
2. Does their optimization correctly handle the problem constraints and examples?
3. Is their complexity analysis accurate and justified for THIS specific problem?
4. What trade-offs are they making, and are they appropriate for this problem?
5. Are there other optimization approaches they haven't considered for this specific problem?

IMPORTANT: Be specific to this problem. Don't give generic optimization advice. If their optimization doesn't make sense for this problem, explain why. If there are better approaches for this specific problem, hint at them without giving away the solution.
"""
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a precise coding interview coach who evaluates optimizations against specific problem requirements."},
                          {"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.2
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"Failed to generate optimization feedback: {str(e)}")

class CodeReviewAgent:
    def __init__(self):
        if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
            logger.warning("OpenAI API key not set. Code review will be limited.")
        openai.api_key = settings.openai_api_key

    def review(self, clarification, brute_force, code, question, language, bf_time=None, bf_space=None, opt_time=None, opt_space=None):
        try:
            if not settings.openai_api_key or settings.openai_api_key == "sk-dummy-key-for-development":
                return {
                    "clarification": {"grade": 7, "feedback": "Good clarification attempt"},
                    "brute_force": {"grade": 7, "feedback": "Reasonable brute force approach"},
                    "coding": {
                        "grade": 7, 
                        "feedback": "Basic implementation provided",
                        "line_by_line": []
                    },
                    "total": 7,
                    "key_pointers": "Set up OpenAI API key for detailed code review"
                }
            
            q_title = question.get("title", "")
            q_desc = question.get("description", "")
            q_examples = "\n".join([f"Input: {ex['input']} | Output: {ex['output']}" for ex in question.get("examples", [])])
            q_constraints = "\n".join(question.get("constraints", []))
            
            prompt = f"""
You are a senior coding interview coach providing a comprehensive review for a specific problem. Analyze the user's performance against the actual problem requirements.

PROBLEM DETAILS:
Title: {q_title}
Description: {q_desc}
Examples: {q_examples}
Constraints: {q_constraints}

Programming Language: {language}

USER'S RESPONSES:
Clarification: {clarification}
Brute-force idea: {brute_force}
Code solution: {code}
Brute-force complexity: Time={bf_time}, Space={bf_space}
Optimized complexity: Time={opt_time}, Space={opt_space}

PROVIDE A DETAILED REVIEW:

1. CLARIFICATION (1-10): Did they understand the problem correctly? Did they ask relevant questions about THIS specific problem?

2. BRUTE-FORCE (1-10): Did their brute-force approach actually solve THIS problem? Did they consider the actual constraints and examples?

3. CODING (1-10): Does their code correctly implement a solution for THIS problem? Analyze line-by-line for:
   - Correctness for this specific problem
   - {language} best practices
   - Handling of edge cases from the constraints
   - Proper output format matching the examples

4. Line-by-line analysis: Identify specific lines with issues and provide concrete suggestions for THIS problem

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

IMPORTANT: Be specific to this problem. Don't give generic feedback. If their code doesn't solve this problem correctly, explain why. If they're missing key aspects of this problem, point them out specifically.
"""
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": f"You are a senior coding interview coach providing detailed, problem-specific feedback for {language} code."},
                          {"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.2
            )
            import re, json as pyjson
            content = response['choices'][0]['message']['content']
            logger.info(f'OpenAI response: {content}')
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    return pyjson.loads(match.group(0))
                except Exception:
                    pass
            return {"clarification": {}, "brute_force": {}, "coding": {}, "total": None, "key_pointers": content}
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"Failed to generate code review: {str(e)}")

# Initialize agents
question_agent = QuestionAgent()
function_definition_agent = FunctionDefinitionAgent()

# API Endpoints with proper validation
@app.get("/api/questions")
async def get_questions():
    """Get all available questions"""
    return [{"id": q["id"], "title": q["title"]} for q in QUESTIONS]

@app.post("/api/start-session")
async def start_session(request: StartSessionRequest):
    """Start a new interview session"""
    try:
        question = question_agent.get_question(request.question_id)
        return {"question": question}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/function-definition")
async def get_function_definition(request: FunctionDefinitionRequest):
    """Get function definition for a specific language"""
    try:
        question = question_agent.get_question(request.question_id)
        function_definition = function_definition_agent.generate(question, request.language)
        return FunctionDefinitionResponse(function_definition=function_definition)
    except (NotFoundError, OpenAIError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.post("/api/clarify")
async def clarify(request: ClarifyRequest):
    """Get clarification feedback"""
    try:
        question = question_agent.get_question(request.question_id)
        response = ClarificationAgent().respond(request.user_input, question)
        return ClarifyResponse(agent="ClarificationAgent", response=response)
    except (NotFoundError, OpenAIError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.post("/api/brute-force")
async def brute_force(request: BruteForceRequest):
    """Get brute force solution feedback"""
    try:
        question = question_agent.get_question(request.question_id)
        response = BruteForceAgent().feedback(
            request.user_idea,
            question,
            request.time_complexity,
            request.space_complexity
        )
        return BruteForceResponse(agent="BruteForceAgent", response=response)
    except (NotFoundError, OpenAIError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.post("/api/optimize")
async def optimize(request: OptimizeRequest):
    """Get optimization feedback"""
    try:
        question = question_agent.get_question(request.question_id)
        response = OptimizeAgent().feedback(
            request.user_idea,
            question,
            request.time_complexity,
            request.space_complexity
        )
        return OptimizeResponse(agent="OptimizeAgent", response=response)
    except (NotFoundError, OpenAIError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.post("/api/code-review")
async def code_review(request: CodeReviewRequest):
    """Get comprehensive code review"""
    try:
        question = question_agent.get_question(request.question_id)
        review = CodeReviewAgent().review(
            request.clarification,
            request.brute_force,
            request.code,
            question,
            request.language,
            request.brute_force_time_complexity,
            request.brute_force_space_complexity,
            request.optimize_time_complexity,
            request.optimize_space_complexity
        )
        return CodeReviewResponse(agent="CodeReviewAgent", review=review)
    except (NotFoundError, OpenAIError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

# User management endpoints (basic implementation)
@app.post("/api/register")
async def register(request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
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
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """Login user"""
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 