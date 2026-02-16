import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Mail, Lock, User, Zap, Bike, Car } from "lucide-react";
import { API } from "@/App";

// Animated EV Icons Component
const AnimatedEVIcons = () => {
  const [icons, setIcons] = useState([]);

  useEffect(() => {
    // Generate random icons
    const generateIcon = () => {
      const types = ['2W', '3W', '4W', 'bolt'];
      const type = types[Math.floor(Math.random() * types.length)];
      return {
        id: Math.random(),
        type,
        left: Math.random() * 80 + 10,
        top: Math.random() * 80 + 10,
        delay: Math.random() * 2,
        duration: 3 + Math.random() * 2,
      };
    };

    // Initial icons
    const initialIcons = Array.from({ length: 8 }, generateIcon);
    setIcons(initialIcons);

    // Add new icons periodically
    const interval = setInterval(() => {
      setIcons(prev => {
        const newIcons = prev.filter(icon => icon.id > Date.now() - 5000);
        return [...newIcons, generateIcon()];
      });
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  const renderIcon = (type) => {
    switch (type) {
      case '2W':
        return (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-full h-full">
            <circle cx="5" cy="17" r="3" />
            <circle cx="19" cy="17" r="3" />
            <path d="M12 17V5l4 4" />
            <path d="M8 17h8" />
            <path d="M5 14l7-9" />
          </svg>
        );
      case '3W':
        return (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-full h-full">
            <circle cx="6" cy="18" r="2" />
            <circle cx="18" cy="18" r="2" />
            <circle cx="18" cy="10" r="2" />
            <path d="M6 18h8M18 12v4M8 18V8h8" />
            <rect x="7" y="6" width="6" height="4" rx="1" />
          </svg>
        );
      case '4W':
        return (
          <Car className="w-full h-full" />
        );
      case 'bolt':
        return (
          <Zap className="w-full h-full" />
        );
      default:
        return null;
    }
  };

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {icons.map((icon) => (
        <div
          key={icon.id}
          className="absolute animate-float-fade"
          style={{
            left: `${icon.left}%`,
            top: `${icon.top}%`,
            animationDelay: `${icon.delay}s`,
            animationDuration: `${icon.duration}s`,
          }}
        >
          <div className={`w-10 h-10 ${icon.type === 'bolt' ? 'text-[#22EDA9]' : 'text-gray-300'}`}>
            {renderIcon(icon.type)}
          </div>
        </div>
      ))}
    </div>
  );
};

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
    <div className="min-h-screen flex bg-white">
      {/* Left Panel - Clean Hero with Animated Icons */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-gray-50 to-white">
        {/* Animated Background Icons */}
        <AnimatedEVIcons />
        
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `radial-gradient(circle, #22EDA9 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }}></div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center items-center w-full px-12">
          {/* Main Heading */}
          <div className="text-center max-w-md">
            {/* EV Vehicle Icons Row */}
            <div className="flex justify-center items-center gap-6 mb-8">
              <div className="w-12 h-12 text-gray-400 hover:text-[#22EDA9] transition-colors duration-300">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="5" cy="17" r="3" />
                  <circle cx="19" cy="17" r="3" />
                  <path d="M12 17V5l4 4" />
                  <path d="M8 17h8" />
                  <path d="M5 14l7-9" />
                </svg>
              </div>
              <div className="w-14 h-14 text-gray-400 hover:text-[#22EDA9] transition-colors duration-300">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="6" cy="18" r="2" />
                  <circle cx="18" cy="18" r="2" />
                  <circle cx="18" cy="10" r="2" />
                  <path d="M6 18h8M18 12v4M8 18V8h8" />
                  <rect x="7" y="6" width="6" height="4" rx="1" />
                </svg>
              </div>
              <div className="w-16 h-16 text-gray-400 hover:text-[#22EDA9] transition-colors duration-300">
                <Car className="w-full h-full" />
              </div>
            </div>

            {/* Bolt Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-[#22EDA9]/10 rounded-2xl flex items-center justify-center">
                <Zap className="w-8 h-8 text-[#22EDA9]" />
              </div>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              EV Failure Intelligence
            </h1>
            
            <p className="text-lg text-[#22EDA9] font-medium mb-4">
              Your Onsite EV Resolution Partner
            </p>
            
            <p className="text-gray-500 text-sm leading-relaxed">
              AI-powered diagnostics for 2W, 3W & 4W electric vehicles. 
              Transform every repair into enterprise-grade knowledge.
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Auth Form */}
      <div className="flex-1 flex flex-col bg-white relative">
        {/* Top Right Logo */}
        <div className="hidden lg:flex justify-end px-6 sm:px-8 py-6">
          <img 
            src="https://customer-assets.emergentagent.com/job_3a595ece-6ef9-4ac6-b3b4-0464858ff726/artifacts/trnes6dt_Screenshot%202026-02-16%20at%2010.25.22%E2%80%AFPM.png" 
            alt="Battwheels" 
            className="h-16 w-auto"
          />
        </div>

        <div className="flex-1 flex items-center justify-center p-6 sm:p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex justify-center mb-8">
            <img 
              src="https://customer-assets.emergentagent.com/job_3a595ece-6ef9-4ac6-b3b4-0464858ff726/artifacts/trnes6dt_Screenshot%202026-02-16%20at%2010.25.22%E2%80%AFPM.png" 
              alt="Battwheels" 
              className="h-12 w-auto"
            />
          </div>

          <Card className="border border-gray-100 shadow-xl rounded-2xl overflow-hidden">
            <CardHeader className="text-center pt-8 pb-4 px-8">
              <CardTitle className="text-2xl font-bold text-gray-900">Battwheels OS</CardTitle>
              <CardDescription className="text-gray-500">Sign in to your account</CardDescription>
            </CardHeader>
            
            <CardContent className="px-8 pb-8">
              <Tabs defaultValue="login" className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6 bg-gray-100 rounded-xl p-1 h-11">
                  <TabsTrigger 
                    value="login" 
                    data-testid="login-tab" 
                    className="rounded-lg font-medium data-[state=active]:bg-[#22EDA9] data-[state=active]:text-black data-[state=active]:shadow-sm transition-all h-9"
                  >
                    Login
                  </TabsTrigger>
                  <TabsTrigger 
                    value="register" 
                    data-testid="register-tab" 
                    className="rounded-lg font-medium data-[state=active]:bg-[#22EDA9] data-[state=active]:text-black data-[state=active]:shadow-sm transition-all h-9"
                  >
                    Register
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="login">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-gray-700 text-sm">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="login-email"
                          type="email"
                          placeholder="you@example.com"
                          className="pl-10 h-11 bg-white border-gray-200 focus:border-[#22EDA9] focus:ring-[#22EDA9] rounded-lg"
                          value={loginData.email}
                          onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                          required
                          data-testid="login-email-input"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="login-password" className="text-gray-700 text-sm">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="login-password"
                          type="password"
                          placeholder="••••••••"
                          className="pl-10 h-11 bg-white border-gray-200 focus:border-[#22EDA9] focus:ring-[#22EDA9] rounded-lg"
                          value={loginData.password}
                          onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                          required
                          data-testid="login-password-input"
                        />
                      </div>
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full h-11 bg-[#22EDA9] text-black hover:bg-[#1DD69A] font-semibold rounded-lg transition-colors" 
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
                      <span className="bg-white px-3 text-gray-400">or</span>
                    </div>
                  </div>

                  <Button 
                    variant="outline" 
                    className="w-full h-11 border-gray-200 text-gray-700 hover:bg-gray-50 rounded-lg"
                    onClick={handleGoogleLogin}
                    data-testid="google-login-btn"
                  >
                    <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    Continue with Google
                  </Button>

                  <p className="mt-6 text-xs text-center text-gray-400">
                    Demo: admin@battwheels.in / admin123
                  </p>
                </TabsContent>

                <TabsContent value="register">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name" className="text-gray-700 text-sm">Full Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-name"
                          type="text"
                          placeholder="John Doe"
                          className="pl-10 h-11 bg-white border-gray-200 focus:border-[#22EDA9] rounded-lg"
                          value={registerData.name}
                          onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                          required
                          data-testid="register-name-input"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-email" className="text-gray-700 text-sm">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-email"
                          type="email"
                          placeholder="you@example.com"
                          className="pl-10 h-11 bg-white border-gray-200 focus:border-[#22EDA9] rounded-lg"
                          value={registerData.email}
                          onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                          required
                          data-testid="register-email-input"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-password" className="text-gray-700 text-sm">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-password"
                          type="password"
                          placeholder="••••••••"
                          className="pl-10 h-11 bg-white border-gray-200 focus:border-[#22EDA9] rounded-lg"
                          value={registerData.password}
                          onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                          required
                          data-testid="register-password-input"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-confirm" className="text-gray-700 text-sm">Confirm Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-confirm"
                          type="password"
                          placeholder="••••••••"
                          className="pl-10 h-11 bg-white border-gray-200 focus:border-[#22EDA9] rounded-lg"
                          value={registerData.confirmPassword}
                          onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                          required
                          data-testid="register-confirm-input"
                        />
                      </div>
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full h-11 bg-[#22EDA9] text-black hover:bg-[#1DD69A] font-semibold rounded-lg transition-colors" 
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
      </div>

      {/* Global Styles for Animation */}
      <style>{`
        @keyframes float-fade {
          0% {
            opacity: 0;
            transform: translateY(20px) scale(0.8);
          }
          20% {
            opacity: 0.6;
            transform: translateY(0) scale(1);
          }
          80% {
            opacity: 0.6;
            transform: translateY(-10px) scale(1);
          }
          100% {
            opacity: 0;
            transform: translateY(-30px) scale(0.8);
          }
        }
        .animate-float-fade {
          animation: float-fade 4s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
