import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Zap, CheckCircle, XCircle, Loader2, Mail } from "lucide-react";

const API = window.location.origin;

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [status, setStatus] = useState("verifying"); // verifying | success | error | resend
  const [message, setMessage] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [resendSent, setResendSent] = useState(false);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token found. Please check your email link.");
      return;
    }
    verifyToken();
  }, [token]);

  const verifyToken = async () => {
    try {
      const res = await fetch(`${API}/api/auth/verify-email?token=${token}`);
      const data = await res.json();
      if (res.ok && data.success) {
        setStatus("success");
        setMessage(data.message);
        setTimeout(() => navigate("/login"), 4000);
      } else {
        setStatus("error");
        setMessage(data.detail || data.message || "Verification failed.");
      }
    } catch {
      setStatus("error");
      setMessage("Something went wrong. Please try again.");
    }
  };

  const handleResend = async () => {
    if (!resendEmail) return;
    try {
      await fetch(`${API}/api/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: resendEmail }),
      });
      setResendSent(true);
    } catch { /* silent */ }
  };

  return (
    <div className="min-h-screen bg-bw-black flex items-center justify-center px-4" data-testid="verify-email-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-bw-volt rounded-lg flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-bw-black" />
          </div>
          <h1 className="text-2xl font-bold text-white">Battwheels OS</h1>
        </div>

        <div className="bg-bw-panel border border-white/[0.07] rounded-lg p-8 text-center">
          {status === "verifying" && (
            <div data-testid="verify-loading">
              <Loader2 className="w-12 h-12 text-bw-volt mx-auto mb-4 animate-spin" />
              <h2 className="text-lg font-semibold text-white mb-2">Verifying your email...</h2>
              <p className="text-white/50 text-sm">Please wait a moment.</p>
            </div>
          )}

          {status === "success" && (
            <div data-testid="verify-success">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-white mb-2">Email Verified!</h2>
              <p className="text-white/50 text-sm mb-4">{message}</p>
              <p className="text-white/30 text-xs">Redirecting to login in 4 seconds...</p>
              <button
                onClick={() => navigate("/login")}
                className="mt-4 bg-bw-volt text-bw-black px-6 py-2.5 rounded font-semibold text-sm hover:bg-bw-volt/90 transition"
                data-testid="go-to-login-btn"
              >
                Go to Login
              </button>
            </div>
          )}

          {status === "error" && (
            <div data-testid="verify-error">
              <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-white mb-2">Verification Failed</h2>
              <p className="text-white/50 text-sm mb-6">{message}</p>
              <div className="border-t border-white/[0.07] pt-6">
                <p className="text-white/40 text-xs mb-3 uppercase tracking-wider font-mono">Resend verification email</p>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="your@email.com"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    className="flex-1 px-3 py-2.5 bg-bw-black border border-white/10 rounded text-white text-sm placeholder-white/30 focus:ring-2 focus:ring-bw-volt/50 focus:border-transparent"
                    data-testid="resend-email-input"
                  />
                  <button
                    onClick={handleResend}
                    disabled={resendSent || !resendEmail}
                    className="bg-bw-volt text-bw-black px-4 py-2.5 rounded font-semibold text-sm hover:bg-bw-volt/90 transition disabled:opacity-50 flex items-center gap-1.5"
                    data-testid="resend-btn"
                  >
                    <Mail className="w-4 h-4" />
                    {resendSent ? "Sent!" : "Resend"}
                  </button>
                </div>
                {resendSent && (
                  <p className="text-green-400 text-xs mt-2">If this email is registered, a verification link has been sent.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
