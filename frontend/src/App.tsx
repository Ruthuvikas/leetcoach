import React, { useState, useRef, useEffect } from 'react';
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
  'Question',
  'Clarify',
  'Brute Force',
  'Optimize',
  'Code',
  'Review',
];

const languages = [
  { value: 'javascript', label: 'JavaScript' },
  { value: 'python', label: 'Python' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'go', label: 'Go' },
];

function App() {
  const [activeTab, setActiveTab] = useState('Question');
  const [question, setQuestion] = useState<Question | null>(null);
  const [questions, setQuestions] = useState<{ id: number; title: string }[]>([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(null);
  const [clarifyInput, setClarifyInput] = useState('');
  const [clarifyResponse, setClarifyResponse] = useState('');
  const [showClarifyFeedback, setShowClarifyFeedback] = useState(false);
  const [bruteForceInput, setBruteForceInput] = useState('');
  const [bruteForceResponse, setBruteForceResponse] = useState('');
  const [showBruteForceFeedback, setShowBruteForceFeedback] = useState(false);
  const [optimizeInput, setOptimizeInput] = useState('');
  const [optimizeResponse, setOptimizeResponse] = useState('');
  const [showOptimizeFeedback, setShowOptimizeFeedback] = useState(false);
  const [codeInput, setCodeInput] = useState('');
  const [language, setLanguage] = useState('javascript');
  const [review, setReview] = useState<any>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));
  const [codeReviewError, setCodeReviewError] = useState('');
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true' || window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });
  const [clarifyLoading, setClarifyLoading] = useState(false);
  const [bruteForceLoading, setBruteForceLoading] = useState(false);
  const [optimizeLoading, setOptimizeLoading] = useState(false);
  const [bruteForceTime, setBruteForceTime] = useState('');
  const [bruteForceSpace, setBruteForceSpace] = useState('');
  const [optimizeTime, setOptimizeTime] = useState('');
  const [optimizeSpace, setOptimizeSpace] = useState('');
  const [timer, setTimer] = useState(45 * 60);
  const [timerActive, setTimerActive] = useState(false);
  const [timeout, setTimeoutReached] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetch('/api/questions')
      .then(res => res.json())
      .then(data => setQuestions(data));
  }, []);

  useEffect(() => {
    if (selectedQuestionId !== null) {
      fetch('/api/start-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: selectedQuestionId })
      })
        .then((res) => res.json())
        .then((data) => {
          setQuestion(data.question);
        });
    }
  }, [selectedQuestionId]);

  useEffect(() => {
    if (question && language) {
      setCodeInput('// Loading function definition...');
      fetch('/api/function-definition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: question.id, language: language })
      })
      .then(res => res.json())
      .then(data => {
        setCodeInput(data.function_definition);
      });
    }
  }, [question, language]);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    }
  }, [darkMode]);

  // Timer effect
  useEffect(() => {
    if (!timerActive || timeout) return;
    if (timer <= 0) {
      setTimeoutReached(true);
      setTimerActive(false);
      return;
    }
    timerRef.current = setTimeout(() => setTimer(t => t - 1), 1000);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [timer, timerActive, timeout]);


  const formatTimer = (t: number) => {
    const m = Math.floor(t / 60).toString().padStart(2, '0');
    const s = (t % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleStartInterview = () => {
    setActiveTab('Clarify');
    setTimerActive(true);
  };

  const handleGetClarifyFeedback = async () => {
    setClarifyLoading(true);
    setShowClarifyFeedback(false);
    const res = await fetch('/api/clarify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: clarifyInput, question_id: selectedQuestionId }),
    });
    const data = await res.json();
    setClarifyResponse(data.response);
    setClarifyLoading(false);
    setShowClarifyFeedback(true);
  };

  const handleGetBruteForceFeedback = async () => {
    setBruteForceLoading(true);
    setShowBruteForceFeedback(false);
    const res = await fetch('/api/brute-force', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_idea: bruteForceInput, time_complexity: bruteForceTime, space_complexity: bruteForceSpace, question_id: selectedQuestionId }),
    });
    const data = await res.json();
    setBruteForceResponse(data.response);
    setBruteForceLoading(false);
    setShowBruteForceFeedback(true);
  };

  const handleGetOptimizeFeedback = async () => {
    setOptimizeLoading(true);
    setShowOptimizeFeedback(false);
    const res = await fetch('/api/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_idea: optimizeInput, time_complexity: optimizeTime, space_complexity: optimizeSpace, question_id: selectedQuestionId }),
    });
    const data = await res.json();
    setOptimizeResponse(data.response);
    setOptimizeLoading(false);
    setShowOptimizeFeedback(true);
  };

  const handleCodeReview = async () => {
    if (window.confirm('Are you sure you want to submit for final review?')) {
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
          language: language,
          brute_force_time_complexity: bruteForceTime,
          brute_force_space_complexity: bruteForceSpace,
          optimize_time_complexity: optimizeTime,
          optimize_space_complexity: optimizeSpace,
          question_id: selectedQuestionId
        }),
      });
      const data = await res.json();
      setReview(data.review);
      setActiveTab('Review');
      setTimerActive(false);
    }
  };

  const handleLoginSuccess = (token: string) => {
    localStorage.setItem('token', token);
    setIsLoggedIn(true);
    setShowLogin(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
  };

  const handleRestart = () => {
    setActiveTab('Question');
    setQuestion(null);
    setSelectedQuestionId(null);
    setClarifyInput('');
    setClarifyResponse('');
    setShowClarifyFeedback(false);
    setBruteForceInput('');
    setBruteForceResponse('');
    setShowBruteForceFeedback(false);
    setOptimizeInput('');
    setOptimizeResponse('');
    setShowOptimizeFeedback(false);
    setCodeInput('');
    setReview(null);
    setCodeReviewError('');
    setTimer(45 * 60);
    setTimerActive(false);
    setTimeoutReached(false);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100`}>
      <header className="p-4 flex justify-between items-center bg-white dark:bg-gray-800 shadow-md">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white">LeetCoach</h1>
        <div className="flex items-center">
          <button onClick={() => setDarkMode(!darkMode)} className="mr-4 p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
            {darkMode ? '☀️' : '🌙'}
          </button>
          {isLoggedIn ? (
            <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600">Logout</button>
          ) : (
            <>
              <button onClick={() => setShowLogin(true)} className="mr-2 bg-indigo-500 text-white px-4 py-2 rounded-md hover:bg-indigo-600">Login</button>
              <button onClick={() => setShowSignup(true)} className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600">Sign Up</button>
            </>
          )}
        </div>
      </header>

      <main className="p-8">
        {question === null ? (
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-4">Select a Question</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {questions.map(q => (
                <div key={q.id} onClick={() => setSelectedQuestionId(q.id)} className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md cursor-pointer hover:shadow-xl transition-shadow">
                  <h3 className="text-xl font-bold">{q.title}</h3>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-3xl font-bold">{question.title}</h2>
              <div className={`text-2xl font-mono p-2 rounded-lg ${timeout ? 'text-red-500' : ''}`}>
                {formatTimer(timer)}
              </div>
            </div>

            <div className="flex border-b border-gray-300 dark:border-gray-700 mb-4">
              {steps.map(s => (
                <button
                  key={s}
                  onClick={() => setActiveTab(s)}
                  className={`px-4 py-2 -mb-px border-b-2 ${activeTab === s ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent hover:text-gray-600 dark:hover:text-gray-300'}`}
                >
                  {s}
                </button>
              ))}
            </div>

            {activeTab === 'Question' && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                <p className="whitespace-pre-wrap mb-4">{question.description}</p>
                <div className="mb-4">
                  <h4 className="font-semibold text-lg mb-2">Examples:</h4>
                  {question.examples.map((ex, i) => (
                    <div key={i} className="bg-gray-100 dark:bg-gray-700 p-3 rounded-md mb-2">
                      <p><strong>Input:</strong> {ex.input}</p>
                      <p><strong>Output:</strong> {ex.output}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 text-center">
                  <button onClick={handleStartInterview} className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors">Start Interview</button>
                </div>
              </div>
            )}

            {activeTab === 'Clarify' && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                <h3 className="text-2xl font-bold mb-4">Clarifying Questions</h3>
                <p className="mb-4">Ask any questions you have to clarify the problem statement, constraints, or examples.</p>
                <textarea
                  value={clarifyInput}
                  onChange={(e) => setClarifyInput(e.target.value)}
                  placeholder="e.g., What should I return if there's no solution? Are the numbers in the input array unique?"
                  className="w-full p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  rows={5}
                />
                <div className="mt-4 text-center">
                  <button onClick={handleGetClarifyFeedback} disabled={clarifyLoading} className="bg-indigo-500 text-white px-6 py-2 rounded-md hover:bg-indigo-600 disabled:bg-gray-400">
                    {clarifyLoading ? 'Getting Feedback...' : 'Get Interviewer Feedback'}
                  </button>
                </div>
                {showClarifyFeedback && (
                  <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-md">
                    <h4 className="font-semibold text-lg mb-2">Interviewer Feedback:</h4>
                    <p className="whitespace-pre-wrap">{clarifyResponse}</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'Brute Force' && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                <h3 className="text-2xl font-bold mb-4">Brute-force Solution</h3>
                <p className="mb-4">Describe your initial, straightforward approach to solving the problem. Don't worry about efficiency yet.</p>
                <textarea
                  value={bruteForceInput}
                  onChange={(e) => setBruteForceInput(e.target.value)}
                  placeholder="Describe your brute-force idea here. e.g., I'll use nested loops to check every pair of numbers..."
                  className="w-full p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  rows={5}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <input
                    type="text"
                    value={bruteForceTime}
                    onChange={(e) => setBruteForceTime(e.target.value)}
                    placeholder="Time Complexity (e.g., O(n^2))"
                    className="p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                  <input
                    type="text"
                    value={bruteForceSpace}
                    onChange={(e) => setBruteForceSpace(e.target.value)}
                    placeholder="Space Complexity (e.g., O(1))"
                    className="p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                <div className="mt-4 text-center">
                  <button onClick={handleGetBruteForceFeedback} disabled={bruteForceLoading} className="bg-indigo-500 text-white px-6 py-2 rounded-md hover:bg-indigo-600 disabled:bg-gray-400">
                    {bruteForceLoading ? 'Getting Feedback...' : 'Get Interviewer Feedback'}
                  </button>
                </div>
                {showBruteForceFeedback && (
                  <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-md">
                    <h4 className="font-semibold text-lg mb-2">Interviewer Feedback:</h4>
                    <p className="whitespace-pre-wrap">{bruteForceResponse}</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'Optimize' && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                <h3 className="text-2xl font-bold mb-4">Optimized Solution</h3>
                <p className="mb-4">Now, describe a more efficient approach. How can you improve the time or space complexity?</p>
                <textarea
                  value={optimizeInput}
                  onChange={(e) => setOptimizeInput(e.target.value)}
                  placeholder="Describe your optimized idea here. e.g., I can use a hash map to store numbers I've seen..."
                  className="w-full p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  rows={5}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <input
                    type="text"
                    value={optimizeTime}
                    onChange={(e) => setOptimizeTime(e.target.value)}
                    placeholder="Time Complexity (e.g., O(n))"
                    className="p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                  <input
                    type="text"
                    value={optimizeSpace}
                    onChange={(e) => setOptimizeSpace(e.target.value)}
                    placeholder="Space Complexity (e.g., O(n))"
                    className="p-3 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                <div className="mt-4 text-center">
                  <button onClick={handleGetOptimizeFeedback} disabled={optimizeLoading} className="bg-indigo-500 text-white px-6 py-2 rounded-md hover:bg-indigo-600 disabled:bg-gray-400">
                    {optimizeLoading ? 'Getting Feedback...' : 'Get Interviewer Feedback'}
                  </button>
                </div>
                {showOptimizeFeedback && (
                  <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-md">
                    <h4 className="font-semibold text-lg mb-2">Interviewer Feedback:</h4>
                    <p className="whitespace-pre-wrap">{optimizeResponse}</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'Code' && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-2xl font-bold">Code Implementation</h3>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                  >
                    {languages.map(lang => (
                      <option key={lang.value} value={lang.value}>{lang.label}</option>
                    ))}
                  </select>
                </div>
                <div className="border rounded-md overflow-hidden">
                  <MonacoEditor
                    height="400px"
                    language={language}
                    theme={darkMode ? 'vs-dark' : 'light'}
                    value={codeInput}
                    onChange={(value) => setCodeInput(value || '')}
                    options={{ minimap: { enabled: false } }}
                  />
                </div>
                <div className="mt-6 text-center">
                  <button onClick={handleCodeReview} className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors">Submit for Final Review</button>
                </div>
                {codeReviewError && <p className="text-red-500 text-center mt-4">{codeReviewError}</p>}
              </div>
            )}

            {activeTab === 'Review' && review && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                <h3 className="text-3xl font-bold mb-6 text-center">Final Interview Report</h3>
                <div className="text-center mb-6">
                  <p className="text-lg">Total Score:</p>
                  <p className="text-5xl font-bold text-indigo-600 dark:text-indigo-400">{review.total}/10</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <h4 className="font-bold text-xl mb-2">Clarification</h4>
                    <p className="text-2xl font-semibold mb-2">{review.clarification.grade}/10</p>
                    <p>{review.clarification.feedback}</p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <h4 className="font-bold text-xl mb-2">Brute-force</h4>
                    <p className="text-2xl font-semibold mb-2">{review.brute_force.grade}/10</p>
                    <p>{review.brute_force.feedback}</p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <h4 className="font-bold text-xl mb-2">Coding</h4>
                    <p className="text-2xl font-semibold mb-2">{review.coding.grade}/10</p>
                    <p>{review.coding.feedback}</p>
                  </div>
                </div>
                
                {/* Line-by-line code feedback */}
                {review.coding.line_by_line && review.coding.line_by_line.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-bold text-xl mb-4">Code Analysis - Line by Line</h4>
                    <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                      <div className="mb-4">
                        <h5 className="font-semibold mb-2">Your Code:</h5>
                        <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-sm overflow-x-auto">
                          <code>{codeInput}</code>
                        </pre>
                      </div>
                      <div>
                        <h5 className="font-semibold mb-2">Issues Found:</h5>
                        {review.coding.line_by_line.map((item: any, index: number) => (
                          <div key={index} className="mb-3 p-3 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400 rounded">
                            <p className="font-semibold text-red-700 dark:text-red-300">
                              Line {item.line}: {item.issue}
                            </p>
                            <p className="text-sm text-red-600 dark:text-red-200 mt-1">
                              <strong>Suggestion:</strong> {item.suggestion}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                
                <div>
                  <h4 className="font-bold text-xl mb-2">Key Pointers for Improvement</h4>
                  <p className="whitespace-pre-wrap">{review.key_pointers}</p>
                </div>
                <div className="mt-8 text-center">
                  <button onClick={handleRestart} className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors">Try Another Question</button>
                </div>
              </div>
            )}

          </div>
        )}

        <LoginModal open={showLogin} onClose={() => setShowLogin(false)} onLoginSuccess={handleLoginSuccess} />
        <SignupModal open={showSignup} onClose={() => setShowSignup(false)} onSignupSuccess={() => setShowSignup(false)} />
      </main>
    </div>
  );
}

export default App; 