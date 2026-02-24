import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  Zap, ArrowRight, Check, ChevronRight, Building2, Users, Shield, 
  BarChart3, Globe, Brain, Cpu, Search, GitBranch, Compass, 
  FolderOpen, TrendingUp, Lock, Link2, Cloud, X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SaaSLanding = () => {
  const navigate = useNavigate();
  const [showSignup, setShowSignup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
    industry_type: 'ev_garage',
    city: '',
    state: ''
  });

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
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

  // EFI Flow Steps
  const efiSteps = [
    { num: '01', icon: Search, title: 'Auto-Detect', desc: 'Identifies vehicle make, model, and BMS architecture instantly.' },
    { num: '02', icon: GitBranch, title: 'Fault Mapping', desc: 'Maps DTCs to structured EV-specific fault trees.' },
    { num: '03', icon: BarChart3, title: 'Root Cause Rank', desc: 'Ranks probable root causes by likelihood.' },
    { num: '04', icon: Compass, title: 'Step Guidance', desc: 'Guides technicians through diagnostic workflows.' },
    { num: '05', icon: FolderOpen, title: 'Failure Cards', desc: 'Every resolution becomes reusable knowledge.' },
    { num: '06', icon: TrendingUp, title: 'Compound Learn', desc: 'The knowledge base grows continuously.' },
  ];

  // Problem Cards
  const problemCards = [
    { color: 'red', title: 'Fleet Operators', desc: 'Lose revenue every hour a vehicle sits idle — without visibility into failure patterns.' },
    { color: 'blue', title: 'OEMs', desc: 'Receive fragmented field reports with no structured intelligence to trace failures at scale.' },
    { color: 'orange', title: 'Battery Networks', desc: 'Face recurring pack failures with no root cause visibility — each incident treated as new.' },
    { color: 'volt', title: 'EV Workshops', desc: 'Technicians rely on personal experience. Every departure is expertise lost.' },
  ];

  // Segments
  const segments = [
    {
      label: 'Fleet Operators',
      title: 'Designed for Uptime, Not Repair',
      desc: 'For every hour a vehicle is idle, revenue is lost. Battwheels OS converts reactive maintenance into a proactive system.',
      features: ['Faster on-site resolution, reduced towing', 'Predictable diagnostic workflows', 'Historical failure trend analysis', 'Recurring fault pattern detection', 'Fleet performance becomes measurable']
    },
    {
      label: 'OEMs & Battery Manufacturers',
      title: 'Structured Field Intelligence',
      desc: "OEMs need structured, analyzable, real-world failure intelligence — mapped to models, components, and regions.",
      features: ['Model-specific failure mapping', 'Real-time field issue trends', 'Field-to-factory feedback loops', 'Pack-level lifecycle analytics', 'Component failure visibility']
    },
    {
      label: 'EV Workshops & Swap Networks',
      title: 'Standardize EV Expertise',
      desc: "EV service cannot depend on one technician's experience. Battwheels OS systematizes expertise.",
      features: ['AI-guided diagnosis', 'BMS anomaly detection', 'AMC, scheduling & ticket management', 'GST-compliant invoicing', 'Technician productivity tracking']
    }
  ];

  // ERP Modules
  const erpModules = [
    { label: 'Operations', title: 'Service Core', features: ['Ticketing & EV diagnostics', 'Vehicle history tracking', 'AMC management', 'Technician assignment'] },
    { label: 'Financial Engine', title: 'Revenue & Compliance', features: ['Estimates → Sales → Invoices', 'GST-compliant reporting', 'Inventory & stock control', 'Zoho Books integration'] },
    { label: 'Workforce', title: 'People & Performance', features: ['Employee management', 'Attendance & payroll', 'Productivity insights'] },
    { label: 'Intelligence Layer', title: 'EFI + AI Core', features: ['Failure Intelligence Engine', 'AI Assistant for diagnostics', 'Fault Tree Import', 'Continuous learning KB'], highlighted: true },
  ];

  // Flywheel Steps
  const flywheelSteps = [
    'More tickets resolved',
    'More structured Failure Cards created',
    'Smarter EFI diagnostics',
    'Faster resolution times',
    'Higher fleet uptime for customers',
  ];

  // Infrastructure Items
  const infraItems = [
    { icon: Lock, title: 'Data Isolation', desc: 'Organization-level data isolation with tenant-scoped EV intelligence.' },
    { icon: Link2, title: 'Encrypted APIs', desc: 'Secure connections to Zoho, OEM systems, and field tooling.' },
    { icon: Zap, title: 'Event-Driven', desc: 'Real-time event architecture ensures zero-latency updates.' },
    { icon: Cloud, title: 'Scalable Cloud', desc: "Multi-tenant SaaS built for India's EV adoption curve." },
  ];

  return (
    <div className="min-h-screen bg-[#080C0F] text-[#F4F6F0] font-sans overflow-x-hidden">
      {/* Grain Overlay */}
      <div className="fixed inset-0 pointer-events-none z-[999] opacity-60" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`
      }} />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 border-b border-white/[0.07] bg-[#080C0F]/85 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-[#C8FF00] rounded flex items-center justify-center overflow-hidden">
            <img src={LogoTransparent} alt="Battwheels OS" className="w-full h-full" />
          </div>
          <span className="text-lg font-extrabold tracking-tight">Battwheels OS</span>
        </div>
        
        <ul className="hidden md:flex gap-9 text-[13px] font-medium tracking-wider uppercase text-white/45">
          <li><a href="#solution" className="hover:text-white transition">EFI Engine</a></li>
          <li><a href="#segments" className="hover:text-white transition">Solutions</a></li>
          <li><a href="#platform" className="hover:text-white transition">Platform</a></li>
          <li><a href="#vision" className="hover:text-white transition">Vision</a></li>
        </ul>
        
        <div className="flex gap-3">
          <button onClick={() => navigate('/login')} className="px-5 py-2.5 text-[13px] font-semibold uppercase tracking-wide border border-white/10 hover:border-[#C8FF00] hover:text-[#C8FF00] transition rounded-sm">
            Book Demo
          </button>
          <button onClick={() => setShowSignup(true)} className="px-5 py-2.5 text-[13px] font-bold uppercase tracking-wide bg-[#C8FF00] text-[#080C0F] hover:bg-[#d4ff1a] hover:shadow-[0_0_24px_rgba(200,255,0,0.3)] transition rounded-sm">
            Free Trial
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col justify-center pt-36 pb-20 px-6 md:px-12 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_70%_50%,rgba(200,255,0,0.05)_0%,transparent_70%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_60%_at_10%_80%,rgba(26,255,228,0.03)_0%,transparent_60%)]" />
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
            backgroundSize: '80px 80px',
            maskImage: 'radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 80%)'
          }} />
        </div>

        <div className="relative z-10 max-w-6xl">
          {/* Status Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-16 text-[10px] tracking-widest text-[#C8FF00] border border-[#C8FF00]/20 bg-[#C8FF00]/5 rounded-sm font-mono">
            <span className="w-1.5 h-1.5 bg-[#C8FF00] rounded-full animate-pulse" />
            EFI Engine · Active · India
          </div>

          {/* Eyebrow */}
          <p className="flex items-center gap-3 text-[11px] tracking-[0.2em] uppercase text-[#C8FF00] mb-7 font-mono animate-fade-up">
            <span className="w-8 h-px bg-[#C8FF00]" />
            Battwheels OS
          </p>

          {/* Main Headline */}
          <h1 className="text-[clamp(52px,6vw,96px)] leading-none font-serif tracking-tight mb-8 animate-fade-up" style={{ animationDelay: '0.1s' }}>
            The Operating System<br />for <em className="italic text-[#C8FF00]">EV Reliability</em>
          </h1>

          {/* Subheadline */}
          <p className="text-lg text-white/45 max-w-xl mb-5 leading-relaxed animate-fade-up" style={{ animationDelay: '0.2s' }}>
            AI-powered diagnostics. Onsite-first service intelligence. Enterprise-grade ERP — built exclusively for electric vehicles.
          </p>

          {/* EFI Tag */}
          <p className="text-xs text-[#1AFFE4] tracking-wider font-mono opacity-80 mb-12 animate-fade-up" style={{ animationDelay: '0.3s' }}>
            Powered by Battwheels EFI™ — Proprietary EV Failure Intelligence Engine
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap gap-4 mb-20 animate-fade-up" style={{ animationDelay: '0.4s' }}>
            <button onClick={() => setShowSignup(true)} className="px-8 py-4 text-sm font-bold uppercase tracking-wide bg-[#C8FF00] text-[#080C0F] hover:bg-[#d4ff1a] hover:shadow-[0_0_24px_rgba(200,255,0,0.3)] transition rounded-sm flex items-center gap-2 animate-pulse-volt">
              Start 14-Day Free Trial
              <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => navigate('/login')} className="px-8 py-4 text-sm font-semibold uppercase tracking-wide border border-white/10 hover:border-[#C8FF00] hover:text-[#C8FF00] transition rounded-sm">
              Book Enterprise Demo
            </button>
          </div>

          {/* Metrics */}
          <div className="flex border border-white/[0.07] max-w-xl animate-fade-up" style={{ animationDelay: '0.5s' }}>
            <div className="flex-1 p-6 border-r border-white/[0.07]">
              <div className="text-4xl font-serif text-[#C8FF00] mb-1">100%</div>
              <div className="text-[11px] text-white/45 uppercase tracking-widest">Onsite resolution goal</div>
            </div>
            <div className="flex-1 p-6 border-r border-white/[0.07]">
              <div className="text-4xl font-serif text-[#C8FF00] mb-1">EV-only</div>
              <div className="text-[11px] text-white/45 uppercase tracking-widest">Trained intelligence</div>
            </div>
            <div className="flex-1 p-6">
              <div className="text-4xl font-serif text-[#C8FF00] mb-1">∞</div>
              <div className="text-[11px] text-white/45 uppercase tracking-widest">Compounding knowledge</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 px-6 md:px-12 bg-[#0D1317] border-y border-white/[0.07]">
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-16 font-mono">
          01 · The Real Problem
          <span className="flex-1 max-w-20 h-px bg-[#111820]/10" />
        </p>

        <div className="grid lg:grid-cols-2 gap-0 max-w-6xl">
          <div className="lg:pr-20 lg:border-r border-white/[0.07]">
            <h2 className="text-[clamp(36px,4vw,60px)] font-serif leading-tight mb-8 tracking-tight">
              EV Downtime Is the Hidden Cost of Electrification
            </h2>
            <p className="text-base text-white/45 leading-relaxed mb-6">
              Electric vehicles are fundamentally different. Battery architectures vary. Motor controllers vary. BMS logic varies. Firmware updates change vehicle behavior. Diagnostic standards are inconsistent across manufacturers.
            </p>
            <p className="text-base text-white/45 leading-relaxed mb-6">
              Most workshops still treat EVs like upgraded ICE vehicles. <span className="text-white">They are not.</span>
            </p>
            <p className="text-base text-white/45 leading-relaxed">
              EV reliability cannot depend on guesswork.
            </p>
          </div>

          <div className="lg:pl-20 pt-12 lg:pt-0 flex flex-col gap-5">
            {problemCards.map((card, idx) => (
              <div key={idx} className="relative bg-[#111820] border border-white/[0.07] p-5 pl-7 overflow-hidden">
                <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${
                  card.color === 'red' ? 'bg-[#FF3B2F]' : 
                  card.color === 'blue' ? 'bg-[#1AFFE4]' : 
                  card.color === 'orange' ? 'bg-[#FF8C00]' : 'bg-[#C8FF00]'
                }`} />
                <div className="text-xs font-semibold uppercase tracking-widest text-white/45 mb-2">{card.title}</div>
                <p className="text-[15px] leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* EFI Solution Section */}
      <section id="solution" className="relative py-24 px-6 md:px-12 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_100%,rgba(200,255,0,0.04)_0%,transparent_70%)]" />
        
        <div className="relative z-10 max-w-6xl">
          <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-16 font-mono">
            02 · EV Failure Intelligence
            <span className="flex-1 max-w-20 h-px bg-[#111820]/10" />
          </p>

          <h2 className="text-[clamp(36px,4vw,64px)] font-serif leading-tight mb-6 tracking-tight max-w-3xl">
            Every EV Failure Becomes Structured Intelligence
          </h2>

          <p className="text-[17px] text-white/45 max-w-xl leading-relaxed mb-4">
            Battwheels EFI is our proprietary AI-powered EV Failure Intelligence Engine. It does not generalize from automotive data.
          </p>

          <p className="text-[13px] text-[#C8FF00] tracking-wider font-mono opacity-90 mb-16">
            EV-only. EV-specific. EV-trained.
          </p>

          {/* EFI Flow */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 border border-white/[0.07] mb-20">
            {efiSteps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className={`relative p-8 border-r border-white/[0.07] last:border-r-0 hover:bg-[#C8FF00]/10 transition group ${idx >= 3 ? 'border-t lg:border-t-0' : ''}`}>
                  {idx < 5 && (
                    <div className="absolute -right-2.5 top-1/2 -translate-y-1/2 w-5 h-5 bg-[#080C0F] border border-white/10 rounded-full flex items-center justify-center text-[10px] text-[#C8FF00] z-10 font-mono hidden lg:flex">
                      →
                    </div>
                  )}
                  <div className="text-[10px] text-white/20 tracking-widest font-mono mb-4">{step.num}</div>
                  <Icon className="w-6 h-6 text-[#C8FF00] mb-3" />
                  <div className="text-[13px] font-bold uppercase tracking-wide mb-2">{step.title}</div>
                  <p className="text-xs text-white/45 leading-relaxed">{step.desc}</p>
                </div>
              );
            })}
          </div>

          <p className="text-[22px] font-serif text-white/45 max-w-3xl leading-relaxed">
            This is not just diagnostics.<br />
            <span className="text-white">This is EV intelligence infrastructure.</span>
          </p>
        </div>
      </section>

      {/* Segments Section */}
      <section id="segments" className="py-24 px-6 md:px-12 bg-[#0D1317] border-y border-white/[0.07]">
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-16 font-mono">
          03 · Built For Every Stakeholder
          <span className="flex-1 max-w-20 h-px bg-[#111820]/10" />
        </p>

        <div className="grid lg:grid-cols-3 border border-white/[0.07] max-w-6xl">
          {segments.map((seg, idx) => (
            <div key={idx} className={`relative p-10 ${idx < 2 ? 'lg:border-r border-white/[0.07]' : ''} group hover:bg-[#111820]/[0.02] transition overflow-hidden`}>
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#C8FF00] scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
              <div className="text-[10px] tracking-[0.2em] uppercase text-[#C8FF00] mb-6 font-mono">{seg.label}</div>
              <h3 className="text-[28px] font-serif mb-5 leading-tight">{seg.title}</h3>
              <p className="text-sm text-white/45 leading-relaxed mb-8">{seg.desc}</p>
              <ul className="space-y-2.5">
                {seg.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-[13px] text-white/45 leading-relaxed">
                    <span className="text-[#C8FF00] font-mono text-xs mt-0.5">→</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ERP Platform Section */}
      <section id="platform" className="py-24 px-6 md:px-12">
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-16 font-mono">
          04 · Complete EV-Specific ERP
          <span className="flex-1 max-w-20 h-px bg-[#111820]/10" />
        </p>

        <div className="grid lg:grid-cols-3 gap-20 max-w-6xl items-start">
          <div>
            <h2 className="text-[clamp(36px,3.5vw,54px)] font-serif leading-tight mb-6 tracking-tight">
              Everything to Run an EV Service Operation
            </h2>
            <p className="text-[15px] text-white/45 leading-relaxed mb-4">
              From service tickets to payroll, Battwheels OS is a complete EV-focused ERP platform — not a generic workshop tool with an EV label.
            </p>
            <p className="text-[15px] text-white/45 leading-relaxed mb-8">
              One platform. One intelligence layer. One EV ecosystem.
            </p>
            <button onClick={() => setShowSignup(true)} className="px-6 py-3 text-sm font-bold uppercase tracking-wide bg-[#C8FF00] text-[#080C0F] hover:bg-[#d4ff1a] transition rounded-sm flex items-center gap-2">
              Explore the Platform
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="lg:col-span-2 grid grid-cols-2 gap-px bg-[#111820]/[0.07] border border-white/[0.07]">
            {erpModules.map((mod, idx) => (
              <div key={idx} className={`bg-[#0D1317] p-7 hover:bg-[#111820] transition ${mod.highlighted ? 'border-t-2 border-t-[#C8FF00]' : ''}`}>
                <div className="text-[9px] tracking-[0.2em] uppercase text-[#C8FF00] mb-3.5 font-mono">{mod.label}</div>
                <div className="text-base font-bold mb-3.5 tracking-tight">{mod.title}</div>
                <ul className="space-y-1.5">
                  {mod.features.map((f, i) => (
                    <li key={i} className="flex items-center gap-2 text-xs text-white/45">
                      <span className="text-[#C8FF00] text-lg leading-none">·</span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Flywheel Section */}
      <section className="py-24 px-6 md:px-12 bg-[#0D1317] border-y border-white/[0.07]">
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-16 font-mono">
          05 · Compounding Intelligence
          <span className="flex-1 max-w-20 h-px bg-[#111820]/10" />
        </p>

        <div className="grid lg:grid-cols-2 gap-20 max-w-6xl items-center">
          <div>
            <h2 className="text-[clamp(36px,3.5vw,54px)] font-serif leading-tight mb-6 tracking-tight">
              The Intelligence Flywheel
            </h2>
            <p className="text-base text-white/45 leading-relaxed mb-8">
              Every ticket makes the platform smarter. Every repair makes the next one faster. This compounding loop is not a feature — it is a structural advantage that widens over time.
            </p>
            <p className="text-[22px] font-serif italic text-[#C8FF00]">
              "This is our moat."
            </p>
          </div>

          <div className="border border-white/[0.07]">
            {flywheelSteps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-5 p-5 border-b border-white/[0.07] last:border-b-0 hover:bg-[#C8FF00]/10 transition">
                <span className="text-[10px] text-[#C8FF00] font-mono w-5">0{idx + 1}</span>
                <span className="text-sm font-semibold flex-1">{step}</span>
                <span className="text-xs text-[#C8FF00] font-mono opacity-60">↓</span>
              </div>
            ))}
            <div className="flex items-center gap-5 p-5 bg-[#C8FF00]/10 border-t border-[#C8FF00]/20">
              <span className="text-[10px] text-[#C8FF00] font-mono w-5">∞</span>
              <span className="text-sm font-semibold text-[#C8FF00]">Stronger intelligence. Deeper moat.</span>
            </div>
          </div>
        </div>
      </section>

      {/* Infrastructure Section */}
      <section className="py-24 px-6 md:px-12">
        <p className="flex items-center gap-4 text-[10px] tracking-[0.25em] uppercase text-white/45 mb-16 font-mono">
          06 · Enterprise-Grade Architecture
          <span className="flex-1 max-w-20 h-px bg-[#111820]/10" />
        </p>

        <div className="max-w-6xl">
          <p className="text-[clamp(28px,3vw,42px)] font-serif mb-12 max-w-2xl leading-tight tracking-tight">
            Built for 5 Vehicles or 50,000. The Platform Scales with You.
          </p>

          <div className="grid grid-cols-2 lg:grid-cols-4 border border-white/[0.07]">
            {infraItems.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div key={idx} className={`p-8 ${idx < 3 ? 'border-r border-white/[0.07]' : ''} hover:bg-[#C8FF00]/10 transition`}>
                  <Icon className="w-7 h-7 text-[#C8FF00] mb-4" />
                  <div className="text-[13px] font-bold uppercase tracking-wide mb-2">{item.title}</div>
                  <p className="text-xs text-white/45 leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Vision / CTA Section */}
      <section id="vision" className="relative py-32 px-6 md:px-12 text-center border-t border-white/[0.07] overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_80%_at_50%_100%,rgba(200,255,0,0.06)_0%,transparent_60%)]" />
        
        <div className="relative z-10 max-w-4xl mx-auto">
          <p className="text-[10px] tracking-[0.25em] uppercase text-[#C8FF00] mb-8 font-mono">07 · Our Vision</p>
          
          <h2 className="text-[clamp(48px,6vw,96px)] font-serif leading-none mb-8 tracking-tight">
            Power the Future of<br /><em className="italic text-[#C8FF00]">EV Reliability</em>
          </h2>
          
          <p className="text-lg text-white/45 max-w-2xl mx-auto mb-16 leading-relaxed">
            We are building India's EV Onsite Reliability Infrastructure. As adoption accelerates, reliability must scale with it. Battwheels OS is the operating system for that future.
          </p>

          <div className="flex flex-wrap justify-center gap-x-12 gap-y-3 mb-20">
            {['No-towing-first philosophy', 'Technician-guided field diagnostics', 'Model-aware AI assistance', 'EV-only structured intelligence'].map((pillar, idx) => (
              <span key={idx} className="flex items-center gap-2 text-xs text-white/45 font-mono tracking-wider">
                <Check className="w-4 h-4 text-[#C8FF00]" />
                {pillar}
              </span>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={() => setShowSignup(true)} className="px-10 py-4 text-sm font-bold uppercase tracking-wide bg-[#C8FF00] text-[#080C0F] hover:bg-[#d4ff1a] hover:shadow-[0_0_24px_rgba(200,255,0,0.3)] transition rounded-sm flex items-center justify-center gap-2">
              Start Your Free Trial
              <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => navigate('/login')} className="px-10 py-4 text-sm font-semibold uppercase tracking-wide border border-white/10 hover:border-[#C8FF00] hover:text-[#C8FF00] transition rounded-sm">
              Request Enterprise Consultation
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-6 md:px-12 border-t border-white/[0.07] flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="text-xs text-white/20 font-mono">
          © 2026 Battwheels Services Private Limited · EFI Engine v2 · India
        </div>
        <ul className="flex gap-8">
          {[['Docs', '/docs'], ['Privacy', '/privacy'], ['Terms', '/terms'], ['Contact', '/contact']].map(([label, href]) => (
            <li key={label}>
              <button onClick={() => navigate(href)} className="text-[11px] text-white/45 uppercase tracking-wider hover:text-[#C8FF00] transition font-mono">{label}</button>
            </li>
          ))}
        </ul>
      </footer>

      {/* Signup Modal */}
      {showSignup && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-[#111820] rounded-sm max-w-md w-full p-8 border border-white/10 shadow-2xl">
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
                  className="w-full px-4 py-3 bg-[#080C0F] border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#C8FF00]/50 focus:border-transparent transition" />
              </div>
              
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Your Name</label>
                <input type="text" name="admin_name" value={formData.admin_name} onChange={handleInputChange} required placeholder="John Doe"
                  className="w-full px-4 py-3 bg-[#080C0F] border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#C8FF00]/50 focus:border-transparent transition" />
              </div>
              
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Email Address</label>
                <input type="email" name="admin_email" value={formData.admin_email} onChange={handleInputChange} required placeholder="you@company.com"
                  className="w-full px-4 py-3 bg-[#080C0F] border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#C8FF00]/50 focus:border-transparent transition" />
              </div>
              
              <div>
                <label className="block text-sm text-white/60 mb-1.5">Password</label>
                <input type="password" name="admin_password" value={formData.admin_password} onChange={handleInputChange} required minLength={6} placeholder="Min 6 characters"
                  className="w-full px-4 py-3 bg-[#080C0F] border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#C8FF00]/50 focus:border-transparent transition" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">City</label>
                  <input type="text" name="city" value={formData.city} onChange={handleInputChange} placeholder="Mumbai"
                    className="w-full px-4 py-3 bg-[#080C0F] border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#C8FF00]/50 focus:border-transparent transition" />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-1.5">State</label>
                  <input type="text" name="state" value={formData.state} onChange={handleInputChange} placeholder="Maharashtra"
                    className="w-full px-4 py-3 bg-[#080C0F] border border-white/10 rounded-sm text-white placeholder-white/30 focus:ring-2 focus:ring-[#C8FF00]/50 focus:border-transparent transition" />
                </div>
              </div>
              
              <button type="submit" disabled={isLoading}
                className="w-full bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] py-3 rounded-sm font-bold text-sm uppercase tracking-wide transition disabled:opacity-50 flex items-center justify-center gap-2 mt-6">
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#080C0F]/30 border-t-[#080C0F] rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    Create Organization
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
              
              <p className="text-center text-white/40 text-sm pt-2">
                Already have an account?{' '}
                <button type="button" onClick={() => { setShowSignup(false); navigate('/login'); }} className="text-[#C8FF00] hover:underline">
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
        
        @keyframes pulse-volt {
          0%, 100% { box-shadow: 0 0 0 0 rgba(200,255,0,0.3); }
          50% { box-shadow: 0 0 20px 4px rgba(200,255,0,0.3); }
        }
        
        .animate-fade-up { animation: fade-up 0.7s ease both; }
        .animate-pulse-volt { animation: pulse-volt 3s 2s ease-in-out infinite; }
      `}</style>
    </div>
  );
};

export default SaaSLanding;
