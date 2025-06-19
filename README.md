# LeetCoach: Agentic LeetCode Interview Simulator

## Overview
LeetCoach is a fullstack application that simulates LeetCode-style technical interviews using LLM-powered agents. The app guides users through a realistic interview workflow, providing feedback and scoring at each step.

## Tech Stack
- **Frontend:** React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, LangGraph
- **LLM:** OpenAI or local model via LangGraph

## Workflow
1. User is shown a random LeetCode-style question.
2. User asks clarifying questions.
3. ClarificationAgent responds as interviewer.
4. User explains brute-force solution.
5. BruteForceAgent gives feedback and prompts for optimization.
6. User explains optimized approach.
7. User writes code.
8. CodeReviewAgent reviews code, gives structured feedback and scores.

## Project Structure
```
leetcoach/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── index.css
│   ├── package.json
│   └── tailwind.config.js
├── questions.json
└── README.md
```

## Getting Started

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Data
- Add more questions to `questions.json` as needed.

---
This is a starter scaffold. Extend the agent logic in `backend/main.py` using LangGraph for a more realistic interview simulation. 