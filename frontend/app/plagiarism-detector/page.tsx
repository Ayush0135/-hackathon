'use client';
import { useState } from 'react';
import Link from 'next/link';
import { UserButton } from '@clerk/nextjs';

export default function PlagiarismDetector() {
    const [textToAnalyze, setTextToAnalyze] = useState('');
    const [status, setStatus] = useState<'idle' | 'running' | 'complete' | 'error'>('idle');
    const [results, setResults] = useState<any>(null);

    const handleAnalyze = async () => {
        if (!textToAnalyze.trim()) return;
        setStatus('running');

        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_URL}/api/plagiarism/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: textToAnalyze
                })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(`Server returned ${res.status}: ${errText}`);
            }
            const data = await res.json();
            setResults(data);
            setStatus('complete');
        } catch (e: any) {
            console.error('Fetch error:', e.message || e);
            setStatus('error');
        }
    };

    return (
        <div className="min-h-[100dvh] bg-[#050505] text-slate-200 font-sans selection:bg-pink-500/30 flex flex-col relative overflow-x-hidden">
            {/* Background Gradients */}
            <div className="absolute top-0 right-0 w-[800px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] pointer-events-none transform-gpu"></div>
            <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-pink-500/10 rounded-full blur-[120px] pointer-events-none transform-gpu"></div>

            {/* Header */}
            <header className="p-6 border-b border-white/5 bg-[#050505]/60 backdrop-blur-xl sticky top-0 z-40">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 group cursor-pointer text-slate-400 hover:text-white transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6" /></svg>
                        <span className="font-mono text-sm tracking-widest uppercase">Back to Hub</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <UserButton />
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 max-w-5xl mx-auto w-full p-8 relative z-10 flex flex-col pt-12">
                <div className="mb-12">
                    <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight font-serif leading-tight mb-4 text-white flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg shadow-pink-500/20">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                        </div>
                        Plagiarism & <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">Novelty Detector</span>
                    </h2>
                    <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
                        Analyze the provided text to evaluate its novelty score, similarity to known clichés, and automatically generate a highly original, paraphrased enhanced version.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    {/* Inputs */}
                    <div className="flex flex-col h-full gap-6">
                        <div className="glass-panel p-6 rounded-2xl relative flex-1 flex flex-col min-h-0">
                            <label className="block text-xs font-mono uppercase tracking-widest text-pink-400 mb-3 ml-1">Input Text</label>
                            <textarea
                                value={textToAnalyze}
                                onChange={(e) => setTextToAnalyze(e.target.value)}
                                placeholder="Paste the text or paragraph you want to analyze here..."
                                className="flex-1 w-full bg-black/20 border border-white/5 rounded-xl p-4 text-slate-300 placeholder-slate-600 focus:outline-none focus:border-pink-500/50 focus:ring-1 focus:ring-pink-500/50 resize-none transition-all custom-scrollbar min-h-[250px] md:min-h-[300px]"
                            />
                        </div>

                        <button
                            onClick={handleAnalyze}
                            disabled={status === 'running' || !textToAnalyze}
                            className="w-full relative group disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
                            <div className="relative bg-black text-white w-full py-4 rounded-xl font-bold tracking-widest uppercase border border-white/10 hover:bg-white/5 transition-colors flex justify-center items-center gap-2">
                                {status === 'running' ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5 text-pink-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Analyzing Semantic Similarity...
                                    </>
                                ) : 'Analyze Novelty'}
                            </div>
                        </button>
                    </div>

                    {/* Results Panel */}
                    <div className="glass-panel rounded-2xl p-8 lg:p-10 flex flex-col h-full min-h-0 overflow-y-auto custom-scrollbar">
                        <h3 className="text-xl font-serif text-white mb-8 border-b border-white/10 pb-4 shrink-0">Detection Results</h3>

                        {status === 'idle' && (
                            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 opacity-60">
                                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><rect width="18" height="18" x="3" y="3" rx="2" /><path d="m9 14 2 2 4-4" /></svg>
                                <p className="font-mono text-sm tracking-widest uppercase">Awaiting Input</p>
                            </div>
                        )}

                        {status === 'running' && (
                            <div className="flex-1 flex flex-col items-center justify-center">
                                <div className="w-16 h-16 border-4 border-pink-500/20 border-t-pink-500 rounded-full animate-spin mb-4"></div>
                                <p className="text-pink-400 font-mono text-sm animate-pulse tracking-widest uppercase">Calculating Vectors</p>
                            </div>
                        )}

                        {status === 'complete' && results && (
                            <div className="flex-1 flex flex-col justify-center space-y-8 animate-in fade-in duration-500">
                                {/* Novelty Score Dial */}
                                <div className="flex flex-col items-center justify-center">
                                    <div className="relative w-40 h-40 flex flex-col items-center justify-center bg-black/30 rounded-full border border-white/5 shadow-inner mb-4">
                                        <svg className="absolute w-full h-full -rotate-90 scale-110" viewBox="0 0 100 100">
                                            <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
                                            <circle
                                                cx="50" cy="50" r="45" fill="none"
                                                stroke={results.novelty_score >= 7 ? "#22c55e" : results.novelty_score >= 4 ? "#eab308" : "#ef4444"}
                                                strokeWidth="4"
                                                strokeDasharray="282.7"
                                                strokeDashoffset={282.7 - (282.7 * (results.novelty_score / 10))}
                                                strokeLinecap="round"
                                                style={{ filter: "drop-shadow(0 0 8px rgba(0,0,0,0.5))" }}
                                            />
                                        </svg>
                                        <span className="text-4xl font-black font-sans text-white tracking-tighter">{results.novelty_score}</span>
                                        <span className="text-[10px] text-slate-400 font-mono tracking-widest uppercase mt-1">/ 10 Score</span>
                                    </div>
                                    <div className="text-center">
                                        <h4 className="font-serif text-2xl text-white mb-1">Novelty Rating</h4>
                                        <p className="text-sm text-slate-400">
                                            {results.novelty_score >= 7 ? 'Highly Original Idea' : results.novelty_score >= 4 ? 'Moderate Paraphrasing' : 'High Plagiarism Risk'}
                                        </p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/10">
                                    <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                                        <div className="text-xs text-slate-500 font-mono uppercase tracking-widest mb-1">Similarity Max</div>
                                        <div className="text-2xl font-bold font-sans text-white">{(results.similarity_score * 100).toFixed(1)}%</div>
                                    </div>
                                    <div className={`rounded-xl p-4 border ${results.paraphrase_detected ? 'bg-red-500/10 border-red-500/20' : 'bg-green-500/10 border-green-500/20'}`}>
                                        <div className="text-xs text-slate-500 font-mono uppercase tracking-widest mb-1">Paraphrased?</div>
                                        <div className={`text-xl font-bold font-sans ${results.paraphrase_detected ? 'text-red-400' : 'text-green-400'}`}>
                                            {results.paraphrase_detected ? 'DETECTED' : 'CLEAN'}
                                        </div>
                                    </div>
                                </div>

                                {/* Details Footer */}
                                <div className="text-xs text-slate-500 font-mono flex justify-between bg-black/20 p-3 rounded-lg">
                                    <span>Engine: {results.engine}</span>
                                    <span>Sentences: {results.total_sentences}</span>
                                </div>

                                {/* Enhanced Text Render */}
                                <div className="mt-8 pt-6 border-t border-white/10">
                                    <h4 className="font-serif text-lg text-white mb-3">Enhanced Paraphrased Result</h4>
                                    <div className="bg-black/20 border border-white/5 rounded-xl p-5 text-slate-300 leading-relaxed max-h-[250px] overflow-y-auto custom-scrollbar font-serif">
                                        {results.paraphrased_text}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

            </main>
        </div>
    );
}
