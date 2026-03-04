import React, { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, ArrowRight, Zap, FileText, CreditCard, Package, LayoutGrid, Activity } from 'lucide-react';

const STEPS = [
  {
    title: 'Your Workshop Dashboard',
    caption: 'Real-time view of your entire workshop. No spreadsheets. No guesswork.',
    icon: LayoutGrid,
    mockup: () => (
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Revenue This Month', value: '\u20B94,23,500', accent: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
          { label: 'Open Tickets', value: '12', accent: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
          { label: 'Inventory Alerts', value: '3 Low Stock', accent: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'AMC Due This Week', value: '5 Renewals', accent: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        ].map((card, i) => (
          <div key={i} className={`${card.bg} border rounded-lg p-4`}>
            <div className="text-[10px] uppercase tracking-wider text-white/40 mb-2">{card.label}</div>
            <div className={`text-xl font-bold ${card.accent}`}>{card.value}</div>
          </div>
        ))}
      </div>
    ),
  },
  {
    title: 'AI-Powered Diagnosis',
    caption: 'Battwheels EFI\u2122 tells your technician exactly what\'s wrong. First time.',
    icon: Zap,
    mockup: () => (
      <div className="space-y-3">
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-[#CBFF00]" />
            <span className="text-xs font-bold text-[#CBFF00] tracking-wider">EFI\u2122 DIAGNOSIS</span>
          </div>
          <div className="bg-zinc-900/60 rounded p-3 border border-zinc-700/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white">Battery Degradation Detected</span>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">94%</span>
            </div>
            <div className="text-xs text-white/40">Cell imbalance in Module 3. Recommend BMS recalibration.</div>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 bg-purple-500/10 border border-purple-500/20 rounded p-2.5 text-center">
            <div className="text-[10px] text-purple-400 uppercase tracking-wider">Fix Steps</div>
            <div className="text-lg font-bold text-purple-300">4</div>
          </div>
          <div className="flex-1 bg-emerald-500/10 border border-emerald-500/20 rounded p-2.5 text-center">
            <div className="text-[10px] text-emerald-400 uppercase tracking-wider">Success Rate</div>
            <div className="text-lg font-bold text-emerald-300">91%</div>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'GST Invoice in One Click',
    caption: 'Create GST-compliant invoices directly from the service ticket. GSTR-1 ready.',
    icon: FileText,
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-bold text-white">INV-2026-0047</span>
          <span className="text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">PAID</span>
        </div>
        <div className="border-t border-zinc-700 pt-3 space-y-1.5 text-xs">
          <div className="flex justify-between text-white/50"><span>Motor Controller Repair</span><span className="text-white">\u20B93,200</span></div>
          <div className="flex justify-between text-white/50"><span>BMS Diagnostic (HSN 9987)</span><span className="text-white">\u20B91,500</span></div>
          <div className="border-t border-zinc-700 pt-2 flex justify-between text-white/50"><span>CGST @ 9%</span><span className="text-white">\u20B9423</span></div>
          <div className="flex justify-between text-white/50"><span>SGST @ 9%</span><span className="text-white">\u20B9423</span></div>
        </div>
        <div className="border-t border-zinc-700 pt-2 flex justify-between font-bold text-sm">
          <span className="text-white/60">Total</span>
          <span className="text-[#CBFF00]">\u20B95,546</span>
        </div>
      </div>
    ),
  },
  {
    title: 'Track Every Payment',
    caption: 'Split payments, track outstanding, send reminders. Cash flow sorted.',
    icon: CreditCard,
    mockup: () => (
      <div className="space-y-3">
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <div className="text-xs text-white/40 uppercase tracking-wider mb-3">Payment Split</div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-sm text-white">Cash</span>
              </div>
              <span className="text-sm font-mono text-emerald-400">\u20B92,000</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-400" />
                <span className="text-sm text-white">UPI</span>
              </div>
              <span className="text-sm font-mono text-blue-400">\u20B93,500</span>
            </div>
          </div>
          <div className="border-t border-zinc-700 mt-3 pt-3 flex justify-between">
            <span className="text-xs text-white/40">Total Received</span>
            <span className="text-sm font-bold text-[#CBFF00]">\u20B95,500</span>
          </div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-300">
          Outstanding: \u20B9546. Reminder scheduled for tomorrow.
        </div>
      </div>
    ),
  },
  {
    title: 'Inventory That Thinks',
    caption: 'Real-time stock with automatic cost tracking.',
    icon: Package,
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-white">BMS Module v3.2</span>
          <span className="text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded">LOW STOCK</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-zinc-900 rounded p-2 text-center">
            <div className="text-[10px] text-white/40">In Stock</div>
            <div className="text-lg font-bold text-amber-400">3</div>
          </div>
          <div className="bg-zinc-900 rounded p-2 text-center">
            <div className="text-[10px] text-white/40">Reorder At</div>
            <div className="text-lg font-bold text-white/60">5</div>
          </div>
          <div className="bg-zinc-900 rounded p-2 text-center">
            <div className="text-[10px] text-white/40">COGS/Unit</div>
            <div className="text-lg font-bold text-emerald-400">\u20B94.2k</div>
          </div>
        </div>
        <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-2">
          Auto reorder alert triggered. Supplier notified.
        </div>
      </div>
    ),
  },
  {
    title: 'Complete Workshop OS',
    caption: '16+ modules. One subscription. Zero paper.',
    icon: LayoutGrid,
    isFinal: true,
    mockup: () => {
      const mods = [
        'Tickets & SLA', 'Invoicing', 'Estimates', 'Inventory',
        'GST Compliance', 'Accounting', 'HR & Payroll', 'EFI\u2122 AI',
        'Credit Notes', 'Period Locking', 'Reports', 'AMC Contracts',
        'Customer Portal', 'Tech Portal', 'Admin Panel', 'Projects',
      ];
      return (
        <div className="grid grid-cols-4 gap-1.5">
          {mods.map((m, i) => (
            <div key={i} className="bg-zinc-800 border border-zinc-700/50 rounded p-2 text-center hover:border-[#CBFF00]/30 hover:bg-[#CBFF00]/5 transition">
              <div className="text-[10px] text-white/60 leading-tight">{m}</div>
            </div>
          ))}
        </div>
      );
    },
  },
];

