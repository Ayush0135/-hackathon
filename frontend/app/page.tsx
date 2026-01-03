'use client';
import { useState, useEffect, useRef } from 'react';
import { useUser, UserButton, SignedIn, SignedOut, RedirectToSignIn } from '@clerk/nextjs';
import ReactMarkdown from 'react-markdown';
import { useRouter } from 'next/navigation';

export default function Home() {
  const { user, isLoaded, isSignedIn } = useUser();
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState<'idle' | 'running' | 'complete'>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [currentStage, setCurrentStage] = useState('Initializing...');
  const [stageNumber, setStageNumber] = useState(0);
  const [finalPaper, setFinalPaper] = useState('');
  const socketRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isSyncing, setIsSyncing] = useState(true);
  // State for history
  const [history, setHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Auth Handling & Backend Sync
  useEffect(() => {
    if (isLoaded) {
      if (!isSignedIn) {
        router.push('/sign-in');
      } else if (user) {
        // User is signed in, sync with backend
        const sync = async () => {
          try {
            const email = user.primaryEmailAddress?.emailAddress;
            if (!email) return;

            // 1. Silent Register
            try {
              await fetch('http://localhost:8000/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  email,
                  password: "temp-secure-pass",
                  otp: "GOOGLE_BYPASS"
                }),
              });
            } catch (e) { }

            // 2. Login
            const res = await fetch('http://localhost:8000/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                email,
                password: "temp-secure-pass"
              }),
            });

            const data = await res.json();
            if (data.access_token) {
              localStorage.setItem('token', data.access_token);
            }
          } catch (e) {
            console.error("Backend sync failed", e);
          } finally {
            setIsSyncing(false);
          }
        };
        sync();
      }
    }
  }, [isLoaded, isSignedIn, user, router]);

  useEffect(() => {
    // Auto-scroll logs
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (!isLoaded || (isSignedIn && isSyncing)) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-amber-500 font-mono">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="tracking-widest uppercase text-xs">Synchronizing Neural Uplink...</p>
        </div>
      </div>
    );
  }

  // Logout is handled by UserButton or Clerk's signOut, but here's a manual wrapper if needed
  // const handleLogout = () => signOut(() => router.push('/login'));

  const startResearch = () => {
    if (!topic.trim()) return;
    setStatus('running');
    setLogs([]);
    setFinalPaper('');
    setStageNumber(1);
    setCurrentStage('Topic Decomposition');

    // Connect to websocket with auto-reconnect
    const connectWebSocket = () => {
      if (socketRef.current?.readyState === WebSocket.OPEN) return;

      socketRef.current = new WebSocket('ws://localhost:8000/ws');

      socketRef.current.onopen = () => {
        console.log("WebSocket connected");
        // Only send START if we are just starting (stageNumber 1), otherwise we might be reconnecting
        if (stageNumber <= 1) {
          socketRef.current?.send(`START:${topic}`);
        }
      };

      socketRef.current.onmessage = (event) => {
        const msg = event.data;
        if (msg === 'DONE') {
          setStatus('complete');
          return;
        }

        if (msg.startsWith('FINAL_PAPER_CONTENT:')) {
          setFinalPaper(msg.replace('FINAL_PAPER_CONTENT:', ''));
          return;
        }
        if (msg.startsWith('STAGE:')) {
          const stageCode = msg.split(':')[1];
          const stageMap: Record<string, string> = {
            '1': 'Topic Decomposition',
            '2': 'Document Discovery',
            '3': 'Deep Analysis',
            '3b': 'Recursive Deepening',
            '4': 'Academic Scoring',
            '5': 'Filtering & Selection',
            '6': 'Synthesis',
            '7': 'Draft Generation',
            '8': 'Peer Review',
          };
          const numMap: Record<string, number> = {
            '1': 1, '2': 2, '3': 3, '3b': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8
          };

          setCurrentStage(stageMap[stageCode] || 'Processing...');
          setStageNumber(numMap[stageCode] || stageNumber);

          // Show errors in the UI instead of suppressing them
          if (msg.startsWith('ERROR:') || msg.toLowerCase().includes('traceback')) {
            setLogs(prev => [...prev.slice(-200), `⚠️ SYSTEM ERROR: ${msg}`]);
          } else {
            setLogs(prev => [...prev.slice(-200), msg]);
          }
        }
      };

      socketRef.current.onerror = (err) => {
        console.error("Socket error", err);
      };

      socketRef.current.onclose = () => {
        console.log("Socket closed. Reconnecting in 3s...");
        if (status === 'running') {
          setTimeout(connectWebSocket, 3000);
        }
      };
    };

    connectWebSocket();
  };



  const fetchHistory = async () => {
    try {
      const res = await fetch('http://localhost:8000/history');
      const data = await res.json();
      setHistory(data);
      setShowHistory(true);
    } catch (e) { console.error(e); }
  }

  // Effect to load final paper if selecting from history (mock logic for now, or just show list)

  return (
    <div className="min-h-screen bg-[#050505] text-slate-200 font-sans selection:bg-amber-500/30 flex flex-col relative overflow-x-hidden">

      {/* History Sidebar - Slide Over */}
      <div className={`fixed inset-y-0 right-0 w-96 bg-[#0e0e0e] border-l border-white/10 transform transition-transform duration-300 z-50 p-6 shadow-2xl ${showHistory ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-xl font-serif text-amber-500">Research Archives</h2>
          <button onClick={() => setShowHistory(false)} className="text-slate-400 hover:text-white">✕</button>
        </div>
        <div className="space-y-4 overflow-y-auto h-[80vh]">
          {Array.isArray(history) && history.length > 0 ? (
            history.map((item: any) => (
              <div key={item.id} className="p-4 bg-white/5 rounded border border-white/5 hover:border-amber-500/50 cursor-pointer transition">
                <div className="text-sm font-bold text-white mb-1">{item.topic}</div>
                <div className="text-xs text-slate-500">{new Date(item.date).toLocaleDateString()}</div>
              </div>
            ))
          ) : (
            <div className="p-4 text-slate-500 text-sm">No archives found (or sync error).</div>
          )}
        </div>
      </div>

      {/* Header */}
      <header className="p-6 border-b border-white/5 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <img src="/logo.png" alt="SureFact Logo" className="w-12 h-12 rounded-xl shadow-[0_0_15px_rgba(251,191,36,0.2)]" />
            <h1 className="text-xl font-serif font-bold tracking-wide text-white">
              SureFact
            </h1>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={fetchHistory} className="text-xs font-mono text-slate-400 hover:text-amber-500 uppercase tracking-widest transition">
              Archives
            </button>
            <div className="border border-white/10 rounded-full p-1">
              <UserButton />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden">

        {/* Background Gradients */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-0 right-0 w-[600px] h-[400px] bg-cyan-500/5 rounded-full blur-[100px] pointer-events-none"></div>

        {status === 'idle' && (
          <div className="z-10 w-full max-w-2xl text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h2 className="text-5xl font-extrabold tracking-tight">
              What do you want to <span className="text-cyan-400">discover</span>?
            </h2>
            <p className="text-lg text-slate-400 max-w-lg mx-auto">
              Deployment of autonomous AI agents to research, analyze, and synthesize academic literature on any topic.
            </p>

            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg blur opacity-25 group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative flex shadow-2xl">
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && startResearch()}
                  placeholder="e.g. 'Impact of Microplastics on Human Biology'"
                  className="block w-full text-lg p-5 rounded-l-lg bg-slate-900 border border-r-0 border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-0 focus:border-slate-600 transition"
                />
                <button
                  onClick={startResearch}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-8 rounded-r-lg font-semibold tracking-wide transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)]"
                >
                  RESEARCH
                </button>
              </div>
            </div>

            <div className="flex gap-4 justify-center text-sm text-slate-500">
              <span className="px-3 py-1 rounded-full border border-slate-800 bg-slate-900/50">8 Stages</span>
              <span className="px-3 py-1 rounded-full border border-slate-800 bg-slate-900/50">Multi-Agent</span>
              <span className="px-3 py-1 rounded-full border border-slate-800 bg-slate-900/50">Live Web Access</span>
            </div>
          </div>
        )}

        {status === 'running' && (
          <div className="w-full flex flex-col items-center justify-center z-10 animate-in fade-in duration-1000 min-h-[60vh] relative">

            {/* Ambient Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-500/5 rounded-full blur-[120px] pointer-events-none animate-pulse"></div>

            {/* Central Visualization */}
            <div className="relative flex flex-col items-center justify-center p-12 backdrop-blur-sm rounded-full bg-white/5 border border-white/5 shadow-2xl shadow-amber-900/10">

              {/* Circular Loader */}
              <div className="relative w-80 h-80 flex items-center justify-center">
                {/* Outer Ring */}
                <svg className="absolute w-full h-full animate-spin-slow opacity-20" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-white" strokeDasharray="4 4" />
                </svg>
                {/* Progress Ring */}
                <svg className="absolute w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="2" strokeOpacity="0.5" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="url(#gradient)" strokeWidth="2"
                    strokeDasharray="251.2"
                    strokeDashoffset={251.2 - (251.2 * (stageNumber / 8))}
                    className="transition-all duration-1000 ease-out"
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#d97706" /> {/* amber-600 */}
                      <stop offset="100%" stopColor="#fbbf24" /> {/* amber-400 */}
                    </linearGradient>
                  </defs>
                </svg>

                {/* Inner Status */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <div className="text-6xl font-serif font-black text-white mix-blend-overlay opacity-90 transition-all duration-300">
                    {Math.round((stageNumber / 8) * 100)}%
                  </div>
                  <div className="text-xs text-amber-500/80 mt-2 uppercase tracking-[0.3em] font-bold">Researching</div>
                </div>
              </div>
            </div>

            {/* Elegant Status Text */}
            <div className="text-center space-y-6 mt-16 z-20 max-w-2xl">
              <h3 className="text-5xl font-serif text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 tracking-tight leading-tight">
                {currentStage}
              </h3>

              {/* Minimalist Log - One line only */}
              <div className="h-8 overflow-hidden">
                <p className="text-amber-500/60 text-sm font-mono tracking-widest uppercase animate-pulse">
                  {logs.length > 0 ? logs[logs.length - 1].replace('STAGE:', '').replace(/[^a-zA-Z0-9\s]/g, '') : "INITIALIZING NEURAL PATHWAYS..."}
                </p>
              </div>
            </div>
          </div>
        )}

        {status === 'complete' && (
          <div className="w-full max-w-4xl z-10 animate-in zoom-in-95 duration-500 bg-[#0a0a0a] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-white/10 bg-white/5 flex justify-between items-center backdrop-blur-sm">
              <h2 className="text-xl font-serif text-amber-500/90 tracking-widest uppercase">Research Compilation</h2>
              <button onClick={() => window.print()} className="text-xs bg-amber-600 text-white px-6 py-2 rounded-full font-bold hover:bg-amber-500 transition tracking-wide shadow-lg shadow-amber-900/20">
                DOWNLOAD PDF
              </button>
            </div>

            <div className="p-12 md:p-20 bg-[#f4f1ea] text-slate-900 min-h-[800px] shadow-inner font-serif">
              <article className="prose prose-xl prose-serif prose-slate max-w-none leading-loose">
                {/* Render with ReactMarkdown - ENLARGED FONTS AS REQUESTED */}
                <ReactMarkdown
                  components={{
                    h1: ({ node, ...props }) => <h1 className="text-6xl font-black text-slate-900 mb-12 text-center border-b-4 border-slate-900 pb-8 uppercase tracking-tight" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-4xl font-bold text-slate-800 mt-20 mb-8 border-l-8 border-amber-600 pl-6" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-3xl font-bold text-slate-700 mt-12 mb-6" {...props} />,
                    p: ({ node, ...props }) => <p className="text-xl text-slate-900 mb-8 leading-loose text-justify" {...props} />, // 'text-xl' makes it very lengthy/readable
                    ul: ({ node, ...props }) => <ul className="list-disc pl-8 space-y-4 mb-8 text-xl" {...props} />,
                    li: ({ node, ...props }) => <li className="pl-2 marker:text-amber-600" {...props} />
                  }}
                >
                  {finalPaper}
                </ReactMarkdown>
              </article>
            </div>

            <div className="p-6 border-t border-white/10 bg-[#050505] flex justify-center">
              <button onClick={() => setStatus('idle')} className="text-amber-500 hover:text-amber-400 text-sm font-mono tracking-widest uppercase hover:underline underline-offset-4">
                Initialize New Protocol
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
