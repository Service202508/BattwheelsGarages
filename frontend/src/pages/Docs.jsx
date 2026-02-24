import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, ChevronRight, BookOpen, Terminal, Layers, Users, BarChart3, Brain, FileText, HelpCircle, ArrowRight } from 'lucide-react';

const GRAIN = `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`;

const sections = [
  {
    id: 'getting-started',
    icon: BookOpen,
    label: '01 · Getting Started',
    title: 'Sign up and go live in minutes',
    content: [
      { heading: 'Create your organisation', body: 'Visit /register and complete the 3-step onboarding: workshop details, admin account, and confirmation. Your workspace is isolated — no data is shared with other organisations.' },
      { heading: 'Onboarding checklist', body: 'After sign-in, Battwheels OS shows a guided checklist: add your first contact, register a vehicle, open a service ticket, add inventory, raise an invoice, and invite a team member. Each step unlocks the next layer of the platform.' },
      { heading: 'Subscription plans', body: 'Free 14-day trial includes all Professional features. Plans: Starter (₹2,999/mo), Professional (₹7,999/mo), Enterprise (custom). Features are enforced at API level — the platform shows an upgrade prompt when a gated feature is accessed on a lower plan.' },
    ]
  },
  {
    id: 'efi-engine',
    icon: Brain,
    label: '02 · EFI Engine',
    title: 'EV Failure Intelligence — how it works',
    content: [
      { heading: 'What is EFI?', body: 'Battwheels EFI™ is a proprietary AI-powered engine trained exclusively on EV failure patterns. Unlike generic automotive AI, EFI maps fault codes to EV-specific fault trees, accounting for BMS architecture, motor controller variants, and firmware versions.' },
      { heading: 'Failure Cards', body: 'Every resolved ticket creates a Failure Card — a structured knowledge entry with vehicle model, fault codes, root cause, resolution steps, and confidence score. Cards are org-scoped; your knowledge base does not merge with other workshops.' },
      { heading: 'AI Diagnostics', body: 'When a ticket is created, EFI automatically matches the complaint against your Failure Card knowledge base. Technicians receive ranked root cause suggestions with step-by-step guidance in plain English (or Hinglish for field technicians).' },
      { heading: 'Confidence scoring', body: 'Each EFI match returns a confidence level: High, Medium, or Low. Low-confidence matches automatically create a draft Failure Card so your team can document the new failure pattern for future reference.' },
    ]
  },
  {
    id: 'service-operations',
    icon: Layers,
    label: '03 · Service Operations',
    title: 'Tickets, vehicles, and job cards',
    content: [
      { heading: 'Service tickets', body: 'Create tickets from the dashboard or the public submission form (/submit-ticket). Each ticket tracks: vehicle info, customer contact, complaint category, assigned technician, SLA deadline, and full status history.' },
      { heading: 'SLA automation', body: 'Define SLA tiers per organisation (e.g., Critical = 4 hours, Standard = 24 hours). The platform calculates deadlines on ticket creation, shows colour-coded breach indicators on the ticket list, and auto-reassigns breached tickets based on workload balance.' },
      { heading: 'Job cards', body: 'Each ticket has an embedded Job Card: estimated parts and services, actual parts consumed (deducted from inventory), labor cost, and COGS journal entry posted automatically on job completion.' },
      { heading: 'AMC management', body: 'Create Annual Maintenance Contracts for repeat fleet customers. AMC schedules generate tickets automatically at due dates and are tracked against the contract value.' },
    ]
  },
  {
    id: 'finance',
    icon: BarChart3,
    label: '04 · Finance & Accounting',
    title: 'GST-compliant double-entry accounting',
    content: [
      { heading: 'Invoice flow', body: 'Estimates → Sales Orders → Invoices. All conversions preserve line items, GST rates, and discounts. Per-organisation sequential numbering (INV-202602-0001) with atomic counters — no gaps, no duplicates.' },
      { heading: 'GST & E-Invoice', body: 'Invoices split CGST/SGST for intra-state and IGST for inter-state. GST reports available under Reports → GST Summary. E-Invoice generation via the Finance tab (PROFESSIONAL plan and above).' },
      { heading: 'Double-entry accounting', body: 'Every financial event (invoice raised, payment received, bill approved, payroll run, job card completed) automatically posts balanced journal entries. Trial Balance, Profit & Loss, and Balance Sheet are available in real time.' },
      { heading: 'Tally XML export', body: 'Export journal entries as TallyPrime-compatible XML (Finance → Journal Entries → Export to Tally). Useful for accountants who continue to work in Tally for statutory filings.' },
    ]
  },
  {
    id: 'hr-payroll',
    icon: Users,
    label: '05 · HR & Payroll',
    title: 'Employee management and payroll',
    content: [
      { heading: 'Employee records', body: 'Store full employee profiles: personal info, employment details, salary structure (Basic, HRA, DA, Special Allowance), PF/ESI enrollment, bank details, and compliance numbers (PAN, Aadhaar, UAN).' },
      { heading: 'Attendance', body: 'Clock-in/clock-out with IP and location logging. Monthly attendance summaries feed directly into payroll calculation.' },
      { heading: 'Payroll processing', body: 'One-click payroll run per month. The engine calculates gross, deductions (PF 12%, ESI 0.75%, Professional Tax, TDS), and net salary. Each payroll run posts a balanced journal entry (Salary Expense → Deductions + Bank).' },
      { heading: 'Form 16 PDF', body: 'Download Form 16 (Part A + Part B) as a WeasyPrint-generated PDF for any employee and financial year. Bulk Form 16 download available as a ZIP archive.' },
    ]
  },
  {
    id: 'platform-admin',
    icon: Terminal,
    label: '06 · Platform Administration',
    title: 'Multi-tenant and platform controls',
    content: [
      { heading: 'Platform admin access', body: 'Users with is_platform_admin=true can access /platform-admin. This dashboard shows all registered organisations, plan types, member counts, MRR, and trial pipeline.' },
      { heading: 'Organisation management', body: 'Platform admins can: suspend or activate organisations, change subscription plans, run the 103-point production audit, and view revenue health metrics.' },
      { heading: 'Data isolation', body: 'Every API endpoint is scoped to the authenticated organisation via TenantGuardMiddleware. Cross-tenant requests are blocked at the middleware level and logged as security events. You cannot see another organisation\'s data.' },
      { heading: 'RBAC', body: 'Seven roles enforced at API level: org_admin, manager, accountant, technician, dispatcher, viewer, and customer/fleet_customer (portal access only). Feature entitlements are enforced independently of RBAC.' },
    ]
  },
  {
    id: 'api',
    icon: FileText,
    label: '07 · API Reference',
    title: 'REST API — base URL and auth',
    content: [
      { heading: 'Base URL', body: 'All API endpoints are prefixed with /api. Example: https://your-domain.com/api/health' },
      { heading: 'Authentication', body: 'Bearer token in Authorization header. Obtain a token via POST /api/auth/login with {"email": "...", "password": "..."}. Tokens expire after 7 days.' },
      { heading: 'Organisation context', body: 'All protected endpoints require the X-Organization-ID header. This is the organization_id returned on login.' },
      { heading: 'Response format', body: 'Paginated endpoints return {"data": [...], "pagination": {"page", "limit", "total_count", "total_pages", "has_next", "has_prev"}}. Default limit: 25. Max: 100.' },
    ]
  },
  {
    id: 'faq',
    icon: HelpCircle,
    label: '08 · FAQ',
    title: 'Frequently asked questions',
    content: [
      { heading: 'Is my data isolated from other workshops?', body: 'Yes. Every piece of data — tickets, invoices, employees, vehicles, knowledge base entries — is scoped to your organisation_id. You cannot read or write another organisation\'s data, and neither can platform administrators (they can only see metadata like plan and member count).' },
      { heading: 'Can I export my data?', body: 'Yes. You can export journal entries as Tally XML, download payslips and Form 16 as PDFs, and request a full data export from Organisation Settings → Data Export.' },
      { heading: 'Does EFI work without internet?', body: 'No. EFI diagnostics require an active internet connection to reach the AI backend. Service ticket creation, job cards, and invoicing work normally offline but syncing requires connectivity.' },
      { heading: 'How do I integrate with Zoho Books?', body: 'Go to Organisation Settings → Integrations tab. Enter your Zoho OAuth credentials. Once connected, contacts, invoices, and bills sync bidirectionally. Zoho import is available in Finance → Import from Zoho.' },
      { heading: 'What happens when my trial ends?', body: 'After 14 days, you are moved to the Free plan. Features gated to Starter and above show an upgrade prompt. Your data is preserved — nothing is deleted. You can upgrade at any time to restore full access.' },
    ]
  },
];

