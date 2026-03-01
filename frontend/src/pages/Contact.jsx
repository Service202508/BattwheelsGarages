import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Mail, Building2, ArrowRight, MessageSquare, Briefcase, Shield, Check } from 'lucide-react';
import { toast } from 'sonner';

const GRAIN = `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`;

const API_URL = process.env.REACT_APP_BACKEND_URL;

const channels = [
  {
    icon: MessageSquare,
    label: 'General Enquiries',
    desc: 'Questions about the platform, features, or pricing.',
    email: 'hello@battwheels.com',
    accent: 'rgb(var(--bw-volt))',
  },
  {
    icon: Briefcase,
    label: 'Enterprise & OEM',
    desc: 'Custom deployments, white-label, or fleet operator partnerships.',
    email: 'enterprise@battwheels.com',
    accent: 'rgb(var(--bw-teal))',
  },
  {
    icon: Shield,
    label: 'Security',
    desc: 'Responsible disclosure of vulnerabilities or security concerns.',
    email: 'security@battwheels.com',
    accent: 'rgb(var(--bw-orange))',
  },
  {
    icon: Building2,
    label: 'Legal & Privacy',
    desc: 'Data requests, privacy queries, and legal correspondence.',
    email: 'legal@battwheels.com',
    accent: 'rgb(var(--bw-volt))',
  },
];

