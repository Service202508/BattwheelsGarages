import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Mail, Lock, User, Zap, ChevronRight, Eye, EyeOff, Sparkles, Brain, Truck, BarChart3, Building2, Wrench } from "lucide-react";
import { API } from "@/App";

// 3D Vehicle Image URLs
const VEHICLE_ICONS = {
  twoWheeler: "https://static.prod-images.emergentagent.com/jobs/b6660fe1-f682-4808-9bae-a4692d3851e2/images/78da35e1e893d4a802576a6efe5889c4f534d1eae0f830c137d048a6a08e20eb.png",
  threeWheeler: "https://static.prod-images.emergentagent.com/jobs/b6660fe1-f682-4808-9bae-a4692d3851e2/images/77bb650e73e4c6a25549a17eda5ee9649e16abfb1cefbb4fa9deb30a665e894e.png",
  car: "https://static.prod-images.emergentagent.com/jobs/b6660fe1-f682-4808-9bae-a4692d3851e2/images/34b2bb260cf90d1adbdad96cd56731da36e34bd8d070754a390e89d0df18647f.png",
  commercial: "https://static.prod-images.emergentagent.com/jobs/b6660fe1-f682-4808-9bae-a4692d3851e2/images/c8bef73afa11c68ce24af82cf634323d61f438023db3236559e15769386057ef.png"
};

// Animated 3D Vehicle Icons Component
const AnimatedVehicleIcons = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex(prev => (prev + 1) % 4);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const vehicles = [
    { src: VEHICLE_ICONS.twoWheeler, label: "2-Wheeler", size: "w-20 h-20" },
    { src: VEHICLE_ICONS.threeWheeler, label: "3-Wheeler", size: "w-24 h-24" },
    { src: VEHICLE_ICONS.car, label: "Electric Car", size: "w-28 h-28" },
    { src: VEHICLE_ICONS.commercial, label: "Commercial", size: "w-24 h-24" },
  ];

  return (
    <div className="flex justify-center items-end gap-4 sm:gap-6 mb-12">
      {vehicles.map((vehicle, index) => (
        <div 
          key={vehicle.label}
          className={`flex flex-col items-center transition-all duration-700 ease-out cursor-pointer ${
            activeIndex === index 
              ? 'scale-110 opacity-100 -translate-y-2' 
              : 'scale-90 opacity-50'
          }`}
          onClick={() => setActiveIndex(index)}
        >
          <div className={`relative transition-all duration-700 ${vehicle.size} flex items-center justify-center`}>
            {activeIndex === index && (
              <div className="absolute inset-0 bg-[#C8FF00]/20 blur-2xl rounded-full animate-pulse" />
            )}
            <img 
              src={vehicle.src} 
              alt={vehicle.label}
              className={`relative z-10 object-contain transition-all duration-500 drop-shadow-lg ${
                activeIndex === index ? 'drop-shadow-2xl' : ''
              }`}
              style={{ 
                filter: activeIndex === index 
                  ? 'drop-shadow(0 10px 20px rgba(200, 255, 0, 0.3))' 
                  : 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))'
              }}
            />
          </div>
          <span className={`text-xs font-semibold mt-3 transition-all duration-500 tracking-wide ${
            activeIndex === index 
              ? 'text-[#C8FF00]' 
              : 'text-[rgba(244,246,240,0.4)]'
          }`}>
            {vehicle.label}
          </span>
        </div>
      ))}
    </div>
  );
};

// Feature Badges
const FeatureBadge = ({ icon: Icon, text }) => (
  <div className="flex items-center gap-2 px-4 py-2 bg-[#111820]/60 backdrop-blur-sm rounded-full border border-[rgba(200,255,0,0.15)]">
    <Icon className="w-4 h-4 text-[#C8FF00]" />
    <span className="text-xs font-medium text-[rgba(244,246,240,0.7)]">{text}</span>
  </div>
);

