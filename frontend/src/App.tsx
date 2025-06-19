import React, { useState } from 'react';

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

  const nextStep = () => setStep((s) => s + 1);

  React.useEffect(() => {
    fetch('/api/start-session', { method: 'POST' })
      .then((res) => res.json())
      .then((data) => setQuestion(data.question));
  }, []);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-100 flex flex-col items-center">
      <header className="w-full py-8 bg-gradient-to-r from-blue-600 to-purple-600 shadow-md mb-8">
        <h1 className="text-4xl font-extrabold text-white text-center tracking-tight drop-shadow-lg">Leet Coach</h1>
        <p className="text-center text-white text-lg mt-2 font-light">Your AI-powered coding interview simulator</p>
      </header>
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-8 mb-8">
        <nav className="flex justify-between mb-6">
          {steps.map((s, i) => (
            <div key={s} className={`flex-1 text-center text-xs font-semibold py-2 rounded-full mx-1 transition-all duration-200 ${step === i ? 'bg-purple-600 text-white shadow-lg scale-105' : 'bg-gray-100 text-gray-500'}`}>{
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
            <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2" value={clarifyInput} onChange={e => setClarifyInput(e.target.value)} placeholder="Ask about input, constraints, etc." />
            <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={handleClarify}>Submit</button>
            {clarifyResponse && <div className="mt-4 p-3 bg-purple-50 border-l-4 border-purple-400 text-purple-900 rounded">Interviewer: {clarifyResponse}</div>}
          </div>
        )}
        {step === 2 && (
          <div>
            <h2 className="font-semibold text-lg text-purple-700 mb-2">Step 2: Explain brute-force solution</h2>
            <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2" value={bruteForceInput} onChange={e => setBruteForceInput(e.target.value)} placeholder="Describe your brute-force approach..." />
            <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={handleBruteForce}>Submit</button>
            {bruteForceResponse && <div className="mt-4 p-3 bg-purple-50 border-l-4 border-purple-400 text-purple-900 rounded">Interviewer: {bruteForceResponse}</div>}
          </div>
        )}
        {step === 3 && (
          <div>
            <h2 className="font-semibold text-lg text-purple-700 mb-2">Step 3: Explain optimized solution</h2>
            <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2" value={optimizeInput} onChange={e => setOptimizeInput(e.target.value)} placeholder="Describe your optimized approach..." />
            <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={handleOptimize}>Submit</button>
            {optimizeResponse && <div className="mt-4 p-3 bg-purple-50 border-l-4 border-purple-400 text-purple-900 rounded">Interviewer: {optimizeResponse}</div>}
          </div>
        )}
        {step === 4 && (
          <div>
            <h2 className="font-semibold text-lg text-purple-700 mb-2">Step 4: Write your code</h2>
            <textarea className="w-full border-2 border-purple-200 rounded-lg p-2 font-mono focus:outline-none focus:ring-2 focus:ring-purple-400 transition mb-2" rows={8} value={codeInput} onChange={e => setCodeInput(e.target.value)} placeholder="Write your code here..." />
            <button className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={handleCodeReview}>Submit for Review</button>
          </div>
        )}
        {step === 5 && review && (
          <div>
            <h2 className="font-semibold text-lg text-purple-700 mb-4">Step 5: Code Review</h2>
            <div className="p-4 bg-purple-50 border-2 border-purple-200 rounded-xl mb-4 shadow">
              <div className="mb-4">
                <strong className="text-purple-700">Input Clarification:</strong> <span className="font-mono">{review.clarification?.grade}/10</span><br/>
                <span className="text-sm text-gray-700">{review.clarification?.feedback}</span>
              </div>
              <div className="mb-4">
                <strong className="text-purple-700">Brute-force Idea:</strong> <span className="font-mono">{review.brute_force?.grade}/10</span><br/>
                <span className="text-sm text-gray-700">{review.brute_force?.feedback}</span>
              </div>
              <div className="mb-4">
                <strong className="text-purple-700">Coding Solution:</strong> <span className="font-mono">{review.coding?.grade}/10</span><br/>
                <span className="text-sm text-gray-700">{review.coding?.feedback}</span>
              </div>
              <div className="mb-2">
                <strong className="text-purple-700">Key Pointers:</strong> <span className="text-sm text-gray-700">{review.key_pointers}</span>
              </div>
            </div>
            <button className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-2 px-6 rounded-full shadow transition-all" onClick={() => window.location.reload()}>Restart</button>
          </div>
        )}
      </div>
      <footer className="text-center text-gray-400 text-xs mt-8 mb-2">&copy; {new Date().getFullYear()} Leet Coach. All rights reserved.</footer>
    </div>
  );
}

export default App; 