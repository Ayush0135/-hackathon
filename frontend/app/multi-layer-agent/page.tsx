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
  const [isListening, setIsListening] = useState(false);
  // State for history
  const [history, setHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const mediaRecorderRef = useRef<any>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Robust Speech-to-Text via Backend AI Whisper
  const toggleListening = async () => {
    if (isListening) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        setTopic("Transcribing your audio using AI...");
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        try {
          const res = await fetch(`${API_URL}/api/transcribe`, {
            method: 'POST',
            body: formData,
          });
          const data = await res.json();
          if (data.transcript) {
            setTopic(data.transcript);
          } else {
            console.warn("Transcription failed", data.error);
            setTopic("");
            alert("Transcription failed: " + (data.error || "Unknown error"));
          }
        } catch (e: any) {
          console.warn("Could not reach transcription server.", e);
          setTopic("");
          alert("Could not reach transcription server.");
        } finally {
          stream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err: any) {
      console.warn("Microphone access blocked", err);
      alert("Microphone access denied or not available. Please check browser permissions.");
    }
  };

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
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            try {
              await fetch(`${API_URL}/register`, {
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
            const res = await fetch(`${API_URL}/login`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                email,
                password: "temp-secure-pass"
              }),
            });

            if (res.ok) {
              const data = await res.json();
              if (data.access_token) {
                localStorage.setItem('token', data.access_token);
              }
            }
          } catch (e) {
            console.warn("Backend sync failed (you may need to start the backend)", e);
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
      <div className="min-h-screen bg-[#050505] flex items-center justify-center text-cyan-500 font-mono relative overflow-hidden">
        <div className="absolute inset-0 bg-premium-gradient opacity-30 animate-pulse-slow pointer-events-none"></div>
        <div className="flex flex-col items-center gap-6 glass-panel p-12 rounded-2xl z-10">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent border-b-transparent rounded-full animate-spin"></div>
          <p className="tracking-[0.2em] uppercase text-sm font-bold text-cyan-400">Synchronizing Neural Uplink...</p>
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

      const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
      socketRef.current = new WebSocket(WS_URL);

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
          setLogs(prev => [...prev.slice(-200), `[STAGE PROGRESSION] Initializing ${stageMap[stageCode]}...`]);
        } else if (msg.startsWith('ERROR:') || msg.toLowerCase().includes('traceback')) {
          setLogs(prev => [...prev.slice(-200), `⚠️ SYSTEM ERROR: ${msg}`]);
        } else if (msg.trim().length > 3) {
          // Standard pipeline console output (e.g. document fetching, filtering output)
          setLogs(prev => [...prev.slice(-200), msg.trim()]);
        }
      };

      socketRef.current.onerror = () => {
        console.warn("WebSocket warning: Connection refused. Will auto-reconnect in 3s if backend is still booting.");
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
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/history`);
      const data = await res.json();
      setHistory(data);
      setShowHistory(true);
    } catch (e) { console.warn("Could not fetch history (backend may be down).", e); }
  }

  const loadHistoryItem = async (id: number) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/history/${id}`);
      if (res.ok) {
        const data = await res.json();
        setTopic(data.topic);
        setFinalPaper(data.content);
        setStatus('complete');
        setShowHistory(false);
      }
    } catch (e) { console.warn("Could not load history item.", e); }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-slate-200 font-sans selection:bg-amber-500/30 flex flex-col relative overflow-x-hidden">

      {/* History Sidebar - Slide Over */}
      <div className={`fixed inset-y-0 right-0 w-96 glass-panel border-l border-white/10 transform transition-transform duration-500 ease-out z-50 p-6 shadow-[0_0_50px_rgba(0,0,0,0.5)] ${showHistory ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-serif text-cyan-400 tracking-wide">Research Archives</h2>
          <button onClick={() => setShowHistory(false)} className="text-slate-400 hover:text-cyan-400 transition-colors p-2 rounded-full hover:bg-white/5">✕</button>
        </div>
        <div className="space-y-4 overflow-y-auto h-[80vh] custom-scrollbar">
          {Array.isArray(history) && history.length > 0 ? (
            history.map((item: any) => (
              <div key={item.id} onClick={() => loadHistoryItem(item.id)} className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-cyan-500/50 hover:bg-cyan-500/5 hover:shadow-[0_0_15px_rgba(56,189,248,0.15)] cursor-pointer transition-all duration-300">
                <div className="text-sm font-semibold text-white mb-2 leading-relaxed">{item.topic}</div>
                <div className="text-xs text-cyan-500/70 font-mono tracking-widest uppercase">{new Date(item.date).toLocaleDateString()}</div>
              </div>
            ))
          ) : (
            <div className="p-4 text-slate-500 text-sm">No archives found (or sync error).</div>
          )}
        </div>
      </div>

      {/* Header */}
      <header className="p-6 border-b border-white/5 bg-[#050505]/60 backdrop-blur-xl supports-[backdrop-filter]:bg-[#050505]/40 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4 group cursor-pointer">
            {/* Logo */}
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
              <img src="/logo.png" alt="SureFact Logo" className="relative w-12 h-12 rounded-xl border border-white/10" />
            </div>
            <h1 className="text-2xl font-serif font-bold tracking-wider text-white">
              Sure<span className="text-cyan-400">Fact</span>
            </h1>
          </div>
          <div className="flex items-center gap-8">
            <button onClick={fetchHistory} className="text-xs font-mono text-slate-400 hover:text-cyan-400 uppercase tracking-[0.2em] transition-colors relative after:absolute after:bottom-[-4px] after:left-0 after:w-full after:h-[1px] after:bg-cyan-400 after:scale-x-0 hover:after:scale-x-100 after:transition-transform after:duration-300 after:origin-right hover:after:origin-left">
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
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-600/15 rounded-full blur-[150px] pointer-events-none animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-0 w-[800px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute top-1/4 left-0 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[150px] pointer-events-none"></div>

        {status === 'idle' && (
          <div className="z-10 w-full max-w-3xl text-center space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-1000 ease-out">
            <h2 className="text-5xl md:text-7xl font-extrabold tracking-tight font-serif leading-tight">
              What do you want to <br /> <span className="text-gradient">discover</span> today?
            </h2>
            <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Deploy autonomous AI agents to research, analyze, and synthesize deep academic literature on any complex topic.
            </p>

            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg blur opacity-25 group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative flex items-center shadow-2xl rounded-2xl p-1 bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:border-white/20">
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && startResearch()}
                  placeholder="e.g. 'Impact of Microplastics on Human Biology'"
                  className="block w-full text-lg p-5 rounded-xl bg-transparent text-white placeholder-slate-500 focus:outline-none focus:ring-0 transition"
                />

                {/* Microphone Button */}
                <button
                  onClick={toggleListening}
                  className={`p-3 mx-2 rounded-full transition-all duration-300 flex items-center justify-center ${isListening
                    ? 'bg-red-500/20 text-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse'
                    : 'bg-white/5 text-slate-400 hover:text-cyan-400 hover:bg-white/10'
                    }`}
                  title={isListening ? "Listening... click to stop" : "Use Microphone"}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" x2="12" y1="19" y2="22" />
                  </svg>
                </button>

                <button
                  onClick={startResearch}
                  className="bg-white text-black hover:bg-slate-200 px-8 py-5 h-full rounded-xl font-bold tracking-wider transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_30px_rgba(255,255,255,0.3)] hover:scale-[1.02] active:scale-95 ml-1"
                >
                  START
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 justify-center text-xs font-mono tracking-widest uppercase text-slate-400 pt-8">
              <span className="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm shadow-inner flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div> 8 Stages
              </span>
              <span className="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm shadow-inner flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div> Multi-Agent
              </span>
              <span className="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm shadow-inner flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500"></div> Live Web Access
              </span>
            </div>
          </div>
        )}

        {status === 'running' && (
          <div className="w-full flex flex-col items-center justify-center z-10 animate-in fade-in duration-1000 min-h-[60vh] relative">

            {/* Ambient Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-500/10 rounded-full blur-[150px] pointer-events-none animate-pulse-slow"></div>

            {/* Central Visualization */}
            <div className="relative flex flex-col items-center justify-center p-16 glass-panel rounded-full shadow-[0_0_100px_rgba(56,189,248,0.15)] animate-float">

              {/* Circular Loader */}
              <div className="relative w-80 h-80 flex items-center justify-center">
                {/* Outer Ring */}
                <svg className="absolute w-full h-full animate-spin-slow opacity-30" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-cyan-400" strokeDasharray="2 6" />
                </svg>
                {/* Middle Ring */}
                <svg className="absolute w-[85%] h-[85%] animate-[spin_12s_linear_infinite_reverse] opacity-20" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="#60a5fa" strokeWidth="1" strokeDasharray="10 10" />
                </svg>

                {/* Progress Ring */}
                <svg className="absolute w-full h-full -rotate-90 scale-x-110 scale-y-110" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1.5" />
                  <circle cx="50" cy="50" r="42" fill="none" stroke="url(#gradient)" strokeWidth="2.5"
                    strokeDasharray="263.89"
                    strokeDashoffset={263.89 - (263.89 * (stageNumber / 8))}
                    className="transition-all duration-1000 ease-in-out"
                    strokeLinecap="round"
                    style={{ filter: "drop-shadow(0 0 8px rgba(56,189,248,0.8))" }}
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#38bdf8" /> {/* cyan-400 */}
                      <stop offset="50%" stopColor="#818cf8" /> {/* indigo-400 */}
                      <stop offset="100%" stopColor="#3b82f6" /> {/* blue-500 */}
                    </linearGradient>
                  </defs>
                </svg>

                {/* Inner Status */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <div className="text-7xl font-sans font-black text-white mix-blend-overlay tracking-tighter shadow-sm transition-all duration-500">
                    {Math.round((stageNumber / 8) * 100)}<span className="text-2xl opacity-50">%</span>
                  </div>
                  <div className="text-[10px] text-cyan-400 mt-4 uppercase tracking-[0.4em] font-semibold">Processing Data</div>
                </div>
              </div>
            </div>

            {/* Elegant Status Text */}
            <div className="text-center space-y-8 mt-20 z-20 max-w-2xl">
              <h3 className="text-4xl md:text-5xl font-serif text-white tracking-wide leading-tight drop-shadow-lg">
                {currentStage}
              </h3>

              {/* Live Pipeline Telemetry Terminal */}
              <div className="w-full mx-auto mt-12 bg-black/40 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden shadow-[0_0_40px_rgba(56,189,248,0.1)] transition-all">
                {/* Terminal Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-white/5">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></div>
                    <span className="text-[10px] font-mono tracking-widest text-cyan-400 uppercase">Live Pipeline Telemetry</span>
                  </div>
                </div>

                {/* Scrollable Logs */}
                <div className="p-5 h-64 overflow-y-auto font-mono text-[11px] leading-6 flex flex-col text-slate-300 custom-scrollbar text-left font-medium">
                  {logs.length === 0 ? (
                    <div className="text-slate-500 italic animate-pulse">Establishing neural uplink...</div>
                  ) : (
                    logs.map((log, i) => (
                      <div key={i} className={`flex items-start tracking-wide break-words transition-all ${log.includes('ERROR') ? 'text-red-400' :
                        log.includes('STAGE') ? 'text-cyan-400 font-bold my-2' :
                          log.includes('Knowledge Graph') ? 'text-purple-400' : 'opacity-80'
                        }`}>
                        <span className="text-slate-600 mr-3 shrink-0 font-bold">{'>'}</span>
                        <span>{log.replace(/[^a-zA-Z0-9\s:[\]\-.,!?'"]/g, '')}</span>
                      </div>
                    ))
                  )}
                  {/* Invisible element to auto-scroll into view */}
                  <div ref={logsEndRef} />
                </div>
              </div>
            </div>
          </div>
        )}

        {status === 'complete' && (
          <div className="w-full max-w-5xl z-10 animate-in zoom-in-95 duration-700 glass-panel rounded-2xl overflow-hidden mt-8 mb-20 shadow-[0_20px_60px_rgba(0,0,0,0.5)] border border-white/10">
            <div className="p-8 border-b border-white/10 bg-white/[0.02] flex justify-between items-center">
              <h2 className="text-xl font-sans font-bold text-white tracking-[0.2em] uppercase flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                Research Compilation
              </h2>
              <div className="flex gap-4">
                <button onClick={() => setStatus('idle')} className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2 font-mono uppercase tracking-widest border border-transparent hover:border-white/10 rounded-lg">
                  New Search
                </button>
                <button onClick={() => window.print()} className="text-sm bg-white text-black px-6 py-2 rounded-lg font-bold hover:bg-slate-200 transition-all tracking-wide shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:shadow-[0_0_30px_rgba(255,255,255,0.4)]">
                  DOWNLOAD PDF
                </button>
              </div>
            </div>

            <div className="p-12 md:p-24 bg-[#FAFAF9] text-slate-800 min-h-[800px] shadow-inner font-serif relative">
              <div className="absolute top-0 inset-x-0 h-4 bg-gradient-to-b from-black/5 to-transparent"></div>
              <article className="prose prose-xl prose-slate max-w-[800px] mx-auto leading-loose selection:bg-cyan-200 selection:text-cyan-900">
                {/* Render with ReactMarkdown */}
                <ReactMarkdown
                  components={{
                    h1: ({ node, ...props }) => <h1 className="text-5xl md:text-6xl font-black text-slate-900 mb-16 text-center border-b-[6px] border-slate-900 pb-10 uppercase tracking-tight font-sans" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mt-24 mb-10 border-l-[6px] border-cyan-500 pl-8 font-sans" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-2xl font-bold text-slate-800 mt-16 mb-6 font-sans tracking-wide" {...props} />,
                    p: ({ node, ...props }) => <p className="text-xl text-slate-700 mb-8 leading-loose text-justify font-serif" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-8 space-y-4 mb-10 text-xl text-slate-700" {...props} />,
                    li: ({ node, ...props }) => <li className="pl-4 marker:text-cyan-500 font-serif leading-relaxed" {...props} />,
                    strong: ({ node, ...props }) => <strong className="font-bold text-slate-900 bg-cyan-500/10 px-1 rounded" {...props} />
                  }}
                >
                  {finalPaper}
                </ReactMarkdown>
              </article>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
