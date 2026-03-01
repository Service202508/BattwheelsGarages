import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Request failed');
      }
      setSubmitted(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="forgot-password-page" className="min-h-screen bg-bw-black flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-bw-panel border-bw-white/[0.08]">
        <CardHeader className="text-center pb-2">
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-bw-volt/10 flex items-center justify-center">
            <Mail className="w-6 h-6 text-bw-volt" />
          </div>
          <CardTitle className="text-xl font-bold text-bw-white">
            {submitted ? 'Check Your Email' : 'Reset Password'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {submitted ? (
            <div className="text-center space-y-4">
              <CheckCircle className="w-12 h-12 mx-auto text-emerald-400" />
              <p data-testid="success-message" className="text-sm text-bw-white/70 leading-relaxed">
                If an account exists for <strong className="text-bw-white">{email}</strong>, you'll receive a password reset link shortly.
              </p>
              <Link to="/login">
                <Button data-testid="back-to-login-btn" className="w-full bg-bw-volt text-black hover:bg-bw-volt-hover font-semibold mt-3">
                  <ArrowLeft className="w-4 h-4 mr-2" /> Back to Login
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <p className="text-sm text-bw-white/50">Enter your email and we'll send a password reset link.</p>
              {error && (
                <div data-testid="forgot-password-error" className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}
              <Input
                data-testid="forgot-email-input"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="bg-bw-black border-bw-white/[0.12] text-bw-white placeholder:text-bw-white/30"
              />
              <Button
                data-testid="send-reset-btn"
                type="submit"
                disabled={loading || !email}
                className="w-full bg-bw-volt text-black hover:bg-bw-volt-hover font-semibold disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </Button>
              <Link to="/login" className="block text-center text-sm text-bw-white/40 hover:text-bw-volt transition">
                <ArrowLeft className="w-3 h-3 inline mr-1" /> Back to Login
              </Link>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
