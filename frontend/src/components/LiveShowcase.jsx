import React, { useState, useEffect, useRef } from 'react';

/* ═══════════════════════════════════════════════════════
   ANIMATION SYSTEM
   ═══════════════════════════════════════════════════════ */

function useScrollAnimation() {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setIsVisible(true); },
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, isVisible];
}

function Animate({ show, delay = 0, type = 'fadeInUp', children, className = '' }) {
  return (
    <div
      className={className}
      style={{
        opacity: show ? undefined : 0,
        animation: show ? `${type} 0.6s ease-out ${delay}s both` : 'none',
      }}
    >
      {children}
    </div>
  );
}

function Counter({ to, show, delay = 0, prefix = '', suffix = '' }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!show) return;
    const timer = setTimeout(() => {
      let n = 0;
      const step = Math.ceil(to / 40);
      const id = setInterval(() => {
        n = Math.min(n + step, to);
        setVal(n);
        if (n >= to) clearInterval(id);
      }, 30);
      return () => clearInterval(id);
    }, delay * 1000);
    return () => clearTimeout(timer);
  }, [show, to, delay]);
  return <span>{prefix}{val.toLocaleString('en-IN')}{suffix}</span>;
}

/* ═══════════════════════════════════════════════════════
   PANEL 1 — Operations (Ticket Flow)
   ═══════════════════════════════════════════════════════ */
