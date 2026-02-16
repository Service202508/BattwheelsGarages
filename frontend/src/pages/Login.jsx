import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Zap, Mail, Lock, User } from "lucide-react";
import { API } from "@/App";

export default function Login({ onLogin }) {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({ 
    name: "", 
    email: "", 
    password: "", 
    confirmPassword: "" 
  });

  const handleGoogleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });

      const data = await response.json();

      if (response.ok) {
        onLogin(data.user, data.token);
        toast.success("Welcome back!");
        navigate("/dashboard", { replace: true });
      } else {
        toast.error(data.detail || "Login failed");
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (registerData.password !== registerData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: registerData.name,
          email: registerData.email,
          password: registerData.password,
          role: "customer"
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success("Account created! Please login.");
        setRegisterData({ name: "", email: "", password: "", confirmPassword: "" });
      } else {
        toast.error(data.detail || "Registration failed");
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex relative overflow-hidden">
      {/* Animated PCB Circuit Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Circuit SVG Pattern */}
        <svg className="absolute inset-0 w-full h-full opacity-30" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="circuit-pattern" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M10 10 L10 30 L30 30" stroke="#22EDA9" strokeWidth="1" fill="none" opacity="0.5"/>
              <path d="M50 10 L50 50 L90 50" stroke="#22EDA9" strokeWidth="1" fill="none" opacity="0.5"/>
              <path d="M70 10 L70 30 L90 30 L90 70" stroke="#22EDA9" strokeWidth="1" fill="none" opacity="0.5"/>
              <path d="M10 70 L30 70 L30 90" stroke="#22EDA9" strokeWidth="1" fill="none" opacity="0.5"/>
              <path d="M50 70 L50 90" stroke="#22EDA9" strokeWidth="1" fill="none" opacity="0.5"/>
              <circle cx="10" cy="10" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="30" cy="30" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="50" cy="10" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="90" cy="50" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="70" cy="10" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="90" cy="70" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="10" cy="70" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="30" cy="90" r="2" fill="#22EDA9" opacity="0.8"/>
              <circle cx="50" cy="90" r="2" fill="#22EDA9" opacity="0.8"/>
            </pattern>
            {/* Glowing effect */}
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#circuit-pattern)"/>
        </svg>
        
        {/* Animated glowing circuits */}
        <div className="absolute inset-0">
          <svg className="w-full h-full" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
            {/* Horizontal lines */}
            <line x1="0" y1="200" x2="600" y2="200" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-1" filter="url(#glow)"/>
            <line x1="0" y1="400" x2="400" y2="400" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-2" filter="url(#glow)"/>
            <line x1="0" y1="600" x2="500" y2="600" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-3" filter="url(#glow)"/>
            <line x1="0" y1="800" x2="350" y2="800" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-4" filter="url(#glow)"/>
            
            {/* Vertical connectors */}
            <line x1="600" y1="200" x2="600" y2="350" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-1" filter="url(#glow)"/>
            <line x1="400" y1="400" x2="400" y2="500" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-2" filter="url(#glow)"/>
            <line x1="500" y1="600" x2="500" y2="750" stroke="#22EDA9" strokeWidth="2" className="animate-circuit-3" filter="url(#glow)"/>
            
            {/* Glowing endpoints */}
            <circle cx="600" cy="350" r="6" fill="#22EDA9" className="animate-pulse-glow" filter="url(#glow)"/>
            <circle cx="400" cy="500" r="6" fill="#22EDA9" className="animate-pulse-glow" filter="url(#glow)"/>
            <circle cx="500" cy="750" r="6" fill="#22EDA9" className="animate-pulse-glow" filter="url(#glow)"/>
            <circle cx="350" cy="800" r="6" fill="#22EDA9" className="animate-pulse-glow" filter="url(#glow)"/>
          </svg>
        </div>
      </div>

      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative z-10">
        <div className="absolute inset-0 flex flex-col items-center justify-center p-12">
          {/* Logo with glow */}
          <div className="relative mb-8">
            <div className="absolute inset-0 bg-[#22EDA9] blur-3xl opacity-30 rounded-full scale-150"></div>
            <img 
              src="https://customer-assets.emergentagent.com/job_evbattwheels/artifacts/ygo0wrln_68469546%20%281%29.png" 
              alt="Battwheels Logo" 
              className="relative w-72 h-auto drop-shadow-[0_0_30px_rgba(34,237,169,0.5)]"
            />
          </div>
          <h2 className="text-4xl font-bold mb-4 tracking-tight text-white text-center">
            EV Command Center
          </h2>
          <p className="text-lg text-gray-400 max-w-md leading-relaxed text-center">
            AI-Powered Electric Failure Intelligence for next-generation EV workshop management.
          </p>
          <div className="mt-10 grid grid-cols-2 gap-5">
            <div className="p-5 rounded-xl bg-[#22EDA9]/10 backdrop-blur-md border border-[#22EDA9]/30 text-center hover:border-[#22EDA9]/60 transition-all hover:shadow-[0_0_30px_rgba(34,237,169,0.2)]">
              <p className="text-4xl font-bold text-[#22EDA9] font-mono">745+</p>
              <p className="text-sm text-gray-400 mt-1">Vehicles Serviced</p>
            </div>
            <div className="p-5 rounded-xl bg-[#22EDA9]/10 backdrop-blur-md border border-[#22EDA9]/30 text-center hover:border-[#22EDA9]/60 transition-all hover:shadow-[0_0_30px_rgba(34,237,169,0.2)]">
              <p className="text-4xl font-bold text-[#22EDA9] font-mono">98%</p>
              <p className="text-sm text-gray-400 mt-1">Success Rate</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Auth Forms */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10">
        <Card className="w-full max-w-md border-0 bg-[#111111] shadow-2xl rounded-2xl overflow-hidden">
          {/* Green Header with Logo */}
          <div className="bg-[#22EDA9] p-6 text-center relative overflow-hidden">
            {/* Subtle circuit pattern in header */}
            <div className="absolute inset-0 opacity-20">
              <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                <pattern id="header-circuit" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M5 5 L5 15 L15 15" stroke="white" strokeWidth="1" fill="none"/>
                  <path d="M25 5 L25 25 L35 25" stroke="white" strokeWidth="1" fill="none"/>
                  <circle cx="5" cy="5" r="2" fill="white"/>
                  <circle cx="15" cy="15" r="2" fill="white"/>
                  <circle cx="35" cy="25" r="2" fill="white"/>
                </pattern>
                <rect width="100%" height="100%" fill="url(#header-circuit)"/>
              </svg>
            </div>
            {/* Logo in header */}
            <div className="relative">
              <img 
                src="https://customer-assets.emergentagent.com/job_evbattwheels/artifacts/ygo0wrln_68469546%20%281%29.png" 
                alt="Battwheels" 
                className="h-12 mx-auto mb-3 brightness-0 invert"
              />
              <div className="flex items-center justify-center gap-2 text-black">
                <Zap className="h-5 w-5" />
                <span className="text-sm font-medium uppercase tracking-wider">AI-Powered EV Intelligence</span>
                <Zap className="h-5 w-5" />
              </div>
            </div>
          </div>
          
          <CardHeader className="text-center pt-6 pb-2">
            <CardTitle className="text-2xl font-bold text-white">Welcome Back</CardTitle>
            <CardDescription className="text-gray-400">Sign in to access your EV Command Center</CardDescription>
          </CardHeader>
          <CardContent className="pb-8">
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6 bg-[#1a1a1a] rounded-xl p-1">
                <TabsTrigger value="login" data-testid="login-tab" className="rounded-lg text-gray-400 data-[state=active]:bg-[#22EDA9] data-[state=active]:text-black data-[state=active]:shadow-md transition-all">Login</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab" className="rounded-lg text-gray-400 data-[state=active]:bg-[#22EDA9] data-[state=active]:text-black data-[state=active]:shadow-md transition-all">Register</TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-gray-300">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="you@example.com"
                        className="pl-10 bg-[#1a1a1a] border-gray-700 text-white placeholder:text-gray-500 focus:border-[#22EDA9] focus:ring-[#22EDA9]/30 rounded-lg"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        required
                        data-testid="login-email-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-gray-300">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="••••••••"
                        className="pl-10 bg-[#1a1a1a] border-gray-700 text-white placeholder:text-gray-500 focus:border-[#22EDA9] focus:ring-[#22EDA9]/30 rounded-lg"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                        data-testid="login-password-input"
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-[#22EDA9] text-black hover:bg-[#1DD69A] font-semibold rounded-lg shadow-[0_0_20px_rgba(34,237,169,0.3)] hover:shadow-[0_0_30px_rgba(34,237,169,0.5)] transition-all" 
                    disabled={isLoading}
                    data-testid="login-submit-btn"
                  >
                    {isLoading ? "Signing in..." : "Sign In"}
                  </Button>
                </form>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-700" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="bg-[#111111] px-2 text-gray-500">or continue with</span>
                  </div>
                </div>

                <Button 
                  variant="outline" 
                  className="w-full border-gray-700 text-gray-300 hover:bg-[#1a1a1a] hover:text-white rounded-lg"
                  onClick={handleGoogleLogin}
                  data-testid="google-login-btn"
                >
                  <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    />
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    />
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    />
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    />
                  </svg>
                  Continue with Google
                </Button>

                <p className="mt-4 text-xs text-center text-gray-500">
                  Demo credentials: admin@battwheels.in / admin123
                </p>
              </TabsContent>

              <TabsContent value="register">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name" className="text-gray-700">Full Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="register-name"
                        type="text"
                        placeholder="John Doe"
                        className="pl-10 bg-gray-50 border-gray-300 focus:border-[#22EDA9] rounded-lg"
                        value={registerData.name}
                        onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                        required
                        data-testid="register-name-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email" className="text-gray-700">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="register-email"
                        type="email"
                        placeholder="you@example.com"
                        className="pl-10 bg-gray-50 border-gray-300 focus:border-[#22EDA9] rounded-lg"
                        value={registerData.email}
                        onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                        required
                        data-testid="register-email-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password" className="text-gray-700">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="register-password"
                        type="password"
                        placeholder="••••••••"
                        className="pl-10 bg-gray-50 border-gray-300 focus:border-[#22EDA9] rounded-lg"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                        required
                        data-testid="register-password-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-confirm" className="text-gray-700">Confirm Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="register-confirm"
                        type="password"
                        placeholder="••••••••"
                        className="pl-10 bg-gray-50 border-gray-300 focus:border-[#22EDA9] rounded-lg"
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                        required
                        data-testid="register-confirm-input"
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-[#22EDA9] text-black hover:bg-[#1DD69A] font-semibold rounded-lg" 
                    disabled={isLoading}
                    data-testid="register-submit-btn"
                  >
                    {isLoading ? "Creating Account..." : "Create Account"}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
