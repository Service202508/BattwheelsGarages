import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  Zap, ArrowRight, Check, ChevronRight, X,
  Clock, TrendingUp, Shield, Eye,
  Ticket, FileText, Calculator, Package, Receipt,
  BookOpen, Users, Brain, CreditCard, Lock,
  BarChart3, Briefcase, Monitor, Settings, FolderOpen
} from 'lucide-react';
import ProductTour from '../components/ProductTour';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Animated counter hook
function useCountUp(target, duration = 1800) {
  const [count, setCount] = useState(0);
  const [started, setStarted] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !started) setStarted(true); },
      { threshold: 0.3 }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [started]);

  useEffect(() => {
    if (!started) return;
    const steps = 40;
    const increment = target / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(current));
    }, duration / steps);
    return () => clearInterval(timer);
  }, [started, target, duration]);

  return { count, ref };
}

// Scroll reveal hook
function useScrollReveal() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold: 0.1 }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return { ref, visible };
}

const SaaSLanding = () => {
  const navigate = useNavigate();
  const [showSignup, setShowSignup] = useState(false);
  const [showBookDemo, setShowBookDemo] = useState(false);
  const [showTour, setShowTour] = useState(false);
  const [bookDemoSubmitted, setBookDemoSubmitted] = useState(false);
  const [bookDemoLoading, setBookDemoLoading] = useState(false);
  const [bookDemoData, setBookDemoData] = useState({
    name: '', workshop_name: '', city: '', phone: '', vehicles_per_month: '<10'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '', admin_name: '', admin_email: '', admin_password: '',
    industry_type: 'ev_garage', city: '', state: ''
  });
  const [activeAudience, setActiveAudience] = useState(0);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleBookDemoSubmit = async (e) => {
    e.preventDefault();
    if (!bookDemoData.name || !bookDemoData.workshop_name || !bookDemoData.city || !bookDemoData.phone) {
      toast.error('Please fill in all required fields');
      return;
    }
    setBookDemoLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/book-demo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookDemoData)
      });
      if (res.ok) {
        setBookDemoSubmitted(true);
      } else {
        const d = await res.json();
        toast.error(d.detail || 'Something went wrong. Please try again.');
      }
    } catch {
      toast.error('Network error. Please try again.');
    } finally {
      setBookDemoLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/organizations/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();
      if (response.ok) {
        toast.success('Organization created successfully!');
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('organization_id', data.organization.organization_id);
        localStorage.setItem('organization', JSON.stringify(data.organization));
        window.location.href = '/dashboard';
      } else {
        toast.error(data.detail || 'Signup failed');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Scroll reveal refs
  const s2 = useScrollReveal();
  const s3 = useScrollReveal();
  const s4 = useScrollReveal();
  const s5 = useScrollReveal();
  const s6 = useScrollReveal();
  const s7 = useScrollReveal();
  const s8 = useScrollReveal();
  const s9 = useScrollReveal();

  // Animated counters for Section 6
  const c1 = useCountUp(16);
  const c2 = useCountUp(10000);
  const c3 = useCountUp(99);
  const c4 = useCountUp(100);

  // Audience data
  const audiences = [
    {
      tab: 'Workshop Owners',
      body: 'Run your entire EV workshop from one dashboard. Tickets, invoicing, inventory, payroll, GST filing. EFI\u2122 guides your technicians to fix it right the first time. No more guesswork.',
      features: ['AI Diagnostics', 'GST Compliance', 'Inventory + COGS', 'HR & Payroll', 'Customer Portal'],
    },
    {
      tab: 'OEMs (Ola, Ather, TVS)',
      body: 'Manage your authorized service network at scale. Track warranty claims, distribute parts, monitor dealer performance. Every repair across every dealer feeds your reliability intelligence.',
      features: ['Dealer Network Management', 'Warranty Claims', 'Parts Distribution', 'Field Failure Intelligence'],
    },
    {
      tab: 'Fleet Operators',
      body: 'Delivery fleets, ride-sharing, corporate vehicles. Predictive maintenance before breakdowns happen. Cost-per-km analytics. Fleet-wide health monitoring.',
      features: ['Predictive Maintenance', 'Fleet Health Dashboard', 'Uptime Optimization', 'Cost Analytics'],
    },
    {
      tab: 'EV Technicians',
      body: 'Access EFI\u2122 diagnostic intelligence on every job. Build your verified service record. Get matched with the right work. Your skills have value here.',
      features: ['AI-Guided Diagnosis', 'Skill Verification', 'Job Matching', 'Service Portfolio'],
    },
  ];

  // Platform modules
  const modules = [
    { icon: Ticket, name: 'Tickets & SLA' },
    { icon: FileText, name: 'Invoicing' },
    { icon: Calculator, name: 'Estimates' },
    { icon: Package, name: 'Inventory & COGS' },
    { icon: Receipt, name: 'GST Compliance' },
    { icon: BookOpen, name: 'Accounting' },
    { icon: Users, name: 'HR & Payroll' },
    { icon: Brain, name: 'EFI\u2122 AI' },
    { icon: CreditCard, name: 'Credit Notes' },
    { icon: Lock, name: 'Period Locking' },
    { icon: BarChart3, name: 'Reports' },
    { icon: Briefcase, name: 'AMC Contracts' },
    { icon: Monitor, name: 'Customer Portal' },
    { icon: Zap, name: 'Tech Portal' },
    { icon: Settings, name: 'Platform Admin' },
    { icon: FolderOpen, name: 'Projects' },
  ];

  const revealClass = (v) => `transition-all duration-700 ${v ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`;

  return (
    <div className="min-h-screen bg-zinc-950 text-white font-sans overflow-x-hidden">
      {/* Grain Overlay */}
      <div className="fixed inset-0 pointer-events-none z-[999] opacity-60" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`
      }} />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 border-b border-white/[0.07] bg-zinc-950/85 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-[#CBFF00] rounded flex items-center justify-center">
            <Zap className="w-4 h-4 text-zinc-900" />
          </div>
          <span className="text-lg font-extrabold tracking-tight">Battwheels OS</span>
        </div>
        <ul className="hidden md:flex gap-9 text-[13px] font-medium tracking-wider uppercase text-white/45">
          <li><a href="#solution" className="hover:text-white transition">EFI Engine</a></li>
          <li><a href="#platform" className="hover:text-white transition">Platform</a></li>
          <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
          <li><a href="#vision" className="hover:text-white transition">Vision</a></li>
        </ul>
        <div className="flex items-center gap-2">
          <button onClick={() => navigate('/login')} className="px-3 py-2 text-[12px] text-white/45 hover:text-white/80 transition tracking-wide" data-testid="nav-login-link">
            Login
          </button>
          <button onClick={() => setShowBookDemo(true)} className="px-5 py-2.5 text-[13px] font-semibold uppercase tracking-wide border border-white/10 hover:border-[#CBFF00] hover:text-[#CBFF00] transition rounded-sm" data-testid="nav-book-demo-btn">
            Book Demo
          </button>
          <button onClick={() => setShowSignup(true)} className="px-5 py-2.5 text-[13px] font-bold uppercase tracking-wide bg-[#CBFF00] text-zinc-900 hover:bg-[#d4ff33] hover:shadow-[0_0_24px_rgba(203,255,0,0.3)] transition rounded-sm" data-testid="nav-free-trial-btn">
            Free Trial
          </button>
        </div>
      </nav>

      {/* ========== SECTION 1: HERO ========== */}
      <section className="relative min-h-screen flex flex-col justify-center pt-36 pb-20 px-6 md:px-12 overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_70%_50%,rgba(203,255,0,0.05)_0%,transparent_70%)]" />
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)',
            backgroundSize: '80px 80px',
            maskImage: 'radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 80%)'
          }} />
        </div>

        <div className="relative z-10 max-w-6xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-12 text-[10px] tracking-widest text-[#CBFF00] border border-[#CBFF00]/20 bg-[#CBFF00]/5 rounded-sm font-mono">
            <span className="w-1.5 h-1.5 bg-[#CBFF00] rounded-full animate-pulse" />
            EFI Engine Active
          </div>

          <p className="flex items-center gap-3 text-[11px] tracking-[0.2em] uppercase text-[#CBFF00] mb-7 font-mono animate-fade-up">
            <span className="w-8 h-px bg-[#CBFF00]" />
            Battwheels OS
          </p>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl leading-none font-serif tracking-tight mb-8 animate-fade-up" style={{ animationDelay: '0.1s' }}>
            India's First AI-Powered<br />
            <em className="italic text-[#CBFF00]">EV Service Platform</em>
          </h1>

          <p className="text-base sm:text-lg text-white/45 max-w-xl mb-12 leading-relaxed animate-fade-up" style={{ animationDelay: '0.2s' }}>
            From a single workshop to a national OEM network. One platform runs it all.
          </p>

          <div className="flex flex-wrap gap-4 mb-16 animate-fade-up" style={{ animationDelay: '0.3s' }}>
            <button onClick={() => setShowSignup(true)} className="px-8 py-4 text-sm font-bold uppercase tracking-wide bg-[#CBFF00] text-zinc-900 hover:bg-[#d4ff33] hover:shadow-[0_0_24px_rgba(203,255,0,0.3)] transition rounded-sm flex items-center gap-2" data-testid="hero-start-trial-btn">
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => setShowBookDemo(true)} className="px-8 py-4 text-sm font-semibold uppercase tracking-wide border border-white/10 hover:border-[#CBFF00] hover:text-[#CBFF00] transition rounded-sm" data-testid="hero-book-demo-btn">
              Book a Demo
            </button>
            <button onClick={() => setShowTour(true)} className="px-8 py-4 text-sm font-semibold uppercase tracking-wide text-white/60 hover:text-[#CBFF00] transition flex items-center gap-2" data-testid="hero-see-tour-btn">
              <Eye className="w-4 h-4" /> See It In Action
            </button>
          </div>

          <div className="flex border border-white/[0.07] max-w-lg animate-fade-up" style={{ animationDelay: '0.4s' }}>
            {[
              { val: '16+', label: 'Modules' },
              { val: '4', label: 'Audience Tiers' },
              { val: 'AI', label: 'Powered Diagnostics' },
            ].map((s, i) => (
              <div key={i} className={`flex-1 p-5 ${i < 2 ? 'border-r border-white/[0.07]' : ''}`}>
                <div className="text-2xl sm:text-3xl font-serif text-[#CBFF00] mb-1">{s.val}</div>
                <div className="text-[10px] text-white/40 uppercase tracking-widest">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== SECTION 2: PAIN STORIES ========== */}
      <section ref={s2.ref} className={`py-20 px-6 md:px-12 bg-zinc-900 border-y border-white/[0.07] ${revealClass(s2.visible)}`}>
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          01 . The Real Problem
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="max-w-5xl">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif leading-tight mb-12 tracking-tight">
            Every EV workshop owner knows these problems
          </h2>

          <div className="grid md:grid-cols-3 gap-5">
            {[
              {
                label: 'Misdiagnosis',
                quote: '"Customer aaya, bola motor mein problem hai. Humne motor khola, 2 ghante lage. Problem BMS mein thi."',
                translation: 'Customer came, said motor problem. We opened the motor, spent 2 hours. Problem was actually in the BMS.',
                stat: '68% of EV repairs start with a wrong diagnosis',
                accent: 'border-red-500/40',
                statColor: 'text-red-400',
              },
              {
                label: 'No Service History',
                quote: '"Pichle mechanic ne kya kiya, koi record nahi. Sab zero se shuru karna padta hai har baar."',
                translation: 'No record of what the last mechanic did. Have to start from zero every time.',
                stat: 'Zero service history means repeated mistakes',
                accent: 'border-amber-500/40',
                statColor: 'text-amber-400',
              },
              {
                label: 'GST Compliance Chaos',
                quote: '"Tax filing mein har mahina 2 din jaate hain. HSN code galat ho gaya toh notice aa jaata hai."',
                translation: 'Tax filing takes 2 days every month. Wrong HSN code and you get a notice.',
                stat: 'Manual GST filing costs 24+ days per year',
                accent: 'border-blue-500/40',
                statColor: 'text-blue-400',
              },
            ].map((card, i) => (
              <div key={i} className={`bg-zinc-950 border-l-2 ${card.accent} border border-white/[0.05] p-6 flex flex-col`}>
                <div className="text-[10px] uppercase tracking-widest text-white/40 mb-4 font-mono">{card.label}</div>
                <p className="text-sm text-white/80 italic leading-relaxed mb-2">{card.quote}</p>
                <p className="text-xs text-white/30 mb-auto leading-relaxed">{card.translation}</p>
                <div className={`mt-5 pt-4 border-t border-white/[0.07] text-xs font-mono ${card.statColor}`}>
                  {card.stat}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== SECTION 3: FOUR AUDIENCES ========== */}
      <section ref={s3.ref} className={`py-20 px-6 md:px-12 ${revealClass(s3.visible)}`} id="segments">
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          02 . Built for the Entire EV Ecosystem
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="max-w-5xl">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif leading-tight mb-10 tracking-tight">
            One Platform. Four Roles. Complete Coverage.
          </h2>

          {/* Tabs */}
          <div className="flex flex-wrap gap-1 mb-8 border-b border-white/[0.07]">
            {audiences.map((a, i) => (
              <button
                key={i}
                onClick={() => setActiveAudience(i)}
                className={`px-5 py-3 text-xs uppercase tracking-wider font-medium transition border-b-2 -mb-px ${
                  i === activeAudience ? 'border-[#CBFF00] text-[#CBFF00]' : 'border-transparent text-white/40 hover:text-white/70'
                }`}
                data-testid={`audience-tab-${i}`}
              >
                {a.tab}
              </button>
            ))}
          </div>

          {/* Active tab content */}
          <div className="bg-zinc-900 border border-white/[0.07] p-6 sm:p-8">
            <p className="text-sm sm:text-base text-white/60 leading-relaxed mb-6">{audiences[activeAudience].body}</p>
            <div className="flex flex-wrap gap-2">
              {audiences[activeAudience].features.map((f, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs bg-[#CBFF00]/5 border border-[#CBFF00]/20 text-[#CBFF00] rounded-sm font-mono">
                  <Check className="w-3 h-3" /> {f}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ========== SECTION 4: EFI INTELLIGENCE ========== */}
      <section ref={s4.ref} id="solution" className={`py-20 px-6 md:px-12 bg-zinc-900 border-y border-white/[0.07] ${revealClass(s4.visible)}`}>
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          03 . Battwheels EFI{'\u2122'}
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="max-w-5xl">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif leading-tight mb-4 tracking-tight">
            Electrified Fault Intelligence
          </h2>
          <p className="text-base text-white/45 max-w-xl mb-12 leading-relaxed">
            The AI engine that learns from every repair.
          </p>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: Clock, title: 'Hours to Minutes', desc: 'Reduces diagnostic time from hours to minutes.' },
              { icon: TrendingUp, title: '90%+ Fix Rate', desc: 'First-time fix rate improves to 90%+ with guided workflows.' },
              { icon: Brain, title: 'Gets Smarter', desc: 'Every resolved ticket makes the next diagnosis smarter.' },
              { icon: Shield, title: 'All EV Brands', desc: 'Works across all EV brands. 2W, 3W, 4W.' },
            ].map((item, i) => {
              const Icon = item.icon;
              return (
                <div key={i} className="bg-zinc-950 border border-white/[0.05] p-6 hover:border-[#CBFF00]/30 hover:bg-[#CBFF00]/[0.02] transition group">
                  <Icon className="w-7 h-7 text-[#CBFF00] mb-4 group-hover:scale-110 transition-transform" />
                  <div className="text-sm font-bold mb-2">{item.title}</div>
                  <p className="text-xs text-white/40 leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========== SECTION 5: COMPLETE PLATFORM ========== */}
      <section ref={s5.ref} id="platform" className={`py-20 px-6 md:px-12 ${revealClass(s5.visible)}`}>
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          04 . Complete EV-Specific ERP
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="max-w-5xl">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif leading-tight mb-10 tracking-tight">
            Everything to run an EV service operation
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-px bg-white/[0.05] border border-white/[0.07]">
            {modules.map((mod, i) => {
              const Icon = mod.icon;
              return (
                <div key={i} className="bg-zinc-950 p-5 flex flex-col items-center text-center hover:bg-[#CBFF00]/[0.03] transition group" data-testid={`module-${i}`}>
                  <Icon className="w-5 h-5 text-white/30 mb-2 group-hover:text-[#CBFF00] transition" />
                  <span className="text-[11px] text-white/50 group-hover:text-white transition leading-tight">{mod.name}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========== SECTION 6: SOCIAL PROOF ========== */}
      <section ref={s6.ref} className={`py-20 px-6 md:px-12 bg-zinc-900 border-y border-white/[0.07] ${revealClass(s6.visible)}`}>
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          05 . Built for Scale
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="grid grid-cols-2 lg:grid-cols-4 border border-white/[0.07] max-w-4xl">
          {[
            { ref: c1.ref, val: c1.count, suffix: '+', label: 'Modules' },
            { ref: c2.ref, val: c2.count >= 10000 ? '10,000' : c2.count.toLocaleString(), suffix: '+', label: 'Fault Patterns in EFI Knowledge Base' },
            { ref: c3.ref, val: c3.count, suffix: '.9%', label: 'Uptime Target' },
            { ref: c4.ref, val: c4.count, suffix: '%', label: 'GST Compliant' },
          ].map((item, i) => (
            <div key={i} ref={item.ref} className={`p-6 sm:p-8 text-center ${i < 3 ? 'border-r border-white/[0.07]' : ''}`}>
              <div className="text-3xl sm:text-4xl font-serif text-[#CBFF00] mb-2">
                {typeof item.val === 'string' ? item.val : item.val}{item.suffix}
              </div>
              <div className="text-[10px] text-white/40 uppercase tracking-widest leading-tight">{item.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ========== SECTION 7: PRICING ========== */}
      <section ref={s7.ref} id="pricing" className={`py-20 px-6 md:px-12 ${revealClass(s7.visible)}`}>
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          06 . Simple, Transparent Pricing
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="max-w-5xl">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif leading-tight mb-10 tracking-tight">
            Start free. Scale as you grow.
          </h2>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                name: 'Free Trial', price: '\u20B90', period: 'for 14 days',
                features: ['10 AI diagnostic tokens', 'Core modules', '1 user'],
                cta: 'Start Free Trial', action: () => setShowSignup(true), highlight: false,
              },
              {
                name: 'Starter', price: '\u20B92,999', period: '/month',
                features: ['25 AI diagnostic tokens/mo', 'Core modules + Reports', 'Up to 3 users'],
                cta: 'Start Free Trial', action: () => setShowSignup(true), highlight: false,
              },
              {
                name: 'Professional', price: '\u20B95,999', period: '/month',
                features: ['100 AI diagnostic tokens/mo', 'All modules', 'Up to 10 users'],
                cta: 'Start Free Trial', action: () => setShowSignup(true), highlight: true,
              },
              {
                name: 'Enterprise', price: 'Custom', period: 'pricing',
                features: ['Unlimited AI tokens', 'All modules + API access', 'Unlimited users', 'Dedicated support'],
                cta: 'Book a Demo', action: () => setShowBookDemo(true), highlight: false,
              },
            ].map((plan, i) => (
              <div
                key={i}
                className={`relative bg-zinc-900 border p-6 flex flex-col ${
                  plan.highlight ? 'border-[#CBFF00]/40 ring-1 ring-[#CBFF00]/20' : 'border-white/[0.07]'
                }`}
                data-testid={`pricing-card-${i}`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[#CBFF00] text-zinc-900 text-[10px] font-bold uppercase tracking-wider rounded-sm">
                    Most Popular
                  </div>
                )}
                <div className="text-xs uppercase tracking-widest text-white/40 mb-3 font-mono">{plan.name}</div>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-3xl font-serif text-white">{plan.price}</span>
                  <span className="text-xs text-white/30">{plan.period}</span>
                </div>
                <ul className="space-y-2 mt-5 mb-6 flex-1">
                  {plan.features.map((f, j) => (
                    <li key={j} className="flex items-start gap-2 text-xs text-white/50">
                      <Check className="w-3.5 h-3.5 text-[#CBFF00] mt-0.5 shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={plan.action}
                  className={`w-full py-2.5 text-xs font-bold uppercase tracking-wide rounded-sm transition ${
                    plan.highlight
                      ? 'bg-[#CBFF00] text-zinc-900 hover:bg-[#d4ff33]'
                      : 'border border-white/10 text-white/60 hover:border-[#CBFF00] hover:text-[#CBFF00]'
                  }`}
                  data-testid={`pricing-cta-${i}`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== SECTION 8: INTELLIGENCE FLYWHEEL ========== */}
      <section ref={s8.ref} className={`py-20 px-6 md:px-12 bg-zinc-900 border-y border-white/[0.07] ${revealClass(s8.visible)}`}>
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-14 font-mono">
          07 . Compounding Intelligence
          <span className="flex-1 max-w-20 h-px bg-white/10" />
        </p>

        <div className="grid lg:grid-cols-2 gap-16 max-w-5xl items-center">
          <div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif leading-tight mb-6 tracking-tight">
              The Intelligence Flywheel
            </h2>
            <p className="text-sm text-white/45 leading-relaxed mb-6">
              Every ticket makes the platform smarter. Every repair makes the next one faster. This compounding loop is not a feature. It is the structural advantage.
            </p>
            <p className="text-lg font-serif italic text-[#CBFF00]">
              "This is our moat."
            </p>
          </div>

          <div className="border border-white/[0.07]">
            {[
              'More repairs completed',
              'More structured failure data captured',
              'Smarter EFI diagnostics',
              'Faster resolution times',
              'Happier customers, more referrals',
            ].map((step, idx) => (
              <div key={idx} className="flex items-center gap-5 p-5 border-b border-white/[0.07] last:border-b-0 hover:bg-[#CBFF00]/[0.03] transition">
                <span className="text-[10px] text-[#CBFF00] font-mono w-5">0{idx + 1}</span>
                <span className="text-sm font-medium flex-1">{step}</span>
                <span className="text-xs text-[#CBFF00] font-mono opacity-60">{'\u2193'}</span>
              </div>
            ))}
            <div className="flex items-center gap-5 p-5 bg-[#CBFF00]/10 border-t border-[#CBFF00]/20">
              <span className="text-[10px] text-[#CBFF00] font-mono w-5">{'\u221E'}</span>
              <span className="text-sm font-semibold text-[#CBFF00]">Stronger intelligence. Deeper moat.</span>
            </div>
          </div>
        </div>
      </section>

      {/* ========== SECTION 9: FINAL CTA ========== */}
      <section ref={s9.ref} id="vision" className={`relative py-28 px-6 md:px-12 text-center border-t border-white/[0.07] overflow-hidden ${revealClass(s9.visible)}`}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_80%_at_50%_100%,rgba(203,255,0,0.06)_0%,transparent_60%)]" />

        <div className="relative z-10 max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-serif leading-none mb-6 tracking-tight">
            Ready to run India's smartest<br /><em className="italic text-[#CBFF00]">EV workshop?</em>
          </h2>
          <p className="text-base text-white/45 max-w-xl mx-auto mb-12 leading-relaxed">
            Join the platform that gets better with every repair.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={() => setShowSignup(true)} className="px-10 py-4 text-sm font-bold uppercase tracking-wide bg-[#CBFF00] text-zinc-900 hover:bg-[#d4ff33] hover:shadow-[0_0_24px_rgba(203,255,0,0.3)] transition rounded-sm flex items-center justify-center gap-2" data-testid="cta-start-trial-btn">
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => setShowBookDemo(true)} className="px-10 py-4 text-sm font-semibold uppercase tracking-wide border border-white/10 hover:border-[#CBFF00] hover:text-[#CBFF00] transition rounded-sm" data-testid="cta-book-demo-btn">
              Book Enterprise Demo
            </button>
          </div>
        </div>
      </section>

      {/* ========== SECTION 10: FOOTER ========== */}
      <footer className="py-10 px-6 md:px-12 border-t border-white/[0.07] flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="text-xs text-white/20 font-mono">
          {'\u00A9'} 2026 Battwheels Technologies Pvt. Ltd.
        </div>
        <ul className="flex gap-8">
          {[['Docs', '/docs'], ['Privacy', '/privacy'], ['Terms', '/terms'], ['Contact', '/contact']].map(([label, href]) => (
            <li key={label}>
              <button onClick={() => navigate(href)} className="text-[11px] text-white/45 uppercase tracking-wider hover:text-[#CBFF00] transition font-mono">{label}</button>
            </li>
          ))}
        </ul>
      </footer>

      {/* Product Tour */}
      <ProductTour isOpen={showTour} onClose={() => setShowTour(false)} onStartTrial={() => setShowSignup(true)} />

      {/* Book Demo Modal */}
      {showBookDemo && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4" data-testid="book-demo-modal">
          <div className="bg-zinc-900 rounded-sm max-w-md w-full p-8 border border-white/10 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-bold">Book a Demo</h2>
                <p className="text-white/40 text-sm mt-1">We'll call you within 1 business day.</p>
              </div>
              <button onClick={() => { setShowBookDemo(false); setBookDemoSubmitted(false); }} className="text-white/40 hover:text-white transition" data-testid="close-book-demo-modal">
                <X className="w-5 h-5" />
              </button>
            </div>

            {bookDemoSubmitted ? (
              <div className="text-center py-8" data-testid="book-demo-success">
                <div className="w-12 h-12 bg-[#CBFF00]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-6 h-6 text-[#CBFF00]" />
                </div>
                <h3 className="text-lg font-bold mb-2">Request Received</h3>
                <p className="text-white/50 text-sm leading-relaxed">
                  Our team will call <strong className="text-white">{bookDemoData.phone}</strong> within 1 business day to schedule your demo.
                </p>
                <button
                  onClick={() => { setShowBookDemo(false); setBookDemoSubmitted(false); }}
                  className="mt-6 px-6 py-2.5 text-sm font-semibold uppercase tracking-wide bg-[#CBFF00] text-zinc-900 rounded-sm hover:bg-[#d4ff33] transition"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleBookDemoSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">Your Name *</label>
                  <input type="text" required placeholder="Rahul Sharma" value={bookDemoData.name}
                    onChange={(e) => setBookDemoData({ ...bookDemoData, name: e.target.value })}
                    className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition"
                    data-testid="demo-name-input" />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">Workshop / Company Name *</label>
                  <input type="text" required placeholder="Mumbai EV Service Center" value={bookDemoData.workshop_name}
                    onChange={(e) => setBookDemoData({ ...bookDemoData, workshop_name: e.target.value })}
                    className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition"
                    data-testid="demo-workshop-input" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-white/60 mb-1.5">City *</label>
                    <input type="text" required placeholder="Mumbai" value={bookDemoData.city}
                      onChange={(e) => setBookDemoData({ ...bookDemoData, city: e.target.value })}
                      className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition"
                      data-testid="demo-city-input" />
                  </div>
                  <div>
                    <label className="block text-sm text-white/60 mb-1.5">Phone *</label>
                    <input type="tel" required placeholder="+91 98765 43210" value={bookDemoData.phone}
                      onChange={(e) => setBookDemoData({ ...bookDemoData, phone: e.target.value })}
                      className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition"
                      data-testid="demo-phone-input" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">Vehicles serviced per month</label>
                  <select value={bookDemoData.vehicles_per_month}
                    onChange={(e) => setBookDemoData({ ...bookDemoData, vehicles_per_month: e.target.value })}
                    className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition"
                    data-testid="demo-vehicles-select">
                    <option value="<10">&lt;10 vehicles</option>
                    <option value="10-50">10 - 50 vehicles</option>
                    <option value="50-200">50 - 200 vehicles</option>
                    <option value="200+">200+ vehicles</option>
                  </select>
                </div>
                <button type="submit" disabled={bookDemoLoading}
                  className="w-full bg-[#CBFF00] hover:bg-[#d4ff33] text-zinc-900 py-3 rounded-sm font-bold text-sm uppercase tracking-wide transition disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
                  data-testid="demo-submit-btn">
                  {bookDemoLoading ? (
                    <><div className="w-4 h-4 border-2 border-zinc-900/30 border-t-zinc-900 rounded-full animate-spin" /> Submitting...</>
                  ) : (
                    <><ChevronRight className="w-4 h-4" /> Request Demo Call</>
                  )}
                </button>
                <p className="text-center text-white/30 text-xs pt-1">
                  No sales pressure. We'll walk you through the platform in 30 minutes.
                </p>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Signup Modal */}
      {showSignup && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-zinc-900 rounded-sm max-w-md w-full p-8 border border-white/10 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Create Your Organization</h2>
              <button onClick={() => setShowSignup(false)} className="text-white/40 hover:text-white transition">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Organization Name</label>
                <input type="text" name="name" value={formData.name} onChange={handleInputChange} required placeholder="e.g., Mumbai EV Service Center"
                  className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition" />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Your Name</label>
                <input type="text" name="admin_name" value={formData.admin_name} onChange={handleInputChange} required placeholder="John Doe"
                  className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition" />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Email Address</label>
                <input type="email" name="admin_email" value={formData.admin_email} onChange={handleInputChange} required placeholder="you@company.com"
                  className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition" />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Password</label>
                <input type="password" name="admin_password" value={formData.admin_password} onChange={handleInputChange} required minLength={6} placeholder="Min 6 characters"
                  className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">City</label>
                  <input type="text" name="city" value={formData.city} onChange={handleInputChange} placeholder="Mumbai"
                    className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition" />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">State</label>
                  <input type="text" name="state" value={formData.state} onChange={handleInputChange} placeholder="Maharashtra"
                    className="w-full px-4 py-3 bg-zinc-950 border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#CBFF00]/50 focus:border-transparent transition" />
                </div>
              </div>
              <button type="submit" disabled={isLoading}
                className="w-full bg-[#CBFF00] hover:bg-[#d4ff33] text-zinc-900 py-3 rounded-sm font-bold text-sm uppercase tracking-wide transition disabled:opacity-50 flex items-center justify-center gap-2 mt-6">
                {isLoading ? (
                  <><div className="w-4 h-4 border-2 border-zinc-900/30 border-t-zinc-900 rounded-full animate-spin" /> Creating...</>
                ) : (
                  <>Create Organization <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
              <p className="text-center text-white/40 text-sm pt-2">
                Already have an account?{' '}
                <button type="button" onClick={() => { setShowSignup(false); navigate('/login'); }} className="text-[#CBFF00] hover:underline">
                  Sign in
                </button>
              </p>
            </form>
          </div>
        </div>
      )}

      {/* Custom Styles */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&display=swap');
        .font-serif { font-family: 'DM Serif Display', serif; }
        @keyframes fade-up {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-up { animation: fade-up 0.7s ease both; }
      `}</style>
    </div>
  );
};

export default SaaSLanding;
