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
    <div className="min-h-screen flex">
      {/* Left Panel - Hero Section */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden bg-gradient-to-br from-[#22EDA9] via-[#1DD69A] to-[#19C98D]">
        {/* Decorative Background Elements */}
        <div className="absolute inset-0">
          {/* Large decorative circles */}
          <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-10 -right-32 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute top-1/3 right-1/4 w-72 h-72 bg-white/5 rounded-full blur-2xl"></div>
          
          {/* Subtle grid pattern */}
          <div className="absolute inset-0 opacity-[0.04]" style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}></div>
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-16 py-12 w-full">
          {/* Large Logo - More Prominent */}
          <div className="mb-8">
            <img 
              src="https://customer-assets.emergentagent.com/job_evbattwheels/artifacts/3abu9yqt_68469546%20%283%29.png" 
              alt="Battwheels Logo" 
              className="h-28 w-auto drop-shadow-[0_4px_20px_rgba(0,0,0,0.15)]"
            />
          </div>
          
          {/* Main Heading */}
          <h1 className="text-5xl lg:text-6xl font-bold text-white leading-tight mb-5 tracking-tight">
            EV Command<br />
            <span className="text-white/95">Center</span>
          </h1>
          
          {/* Tagline */}
          <p className="text-xl text-white/90 max-w-lg leading-relaxed mb-8">
            Next-generation <span className="font-semibold text-white">AI-powered</span> Electric Failure Intelligence for comprehensive EV workshop management.
          </p>
          
          {/* Feature Pills */}
          <div className="flex flex-wrap gap-3 mb-10">
            <span className="px-4 py-2.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium text-white border border-white/30 shadow-sm">
              🤖 AI Diagnostics
            </span>
            <span className="px-4 py-2.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium text-white border border-white/30 shadow-sm">
              ⚡ Real-time Tracking
            </span>
            <span className="px-4 py-2.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium text-white border border-white/30 shadow-sm">
              📊 Smart Analytics
            </span>
          </div>
          
          {/* Stats Cards */}
          <div className="flex gap-4">
            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-5 border border-white/30 shadow-lg hover:bg-white/25 transition-all duration-300 hover:scale-[1.02] cursor-default flex-1 max-w-[150px]">
              <p className="text-3xl font-bold text-white mb-0.5">745+</p>
              <p className="text-xs text-white/80 font-medium">Vehicles Serviced</p>
            </div>
            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-5 border border-white/30 shadow-lg hover:bg-white/25 transition-all duration-300 hover:scale-[1.02] cursor-default flex-1 max-w-[150px]">
              <p className="text-3xl font-bold text-white mb-0.5">98%</p>
              <p className="text-xs text-white/80 font-medium">Success Rate</p>
            </div>
            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-5 border border-white/30 shadow-lg hover:bg-white/25 transition-all duration-300 hover:scale-[1.02] cursor-default flex-1 max-w-[150px]">
              <p className="text-3xl font-bold text-white mb-0.5">24/7</p>
              <p className="text-xs text-white/80 font-medium">Support Available</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Auth Forms */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <Card className="w-full max-w-md border-0 bg-white shadow-2xl rounded-3xl overflow-hidden">
          {/* Mobile Logo Header */}
          <div className="lg:hidden bg-gradient-to-r from-[#22EDA9] to-[#1DD69A] p-6">
            <img 
              src="https://customer-assets.emergentagent.com/job_evbattwheels/artifacts/3abu9yqt_68469546%20%283%29.png" 
              alt="Battwheels Logo" 
              className="h-12 mx-auto"
            />
          </div>
          
          <CardHeader className="text-center pt-8 pb-4">
            <CardTitle className="text-2xl font-bold text-gray-900">Welcome Back</CardTitle>
            <CardDescription className="text-gray-500">Sign in to access your EV Command Center</CardDescription>
          </CardHeader>
          <CardContent className="px-8 pb-8">
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6 bg-gray-100 rounded-xl p-1 h-12">
                <TabsTrigger value="login" data-testid="login-tab" className="rounded-lg font-medium data-[state=active]:bg-[#22EDA9] data-[state=active]:text-black data-[state=active]:shadow-md transition-all h-10">Login</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab" className="rounded-lg font-medium data-[state=active]:bg-[#22EDA9] data-[state=active]:text-black data-[state=active]:shadow-md transition-all h-10">Register</TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-gray-700">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="you@example.com"
                        className="pl-10 bg-gray-50 border-gray-300 focus:border-[#22EDA9] focus:ring-[#22EDA9] rounded-lg"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        required
                        data-testid="login-email-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-gray-700">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="••••••••"
                        className="pl-10 bg-gray-50 border-gray-300 focus:border-[#22EDA9] focus:ring-[#22EDA9] rounded-lg"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                        data-testid="login-password-input"
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-[#22EDA9] text-black hover:bg-[#1DD69A] font-semibold rounded-lg" 
                    disabled={isLoading}
                    data-testid="login-submit-btn"
                  >
                    {isLoading ? "Signing in..." : "Sign In"}
                  </Button>
                </form>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="bg-white px-2 text-gray-500">or continue with</span>
                  </div>
                </div>

                <Button 
                  variant="outline" 
                  className="w-full border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg"
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