export default function ProductTour({ isOpen, onClose, onStartTrial }) {
  const [step, setStep] = useState(0);

  const goNext = useCallback(() => setStep(s => Math.min(s + 1, STEPS.length - 1)), []);
  const goPrev = useCallback(() => setStep(s => Math.max(s - 1, 0)), []);

  useEffect(() => {
    if (!isOpen) { setStep(0); return; }
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') goNext();
      if (e.key === 'ArrowLeft') goPrev();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose, goNext, goPrev]);

  if (!isOpen) return null;

  const current = STEPS[step];
  const Icon = current.icon;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4" data-testid="product-tour-overlay">
      <div className="bg-zinc-900 border border-white/10 rounded-lg max-w-lg w-full shadow-2xl overflow-hidden" data-testid="product-tour-card">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.07]">
          <div className="flex items-center gap-2">
            <Icon className="w-4 h-4 text-[#CBFF00]" />
            <span className="text-sm font-bold text-white">{current.title}</span>
            <span className="text-[10px] text-white/30 font-mono ml-2">{step + 1}/{STEPS.length}</span>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white transition" data-testid="product-tour-close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mockup */}
        <div className="px-6 py-5 min-h-[260px]">
          {current.mockup()}
        </div>

        {/* Caption + Nav */}
        <div className="px-6 pb-5 space-y-4">
          <p className="text-sm text-white/50 leading-relaxed">{current.caption}</p>

          <div className="flex items-center justify-between">
            {/* Dots */}
            <div className="flex gap-1.5">
              {STEPS.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setStep(i)}
                  className={`w-2 h-2 rounded-full transition ${i === step ? 'bg-[#CBFF00]' : 'bg-white/20 hover:bg-white/40'}`}
                  data-testid={`tour-dot-${i}`}
                />
              ))}
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-2">
              {step > 0 && (
                <button onClick={goPrev} className="p-2 text-white/40 hover:text-white transition rounded" data-testid="tour-prev">
                  <ChevronLeft className="w-5 h-5" />
                </button>
              )}
              {current.isFinal ? (
                <button
                  onClick={() => { onClose(); onStartTrial(); }}
                  className="px-5 py-2 text-xs font-bold uppercase tracking-wide bg-[#CBFF00] text-zinc-900 hover:bg-[#d4ff33] rounded-sm flex items-center gap-1.5 transition"
                  data-testid="tour-start-trial"
                >
                  Start Your Free Trial <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <button onClick={goNext} className="p-2 text-white/40 hover:text-white transition rounded" data-testid="tour-next">
                  <ChevronRight className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
