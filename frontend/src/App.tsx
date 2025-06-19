import React, { useState, useRef } from 'react';
import LoginModal from './LoginModal';
import SignupModal from './SignupModal';
import MonacoEditor from '@monaco-editor/react';

interface Question {
  id: number;
  title: string;
  description: string;
  examples: { input: string; output: string }[];
  constraints: string[];
}

const steps = [
  'question',
  'clarify',
  'bruteForce',
  'optimize',
  'code',
  'review',
];

function App() {
  const [step, setStep] = useState(0);
  const [question, setQuestion] = useState<Question | null>(null);
  const [clarifyInput, setClarifyInput] = useState('');
  const [clarifyResponse, setClarifyResponse] = useState('');
  const [bruteForceInput, setBruteForceInput] = useState('');
  const [bruteForceResponse, setBruteForceResponse] = useState('');
  const [optimizeInput, setOptimizeInput] = useState('');
  const [optimizeResponse, setOptimizeResponse] = useState('');
  const [codeInput, setCodeInput] = useState('');
  const [review, setReview] = useState<any>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));
  const [codeReviewError, setCodeReviewError] = useState('');
  const [darkMode, setDarkMode] = useState(() => {
    // Default to system preference
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true' || window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });
  const [clarifyLoading, setClarifyLoading] = useState(false);
  const [bruteForceLoading, setBruteForceLoading] = useState(false);
  const [optimizeLoading, setOptimizeLoading] = useState(false);
  const clarifyTimeout = useRef<NodeJS.Timeout | null>(null);
  const bruteForceTimeout = useRef<NodeJS.Timeout | null>(null);
  const optimizeTimeout = useRef<NodeJS.Timeout | null>(null);

  const nextStep = () => setStep((s) => s + 1);

  React.useEffect(() => {
    fetch('/api/start-session', { method: 'POST' })
      .then((res) => res.json())
      .then((data) => setQuestion(data.question));
  }, []);

  React.useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    }
  }, [darkMode]);

  // Live feedback for clarify
  React.useEffect(() => {
    if (step !== 1) return;
    if (clarifyTimeout.current) clearTimeout(clarifyTimeout.current);
    if (!clarifyInput.trim()) {
      setClarifyResponse('');
      return;
    }
    setClarifyLoading(true);
    clarifyTimeout.current = setTimeout(() => {
      fetch('/api/clarify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: clarifyInput }),
      })
        .then(res => res.json())
        .then(data => setClarifyResponse(data.response))
        .finally(() => setClarifyLoading(false));
    }, 600);
    // eslint-disable-next-line
  }, [clarifyInput, step]);

  // Live feedback for brute-force
  React.useEffect(() => {
    if (step !== 2) return;
    if (bruteForceTimeout.current) clearTimeout(bruteForceTimeout.current);
    if (!bruteForceInput.trim()) {
      setBruteForceResponse('');
      return;
    }
    setBruteForceLoading(true);
    bruteForceTimeout.current = setTimeout(() => {
      fetch('/api/brute-force', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_idea: bruteForceInput }),
      })
        .then(res => res.json())
        .then(data => setBruteForceResponse(data.response))
        .finally(() => setBruteForceLoading(false));
    }, 600);
    // eslint-disable-next-line
  }, [bruteForceInput, step]);

  // Live feedback for optimize
  React.useEffect(() => {
    if (step !== 3) return;
    if (optimizeTimeout.current) clearTimeout(optimizeTimeout.current);
    if (!optimizeInput.trim()) {
      setOptimizeResponse('');
      return;
    }
    setOptimizeLoading(true);
    optimizeTimeout.current = setTimeout(() => {
      fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_idea: optimizeInput }),
      })
        .then(res => res.json())
        .then(data => setOptimizeResponse(data.response))
        .finally(() => setOptimizeLoading(false));
    }, 600);
    // eslint-disable-next-line
  }, [optimizeInput, step]);

  const handleClarify = async () => {
    const res = await fetch('/api/clarify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: clarifyInput }),
    });
    const data = await res.json();
    setClarifyResponse(data.response);
    nextStep();
  };

  const handleBruteForce = async () => {
    const res = await fetch('/api/brute-force', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_idea: bruteForceInput }),
    });
    const data = await res.json();
    setBruteForceResponse(data.response);
    nextStep();
  };

  const handleOptimize = async () => {
    const res = await fetch('/api/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_idea: optimizeInput }),
    });
    const data = await res.json();
    setOptimizeResponse(data.response);
    nextStep();
  };

  const handleCodeReview = async () => {
    if (!clarifyInput.trim() && !bruteForceInput.trim() && !codeInput.trim()) {
      setCodeReviewError('Please provide at least one answer before submitting for review.');
      return;
    }
    setCodeReviewError('');
    const res = await fetch('/api/code-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        clarification: clarifyInput,
        brute_force: bruteForceInput,
        code: codeInput,
      }),
    });
    const data = await res.json();
    setReview(data.review);
    nextStep();
  };

  const handleLoginSuccess = (token: string) => {
    localStorage.setItem('token', token);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
  };

  const handleRestart = () => {
    setStep(0);
    setClarifyInput('');
    setClarifyResponse('');
    setBruteForceInput('');
    setBruteForceResponse('');
    setOptimizeInput('');
    setOptimizeResponse('');
    setCodeInput('');
    setReview(null);
    fetch('/api/start-session', { method: 'POST' })
      .then((res) => res.json())
      .then((data) => setQuestion(data.question));
  };

  return (
    <div className={"min-h-screen flex flex-col items-center " + (darkMode ? 'bg-gradient-to-br from-gray-900 to-gray-800' : 'bg-gradient-to-br from-blue-50 to-purple-100') + " dark:bg-gradient-to-br dark:from-gray-900 dark:to-gray-800"}>
      <header className={"w-full py-8 shadow-md mb-8 relative " + (darkMode ? 'bg-gradient-to-r from-gray-900 to-gray-800' : 'bg-gradient-to-r from-blue-600 to-purple-600') + " dark:bg-gradient-to-r dark:from-gray-900 dark:to-gray-800"}>
        <h1 className="text-4xl font-extrabold text-white text-center tracking-tight drop-shadow-lg">Leet Coach</h1>
        <p className="text-center text-white text-lg mt-2 font-light">Your AI-powered coding interview simulator</p>
        <div className="absolute top-4 right-8 flex items-center space-x-2">
          <button
            className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 mr-2"
            onClick={() => setDarkMode(dm => !dm)}
            aria-label="Toggle dark mode"
          >
            {darkMode ? '🌙' : '☀️'}
          </button>
          {!isLoggedIn ? (
            <>
              <button
                className="mr-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => setShowLogin(true)}
              >
                Login
              </button>
              <button
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                onClick={() => setShowSignup(true)}
              >
                Sign Up
              </button>
            </>
          ) : (
            <button
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              onClick={handleLogout}
            >
              Logout
            </button>
          )}
        </div>
      </header>
      {isLoggedIn ? (
        <div className={"w-full max-w-2xl rounded-2xl shadow-xl p-8 mb-8 " + (darkMode ? 'bg-gray-900 text-gray-100' : 'bg-white') + " dark:bg-gray-900 dark:text-gray-100"}>
          <nav className="flex justify-between mb-6">
            {steps.map((s, i) => (
              <div
                key={s}
                className={`flex-1 text-center text-xs font-semibold py-2 rounded-full mx-1 transition-all duration-200 cursor-pointer ${step === i ? (darkMode ? 'bg-purple-900 text-white shadow-lg scale-105' : 'bg-purple-600 text-white shadow-lg scale-105') : i <= step ? (darkMode ? 'bg-gray-800 text-gray-300 hover:bg-purple-900' : 'bg-gray-100 text-gray-500 hover:bg-purple-200') : (darkMode ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 'bg-gray-50 text-gray-300 cursor-not-allowed')}`}
                onClick={() => { if (i <= step) setStep(i); }}
              >{
                s === 'question' ? 'Question' :
                s === 'clarify' ? 'Clarify' :
                s === 'bruteForce' ? 'Brute Force' :
                s === 'optimize' ? 'Optimize' :
                s === 'code' ? 'Code' :
                s === 'review' ? 'Review' : s
              }</div>
            ))}
          </nav>
          {step === 0 && question && (
            <div>
              <h2 className="text-2xl font-bold mb-2 text-purple-700">{question.title}</h2>
              <p className="mb-4 text-gray-700 text-lg">{question.description}</p>
              <div className="mb-4">
                <strong className="text-gray-800">Examples:</strong>
                {question.examples.map((ex, i) => (
                  <div key={i} className="ml-4 text-sm text-gray-600">Input: {ex.input} <span className="text-gray-400">→</span> Output: {ex.output}</div>
                ))}
              </div>
              <div className="mb-4">
                <strong className="text-gray-800">Constraints:</strong>
                <ul className="list-disc ml-6 text-sm text-gray-600">
                  {question.constraints.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
              <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={nextStep}>Start Interview</button>
            </div>
          )}
          {step === 1 && (
            <div>
              <h2 className="font-semibold text-lg text-purple-700 mb-2">Step 1: Ask clarifying questions</h2>
              <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400 dark:border-gray-700" value={clarifyInput} onChange={e => setClarifyInput(e.target.value)} placeholder="Ask about input, constraints, etc." />
              {clarifyLoading && <div className="text-xs text-gray-400">Loading feedback...</div>}
              {clarifyResponse && <div className="mt-4 p-3 bg-purple-50 dark:bg-gray-800 border-l-4 border-purple-400 text-purple-900 dark:text-purple-200 rounded">Interviewer: {clarifyResponse}</div>}
              <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all mt-2" onClick={handleClarify}>Next</button>
            </div>
          )}
          {step === 2 && (
            <div>
              <h2 className="font-semibold text-lg text-purple-700 mb-2">Step 2: Explain brute-force solution</h2>
              <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400 dark:border-gray-700" value={bruteForceInput} onChange={e => setBruteForceInput(e.target.value)} placeholder="Describe your brute-force approach..." />
              {bruteForceLoading && <div className="text-xs text-gray-400">Loading feedback...</div>}
              {bruteForceResponse && <div className="mt-4 p-3 bg-purple-50 dark:bg-gray-800 border-l-4 border-purple-400 text-purple-900 dark:text-purple-200 rounded">Interviewer: {bruteForceResponse}</div>}
              <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all mt-2" onClick={handleBruteForce}>Next</button>
            </div>
          )}
          {step === 3 && (
            <div>
              <h2 className="font-semibold text-lg text-purple-700 mb-2">Step 3: Explain optimized solution</h2>
              <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400 dark:border-gray-700" value={optimizeInput} onChange={e => setOptimizeInput(e.target.value)} placeholder="Describe your optimized approach..." />
              {optimizeLoading && <div className="text-xs text-gray-400">Loading feedback...</div>}
              {optimizeResponse && <div className="mt-4 p-3 bg-purple-50 dark:bg-gray-800 border-l-4 border-purple-400 text-purple-900 dark:text-purple-200 rounded">Interviewer: {optimizeResponse}</div>}
              <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all mt-2" onClick={handleOptimize}>Next</button>
            </div>
          )}
          {step === 4 && (
            <div>
              <h2 className="font-semibold text-lg text-purple-700 dark:text-purple-300 mb-2">Step 4: Write your code</h2>
              <div className="mb-2">
                <MonacoEditor
                  height="300px"
                  language="python"
                  theme={darkMode ? 'vs-dark' : 'vs-light'}
                  value={codeInput}
                  onChange={(value: string | undefined) => setCodeInput(value || '')}
                  options={{ fontSize: 14, minimap: { enabled: false } }}
                />
              </div>
              {codeReviewError && <div className="text-red-500 text-sm mb-2">{codeReviewError}</div>}
              <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={handleCodeReview} disabled={!clarifyInput.trim() && !bruteForceInput.trim() && !codeInput.trim()}>Submit for Review</button>
            </div>
          )}
          {step === 5 && review && (
            <div>
              <h2 className="font-semibold text-lg text-purple-700 mb-4">Step 5: Code Review</h2>
              <div className="p-4 bg-purple-50 border-2 border-purple-200 rounded-xl mb-4 shadow">
                {typeof review.total === 'number' && (
                  <div className="mb-4 text-xl font-bold text-purple-800 dark:text-purple-200">
                    Total Score: <span className="font-mono">{review.total}/10</span>
                    <div className="text-sm text-gray-600 dark:text-gray-300 font-normal mt-1">This is your overall performance score for the interview, based on all stages.</div>
                  </div>
                )}
                <div className="mb-4">
                  <strong className="text-purple-700">Input Clarification:</strong> <span className="font-mono">{review.clarification?.grade}/10</span>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">How well you clarified the problem and requirements.</div>
                  <span className="text-sm text-gray-700">{review.clarification?.feedback}</span>
                </div>
                <div className="mb-4">
                  <strong className="text-purple-700">Brute-force Idea:</strong> <span className="font-mono">{review.brute_force?.grade}/10</span>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">How well you proposed and analyzed a brute-force solution.</div>
                  <span className="text-sm text-gray-700">{review.brute_force?.feedback}</span>
                </div>
                <div className="mb-4">
                  <strong className="text-purple-700">Coding Solution:</strong> <span className="font-mono">{review.coding?.grade}/10</span>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">How correct, efficient, and clear your final code was.</div>
                  <span className="text-sm text-gray-700">{review.coding?.feedback}</span>
                </div>
                <div className="mb-2">
                  <strong className="text-purple-700">Key Pointers:</strong> <span className="text-sm text-gray-700">{review.key_pointers}</span>
                </div>
              </div>
              <button className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={handleRestart}>Restart</button>
            </div>
          )}
        </div>
      ) : (
        <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl p-8 mb-8 flex flex-col items-center">
          <h2 className="text-2xl font-bold text-purple-700 mb-2">Welcome to Leet Coach!</h2>
          <p className="text-gray-700 text-lg mb-4 text-center">Sign up or log in to start your personalized coding interview simulation and get AI-powered feedback on your solutions.</p>
          <div className="flex space-x-4">
            <button
              className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              onClick={() => setShowLogin(true)}
            >
              Login
            </button>
            <button
              className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              onClick={() => setShowSignup(true)}
            >
              Sign Up
            </button>
          </div>
        </div>
      )}
      <footer className="text-center text-gray-400 text-xs mt-8 mb-2 dark:text-gray-500">&copy; {new Date().getFullYear()} Leet Coach. All rights reserved.</footer>
      <LoginModal
        open={showLogin}
        onClose={() => setShowLogin(false)}
        onLoginSuccess={handleLoginSuccess}
      />
      <SignupModal
        open={showSignup}
        onClose={() => setShowSignup(false)}
        onSignupSuccess={() => setShowSignup(false)}
      />
    </div>
  );
}

export default App; 