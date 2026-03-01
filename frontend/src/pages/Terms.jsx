import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, FileText, CreditCard, AlertTriangle, Scale, RefreshCw, Lock } from 'lucide-react';

const GRAIN = `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E")`;

const Section = ({ icon: Icon, num, title, children }) => (
  <section className="mb-12">
    <div className="flex items-center gap-3 mb-5">
      <div className="w-7 h-7 bg-bw-volt/10 border border-bw-volt/20 rounded flex items-center justify-center shrink-0">
        <Icon className="w-3.5 h-3.5 text-bw-volt" />
      </div>
      <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest mr-1">{num}</span>
      <h2 className="text-lg font-bold">{title}</h2>
    </div>
    <div className="text-white/55 text-sm leading-relaxed space-y-3 pl-10">{children}</div>
    <div className="mt-10 border-b border-white/[0.04]" />
  </section>
);

const plans = [
  { name: 'Free Trial', price: '₹0', duration: '14 days', features: 'All Professional features' },
  { name: 'Starter', price: '₹2,999', duration: '/month', features: 'Core operations, basic reports, 5 users' },
  { name: 'Professional', price: '₹7,999', duration: '/month', features: 'HR & Payroll, E-Invoice, EFI AI, 25 users' },
  { name: 'Enterprise', price: 'Custom', duration: 'annual', features: 'Unlimited users, SLA, custom onboarding, dedicated support' },
];

