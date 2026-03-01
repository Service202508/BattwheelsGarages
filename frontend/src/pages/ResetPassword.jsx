import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Lock, ArrowLeft, Check } from "lucide-react";
import { API, AUTH_API } from "@/App";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleReset = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${AUTH_API}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      if (res.ok) {
        setDone(true);
        toast.success("Password reset successfully!");
      } else {
        let errorMsg;
        try {
          const data = await res.clone().json();
          errorMsg = data.detail;
        } catch {
          // Body already consumed by Sentry instrumentation — use status-based fallback
          if (res.status === 400) errorMsg = "Invalid or expired reset link";
          else if (res.status === 422) errorMsg = "Invalid input";
          else errorMsg = `Request failed (${res.status})`;
        }
        toast.error(errorMsg || "Failed to reset password");
      }
    } catch {
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bw-black p-4">
        <Card className="w-full max-w-md border-white/10 bg-card/80">
          <CardContent className="pt-6 text-center space-y-4">
            <p className="text-destructive">Invalid reset link — no token provided.</p>
            <Button variant="outline" onClick={() => navigate("/login")} data-testid="back-to-login-btn">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (done) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bw-black p-4">
        <Card className="w-full max-w-md border-white/10 bg-card/80">
          <CardContent className="pt-6 text-center space-y-4">
            <div className="h-16 w-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
              <Check className="h-8 w-8 text-green-500" />
            </div>
            <h2 className="text-xl font-bold">Password Reset Complete</h2>
            <p className="text-muted-foreground">Your password has been updated. You can now sign in.</p>
            <Button className="glow-primary w-full" onClick={() => navigate("/login")} data-testid="go-to-login-btn">
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bw-black p-4">
      <Card className="w-full max-w-md border-white/10 bg-card/80">
        <CardHeader className="text-center">
          <div className="h-12 w-12 mx-auto bg-primary/20 rounded-full flex items-center justify-center mb-2">
            <Lock className="h-6 w-6 text-primary" />
          </div>
          <CardTitle>Set New Password</CardTitle>
          <CardDescription>Enter your new password below.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleReset} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min 6 characters"
                required
                minLength={6}
                data-testid="reset-new-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm Password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                required
                data-testid="reset-confirm-password-input"
              />
            </div>
            <Button type="submit" className="glow-primary w-full" disabled={loading} data-testid="reset-password-submit-btn">
              {loading ? "Resetting..." : "Reset Password"}
            </Button>
            <Button type="button" variant="ghost" className="w-full" onClick={() => navigate("/login")} data-testid="reset-back-to-login">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to Login
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
