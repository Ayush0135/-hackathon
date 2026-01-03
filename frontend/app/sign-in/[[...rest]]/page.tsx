'use client';
import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
    return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4 relative overflow-hidden">

            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-500/5 rounded-full blur-[120px] pointer-events-none"></div>

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <img src="/logo.png" alt="Logo" className="w-16 h-16 rounded-xl mx-auto mb-4 shadow-lg shadow-amber-500/20" />
                    <h1 className="text-3xl font-serif font-bold text-white mb-2">SureFact</h1>
                    <p className="text-slate-400 text-sm">Autonomous Research Interface</p>
                </div>

                <div className="backdrop-blur-md border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex justify-center bg-white/5 p-6">
                    <SignIn
                        path="/sign-in"
                        routing="path"
                        forceRedirectUrl="/"
                        signUpUrl="/sign-up"
                        appearance={{
                            elements: {
                                rootBox: "w-full",
                                card: "bg-transparent shadow-none w-full",
                                headerTitle: "text-white",
                                headerSubtitle: "text-slate-400",
                                socialButtonsBlockButton: "text-white border-slate-700 hover:bg-slate-800",
                                formButtonPrimary: "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500",
                                formFieldLabel: "text-slate-300",
                                formFieldInput: "bg-slate-900/50 border-slate-700 text-white",
                                footerActionLink: "text-amber-500 hover:text-amber-400"
                            }
                        }}
                    />
                </div>
            </div>
        </div>
    );
}
