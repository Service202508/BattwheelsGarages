import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Shield, Database, Eye, Lock, FileText, Mail } from 'lucide-react';

const GRAIN = `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`;

const Section = ({ icon: Icon, title, children }) => (
  <section className="mb-12">
    <div className="flex items-center gap-3 mb-5">
      <div className="w-7 h-7 bg-bw-volt/10 border border-bw-volt/20 rounded flex items-center justify-center shrink-0">
        <Icon className="w-3.5 h-3.5 text-bw-volt" />
      </div>
      <h2 className="text-lg font-bold">{title}</h2>
    </div>
    <div className="text-white/55 text-sm leading-relaxed space-y-3 pl-10">{children}</div>
    <div className="mt-10 border-b border-white/[0.04]" />
  </section>
);

export default function Privacy() {
  const navigate = useNavigate();

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
        <span className="text-[11px] font-mono text-white/30 uppercase tracking-widest">Privacy Policy</span>
      </nav>

      <main className="pt-[73px] max-w-3xl mx-auto px-6 md:px-12 py-14">
        {/* Header */}
        <div className="mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 text-[10px] tracking-widest text-bw-volt border border-bw-volt/20 bg-bw-volt/5 rounded-sm font-mono">
            <Shield className="w-3 h-3" />
            Last updated: 24 February 2026
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
            Privacy <span className="text-bw-volt">Policy</span>
          </h1>
          <p className="text-white/45 text-sm leading-relaxed max-w-xl">
            Battwheels Services Private Limited ("Battwheels", "we", "our") operates Battwheels OS — an EV service management platform. This policy explains what data we collect, how we use it, and how we protect it. By using Battwheels OS, you agree to the practices described here.
          </p>
        </div>

        <Section icon={Database} title="1. Data We Collect">
          <p><span className="text-white/80 font-medium">Organisation data.</span> When you register a workshop, we collect your organisation name, GSTIN, city, state, industry type, and the email address and name of the admin user.</p>
          <p><span className="text-white/80 font-medium">User data.</span> For each team member you add: name, work email, role, phone number (optional), and bcrypt-hashed password. We never store plaintext passwords.</p>
          <p><span className="text-white/80 font-medium">Operational data.</span> Service tickets, vehicle records, customer contact information, invoices, bills, inventory, payroll records, attendance logs, and journal entries — all created by your team during normal platform use.</p>
          <p><span className="text-white/80 font-medium">EFI intelligence.</span> Failure Cards and diagnostic patterns generated from resolved tickets within your organisation. This knowledge base is scoped to your organisation and is not shared with other organisations.</p>
          <p><span className="text-white/80 font-medium">Usage and technical data.</span> Log entries including IP address, user agent, request timestamps, and error events (sent to Sentry for error monitoring). We do not use third-party advertising trackers.</p>
          <p><span className="text-white/80 font-medium">Payment data.</span> We do not store payment card numbers. Payments are processed via Razorpay (for Indian customers) or Stripe. We retain Razorpay payment IDs and order IDs for audit purposes.</p>
        </Section>

        <Section icon={Lock} title="2. How We Use Your Data">
          <p>To <span className="text-white/80">provide the service</span> — running your workshop's tickets, invoices, payroll, and EFI diagnostics.</p>
          <p>To <span className="text-white/80">send transactional communications</span> — invoice emails to your customers, SLA breach alerts to your team, welcome emails on signup. All sent via Resend using your organisation's verified domain where configured.</p>
          <p>To <span className="text-white/80">monitor and improve reliability</span> — error events sent to Sentry are scrubbed of PII (passwords, tokens, bank details, GSTIN) before transmission. Sentry does not receive customer financial data.</p>
          <p>To <span className="text-white/80">enforce subscription entitlements</span> — we check your plan type on every API request to determine which features are accessible. This check uses only internal metadata, not your operational data.</p>
          <p>We do not sell your data, use it for advertising, or share it with third parties except as described in Section 4.</p>
        </Section>

        <Section icon={Shield} title="3. Multi-Tenant Data Isolation">
          <p>Battwheels OS is a multi-tenant SaaS. Every database query is filtered by your <span className="font-mono text-bw-volt text-xs">organization_id</span>. TenantGuardMiddleware enforces this on every authenticated API request — no route bypasses this check.</p>
          <p>Platform administrators (Battwheels staff) can view metadata about your organisation (plan, member count, last activity) for billing and support purposes, but cannot read your operational data (tickets, invoices, employees, vehicles).</p>
          <p>Cross-tenant access attempts are blocked at the middleware level and logged as security events.</p>
        </Section>

        <Section icon={Eye} title="4. Third-Party Services">
          {[
            ['Razorpay', "Payment processing for Indian customers. Razorpay receives payment amounts, order references, and your customers' phone/email when required for payment links. Razorpay Privacy Policy: razorpay.com/privacy."],
            ['Stripe', 'Payment processing for international or test transactions. Stripe Privacy Policy: stripe.com/privacy.'],
            ['Resend', 'Transactional email delivery (invoices, SLA alerts, welcome emails). Resend receives recipient email addresses and email body content. Resend Privacy Policy: resend.com/legal/privacy-policy.'],
            ['Google Gemini (via Emergent)', 'EFI AI diagnostics and assistant responses. Ticket descriptions and vehicle details are sent to the Gemini API for AI processing. Gemini does not use your data to train its models (enterprise API usage).'],
            ['Sentry', 'Error monitoring. Stack traces and request context are sent on application errors, with PII fields scrubbed before transmission. Sentry Privacy Policy: sentry.io/privacy.'],
          ].map(([name, desc]) => (
            <p key={name}><span className="text-white/80 font-medium">{name}.</span> {desc}</p>
          ))}
        </Section>

        <Section icon={Database} title="5. Data Retention">
          <p>Your operational data is retained for as long as your organisation account is active. If you delete your account, data is marked inactive and permanently deleted within 30 days, except where retention is required by Indian law (e.g., GST records must be retained for 8 years under CGST Act).</p>
          <p>Audit logs are retained for 90 days. Server access logs are retained for 30 days.</p>
          <p>You may request a full export of your organisation's data at any time from Organisation Settings → Data Export. Exports are delivered as a JSON/CSV archive within 48 hours.</p>
        </Section>

        <Section icon={FileText} title="6. Your Rights">
          <p>Under the Information Technology Act, 2000 and the Digital Personal Data Protection Act, 2023 (India), and where applicable the General Data Protection Regulation (GDPR), you have the right to:</p>
          {['Access the personal data we hold about you', 'Correct inaccurate data', 'Delete your account and associated data (subject to legal retention obligations)', 'Export your organisation data', 'Object to processing (contact us — we will respond within 30 days)'].map(r => (
            <p key={r} className="flex items-start gap-2"><span className="text-bw-volt mt-0.5">→</span>{r}</p>
          ))}
          <p>To exercise these rights, email <a href="mailto:privacy@battwheels.com" className="text-bw-volt hover:underline">privacy@battwheels.com</a> with the subject line "Data Request — [your organisation name]".</p>
        </Section>

        <Section icon={Shield} title="7. Security">
          <p>All data is encrypted in transit via TLS. Passwords are hashed using bcrypt (cost factor 12). JWT tokens expire after 7 days. API keys are stored encrypted using Fernet symmetric encryption per organisation.</p>
          <p>We run automated dependency vulnerability scans (pip-audit + npm audit) on every code change. Security headers (X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, Content-Security-Policy) are injected on every API response.</p>
          <p>If you discover a security vulnerability, please email <a href="mailto:security@battwheels.com" className="text-bw-volt hover:underline">security@battwheels.com</a>. We aim to acknowledge reports within 24 hours.</p>
        </Section>

        <Section icon={Mail} title="8. Contact for Privacy Queries">
          <p>Battwheels Services Private Limited<br />India</p>
          <p>Privacy Officer: <a href="mailto:privacy@battwheels.com" className="text-bw-volt hover:underline">privacy@battwheels.com</a></p>
          <p>This policy may be updated periodically. We will notify registered admin users by email of material changes at least 14 days before they take effect.</p>
        </Section>
      </main>

      {/* Footer */}
      <footer className="py-10 px-6 md:px-12 border-t border-white/[0.07] flex flex-col md:flex-row items-center justify-between gap-6">
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