export default function Docs() {
  const navigate = useNavigate();
  const [active, setActive] = useState('getting-started');

  return (
    <div className="min-h-screen bg-[#080C0F] text-[#F4F6F0] font-sans overflow-x-hidden">
      {/* Grain */}
      <div className="fixed inset-0 pointer-events-none z-[999] opacity-60" style={{ backgroundImage: GRAIN }} />

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 border-b border-white/[0.07] bg-[#080C0F]/85 backdrop-blur-xl">
        <button onClick={() => navigate('/')} className="flex items-center gap-3 group">
          <div className="w-7 h-7 bg-[#C8FF00] rounded flex items-center justify-center">
            <Zap className="w-4 h-4 text-[#080C0F]" />
          </div>
          <span className="text-lg font-extrabold tracking-tight group-hover:text-[#C8FF00] transition">Battwheels OS</span>
        </button>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono text-white/30 uppercase tracking-widest">Documentation</span>
          <button onClick={() => navigate('/register')} className="px-4 py-2 text-[12px] font-bold uppercase tracking-wide bg-[#C8FF00] text-[#080C0F] hover:bg-[#d4ff1a] transition rounded-sm">
            Free Trial
          </button>
        </div>
      </nav>

      <div className="flex pt-[73px] min-h-screen">
        {/* Sidebar */}
        <aside className="hidden md:flex flex-col w-64 shrink-0 border-r border-white/[0.07] py-10 px-6 sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
          <p className="text-[10px] font-mono text-white/25 uppercase tracking-widest mb-6">Contents</p>
          <nav className="flex flex-col gap-1">
            {sections.map(s => (
              <button
                key={s.id}
                onClick={() => { setActive(s.id); document.getElementById(s.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }}
                className={`flex items-center gap-2.5 px-3 py-2 rounded text-left text-[12px] transition group ${active === s.id ? 'bg-[#C8FF00]/10 text-[#C8FF00]' : 'text-white/40 hover:text-white/80'}`}
              >
                <s.icon className="w-3.5 h-3.5 shrink-0" />
                <span className="font-mono">{s.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 max-w-3xl mx-auto px-6 md:px-12 py-14">
          {/* Page header */}
          <div className="mb-14">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 text-[10px] tracking-widest text-[#C8FF00] border border-[#C8FF00]/20 bg-[#C8FF00]/5 rounded-sm font-mono">
              <span className="w-1.5 h-1.5 bg-[#C8FF00] rounded-full animate-pulse" />
              EFI Engine · Active · India
            </div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
              Battwheels OS<br /><span className="text-[#C8FF00]">Documentation</span>
            </h1>
            <p className="text-white/45 text-base leading-relaxed max-w-xl">
              Everything you need to deploy, operate, and extend the platform — from onboarding to the REST API.
            </p>
          </div>

          {/* Sections */}
          {sections.map(s => (
            <section key={s.id} id={s.id} className="mb-16 scroll-mt-24">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 bg-[#C8FF00]/10 border border-[#C8FF00]/20 rounded flex items-center justify-center">
                  <s.icon className="w-4 h-4 text-[#C8FF00]" />
                </div>
                <span className="text-[11px] font-mono text-white/30 uppercase tracking-widest">{s.label}</span>
              </div>
              <h2 className="text-2xl font-bold mb-8">{s.title}</h2>
              <div className="flex flex-col gap-6">
                {s.content.map((c, i) => (
                  <div key={i} className="border border-white/[0.07] rounded p-6 bg-white/[0.02]">
                    <h3 className="text-[13px] font-semibold text-[#C8FF00] mb-2 font-mono uppercase tracking-wide">{c.heading}</h3>
                    <p className="text-white/60 text-sm leading-relaxed">{c.body}</p>
                  </div>
                ))}
              </div>
              <div className="mt-6 border-b border-white/[0.04]" />
            </section>
          ))}

          {/* CTA */}
          <div className="mt-8 p-8 border border-[#C8FF00]/20 bg-[#C8FF00]/5 rounded">
            <p className="text-[10px] font-mono text-[#C8FF00] uppercase tracking-widest mb-3">Ready to start?</p>
            <h3 className="text-xl font-bold mb-2">Your first workshop, live in 10 minutes.</h3>
            <p className="text-white/45 text-sm mb-5">No credit card required. 14-day free trial includes all Professional features.</p>
            <button onClick={() => navigate('/register')} className="inline-flex items-center gap-2 px-6 py-3 bg-[#C8FF00] text-[#080C0F] text-[13px] font-bold uppercase tracking-wide rounded-sm hover:bg-[#d4ff1a] transition">
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="py-10 px-6 md:px-12 border-t border-white/[0.07] flex flex-col md:flex-row items-center justify-between gap-6 mt-10">
        <div className="text-xs text-white/20 font-mono">© 2026 Battwheels Services Private Limited · EFI Engine v2 · India</div>
        <ul className="flex gap-8">
          {[['Docs', '/docs'], ['Privacy', '/privacy'], ['Terms', '/terms'], ['Contact', '/contact']].map(([label, href]) => (
            <li key={label}>
              <button onClick={() => navigate(href)} className="text-[11px] text-white/45 uppercase tracking-wider hover:text-[#C8FF00] transition font-mono">{label}</button>
            </li>
          ))}
        </ul>
      </footer>
    </div>
  );
}
