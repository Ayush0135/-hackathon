import Link from 'next/link';
import { UserButton, SignedIn, SignedOut } from '@clerk/nextjs';

const NetworkIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22a4 4 0 0 0 4-4c0-1.6-1.2-3.2-2.3-4.1a8 8 0 0 1-3.4-6.9v-1a4 4 0 1 0-4 0v1a8 8 0 0 0 3.4 6.9c1.1.9 2.3 2.5 2.3 4.1a4 4 0 0 1-4 4" /></svg>
);

const ShieldIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
);

export default function Dashboard() {
  const agents = [
    {
      id: "multi-layer-agent",
      title: "Multi-Layer Research Agent",
      description: "Autonomous AI agents to research, analyze, and synthesize deep academic literature.",
      icon: <NetworkIcon />,
      tags: ["8 Stages", "Multi-Agent", "Live Web"],
      color: "from-cyan-500 to-blue-600",
      href: "/multi-layer-agent",
      status: "Active"
    },
    {
      id: "plagiarism-detector",
      title: "AI Research Plagiarism & Novelty Detector",
      description: "Detects similarity with existing research, repeated AI phrasing, and novelty score of generated content. Integrates after Writer Agent.",
      icon: <ShieldIcon />,
      tags: ["Semantic Similarity", "Novelty Scoring", "Paraphrase Detection"],
      color: "from-purple-500 to-pink-600",
      href: "/plagiarism-detector",
      status: "Active"
    }
  ];

  return (
    <div className="min-h-screen bg-[#050505] text-slate-200 font-sans selection:bg-amber-500/30 flex flex-col relative overflow-x-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-600/10 rounded-full blur-[150px] pointer-events-none animate-pulse-slow"></div>
      <div className="absolute bottom-0 right-0 w-[800px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Header */}
      <header className="p-6 border-b border-white/5 bg-[#050505]/60 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4 group cursor-pointer">
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
              {/* Note: Using existing logo if it exists, otherwise fallback to simple styling */}
              <img src="/logo.png" alt="Logo" className="relative w-12 h-12 rounded-xl border border-white/10" />
            </div>
            <h1 className="text-2xl font-serif font-bold tracking-wider text-white">
              Agent<span className="text-cyan-400">OS</span> Hub
            </h1>
          </div>
          <div className="flex items-center gap-6">
            <SignedIn>
              <UserButton />
            </SignedIn>
            <SignedOut>
              <Link href="/sign-in" className="text-sm bg-white/10 hover:bg-white/20 text-white px-6 py-2 rounded-lg font-bold transition-all border border-white/10">
                Sign In
              </Link>
            </SignedOut>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-8 relative z-10 flex flex-col pt-16">
        <div className="mb-16 text-center z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000 ease-out">
          <h2 className="text-5xl md:text-6xl font-extrabold tracking-tight font-serif leading-tight mb-6">
            Command Center for <br /> <span className="text-gradient">Agentic Workflows</span>
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Select an autonomous module to deploy. Each module is specialized for different tasks ranging from deep academic research to intelligent automation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8 z-10 animate-in fade-in duration-1000 delay-300 fill-mode-both">
          {agents.map((agent) => (
            <Link href={agent.href} key={agent.id} className="group relative block">
              <div className={`absolute -inset-0.5 bg-gradient-to-r ${agent.color} rounded-2xl blur opacity-0 group-hover:opacity-30 transition duration-500`}></div>
              <div className="relative h-full glass-panel rounded-2xl p-8 flex flex-col transition-all duration-300 hover:border-white/20 hover:bg-white/[0.04]">
                <div className="flex justify-between items-start mb-6">
                  <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-3xl bg-gradient-to-br ${agent.color} shadow-lg shadow-black/50`}>
                    {agent.icon}
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-xs font-mono uppercase tracking-widest text-slate-300">
                    <div className={`w-2 h-2 rounded-full ${agent.status === 'Active' ? 'bg-green-400 animate-pulse' : agent.status === 'Configured' ? 'bg-amber-400' : 'bg-slate-500'}`}></div>
                    {agent.status}
                  </div>
                </div>

                <h3 className="text-2xl font-bold text-white mb-3 font-serif tracking-wide group-hover:text-cyan-300 transition-colors">{agent.title}</h3>
                <p className="text-slate-400 leading-relaxed mb-8 flex-1">
                  {agent.description}
                </p>

                <div className="flex flex-wrap gap-2 mt-auto">
                  {agent.tags.map(tag => (
                    <span key={tag} className="px-3 py-1 rounded-md bg-white/5 border border-white/5 text-xs text-slate-300 font-mono">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