export default function Terms() {
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
        <span className="text-[11px] font-mono text-white/30 uppercase tracking-widest">Terms of Service</span>
      </nav>

      <main className="pt-[73px] max-w-3xl mx-auto px-6 md:px-12 py-14">
        {/* Header */}
        <div className="mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 text-[10px] tracking-widest text-bw-volt border border-bw-volt/20 bg-bw-volt/5 rounded-sm font-mono">
            <Scale className="w-3 h-3" />
            Last updated: 24 February 2026
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
            Terms of <span className="text-bw-volt">Service</span>
          </h1>
          <p className="text-white/45 text-sm leading-relaxed max-w-xl">
            These Terms of Service ("Terms") constitute a binding agreement between Battwheels Services Private Limited ("Battwheels", "we", "our") and the organisation ("Customer", "you") that registers for and uses Battwheels OS. By creating an account, you accept these Terms on behalf of your organisation.
          </p>
        </div>

        <Section icon={FileText} num="01" title="The Service">
          <p>Battwheels OS is a cloud-based SaaS platform for electric vehicle service management. It includes: service ticketing, EFI AI diagnostics, invoicing (GST-compliant), HR and payroll, inventory management, and analytics.</p>
          <p>The platform is operated from India and is designed primarily for the Indian EV services market. Enterprise customers outside India may contact us for custom arrangements.</p>
          <p>We may update, modify, or discontinue features with reasonable notice. Material removals will be communicated via email to registered admin users at least 30 days in advance.</p>
        </Section>

        <Section icon={CreditCard} num="02" title="Subscription, Billing & Trial">
          {/* Plan table */}
          <div className="overflow-x-auto -mx-2 mb-4">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="py-2 px-3 font-mono text-white/30 uppercase tracking-wider">Plan</th>
                  <th className="py-2 px-3 font-mono text-white/30 uppercase tracking-wider">Price</th>
                  <th className="py-2 px-3 font-mono text-white/30 uppercase tracking-wider">Includes</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((p, i) => (
                  <tr key={i} className="border-b border-white/[0.05] hover:bg-white/[0.02]">
                    <td className="py-2.5 px-3 font-medium text-white/70">{p.name}</td>
                    <td className="py-2.5 px-3 font-mono text-bw-volt">{p.price} <span className="text-white/30">{p.duration}</span></td>
                    <td className="py-2.5 px-3 text-white/45">{p.features}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>All paid subscriptions are billed monthly or annually (annual billing offers a 2-month discount). Prices are in INR and exclusive of applicable GST (18%).</p>
          <p>Payment is collected in advance via Razorpay (Indian accounts) or Stripe. If a payment fails, we will retry three times over 7 days. After the third failure, the account reverts to the Free plan until payment is resolved.</p>
          <p>The 14-day free trial does not require a payment method. At the end of the trial, the account is automatically moved to the Free plan. No charges are applied without explicit action by the Customer.</p>
        </Section>

        <Section icon={RefreshCw} num="03" title="Cancellation & Refunds">
          <p>You may cancel your subscription at any time from Organisation Settings. Cancellation takes effect at the end of the current billing period — you retain access until then.</p>
          <p>Battwheels does not provide pro-rated refunds for partial months. If you cancel on day 5 of a monthly subscription, you retain access for the remaining 25 days with no refund.</p>
          <p>Exception: if the platform is unavailable for more than 24 cumulative hours in a billing month due to a fault on our side (not scheduled maintenance or force majeure), you are entitled to a credit equal to one month's subscription fee. Credits are applied to the next invoice.</p>
        </Section>

        <Section icon={Lock} num="04" title="Data Ownership & Intellectual Property">
          <p><span className="text-white/80 font-medium">Your data is yours.</span> All operational data created by your organisation (tickets, invoices, employees, vehicles, customers) remains your property. You may export it at any time. We do not claim ownership of your data.</p>
          <p><span className="text-white/80 font-medium">EFI knowledge base.</span> Failure Cards created from your tickets are scoped to your organisation. We do not use your resolution data to train models shared with other organisations.</p>
          <p><span className="text-white/80 font-medium">Platform IP.</span> The Battwheels OS platform, EFI Engine, and all associated code, algorithms, designs, and trademarks are owned by Battwheels Services Private Limited. You receive a limited, non-exclusive, non-transferable licence to use the platform during your subscription.</p>
          <p><span className="text-white/80 font-medium">Feedback.</span> If you submit feature requests or feedback, you grant us the right to use that feedback without compensation.</p>
        </Section>

        <Section icon={AlertTriangle} num="05" title="Acceptable Use">
          <p>You agree not to:</p>
          {[
            'Use the platform for any purpose that violates applicable Indian law or regulations',
            'Attempt to access another organisation\'s data or probe the multi-tenant isolation boundary',
            'Reverse-engineer, decompile, or attempt to extract source code from the platform',
            'Use automated tools to scrape data from the platform beyond the official API',
            'Upload malicious code, scripts, or payloads to any input field',
            'Share API credentials or JWT tokens across organisations',
            'Resell or sublicense access to the platform without written permission',
          ].map(r => (
            <p key={r} className="flex items-start gap-2"><span className="text-white/30 font-mono shrink-0">—</span>{r}</p>
          ))}
          <p>Violation of acceptable use may result in immediate suspension without refund.</p>
        </Section>

        <Section icon={AlertTriangle} num="06" title="Limitation of Liability">
          <p>Battwheels OS is provided "as is". We make reasonable efforts to ensure availability and data integrity but do not guarantee 100% uptime or error-free operation.</p>
          <p>To the maximum extent permitted by Indian law, Battwheels' total liability to you for any claim arising from use of the platform shall not exceed the amount you paid in subscription fees in the 3 months preceding the claim.</p>
          <p>We are not liable for: loss of revenue, indirect or consequential damages, data loss resulting from your failure to export backups, or downtime caused by third-party services (Razorpay, Resend, etc.).</p>
        </Section>

        <Section icon={Scale} num="07" title="Governing Law & Disputes">
          <p>These Terms are governed by the laws of India. Any disputes arising from these Terms shall be subject to the exclusive jurisdiction of the courts in Bangalore, Karnataka, India.</p>
          <p>Before initiating legal proceedings, you agree to first contact us at <a href="mailto:legal@battwheels.com" className="text-bw-volt hover:underline">legal@battwheels.com</a> and allow 30 days for good-faith resolution.</p>
        </Section>

        <Section icon={FileText} num="08" title="Changes to These Terms">
          <p>We may update these Terms as the platform and applicable regulations evolve. Material changes will be communicated to registered admin users by email at least 14 days before they take effect.</p>
          <p>Continued use of Battwheels OS after the effective date of changes constitutes acceptance of the updated Terms.</p>
          <p>Questions? Email <a href="mailto:legal@battwheels.com" className="text-bw-volt hover:underline">legal@battwheels.com</a></p>
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
