import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openai
import os

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
    def get_question(self):
        return QUESTIONS[0]  # For demo, always return first question

class ClarificationAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def respond(self, user_input):
        prompt = f"""
You are a helpful assistant for clarifying coding questions. Given the user's input, provide a detailed clarification or ask for more information if needed. Be specific and constructive.

User input:
{user_input}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant for clarifying coding questions."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class BruteForceAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def feedback(self, user_idea):
        prompt = f"""
You are a coding assistant. Given the user's brute-force idea for solving a problem, provide a detailed review. Include strengths, weaknesses, and suggestions for improvement. Be specific and constructive.

Brute-force idea:
{user_idea}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful coding assistant for reviewing brute-force ideas."},
                      {"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class OptimizeAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def feedback(self, user_idea):
        prompt = f"""
You are a coding assistant. Given the user's optimized idea for solving a problem, provide a detailed review. Include strengths, weaknesses, and suggestions for further optimization. Be specific and constructive.

Optimized idea:
{user_idea}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful coding assistant for reviewing optimized ideas."},
                      {"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3
        )
        return response['choices'][0]['message']['content']

class CodeReviewAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def review(self, clarification, brute_force, code, question):
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
2. Brute-force Idea: How well did the user propose and analyze a brute-force solution?
3. Coding Solution: How correct, efficient, and clear is the final code?

Return a JSON object with this structure:
{{
  "clarification": {{"grade": int, "feedback": str}},
  "brute_force": {{"grade": int, "feedback": str}},
  "coding": {{"grade": int, "feedback": str}},
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
            max_tokens=500,
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
        return {"clarification": {}, "brute_force": {}, "coding": {}, "key_pointers": content}

# Simulate agent flow for demo
@app.post("/api/start-session")
async def start_session(request: Request):
    question = QuestionAgent().get_question()
    return {"question": question}

@app.post("/api/clarify")
async def clarify(request: Request):
    data = await request.json()
    response = ClarificationAgent().respond(data.get("user_input", ""))
    return {"agent": "ClarificationAgent", "response": response}

@app.post("/api/brute-force")
async def brute_force(request: Request):
    data = await request.json()
    response = BruteForceAgent().feedback(data.get("user_idea", ""))
    return {"agent": "BruteForceAgent", "response": response}

@app.post("/api/optimize")
async def optimize(request: Request):
    data = await request.json()
    response = OptimizeAgent().feedback(data.get("user_idea", ""))
    return {"agent": "OptimizeAgent", "response": response}

@app.post("/api/code-review")
async def code_review(request: Request):
    data = await request.json()
    # For now, always use the first question
    question = QUESTIONS[0]
    review = CodeReviewAgent().review(
        data.get("clarification", ""),
        data.get("brute_force", ""),
        data.get("code", ""),
        question
    )
    return {"agent": "CodeReviewAgent", "review": review} 