import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Mail, Lock, User, Zap } from "lucide-react";
import { API } from "@/App";

// Standard EV Vehicle Icons
const BikeIcon = ({ className }) => (
  <svg viewBox="0 0 64 64" fill="none" className={className}>
    <circle cx="14" cy="46" r="10" stroke="currentColor" strokeWidth="3" fill="none"/>
    <circle cx="50" cy="46" r="10" stroke="currentColor" strokeWidth="3" fill="none"/>
    <path d="M14 46L24 26H40L50 46" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M24 26L32 18L40 26" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="32" cy="18" r="4" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M28 36H36" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
  </svg>
);

const AutoIcon = ({ className }) => (
  <svg viewBox="0 0 64 64" fill="none" className={className}>
    <circle cx="12" cy="48" r="8" stroke="currentColor" strokeWidth="3" fill="none"/>
    <circle cx="52" cy="48" r="8" stroke="currentColor" strokeWidth="3" fill="none"/>
    <path d="M20 48H44" stroke="currentColor" strokeWidth="3"/>
    <path d="M8 36L16 20H48L56 36" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M8 36V44H20" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M56 36V44H44" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M20 28H44" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="32" cy="12" r="4" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M32 16V20" stroke="currentColor" strokeWidth="2"/>
  </svg>
);

const CarIcon = ({ className }) => (
  <svg viewBox="0 0 64 64" fill="none" className={className}>
    <circle cx="16" cy="46" r="8" stroke="currentColor" strokeWidth="3" fill="none"/>
    <circle cx="48" cy="46" r="8" stroke="currentColor" strokeWidth="3" fill="none"/>
    <path d="M8 38H56" stroke="currentColor" strokeWidth="3"/>
    <path d="M8 38V30C8 28 10 26 12 26H20L26 18H38L44 26H52C54 26 56 28 56 30V38" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M24 38V32H40V38" stroke="currentColor" strokeWidth="2"/>
    <rect x="12" y="30" width="8" height="4" rx="1" stroke="currentColor" strokeWidth="2"/>
    <rect x="44" y="30" width="8" height="4" rx="1" stroke="currentColor" strokeWidth="2"/>
  </svg>
);

const BoltIcon = ({ className }) => (
  <svg viewBox="0 0 64 64" fill="none" className={className}>
    <path d="M36 8L16 36H30L28 56L48 28H34L36 8Z" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// Animated Icons Row Component
const AnimatedIconsRow = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex(prev => (prev + 1) % 4);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const icons = [
    { Icon: BikeIcon, label: "2W" },
    { Icon: AutoIcon, label: "3W" },
    { Icon: CarIcon, label: "4W" },
    { Icon: BoltIcon, label: "EV" },
  ];

  return (
    <div className="flex justify-center items-end gap-8 mb-10">
      {icons.map((item, index) => (
        <div 
          key={item.label}
          className={`flex flex-col items-center transition-all duration-500 ${
            activeIndex === index 
              ? 'scale-110 opacity-100' 
              : 'scale-100 opacity-40'
          }`}
        >
          <div className={`transition-all duration-500 ${
            activeIndex === index 
              ? 'text-[#22EDA9]' 
              : 'text-gray-400'
          }`}>
            <item.Icon className={`${
              index === 3 ? 'w-10 h-10' : 
              index === 2 ? 'w-16 h-16' : 
              index === 1 ? 'w-14 h-14' : 'w-12 h-12'
            }`} />
          </div>
          <span className={`text-xs font-medium mt-2 transition-all duration-500 ${
            activeIndex === index 
              ? 'text-[#22EDA9]' 
              : 'text-gray-400'
          }`}>
            {item.label}
          </span>
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
      {/* Left Panel - Clean Hero */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-gray-50 via-white to-gray-50">
        {/* Subtle background pattern */}
        <div className="absolute inset-0 opacity-[0.4]" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, #e5e7eb 1px, transparent 0)`,
          backgroundSize: '32px 32px'
        }}></div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center items-center w-full px-12">
          <div className="text-center max-w-md">
            {/* Animated Vehicle Icons */}
            <AnimatedIconsRow />

            {/* Main Heading */}
            <h1 className="text-3xl font-bold text-gray-900 mb-3">
              EV Failure Intelligence
            </h1>
            
            <p className="text-lg text-[#22EDA9] font-semibold mb-4">
              Your Onsite EV Resolution Partner
            </p>
            
            <p className="text-gray-500 text-sm leading-relaxed max-w-sm mx-auto">
              AI-powered diagnostics for electric 2-wheelers, 3-wheelers & 4-wheelers. 
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
          {/* Mobile Logo & Icons */}
          <div className="lg:hidden flex flex-col items-center mb-8">
            <img 
              src="https://customer-assets.emergentagent.com/job_3a595ece-6ef9-4ac6-b3b4-0464858ff726/artifacts/trnes6dt_Screenshot%202026-02-16%20at%2010.25.22%E2%80%AFPM.png" 
              alt="Battwheels" 
              className="h-12 w-auto mb-4"
            />
            <div className="flex gap-4 text-gray-400">
              <BikeIcon className="w-8 h-8" />
              <AutoIcon className="w-9 h-9" />
              <CarIcon className="w-10 h-10" />
            </div>
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
    </div>
  );
}
