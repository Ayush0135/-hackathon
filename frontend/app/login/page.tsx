'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth, googleProvider } from '../../lib/firebase';
import { signInWithPopup } from 'firebase/auth';

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const router = useRouter();

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        await performBackendAuth(email, password, isLogin, otp);
    };

    const handleSendOtp = async () => {
        if (!email || !email.includes('@')) {
            setError("Please enter a valid email first.");
            return;
        }
        setError("");
        setIsLoading(true);
        try {
            const res = await fetch('http://localhost:8000/send-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            const data = await res.json();
            if (data.error) {
                setError(data.error);
            } else {
                setOtpSent(true);
                setError("Code sent! Check server console/logs.");
            }
        } catch (e) {
            setError("Failed to reach server.");
        } finally {
            setIsLoading(false);
        }
    };

    const performBackendAuth = async (email: string, password?: string, isLoginMode: boolean = true, otpValue?: string) => {
        setError('');
        setIsLoading(true);
        const endpoint = isLoginMode ? '/login' : '/register';
        // Use a dummy password for Google users
        const payload: any = { email, password: password || "google-auth-secure-placeholder" };

        // IF registering...
        if (!isLoginMode) {
            // If Google User (no password passed), use BYPASS token
            if (!password) {
                payload.otp = "GOOGLE_BYPASS";
            }
            // If Normal User
            else {
                if (!otpSent) {
                    setError("Please verify email first.");
                    setIsLoading(false);
                    return;
                }
                if (otpValue) payload.otp = otpValue;
            }
        }

        try {
            // IF Google Login (Implicit)
            if (!password) {
                // 1. Try to Register silently (it might fail if already exists, which is fine)
                try {
                    await fetch('http://localhost:8000/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ...payload, otp: "GOOGLE_BYPASS" }),
                    });
                } catch (e) { }

                // 2. Then Login
                const res = await fetch('http://localhost:8000/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (data.access_token) {
                    localStorage.setItem('token', data.access_token);
                    router.push('/');
                } else {
                    setError(data.error || "Authentication failed");
                }
                return;
            }

            // Normal Flow
            const res = await fetch(`http://localhost:8000${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (data.error) {
                setError(data.error);
                setIsLoading(false);
                return;
            }

            if (isLoginMode && data.access_token) {
                localStorage.setItem('token', data.access_token);
                router.push('/');
            } else if (!isLoginMode) {
                setIsLogin(true);
                setOtpSent(false);
                setOtp("");
                setError('Account created! Please login.');
            }

        } catch (err) {
            setError('Connection failed. Is server running?');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        try {
            const result = await signInWithPopup(auth, googleProvider);
            const user = result.user;
            if (user.email) {
                // Auto-auth with backend using Google email
                await performBackendAuth(user.email, undefined, true);
            }
        } catch (error: any) {
            console.error(error);

            // CHECK FOR MISSING CONFIG -> FALLBACK TO MOCK MODE
            if (error.code === 'auth/configuration-not-found' || error.code === 'auth/api-key-not-valid' || error.code === 'auth/invalid-api-key') {
                const useMock = confirm("Firebase keys are missing. Would you like to use a MOCK Google Login to test the flow?");
                if (useMock) {
                    // Simulate Google User
                    const mockEmail = "mock.google.user@gmail.com";
                    await performBackendAuth(mockEmail, undefined, true);
                    // No alert needed, router.push happens in performBackendAuth
                } else {
                    alert("Please update frontend/lib/firebase.ts with your actual keys to use real Google Login.");
                }
            } else {
                setError(error.message);
            }
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4 relative overflow-hidden text-slate-200 font-sans">

            {/* Background Gradients */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-500/5 rounded-full blur-[120px] pointer-events-none"></div>

            <div className="w-full max-w-md bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl relative z-10">
                <div className="text-center mb-8">
                    <img src="/logo.png" alt="Logo" className="w-16 h-16 rounded-xl mx-auto mb-4 shadow-lg shadow-amber-500/20" />
                    <h1 className="text-3xl font-serif font-bold text-white mb-2">SureFact</h1>
                    <p className="text-slate-400 text-sm">Autonomous Research Interface</p>
                </div>

                <form onSubmit={handleAuth} className="space-y-6">
                    <div>
                        <label className="block text-xs font-mono text-slate-400 mb-2 uppercase tracking-widest">Email Access</label>
                        <input
                            type="email"
                            required
                            disabled={otpSent}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-white focus:border-amber-500 focus:outline-none transition disabled:opacity-50"
                            placeholder="researcher@institute.org"
                        />
                    </div>

                    {!otpSent && (
                        <div>
                            <label className="block text-xs font-mono text-slate-400 mb-2 uppercase tracking-widest">Secure Key</label>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-white focus:border-amber-500 focus:outline-none transition"
                                placeholder="••••••••"
                            />
                        </div>
                    )}

                    {/* OTP SECTION for Signup */}
                    {!isLogin && (
                        <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                            {!otpSent ? (
                                <button type="button" onClick={handleSendOtp} disabled={isLoading} className="w-full bg-slate-700 hover:bg-slate-600 text-white py-2 rounded border border-slate-500/30 text-sm font-mono uppercase tracking-wide">
                                    {isLoading ? "Sending..." : "Send Verification Code"}
                                </button>
                            ) : (
                                <div>
                                    <label className="block text-xs font-mono text-amber-500 mb-2 uppercase tracking-widest animate-pulse">Enter Verification Code</label>
                                    <input
                                        type="text"
                                        required
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value)}
                                        className="w-full bg-amber-500/10 border border-amber-500/50 rounded-lg p-3 text-white text-center tracking-[0.5em] font-bold focus:outline-none transition"
                                        placeholder="000000"
                                        maxLength={6}
                                    />
                                    <p className="text-xs text-center mt-2 text-slate-500">Code sent to server console.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {error && <div className="text-red-400 text-sm text-center bg-red-500/10 p-2 rounded border border-red-500/20">{error}</div>}

                    <button type="submit" disabled={isLoading || (!isLogin && !otpSent)} className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-amber-900/40 transition-all transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed">
                        {isLogin ? 'AUTHENTICATE' : 'CREATE ACCOUNT'}
                    </button>
                </form>

                <div className="my-6 flex items-center gap-4">
                    <div className="h-px bg-white/10 flex-1"></div>
                    <span className="text-xs text-slate-500 uppercase">Or Continue With</span>
                    <div className="h-px bg-white/10 flex-1"></div>
                </div>

                <button onClick={handleGoogleLogin} className="w-full bg-white text-slate-900 font-bold py-3 rounded-lg hover:bg-slate-100 transition flex items-center justify-center gap-3 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-blue-50/50 opacity-0 group-hover:opacity-100 transition"></div>
                    <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24"><path fill="currentColor" d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z" /></svg>
                    <span className="relative z-10">Google Access (Firebase)</span>
                </button>

                <div className="text-center mt-4 p-2 bg-blue-500/10 border border-blue-500/20 rounded text-[10px] text-blue-300">
                    Note: Configure keys in <code>frontend/lib/firebase.ts</code> to enable real Google Login.
                </div>

                <p className="text-center mt-6 text-sm text-slate-500">
                    {isLogin ? "New to the network?" : "Already have credentials?"}
                    <button onClick={() => { setIsLogin(!isLogin); setError(""); setOtpSent(false); }} className="text-amber-500 hover:text-amber-400 ml-2 font-bold hover:underline">
                        {isLogin ? "Sign Up" : "Login"}
                    </button>
                </p>
            </div>
        </div>
    );
}
