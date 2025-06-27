from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Pydantic Models for API
class UserBase(BaseModel):
    username: str
    email: str
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v
    
    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Interview-related models
class ClarifyRequest(BaseModel):
    user_input: str
    question_id: int
    
    @validator('user_input')
    def input_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Input cannot be empty')
        if len(v) > 1000:
            raise ValueError('Input must be less than 1000 characters')
        return v.strip()

class BruteForceRequest(BaseModel):
    user_idea: str
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    question_id: int
    
    @validator('user_idea')
    def idea_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Idea cannot be empty')
        if len(v) > 2000:
            raise ValueError('Idea must be less than 2000 characters')
        return v.strip()

class OptimizeRequest(BaseModel):
    user_idea: str
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    question_id: int
    
    @validator('user_idea')
    def idea_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Idea cannot be empty')
        if len(v) > 2000:
            raise ValueError('Idea must be less than 2000 characters')
        return v.strip()

class FunctionDefinitionRequest(BaseModel):
    question_id: int
    language: str
    
    @validator('language')
    def language_must_be_valid(cls, v):
        valid_languages = ['javascript', 'python', 'java', 'cpp', 'go']
        if v not in valid_languages:
            raise ValueError(f'Language must be one of: {", ".join(valid_languages)}')
        return v

class CodeReviewRequest(BaseModel):
    clarification: str
    brute_force: str
    code: str
    language: str
    brute_force_time_complexity: Optional[str] = None
    brute_force_space_complexity: Optional[str] = None
    optimize_time_complexity: Optional[str] = None
    optimize_space_complexity: Optional[str] = None
    question_id: int
    
    @validator('code')
    def code_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Code cannot be empty')
        if len(v) > 10000:
            raise ValueError('Code must be less than 10000 characters')
        return v.strip()

class StartSessionRequest(BaseModel):
    question_id: int
    
    @validator('question_id')
    def question_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Question ID must be positive')
        return v

# Response models
class ClarifyResponse(BaseModel):
    agent: str
    response: str

class BruteForceResponse(BaseModel):
    agent: str
    response: str

class OptimizeResponse(BaseModel):
    agent: str
    response: str

class FunctionDefinitionResponse(BaseModel):
    function_definition: str

class CodeReviewResponse(BaseModel):
    agent: str
    review: dict

class QuestionResponse(BaseModel):
    id: int
    title: str
    description: str
    examples: List[dict]
    constraints: List[str]

class QuestionsResponse(BaseModel):
    questions: List[dict] 