export default function Contact() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', company: '', type: 'general', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) {
      toast.error('Please fill in all required fields.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (res.ok) {
        setSubmitted(true);
      } else {
        toast.error(data.detail || 'Something went wrong. Please try again.');
      }
    } catch {
      toast.error('Network error. Please email us directly at hello@battwheels.com');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bw-black text-bw-white font-sans overflow-x-hidden">
      <div className="fixed inset-0 pointer-events-none z-[999] opacity-60" style={{ backgroundImage: GRAIN }} />

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 border-b border-white/[0.07] bg-bw-black/85 backdrop-blur-xl">
        <button onClick={() => navigate('/')} className="flex items-center gap-3 group">
          <div className="w-7 h-7 bg-bw-volt rounded flex items-center justify-center">
            <Zap className="w-4 h-4 text-bw-black" />
          </div>
          <span className="text-lg font-extrabold tracking-tight group-hover:text-bw-volt transition">Battwheels OS</span>
        </button>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono text-white/30 uppercase tracking-widest">Contact</span>
          <button onClick={() => navigate('/register')} className="px-4 py-2 text-[12px] font-bold uppercase tracking-wide bg-bw-volt text-bw-black hover:bg-bw-volt-hover transition rounded-sm">
            Free Trial
          </button>
        </div>
      </nav>

      <main className="pt-[73px] max-w-5xl mx-auto px-6 md:px-12 py-14">
        {/* Header */}
        <div className="mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 text-[10px] tracking-widest text-bw-volt border border-bw-volt/20 bg-bw-volt/5 rounded-sm font-mono">
            <span className="w-1.5 h-1.5 bg-bw-volt rounded-full animate-pulse" />
            Battwheels Services Private Limited · India
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
            Get in <span className="text-bw-volt">Touch</span>
          </h1>
          <p className="text-white/45 text-base leading-relaxed max-w-xl">
            We're building India's EV reliability infrastructure — and we're early enough that your message will reach the team directly.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Left — channels */}
          <div>
            <p className="text-[10px] font-mono text-white/30 uppercase tracking-widest mb-6">Contact channels</p>
            <div className="flex flex-col gap-4 mb-10">
              {channels.map(c => (
                <a
                  key={c.label}
                  href={`mailto:${c.email}`}
                  className="group flex items-start gap-4 p-5 border border-white/[0.07] rounded hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.04] transition"
                >
                  <div className="w-8 h-8 rounded flex items-center justify-center shrink-0 mt-0.5" style={{ background: `${c.accent}18`, border: `1px solid ${c.accent}30` }}>
                    <c.icon className="w-4 h-4" style={{ color: c.accent }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold mb-0.5">{c.label}</p>
                    <p className="text-white/40 text-[11px] mb-2">{c.desc}</p>
                    <span className="font-mono text-[11px] text-bw-volt group-hover:underline">{c.email}</span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-white/60 mt-1 transition shrink-0" />
                </a>
              ))}
            </div>

            <div className="border border-white/[0.07] rounded p-5 bg-white/[0.02]">
              <p className="text-[10px] font-mono text-white/30 uppercase tracking-widest mb-3">Company</p>
              <p className="text-sm text-white/60 mb-1">Battwheels Services Private Limited</p>
              <p className="text-sm text-white/40">Incorporated in India · EFI Engine v2</p>
              <div className="mt-4 pt-4 border-t border-white/[0.06] flex gap-6">
                <div>
                  <p className="text-[10px] font-mono text-white/25 uppercase tracking-widest mb-1">Response time</p>
                  <p className="text-sm font-medium">Within 48 hours</p>
                </div>
                <div>
                  <p className="text-[10px] font-mono text-white/25 uppercase tracking-widest mb-1">Support hours</p>
                  <p className="text-sm font-medium">Mon–Sat, 9 AM–6 PM IST</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right — form */}
          <div>
            <p className="text-[10px] font-mono text-white/30 uppercase tracking-widest mb-6">Send a message</p>

            {submitted ? (
              <div className="flex flex-col items-center justify-center h-64 border border-bw-volt/20 bg-bw-volt/5 rounded p-8 text-center">
                <div className="w-10 h-10 bg-bw-volt rounded-full flex items-center justify-center mb-4">
                  <Check className="w-5 h-5 text-bw-black" />
                </div>
                <h3 className="text-lg font-bold mb-2">Message received</h3>
                <p className="text-white/45 text-sm">We'll get back to you at <span className="text-bw-volt">{form.email}</span> within 48 hours.</p>
                <button onClick={() => { setSubmitted(false); setForm({ name: '', email: '', company: '', type: 'general', message: '' }); }} className="mt-6 text-[11px] font-mono text-white/30 hover:text-white/60 transition underline">
                  Send another message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-mono text-white/30 uppercase tracking-widest mb-1.5">Name <span className="text-bw-volt">*</span></label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={e => setForm({ ...form, name: e.target.value })}
                      placeholder="Your name"
                      className="w-full bg-white/[0.04] border border-white/10 rounded px-3 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-bw-volt/50 transition"
                      data-testid="contact-name"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-white/30 uppercase tracking-widest mb-1.5">Email <span className="text-bw-volt">*</span></label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => setForm({ ...form, email: e.target.value })}
                      placeholder="you@workshop.com"
                      className="w-full bg-white/[0.04] border border-white/10 rounded px-3 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-bw-volt/50 transition"
                      data-testid="contact-email"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-white/30 uppercase tracking-widest mb-1.5">Company / Workshop</label>
                  <input
                    type="text"
                    value={form.company}
                    onChange={e => setForm({ ...form, company: e.target.value })}
                    placeholder="Your workshop or organisation name"
                    className="w-full bg-white/[0.04] border border-white/10 rounded px-3 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-bw-volt/50 transition"
                    data-testid="contact-company"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-white/30 uppercase tracking-widest mb-1.5">Enquiry type</label>
                  <select
                    value={form.type}
                    onChange={e => setForm({ ...form, type: e.target.value })}
                    className="w-full bg-bw-black border border-white/10 rounded px-3 py-2.5 text-sm text-white focus:outline-none focus:border-bw-volt/50 transition appearance-none"
                    data-testid="contact-type"
                  >
                    <option value="general">General enquiry</option>
                    <option value="enterprise">Enterprise / OEM partnership</option>
                    <option value="demo">Book a demo</option>
                    <option value="support">Technical support</option>
                    <option value="billing">Billing question</option>
                    <option value="security">Security report</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-white/30 uppercase tracking-widest mb-1.5">Message <span className="text-bw-volt">*</span></label>
                  <textarea
                    value={form.message}
                    onChange={e => setForm({ ...form, message: e.target.value })}
                    rows={5}
                    placeholder="Tell us about your workshop, fleet size, or what you're trying to solve…"
                    className="w-full bg-white/[0.04] border border-white/10 rounded px-3 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-bw-volt/50 transition resize-none"
                    data-testid="contact-message"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  data-testid="contact-submit"
                  className="flex items-center justify-center gap-2 px-6 py-3.5 bg-bw-volt text-bw-black text-[13px] font-bold uppercase tracking-wide rounded-sm hover:bg-bw-volt-hover hover:shadow-[0_0_24px_rgba(200,255,0,0.3)] transition disabled:opacity-50"
                >
                  {loading ? (
                    <span className="w-4 h-4 border-2 border-bw-black/40 border-t-bw-black rounded-full animate-spin" />
                  ) : (
                    <>Send Message <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>

                <p className="text-[10px] text-white/25 font-mono">
                  By submitting this form you agree to our{' '}
                  <button type="button" onClick={() => navigate('/privacy')} className="text-white/40 hover:text-bw-volt underline transition">Privacy Policy</button>.
                </p>
              </form>
            )}
          </div>
        </div>

        {/* CTA strip */}
        <div className="mt-16 p-8 border border-white/[0.07] rounded bg-white/[0.02] flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <p className="text-[10px] font-mono text-bw-volt uppercase tracking-widest mb-1">Not ready to talk yet?</p>
            <p className="font-bold">Start a free 14-day trial — no credit card required.</p>
            <p className="text-white/40 text-sm mt-0.5">Full Professional access. Your data, your workspace.</p>
          </div>
          <button onClick={() => navigate('/register')} className="shrink-0 inline-flex items-center gap-2 px-6 py-3 bg-bw-volt text-bw-black text-[13px] font-bold uppercase tracking-wide rounded-sm hover:bg-bw-volt-hover transition">
            Start Free Trial <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-10 px-6 md:px-12 border-t border-white/[0.07] flex flex-col md:flex-row items-center justify-between gap-6 mt-10">
        <div className="text-xs text-white/20 font-mono">© 2026 Battwheels Services Private Limited · EFI Engine v2 · India</div>
        <ul className="flex gap-8">
          {[['Docs', '/docs'], ['Privacy', '/privacy'], ['Terms', '/terms'], ['Contact', '/contact']].map(([label, href]) => (
            <li key={label}>
              <button onClick={() => navigate(href)} className="text-[11px] text-white/45 uppercase tracking-wider hover:text-bw-volt transition font-mono">{label}</button>
            </li>
          ))}
        </ul>
      </footer>
    </div>
  );
}