// Auto-Scrolling Feature Cards
const FEATURE_CARDS = [
  { 
    icon: Brain, 
    title: "AI Diagnostics & Resolutions", 
    description: "Intelligent fault detection with ML-powered root cause analysis and step-by-step repair guidance" 
  },
  { 
    icon: Truck, 
    title: "Fleet Service & Uptime Management", 
    description: "Maximize fleet availability with predictive maintenance and real-time service scheduling" 
  },
  { 
    icon: BarChart3, 
    title: "Realtime Fleet Insights", 
    description: "Live dashboards with vehicle health metrics, usage patterns, and performance analytics" 
  },
  { 
    icon: Building2, 
    title: "Dealer Management System", 
    description: "Streamline dealer operations with inventory tracking, order management, and performance metrics" 
  },
  { 
    icon: Wrench, 
    title: "Service Center Management", 
    description: "End-to-end workshop operations including job cards, technician allocation, and parts tracking" 
  },
];

const AutoScrollFeatureCards = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  const scrollRef = useRef(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex(prev => (prev + 1) % FEATURE_CARDS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      const cardWidth = 280;
      const scrollPosition = activeIndex * cardWidth;
      scrollRef.current.scrollTo({
        left: scrollPosition,
        behavior: 'smooth'
      });
    }
  }, [activeIndex]);

  return (
    <div className="w-full mt-8">
      {/* Scrolling Container */}
      <div 
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto scrollbar-hide pb-4 snap-x snap-mandatory"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {FEATURE_CARDS.map((feature, index) => {
          const Icon = feature.icon;
          const isActive = index === activeIndex;
          return (
            <div
              key={feature.title}
              onClick={() => setActiveIndex(index)}
              className={`flex-shrink-0 w-[260px] p-4 rounded cursor-pointer transition-all duration-500 snap-start ${
                isActive 
                  ? 'bg-[rgba(200,255,0,0.08)] border-2 border-[rgba(200,255,0,0.25)] scale-105' 
                  : 'bg-[#111820]/50 border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.15)] hover:bg-[rgba(200,255,0,0.04)]'
              }`}
            >
              <div className={`w-10 h-10 rounded flex items-center justify-center mb-3 transition-all duration-500 ${
                isActive 
                  ? 'bg-[#C8FF00]' 
                  : 'bg-[#111820]'
              }`}>
                <Icon className={`w-5 h-5 transition-colors duration-500 ${isActive ? 'text-[#080C0F]' : 'text-[rgba(244,246,240,0.5)]'}`} />
              </div>
              <h3 className={`font-semibold text-sm mb-1.5 transition-colors duration-500 ${
                isActive ? 'text-[#C8FF00]' : 'text-[rgba(244,246,240,0.7)]'
              }`}>
                {feature.title}
              </h3>
              <p className="text-xs text-[rgba(244,246,240,0.4)] leading-relaxed line-clamp-2">
                {feature.description}
              </p>
            </div>
          );
        })}
      </div>
      
      {/* Progress Indicators */}
      <div className="flex justify-center gap-2 mt-4">
        {FEATURE_CARDS.map((_, index) => (
          <button
            key={index}
            onClick={() => setActiveIndex(index)}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index === activeIndex 
                ? 'w-6 bg-[#C8FF00]' 
                : 'w-1.5 bg-[rgba(255,255,255,0.2)] hover:bg-[rgba(255,255,255,0.3)]'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

// Premium Input Component with 3D styling
const PremiumInput = ({ icon: Icon, type, id, placeholder, value, onChange, required, showPasswordToggle, dataTestId }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  
  const inputType = showPasswordToggle ? (showPassword ? "text" : "password") : type;
  
  return (
    <div className={`relative group transition-all duration-300 ${isFocused ? 'transform scale-[1.02]' : ''}`}>
      {/* 3D Shadow Effect */}
      <div className={`absolute inset-0 rounded-lg transition-all duration-300 ${
        isFocused 
          ? 'bg-[rgba(200,255,0,0.1)] blur-xl opacity-100' 
          : 'opacity-0'
      }`} />
      
      {/* Input Container */}
      <div className={`relative rounded transition-all duration-300 ${
        isFocused 
          ? 'ring-2 ring-[rgba(200,255,0,0.4)]' 
          : 'border border-[rgba(255,255,255,0.07)]'
      }`}>
        {/* Icon */}
        <div className={`absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded transition-all duration-300 ${
          isFocused 
            ? 'bg-[#C8FF00]' 
            : 'bg-[#111820]'
        }`}>
          <Icon className={`h-4 w-4 transition-colors duration-300 ${
            isFocused ? 'text-[#080C0F]' : 'text-[rgba(244,246,240,0.5)]'
          }`} />
        </div>
        
        <Input
          id={id}
          type={inputType}
          placeholder={placeholder}
          className={`pl-16 pr-${showPasswordToggle ? '14' : '4'} h-14 bg-[#111820] border-2 rounded text-base font-medium text-[#F4F6F0] transition-all duration-300 ${
            isFocused 
              ? 'border-[#C8FF00] bg-[#111820]' 
              : 'border-[rgba(255,255,255,0.1)] hover:border-[rgba(255,255,255,0.2)]'
          }`}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          required={required}
          data-testid={dataTestId}
        />
        
        {/* Password Toggle */}
        {showPasswordToggle && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className={`absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded transition-all duration-300 hover:bg-[rgba(255,255,255,0.1)] ${
              isFocused ? 'text-[#C8FF00]' : 'text-[rgba(244,246,240,0.4)]'
            }`}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );
};

// Premium Button Component
const PremiumButton = ({ children, onClick, type, disabled, variant = "primary", className = "", dataTestId }) => {
  const [isPressed, setIsPressed] = useState(false);
  
  const baseStyles = "relative w-full h-14 font-bold rounded transition-all duration-300 overflow-hidden";
  
  const variants = {
    primary: `bg-[#C8FF00] text-[#080C0F] 
      hover:bg-[#d4ff1a] hover:-translate-y-0.5
      hover:shadow-[0_0_20px_rgba(200,255,0,0.30)]
      active:translate-y-0
      disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0`,
    outline: `bg-[#111820] border-2 border-[rgba(255,255,255,0.15)] text-[rgba(244,246,240,0.7)] 
      hover:border-[rgba(200,255,0,0.3)] hover:text-[#F4F6F0] hover:-translate-y-0.5
      hover:shadow-[0_0_20px_rgba(200,255,0,0.30)]
      active:translate-y-0`
  };
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
      className={`${baseStyles} ${variants[variant]} ${className}`}
      data-testid={dataTestId}
    >
      {/* Shine Effect */}
      {variant === "primary" && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
      )}
      
      {/* Content */}
      <span className="relative flex items-center justify-center gap-2">
        {children}
      </span>
    </button>
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
        // Check if login returns organizations list (multi-org support)
        const orgs = data.organizations || [];
        
        // If single org returned in response, store it
        if (data.organization) {
          localStorage.setItem("organization_id", data.organization.organization_id);
          localStorage.setItem("organization", JSON.stringify(data.organization));
        }
        
        // Pass organizations to login handler
        await onLogin(data.user, data.token, orgs);
        
        toast.success("Welcome back!");
        
        // Navigate based on orgs - if multiple, App.js will show org selection
        if (orgs.length <= 1) {
          navigate("/dashboard", { replace: true });
        }
        // If multiple orgs, let App.js handle the org selection screen
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
    <div className="min-h-screen flex bg-[#080C0F]">
      {/* Left Panel - Premium Hero */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#080C0F] via-[#0D1317] to-[#111820]" />
        
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: `linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                           linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }} />
        
        {/* Decorative circles */}
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-[rgba(200,255,0,0.08)] rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-[rgba(200,255,0,0.04)] rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br from-[rgba(200,255,0,0.05)] to-transparent rounded-full blur-3xl" />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center items-center w-full px-16">
          <div className="text-center max-w-lg">
            {/* Animated 3D Vehicle Icons */}
            <AnimatedVehicleIcons />

            {/* Main Heading with gradient */}
            <h1 className="text-4xl xl:text-5xl font-bold text-[#F4F6F0] mb-4 leading-tight">
              EV Failure
              <span className="block text-[#C8FF00]">
                Intelligence
              </span>
            </h1>
            
            <p className="text-lg xl:text-xl text-[#C8FF00] font-semibold mb-6 tracking-wide">
              Your Onsite EV Resolution Partner
            </p>
            
            <p className="text-[rgba(244,246,240,0.5)] text-base leading-relaxed mb-10 max-w-md mx-auto">
              AI-powered diagnostics for Electric 2W, 3W & 4W Vehicles—turning every breakdown into structured, reusable enterprise intelligence.
            </p>

            {/* Tagline with glowing icons */}
            <div className="flex flex-wrap justify-center items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="absolute inset-0 bg-[rgba(200,255,0,0.4)] rounded-full blur-md animate-pulse" />
                  <div className="relative w-8 h-8 rounded-full bg-[#C8FF00] flex items-center justify-center">
                    <Zap className="w-4 h-4 text-[#080C0F]" />
                  </div>
                </div>
                <span className="text-sm font-semibold text-[rgba(244,246,240,0.6)]">Diagnose faster.</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="absolute inset-0 bg-[rgba(200,255,0,0.4)] rounded-full blur-md animate-pulse" style={{ animationDelay: '0.3s' }} />
                  <div className="relative w-8 h-8 rounded-full bg-[#C8FF00] flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-[#080C0F]" />
                  </div>
                </div>
                <span className="text-sm font-semibold text-[rgba(244,246,240,0.6)]">Resolve smarter.</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="absolute inset-0 bg-[rgba(200,255,0,0.4)] rounded-full blur-md animate-pulse" style={{ animationDelay: '0.6s' }} />
                  <div className="relative w-8 h-8 rounded-full bg-[#C8FF00] flex items-center justify-center">
                    <Brain className="w-4 h-4 text-[#080C0F]" />
                  </div>
                </div>
                <span className="text-sm font-semibold text-[rgba(244,246,240,0.6)]">Learn forever.</span>
              </div>
            </div>

            {/* Auto-Scrolling Feature Cards */}
            <AutoScrollFeatureCards />
          </div>
        </div>
        
        {/* Copyright Footer - Left Panel */}
        <div className="absolute bottom-6 left-0 right-0 text-center z-10">
          <p className="text-xs text-[rgba(244,246,240,0.3)] font-medium tracking-wide">
            © 2026 BATTWHEELS SERVICES PRIVATE LIMITED. All rights reserved.
          </p>
        </div>
      </div>

      {/* Right Panel - Premium Auth Form */}
      <div className="flex-1 flex flex-col relative overflow-hidden min-h-screen">
        {/* Premium Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0D1317] via-[#111820] to-[#0D1317]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[rgba(200,255,0,0.05)] rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-[rgba(200,255,0,0.03)] rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        
        {/* Top Header with Logo */}
        <div className="relative z-10 flex justify-between items-center px-4 sm:px-6 lg:px-8 pt-4 sm:pt-6">
          {/* Spacer for mobile/tablet to push logo to right */}
          <div className="flex-1" />
          
          {/* Logo with Volt Glow - Compact */}
          <div className="relative group">
            {/* Outer volt glow */}
            <div className="absolute -inset-3 sm:-inset-4 bg-gradient-to-br from-[rgba(200,255,0,0.3)] via-[rgba(200,255,0,0.15)] to-transparent rounded blur-xl opacity-70 group-hover:opacity-90 transition-opacity duration-500" />
            {/* Inner glow ring */}
            <div className="absolute -inset-2 sm:-inset-2.5 bg-gradient-to-r from-[rgba(200,255,0,0.2)] to-[rgba(200,255,0,0.15)] rounded blur-lg opacity-60" />
            {/* Subtle pulse animation */}
            <div className="absolute -inset-2.5 sm:-inset-3 bg-[rgba(200,255,0,0.1)] rounded blur-md animate-pulse opacity-40" style={{ animationDuration: '3s' }} />
            <img 
              src="https://customer-assets.emergentagent.com/job_accounting-os-1/artifacts/0f7szaub_89882536.png" 
              alt="Battwheels" 
              className="relative h-10 sm:h-12 md:h-14 lg:h-16 w-auto"
            />
          </div>
        </div>

        <div className="relative z-10 flex-1 flex items-center justify-center px-4 sm:px-8 lg:px-12 py-4 sm:py-6 lg:py-0">
          <div className="w-full max-w-md">
            {/* Mobile/Tablet 3D Icons - Hidden on desktop */}
            <div className="lg:hidden flex flex-col items-center mb-6">
              <div className="flex gap-3 items-end">
                <img src={VEHICLE_ICONS.twoWheeler} alt="2W" className="w-10 h-10 sm:w-12 sm:h-12 object-contain opacity-80 hover:opacity-100 transition-opacity" />
                <img src={VEHICLE_ICONS.threeWheeler} alt="3W" className="w-12 h-12 sm:w-14 sm:h-14 object-contain opacity-80 hover:opacity-100 transition-opacity" />
                <img src={VEHICLE_ICONS.car} alt="4W" className="w-14 h-14 sm:w-16 sm:h-16 object-contain" />
                <img src={VEHICLE_ICONS.commercial} alt="Truck" className="w-12 h-12 sm:w-14 sm:h-14 object-contain opacity-80 hover:opacity-100 transition-opacity" />
              </div>
              {/* Mobile tagline */}
              <p className="text-sm text-[#C8FF00] font-medium mt-3 tracking-wide">EV Failure Intelligence</p>
            </div>

            {/* Premium Glass Card */}
            <div className="relative">
              {/* Card Glow */}
              <div className="absolute -inset-1 bg-gradient-to-r from-[rgba(200,255,0,0.15)] via-transparent to-[rgba(200,255,0,0.15)] rounded blur-xl opacity-60" />
              
              {/* Main Card */}
              <Card className="relative border border-[rgba(255,255,255,0.07)] rounded overflow-hidden bg-[#111820]/95 backdrop-blur-xl" style={{ borderRadius: '4px' }}>
                {/* Top Accent Line */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#C8FF00] to-transparent" />
                
                <CardHeader className="text-center pt-8 pb-4 px-6 sm:px-8">
                  {/* Decorative Icon */}
                  <div className="mx-auto mb-3 w-12 h-12 rounded-lg bg-[rgba(200,255,0,0.1)] border border-[rgba(200,255,0,0.2)] flex items-center justify-center shadow-inner">
                    <Zap className="w-6 h-6 text-[#C8FF00]" />
                  </div>
                  <CardTitle className="text-2xl sm:text-3xl font-bold text-[#F4F6F0] tracking-tight">Battwheels OS</CardTitle>
                  <CardDescription className="text-[rgba(244,246,240,0.5)] mt-1.5 text-sm sm:text-base">Sign in to your account</CardDescription>
                </CardHeader>
                
                <CardContent className="px-6 sm:px-8 pb-8">
                  <Tabs defaultValue="login" className="w-full">
                    {/* Premium Tab List */}
                    <TabsList className="grid w-full grid-cols-2 mb-6 bg-[#080C0F] rounded p-1 h-12 border border-[rgba(255,255,255,0.07)]">
                      <TabsTrigger 
                        value="login" 
                        data-testid="login-tab" 
                        className="rounded font-semibold text-sm transition-all duration-300
                          data-[state=active]:bg-[#C8FF00]
                          data-[state=active]:text-[#080C0F]
                          data-[state=inactive]:text-[rgba(244,246,240,0.5)] data-[state=inactive]:hover:text-[#F4F6F0]
                          h-10"
                      >
                        Login
                      </TabsTrigger>
                      <TabsTrigger 
                        value="register" 
                        data-testid="register-tab" 
                        className="rounded font-semibold text-sm transition-all duration-300
                          data-[state=active]:bg-[#C8FF00]
                          data-[state=active]:text-[#080C0F]
                          data-[state=inactive]:text-[rgba(244,246,240,0.5)] data-[state=inactive]:hover:text-[#F4F6F0]
                          h-10"
                      >
                        Register
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="login" className="mt-0">
                      <form onSubmit={handleLogin} className="space-y-4">
                        <div className="space-y-1.5">
                          <Label htmlFor="login-email" className="text-[rgba(244,246,240,0.7)] text-sm font-semibold ml-1">Email</Label>
                          <PremiumInput
                            icon={Mail}
                            type="email"
                            id="login-email"
                            placeholder="you@example.com"
                            value={loginData.email}
                            onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                            required
                            dataTestId="login-email-input"
                          />
                        </div>
                        
                        <div className="space-y-1.5">
                          <Label htmlFor="login-password" className="text-[rgba(244,246,240,0.7)] text-sm font-semibold ml-1">Password</Label>
                          <PremiumInput
                            icon={Lock}
                            type="password"
                            id="login-password"
                            placeholder="••••••••"
                            value={loginData.password}
                            onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                            required
                            showPasswordToggle
                            dataTestId="login-password-input"
                          />
                        </div>
                        
                        <div className="pt-1">
                          <PremiumButton 
                            type="submit" 
                            disabled={isLoading}
                            dataTestId="login-submit-btn"
                          >
                            {isLoading ? (
                              <>
                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                <span>Signing in...</span>
                              </>
                            ) : (
                              <>
                                <span>Sign In</span>
                                <ChevronRight className="w-5 h-5" />
                              </>
                            )}
                          </PremiumButton>
                        </div>
                      </form>

                      {/* Divider */}
                      <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                          <div className="w-full border-t border-[rgba(255,255,255,0.1)]" />
                        </div>
                        <div className="relative flex justify-center">
                          <span className="bg-[#111820] px-3 text-xs text-[rgba(244,246,240,0.4)] font-medium">
                            or continue with
                          </span>
                        </div>
                      </div>

                      {/* Google Button */}
                      <PremiumButton 
                        variant="outline"
                        onClick={handleGoogleLogin}
                        dataTestId="google-login-btn"
                      >
                        <svg className="h-5 w-5" viewBox="0 0 24 24">
                          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                        </svg>
                        <span>Continue with Google</span>
                      </PremiumButton>
                    </TabsContent>

                    <TabsContent value="register" className="mt-0">
                      <form onSubmit={handleRegister} className="space-y-4">
                        <div className="space-y-1.5">
                          <Label htmlFor="register-name" className="text-[rgba(244,246,240,0.7)] text-sm font-semibold ml-1">Full Name</Label>
                          <PremiumInput
                            icon={User}
                            type="text"
                            id="register-name"
                            placeholder="John Doe"
                            value={registerData.name}
                            onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                            required
                            dataTestId="register-name-input"
                          />
                        </div>
                        
                        <div className="space-y-1.5">
                          <Label htmlFor="register-email" className="text-[rgba(244,246,240,0.7)] text-sm font-semibold ml-1">Email</Label>
                          <PremiumInput
                            icon={Mail}
                            type="email"
                            id="register-email"
                            placeholder="you@example.com"
                            value={registerData.email}
                            onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                            required
                            dataTestId="register-email-input"
                          />
                        </div>
                        
                        <div className="space-y-1.5">
                          <Label htmlFor="register-password" className="text-[rgba(244,246,240,0.7)] text-sm font-semibold ml-1">Password</Label>
                          <PremiumInput
                            icon={Lock}
                            type="password"
                            id="register-password"
                            placeholder="••••••••"
                            value={registerData.password}
                            onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                            required
                            showPasswordToggle
                            dataTestId="register-password-input"
                          />
                        </div>
                        
                        <div className="space-y-1.5">
                          <Label htmlFor="register-confirm" className="text-[rgba(244,246,240,0.7)] text-sm font-semibold ml-1">Confirm Password</Label>
                          <PremiumInput
                            icon={Lock}
                            type="password"
                            id="register-confirm"
                            placeholder="••••••••"
                            value={registerData.confirmPassword}
                            onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                            required
                            showPasswordToggle
                            dataTestId="register-confirm-input"
                          />
                        </div>
                        
                        <div className="pt-1">
                          <PremiumButton 
                            type="submit" 
                            disabled={isLoading}
                            dataTestId="register-submit-btn"
                          >
                            {isLoading ? (
                              <>
                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                <span>Creating Account...</span>
                              </>
                            ) : (
                              <>
                                <span>Create Account</span>
                                <ChevronRight className="w-5 h-5" />
                              </>
                            )}
                          </PremiumButton>
                        </div>
                      </form>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </div>
            
            {/* Copyright Footer - Mobile/Tablet (shown below card) */}
            <div className="lg:hidden mt-6 text-center">
              <p className="text-xs text-[rgba(244,246,240,0.45)] font-medium tracking-wide">
                © 2026 BATTWHEELS SERVICES PRIVATE LIMITED. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