function OperationsPanel({ onOpen }) {
  const [ref, vis] = useScrollAnimation();
  return (
    <div ref={ref} className="max-w-[600px] mx-auto" data-testid="showcase-panel-operations">
      <div className="flex justify-end mb-3">
        <span className="text-[9px] font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/30">
          Owner / Manager
        </span>
      </div>
      <div className="bg-[#0f1419] rounded-2xl border border-white/5 p-5 sm:p-7">

      <Animate show={vis} delay={0.3}>
        <div className="text-[9px] text-white/25 uppercase tracking-[0.2em] font-mono mb-4">
          Battwheels OS &middot; Volt Motors EV Service
        </div>
      </Animate>

      <Animate show={vis} delay={0.6}>
        <div className="bg-[#161b22] rounded-xl p-4 border border-white/[0.04]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] text-white/80 font-medium">Rajesh Kumar &middot; Ola S1 Pro</span>
            <span className="text-[8px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/30">HIGH</span>
          </div>
          <p className="text-[11px] text-white/40 leading-relaxed">Battery not charging after firmware update</p>

          <Animate show={vis} delay={1.2} type="slideInRight">
            <div className="mt-3 flex items-center gap-2 text-[12px] text-teal-400 font-medium">
              <span className="text-white/20">&rarr;</span> Assigned: Ankit Verma
            </div>
          </Animate>

          <Animate show={vis} delay={1.8} type="slideInRight">
            <div className="mt-1.5 flex items-center gap-2 text-[12px] text-amber-400 font-medium"
              style={{ animation: vis ? 'pulseGlow 2.5s ease-in-out infinite 2.5s' : 'none' }}>
              <span className="text-white/20">&rarr;</span> SLA: 3h 42m
            </div>
          </Animate>

          <Animate show={vis} delay={2.4} type="scaleIn">
            <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider bg-teal-500/10 text-teal-400 border border-teal-500/30"
              style={{ animation: vis ? 'pulseGlow 2.5s ease-in-out infinite 3s' : 'none' }}>
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
              Technician Assigned
            </div>
          </Animate>
        </div>
      </Animate>

      </div>
      <Animate show={vis} delay={2.8}>
        <p className="text-white/35 text-sm mt-5 leading-relaxed">Complaint to assignment in under 60 seconds.</p>
      </Animate>
      <Animate show={vis} delay={3.0}>
        <div className="mt-4 space-y-2 text-xs leading-relaxed">
          <p className="text-white/25"><span className="text-red-400/60">Without Battwheels:</span> WhatsApp message → forgotten → customer calls back → 2 days wasted</p>
          <p className="text-white/25"><span className="text-teal-400/60">With Battwheels:</span> Complaint → assigned → tracked → 60 seconds</p>
        </div>
      </Animate>
      <Animate show={vis} delay={3.0}>
        <button onClick={onOpen} className="text-[#CBFF00] text-sm mt-2 hover:underline transition" data-testid="showcase-link-operations">
          See all 15 steps &rarr;
        </button>
      </Animate>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   PANEL 2 — EVFI™ Diagnosis (AI Working)
   ═══════════════════════════════════════════════════════ */
function DiagnosisPanel({ onOpen }) {
  const [ref, vis] = useScrollAnimation();
  return (
    <div ref={ref} className="max-w-[600px] mx-auto" data-testid="showcase-panel-efi">
      <div className="flex justify-end mb-3">
        <span className="text-[9px] font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-[#CBFF00]/15 text-[#0f1419] border border-[#CBFF00]/40" style={{ backgroundColor: 'rgba(203,255,0,0.85)' }}>
          Technician
        </span>
      </div>
      <div className="bg-[#0f1419] rounded-2xl border border-white/5 border-l-4 border-l-[#CBFF00] p-5 sm:p-7">

      <Animate show={vis} delay={0.3}>
        <div className="text-[11px] font-bold text-[#CBFF00] tracking-wider font-mono mb-1">
          &#9889; BATTWHEELS EVFI&trade; DIAGNOSTIC REPORT
        </div>
      </Animate>
      <Animate show={vis} delay={0.5}>
        <div className="text-[10px] text-white/40 mb-4">Vehicle: Ola S1 Pro (2W) &middot; 48V System</div>
      </Animate>

      {/* Safety Block */}
      <Animate show={vis} delay={0.8}>
        <div className="border-l-3 border-l-red-500 bg-red-900/20 rounded-r-lg px-3.5 py-3 mb-4" style={{ borderLeftWidth: '3px', borderLeftColor: '#ef4444' }}>
          <div className="text-[10px] font-semibold text-red-300">&#9889; SAFETY: 48V system. Insulated gloves required.</div>
        </div>
      </Animate>

      {/* Diagnostic Steps */}
      <div className="space-y-2">
        <Animate show={vis} delay={1.5}>
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/[0.06] border border-emerald-500/20">
            <span className="text-[11px] text-white/70 flex items-center gap-2">
              <span className="text-emerald-400">&#9989;</span> 12V battery load test
            </span>
            <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">PASS</span>
          </div>
        </Animate>

        <Animate show={vis} delay={2.2}>
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-red-500/[0.06] border border-red-500/20">
            <span className="text-[11px] text-white/70 flex items-center gap-2">
              <span className="text-red-400">&#10060;</span> DC-DC converter output
            </span>
            <span className="text-[9px] font-bold uppercase tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded">FAIL</span>
          </div>
        </Animate>

        <Animate show={vis} delay={2.9}>
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05]">
            <span className="text-[11px] text-white/30 flex items-center gap-2">
              <span>&#11036;</span> HV interlock inspection
            </span>
          </div>
        </Animate>

        <Animate show={vis} delay={3.2}>
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05]">
            <span className="text-[11px] text-white/30 flex items-center gap-2">
              <span>&#11036;</span> BMS communication check
            </span>
          </div>
        </Animate>
      </div>

      {/* Root Cause */}
      <Animate show={vis} delay={3.8}>
        <div className="mt-4 bg-[#CBFF00]/[0.06] border border-[#CBFF00]/20 rounded-lg p-3">
          <span className="text-[11px] text-[#CBFF00] font-medium">&#128295; Root Cause: DC-DC converter failure</span>
        </div>
      </Animate>

      {/* Confidence */}
      <Animate show={vis} delay={4.2}>
        <div className="mt-3 text-right">
          <span className="text-[10px] text-white/30 mr-1.5">Confidence:</span>
          <span className="text-base font-bold text-[#CBFF00]">
            <Counter to={87} show={vis} delay={4.2} suffix="%" />
          </span>
        </div>
      </Animate>

      </div>
      <Animate show={vis} delay={4.8}>
        <p className="text-white/50 text-sm mt-5 leading-relaxed italic">Your technician opens the ticket. EVFI{'\u2122'} tells them exactly what to check, in what order, with safety warnings built in. No guessing. No wasted hours.</p>
      </Animate>
      <Animate show={vis} delay={4.8}>
        <p className="text-white/35 text-sm mt-2 leading-relaxed">10x faster diagnosis & resolution than manual troubleshooting. 84% first-visit fix rate.</p>
      </Animate>
      <Animate show={vis} delay={4.8}>
        <button onClick={onOpen} className="text-[#CBFF00] text-sm mt-2 hover:underline transition" data-testid="showcase-link-efi">
          See all 15 steps &rarr;
        </button>
      </Animate>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   PANEL 3 — Billing (Invoice with GST)
   ═══════════════════════════════════════════════════════ */
function BillingPanel({ onOpen }) {
  const [ref, vis] = useScrollAnimation();
  return (
    <div ref={ref} className="max-w-[600px] mx-auto" data-testid="showcase-panel-billing">
      <div className="flex justify-end mb-3">
        <span className="text-[9px] font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
          Accountant
        </span>
      </div>
      <div className="bg-[#0f1419] rounded-2xl border border-white/5 border-r-4 border-r-amber-500 p-5 sm:p-7">

      <Animate show={vis} delay={0.3}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-bold text-white/60 tracking-wider font-mono">INVOICE #INV-2026-0847</span>
          <span className="text-[9px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded font-medium">GST COMPLIANT &#10003;</span>
        </div>
      </Animate>
      <Animate show={vis} delay={0.5}>
        <div className="text-[10px] text-white/30 mb-4">Rajesh Kumar &middot; GSTIN: 07AABCR1234R1Z1</div>
      </Animate>

      {/* Line Items */}
      <Animate show={vis} delay={1.0} type="slideInRight">
        <div className="flex items-center justify-between p-3 rounded-lg bg-[#161b22] border border-white/[0.04] mb-2">
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-white/70">DC-DC Converter</span>
            <span className="text-[9px] text-white/25 font-mono">HSN: 85044090</span>
          </div>
          <span className="text-[13px] text-white font-medium">&#8377;<Counter to={4200} show={vis} delay={1.0} /></span>
        </div>
      </Animate>

      <Animate show={vis} delay={1.8} type="slideInRight">
        <div className="flex items-center justify-between p-3 rounded-lg bg-[#161b22] border border-white/[0.04] mb-3">
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-white/70">Diagnostic Labour</span>
            <span className="text-[9px] text-white/25 font-mono">SAC: 998714</span>
          </div>
          <span className="text-[13px] text-white font-medium">&#8377;<Counter to={500} show={vis} delay={1.8} /></span>
        </div>
      </Animate>

      {/* Divider */}
      <Animate show={vis} delay={2.5}>
        <div className="border-t border-white/[0.06] my-2" />
      </Animate>

      {/* Calculations */}
      <div className="space-y-1.5">
        <Animate show={vis} delay={2.7}>
          <div className="flex justify-between text-[11px] px-1">
            <span className="text-white/30">Subtotal</span>
            <span className="text-white/60">&#8377;<Counter to={4700} show={vis} delay={2.7} /></span>
          </div>
        </Animate>
        <Animate show={vis} delay={3.0}>
          <div className="flex justify-between text-[11px] px-1">
            <span className="text-white/30">CGST @ 9%</span>
            <span className="text-white/60">&#8377;<Counter to={423} show={vis} delay={3.0} /></span>
          </div>
        </Animate>
        <Animate show={vis} delay={3.2}>
          <div className="flex justify-between text-[11px] px-1">
            <span className="text-white/30">SGST @ 9%</span>
            <span className="text-white/60">&#8377;<Counter to={423} show={vis} delay={3.2} /></span>
          </div>
        </Animate>
        <Animate show={vis} delay={3.5}>
          <div className="flex justify-between items-center px-1 pt-2 border-t border-white/[0.06]"
            style={{ animation: vis ? 'pulseGlow 2.5s ease-in-out infinite 4s' : 'none' }}>
            <span className="text-sm font-bold text-white">GRAND TOTAL</span>
            <span className="text-xl font-bold text-[#CBFF00]">&#8377;<Counter to={5546} show={vis} delay={3.5} /></span>
          </div>
        </Animate>
      </div>

      {/* Action Buttons */}
      <Animate show={vis} delay={4.0}>
        <div className="flex gap-2 mt-4">
          {['PDF', 'Email', 'WhatsApp'].map((label) => (
            <div key={label} className="flex-1 bg-[#161b22] border border-white/[0.05] rounded-lg py-2 text-center text-[10px] text-white/40 font-medium">
              {label}
            </div>
          ))}
        </div>
      </Animate>

      </div>
      <Animate show={vis} delay={4.3}>
        <p className="text-white/35 text-sm mt-5 leading-relaxed">Estimate → customer approved → one-click invoice → GST auto-calculated with HSN/SAC → GSTR-1 & 3B ready → filed. The complete digital billing chain.</p>
      </Animate>
      <Animate show={vis} delay={4.3}>
        <button onClick={onOpen} className="text-[#CBFF00] text-sm mt-2 hover:underline transition" data-testid="showcase-link-billing">
          See all 15 steps &rarr;
        </button>
      </Animate>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   PANEL 4 — Fleet Management
   ═══════════════════════════════════════════════════════ */
function FleetPanel({ onOpen }) {
  const [ref, vis] = useScrollAnimation();
  const stats = [
    { label: 'Vehicles', to: 24, color: '#3b82f6', delay: 0.8 },
    { label: 'Open Tickets', to: 3, color: '#f59e0b', delay: 1.1 },
    { label: 'Resolved/Mo', to: 12, color: '#10b981', delay: 1.4 },
    { label: 'AMC Due', to: 1, color: '#a855f7', delay: 1.7 },
  ];

  return (
    <div ref={ref} className="max-w-[600px] mx-auto" data-testid="showcase-panel-fleet">
      <div className="flex justify-end mb-3">
        <span className="text-[9px] font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
          Fleet Operator
        </span>
      </div>
      <div className="bg-[#0f1419] rounded-2xl border border-white/5 border-t-4 border-t-blue-500 p-5 sm:p-7">

      <Animate show={vis} delay={0.3}>
        <div className="text-[11px] text-white/25 uppercase tracking-[0.15em] font-mono mb-0.5">&#128666; Fleet Dashboard</div>
        <div className="text-[13px] text-white/60 font-medium mb-4">Delhi EV Fleet Pvt Ltd</div>
      </Animate>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
        {stats.map((s) => (
          <Animate key={s.label} show={vis} delay={s.delay} type="scaleIn">
            <div className="bg-[#161b22] border border-white/[0.04] rounded-xl p-3 text-center">
              <div className="text-2xl font-bold" style={{ color: s.color }}>
                <Counter to={s.to} show={vis} delay={s.delay} />
              </div>
              <div className="text-[8px] text-white/25 uppercase tracking-wider mt-1 leading-tight">{s.label}</div>
            </div>
          </Animate>
        ))}
      </div>

      {/* Recent Ticket */}
      <Animate show={vis} delay={2.2}>
        <div className="bg-[#161b22] border border-white/[0.04] rounded-xl p-3.5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] text-white/70 font-medium">Bajaj Chetak DL03IJ7890</span>
            <span className="inline-flex items-center gap-1 text-[9px] text-amber-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              Work In Progress
            </span>
          </div>
          <p className="text-[10px] text-white/35">Motor controller fault</p>
          <p className="text-[10px] text-white/25 mt-1">Tech: Ravi Kumar</p>
        </div>
      </Animate>

      {/* Buttons */}
      <Animate show={vis} delay={3.0}>
        <div className="flex gap-2 mt-4">
          <div className="flex-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg py-2.5 text-center text-[11px] text-emerald-400 font-medium">
            + Raise Ticket
          </div>
          <div className="flex-1 bg-[#161b22] border border-white/[0.05] rounded-lg py-2.5 text-center text-[11px] text-white/40 font-medium">
            Bulk Payment
          </div>
        </div>
      </Animate>

      </div>
      <Animate show={vis} delay={3.3}>
        <p className="text-white/35 text-sm mt-5 leading-relaxed">All vehicles. All tickets. One dashboard. Bulk payment for multiple invoices.</p>
      </Animate>
      <Animate show={vis} delay={3.3}>
        <button onClick={onOpen} className="text-[#CBFF00] text-sm mt-2 hover:underline transition" data-testid="showcase-link-fleet">
          See all 15 steps &rarr;
        </button>
      </Animate>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   PANEL 5 — EVFI Intelligence (Brain Learning)
   ═══════════════════════════════════════════════════════ */
function IntelligencePanel({ onOpen }) {
  const [ref, vis] = useScrollAnimation();
  const flow = [
    { label: 'Ticket Resolved', delay: 0.8, glow: false },
    { label: 'Failure Card Created', delay: 1.8, glow: false },
    { label: 'Anonymized & Learned', delay: 2.8, glow: false },
    { label: 'Next Diagnosis Smarter', delay: 3.8, glow: true },
  ];
  const arrowDelays = [1.3, 2.3, 3.3];

  return (
    <div ref={ref} className="max-w-[600px] mx-auto" data-testid="showcase-panel-intelligence">
      <div className="flex justify-end mb-3">
        <span className="text-[9px] font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/30">
          Platform
        </span>
      </div>
      <div className="bg-[#0f1419] rounded-2xl border border-white/5 p-5 sm:p-7"
        style={{ boxShadow: '0 4px 20px rgba(200,255,0,0.1)' }}>

      <Animate show={vis} delay={0.3}>
        <div className="text-[11px] font-bold text-purple-400 tracking-wider font-mono mb-5">&#129504; EVFI INTELLIGENCE</div>
      </Animate>

      {/* Flow */}
      <div className="max-w-[320px] mx-auto">
        {flow.map((step, i) => (
          <React.Fragment key={i}>
            <Animate show={vis} delay={step.delay}>
              <div
                className={`rounded-xl p-3 text-center text-[12px] font-medium ${
                  step.glow
                    ? 'bg-[#CBFF00]/[0.07] border-2 border-[#CBFF00]/30 text-[#CBFF00]'
                    : 'bg-[#161b22] border border-white/[0.05] text-white/60'
                }`}
                style={step.glow && vis ? { animation: 'pulseGlow 2.5s ease-in-out infinite 4.5s' } : undefined}
              >
                {step.label}
              </div>
            </Animate>
            {i < flow.length - 1 && (
              <Animate show={vis} delay={arrowDelays[i]} className="text-center py-1.5">
                <span className="text-white/15 text-lg leading-none">&darr;</span>
              </Animate>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Stat Counters */}
      <Animate show={vis} delay={4.5}>
        <div className="flex gap-3 mt-6">
          <div className="flex-1 bg-purple-500/[0.06] border border-purple-500/20 rounded-xl p-3.5 text-center">
            <div className="text-xl font-bold text-purple-300">
              <Counter to={990} show={vis} delay={4.5} suffix="+" />
            </div>
            <div className="text-[8px] text-purple-400/50 uppercase tracking-wider mt-1">Patterns Learned</div>
          </div>
          <div className="flex-1 bg-purple-500/[0.06] border border-purple-500/20 rounded-xl p-3.5 text-center">
            <div className="text-xl font-bold text-purple-300">
              <Counter to={795} show={vis} delay={4.5} suffix="+" />
            </div>
            <div className="text-[8px] text-purple-400/50 uppercase tracking-wider mt-1">Knowledge Articles</div>
          </div>
        </div>
      </Animate>

      </div>
      <Animate show={vis} delay={5.0}>
        <p className="text-white/35 text-sm mt-5 leading-relaxed">Every resolved ticket makes EVFI smarter. Your technicians get better every day.</p>
      </Animate>
      <Animate show={vis} delay={5.2}>
        <p className="text-white/40 text-sm mt-2 italic leading-relaxed">"Har repair ke baad EVFI{'\u2122'} aur smart hota hai. Aapke technicians ko har baar better guidance milti hai."</p>
        <p className="text-xs text-white/20 mt-1">(After every repair, EVFI{'\u2122'} gets smarter. Your technicians get better guidance every time.)</p>
      </Animate>
      <Animate show={vis} delay={5.0}>
        <button onClick={onOpen} className="text-[#CBFF00] text-sm mt-2 hover:underline transition" data-testid="showcase-link-intelligence">
          See all 15 steps &rarr;
        </button>
      </Animate>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN: LiveShowcase — EXACTLY 5 Panels
   ═══════════════════════════════════════════════════════ */
export default function LiveShowcase({ onOpenTour }) {
  return (
    <>
      <div className="space-y-24 md:space-y-32" data-testid="live-showcase-container">
        <OperationsPanel onOpen={() => onOpenTour(0)} />
        <DiagnosisPanel onOpen={() => onOpenTour(3)} />
        <BillingPanel onOpen={() => onOpenTour(7)} />
        <FleetPanel onOpen={() => onOpenTour(10)} />
        <IntelligencePanel onOpen={() => onOpenTour(13)} />
      </div>

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(40px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.8); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 0 0 rgba(200,255,0,0.3); }
          50% { box-shadow: 0 0 20px 4px rgba(200,255,0,0.1); }
        }
      `}</style>
    </>
  );
}
