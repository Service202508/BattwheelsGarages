import React, { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, ArrowRight, Zap, FileText, CreditCard, Package, LayoutGrid, PlusCircle, UserCheck, ClipboardCheck, CheckCircle, Users, Truck, FileCheck, Brain, Shield } from 'lucide-react';

const SECTIONS = [
  { label: 'Operations', accent: '#14b8a6', steps: [0, 1, 2] },
  { label: 'Diagnosis & Repair', accent: '#CBFF00', steps: [3, 4, 5] },
  { label: 'Billing & Payments', accent: '#f59e0b', steps: [6, 7, 8] },
  { label: 'Management', accent: '#3b82f6', steps: [9, 10, 11, 12] },
  { label: 'Intelligence', accent: '#a855f7', steps: [13, 14] },
];

const B = ({ children, color }) => (
  <span className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-sm border" style={{ color, borderColor: `${color}44`, background: `${color}11` }}>{children}</span>
);

const Row = ({ label, value, bold, border }) => (
  <div className={`flex justify-between py-1.5 text-xs ${border ? 'border-t border-zinc-700 mt-1 pt-2' : ''} ${bold ? 'font-bold text-white' : 'text-white/50'}`}>
    <span>{label}</span><span className={bold ? 'text-[#CBFF00]' : 'text-white'}>{value}</span>
  </div>
);

const STEPS = [
  {
    title: 'Your Service Dashboard',
    badge: 'OWNER',
    icon: LayoutGrid,
    section: 0,
    caption: 'Everything about your EV service operation. One glance. Serving 23 Lakh+ EVs sold in India in 2025.',
    mockup: () => (
      <div className="grid grid-cols-2 gap-2.5">
        {[
          { label: 'Revenue', value: '₹4,82,350', sub: 'This month', color: '#CBFF00' },
          { label: 'Open Tickets', value: '13', sub: '3 urgent', color: '#f59e0b' },
          { label: 'Inventory Alerts', value: '3', sub: 'Low stock', color: '#ef4444' },
          { label: 'AMC Due', value: '2', sub: 'This week', color: '#3b82f6' },
        ].map((s, i) => (
          <div key={i} className="bg-zinc-800 border border-zinc-700/50 rounded-lg p-3.5">
            <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1">{s.label}</div>
            <div className="text-xl font-bold" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[10px] text-white/30 mt-0.5">{s.sub}</div>
          </div>
        ))}
      </div>
    ),
  },
  {
    title: 'Create a Service Ticket',
    badge: 'OWNER / MANAGER',
    icon: PlusCircle,
    section: 0,
    caption: 'Structured complaint intake. Vehicle details auto-feed into EVFI for instant AI diagnosis.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="text-xs font-bold text-white/70 uppercase tracking-wider mb-1">New Service Ticket</div>
        {[
          { l: 'Customer', v: 'Rajesh Kumar' },
          { l: 'Vehicle', v: 'Ola S1 Pro (2W) — DL01AB1234' },
          { l: 'Issue', v: 'Vehicle not charging after firmware update' },
        ].map((f, i) => (
          <div key={i}>
            <div className="text-[10px] text-white/30 mb-0.5">{f.l}</div>
            <div className="bg-zinc-900 border border-zinc-700/50 rounded px-3 py-2 text-xs text-white/70">{f.v}</div>
          </div>
        ))}
        <div className="flex gap-2">
          <div className="flex-1">
            <div className="text-[10px] text-white/30 mb-0.5">Priority</div>
            <div className="bg-red-500/10 border border-red-500/30 rounded px-3 py-2 text-xs text-red-400 font-medium">High</div>
          </div>
          <div className="flex-1">
            <div className="text-[10px] text-white/30 mb-0.5">Type</div>
            <div className="bg-zinc-900 border border-zinc-700/50 rounded px-3 py-2 text-xs text-white/70">Electrical</div>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'Assign & Track',
    badge: 'MANAGER',
    icon: UserCheck,
    section: 0,
    caption: 'Right technician. Right ticket. SLA countdown starts automatically.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-white">TKT-2026-0847</div>
          <span className="text-[9px] bg-teal-500/15 text-teal-400 border border-teal-500/30 px-2 py-0.5 rounded font-medium">Technician Assigned</span>
        </div>
        <div className="bg-zinc-900/60 rounded p-3 border border-zinc-700/40">
          <div className="text-[10px] text-white/30 mb-1">Assigned To</div>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-[10px] font-bold text-teal-400">AV</div>
            <div>
              <div className="text-xs font-medium text-white">Ankit Verma</div>
              <div className="text-[10px] text-white/30">Senior Technician</div>
            </div>
          </div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded p-3 flex items-center justify-between">
          <div className="text-[10px] text-amber-400 uppercase tracking-wider font-medium">SLA Remaining</div>
          <div className="text-lg font-bold font-mono text-amber-400">3h 42m</div>
        </div>
      </div>
    ),
  },
  {
    title: 'EVFI™ AI Diagnosis & Resolution',
    badge: 'TECHNICIAN',
    icon: Zap,
    section: 1,
    caption: 'EVFI™ analyses 100+ EV models across 20+ Indian brands. Your technician gets expert-level guidance from day one. 84% first-visit fix rate.',
    mockup: () => (
      <div className="space-y-2.5">
        <div className="bg-slate-900 border border-[#CBFF00]/20 rounded-lg overflow-hidden">
          {/* Branded Header */}
          <div className="p-3 border-b border-[#CBFF00]/10 bg-gradient-to-br from-[#CBFF00]/[0.04] to-transparent">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#CBFF00]" />
                <span className="text-[10px] font-bold text-[#CBFF00] tracking-wider">BATTWHEELS EVFI&trade; DIAGNOSTIC REPORT</span>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-medium bg-blue-500/15 text-blue-300 border border-blue-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                Known EV Model
              </span>
            </div>
            <div className="mt-1.5 text-[11px] text-white/60">
              Vehicle: <span className="text-white/80">Ola S1 Pro (2W)</span>
            </div>
          </div>
          {/* Safety Section */}
          <div className="mx-2.5 mt-2.5 p-2.5 bg-red-900/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-1.5 mb-1">
              <Shield className="w-3.5 h-3.5 text-red-400" />
              <span className="text-[10px] font-semibold text-red-300">Safety Precautions</span>
            </div>
            <div className="text-[10px] text-red-200/70 leading-relaxed">
              Vehicle powered OFF, key removed. Insulated gloves (Class 0). 48V nominal system.
            </div>
          </div>
          {/* Diagnostic Steps */}
          <div className="p-2.5 space-y-1.5">
            <div className="text-[9px] text-[#CBFF00] uppercase tracking-wider mb-1">Diagnostic Steps</div>
            {["Check 12V auxiliary — Expected: 12.6V+", "DC-DC converter output — Expected: 13.2-14.4V", "BMS communication check via CAN"].map((step, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-slate-800/60 rounded border border-slate-700/50">
                <span className="w-4 h-4 rounded-full bg-[#CBFF00]/10 text-[#CBFF00] text-[9px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{i+1}</span>
                <span className="text-[10px] text-white/70">{step}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 bg-emerald-500/10 border border-emerald-500/20 rounded p-2 text-center">
            <div className="text-[9px] text-emerald-400 uppercase tracking-wider">First-Visit Fix</div>
            <div className="text-lg font-bold text-emerald-300">84%</div>
          </div>
          <div className="flex-1 bg-blue-500/10 border border-blue-500/20 rounded p-2 text-center">
            <div className="text-[9px] text-blue-400 uppercase tracking-wider">Speed</div>
            <div className="text-lg font-bold text-blue-300">10x</div>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'Guided Repair Steps',
    badge: 'TECHNICIAN',
    icon: ClipboardCheck,
    section: 1,
    caption: '10x faster diagnosis & resolution than manual troubleshooting.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs font-bold text-white/70">Repair Checklist</div>
          <span className="text-[10px] font-mono text-[#CBFF00]">2/3 complete</span>
        </div>
        {[
          { step: '12V battery load test', status: 'pass', val: '12.8V', done: true },
          { step: 'DC-DC converter output', status: 'fail', val: '11.2V (low)', done: true },
          { step: 'Inspect HV interlock connector', status: null, val: null, done: false },
        ].map((s, i) => (
          <div key={i} className={`flex items-center gap-3 p-2.5 rounded border ${s.done ? (s.status === 'pass' ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20') : 'bg-zinc-900/40 border-zinc-700/30'}`}>
            <div className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold ${s.done ? (s.status === 'pass' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400') : 'bg-zinc-700/40 text-white/30'}`}>
              {s.done ? (s.status === 'pass' ? '✓' : '✗') : (i + 1)}
            </div>
            <div className="flex-1">
              <div className="text-xs text-white/70">{s.step}</div>
              {s.val && <div className={`text-[10px] ${s.status === 'pass' ? 'text-emerald-400' : 'text-red-400'}`}>{s.val}</div>}
            </div>
          </div>
        ))}
        <div className="w-full bg-zinc-700/30 rounded-full h-1.5 mt-1">
          <div className="bg-[#CBFF00] h-1.5 rounded-full" style={{ width: '66%' }} />
        </div>
      </div>
    ),
  },
  {
    title: 'Create Estimate',
    badge: 'TECHNICIAN',
    icon: FileText,
    section: 1,
    caption: 'Real parts. Real pricing. GST auto-calculated with HSN/SAC codes. Send to customer in one tap.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-1">
        <div className="text-xs font-bold text-white/70 mb-2">Estimate #EST-2026-0421</div>
        <div className="border border-zinc-700/50 rounded overflow-hidden mb-2">
          <div className="grid grid-cols-4 gap-px text-[9px] uppercase tracking-wider text-white/30 bg-zinc-900 p-2">
            <span>Item</span><span className="text-right">HSN/SAC</span><span className="text-right">Qty</span><span className="text-right">Amount</span>
          </div>
          {[
            { name: 'DC-DC Converter', hsn: '85044090', qty: '1', amt: '₹4,200' },
            { name: 'Diagnostic Labour', hsn: '998714', qty: '1hr', amt: '₹500' },
          ].map((item, i) => (
            <div key={i} className="grid grid-cols-4 gap-px text-xs text-white/60 px-2 py-1.5 border-t border-zinc-700/30">
              <span className="text-white/80">{item.name}</span><span className="text-right font-mono text-[10px]">{item.hsn}</span><span className="text-right">{item.qty}</span><span className="text-right text-white">{item.amt}</span>
            </div>
          ))}
        </div>
        <Row label="Subtotal" value="₹4,700" />
        <Row label="CGST @ 9%" value="₹423" />
        <Row label="SGST @ 9%" value="₹423" />
        <Row label="Grand Total" value="₹5,546" bold border />
      </div>
    ),
  },
  {
    title: 'Customer Approves',
    badge: 'CUSTOMER',
    icon: CheckCircle,
    section: 2,
    caption: 'Customers approve from their portal or phone. No phone tag. No WhatsApp confusion. Instant approval.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 rounded-full bg-[#CBFF00]/10 border border-[#CBFF00]/20 flex items-center justify-center text-[10px] font-bold text-[#CBFF00]">VM</div>
          <div>
            <div className="text-xs font-bold text-white">Volt Motors EV Service</div>
            <div className="text-[10px] text-white/30">Estimate for your vehicle</div>
          </div>
        </div>
        <div className="bg-zinc-900/60 rounded p-3 border border-zinc-700/40 space-y-1.5">
          <div className="flex justify-between text-xs"><span className="text-white/50">DC-DC Converter</span><span className="text-white">{'₹'}4,200</span></div>
          <div className="flex justify-between text-xs"><span className="text-white/50">Diagnostic Labour</span><span className="text-white">{'₹'}500</span></div>
          <div className="flex justify-between text-xs border-t border-zinc-700/30 pt-1.5 font-bold"><span className="text-white">Total (incl. GST)</span><span className="text-[#CBFF00]">{'₹'}5,546</span></div>
        </div>
        <div className="flex gap-2">
          <button className="flex-1 bg-emerald-500 text-white text-xs font-bold py-2.5 rounded text-center">{'✓'} Approve</button>
          <button className="flex-1 bg-zinc-700 text-white/50 text-xs font-bold py-2.5 rounded text-center">{'✗'} Decline</button>
        </div>
      </div>
    ),
  },
  {
    title: 'GST Invoice in One Click',
    badge: 'ACCOUNTANT',
    icon: FileText,
    section: 2,
    caption: 'Estimate \u2192 customer approved \u2192 one-click invoice \u2192 GST auto-calculated with HSN/SAC \u2192 GSTR-1 & 3B ready \u2192 filed. The complete digital billing chain.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs font-bold text-white/70">Tax Invoice INV-2026-0398</div>
          <span className="text-[9px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">GST COMPLIANT</span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between text-white/50"><span>Motor Controller Repair</span><span className="text-white">{'₹'}3,200</span></div>
          <div className="flex justify-between text-white/50"><span>BMS Diagnostic (SAC: 9987)</span><span className="text-white">{'₹'}1,500</span></div>
          <div className="border-t border-zinc-700 pt-2 flex justify-between text-white/50"><span>Subtotal</span><span className="text-white">{'₹'}4,700</span></div>
          <div className="flex justify-between text-white/50"><span>CGST @ 9%</span><span className="text-white">{'₹'}423</span></div>
          <div className="flex justify-between text-white/50"><span>SGST @ 9%</span><span className="text-white">{'₹'}423</span></div>
          <div className="border-t border-zinc-700 pt-2 flex justify-between font-bold text-sm"><span className="text-white">Grand Total</span><span className="text-[#CBFF00]">{'₹'}5,546</span></div>
        </div>
      </div>
    ),
  },
  {
    title: 'Track Every Payment',
    badge: 'ACCOUNTANT',
    icon: CreditCard,
    section: 2,
    caption: 'Cash, UPI, card, bank transfer, Razorpay. Every rupee tracked. Auto-posted to your books.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs font-bold text-white/70">Payment — INV-2026-0398</div>
          <span className="text-[9px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">PAID</span>
        </div>
        <div className="space-y-2">
          {[
            { method: 'UPI', amount: '₹3,000', icon: '◎', time: 'Today 2:30 PM' },
            { method: 'Cash', amount: '₹2,546', icon: '■', time: 'Today 2:35 PM' },
          ].map((p, i) => (
            <div key={i} className="flex items-center justify-between bg-zinc-900/60 rounded p-2.5 border border-zinc-700/40">
              <div className="flex items-center gap-2">
                <span className="text-[#CBFF00] text-sm">{p.icon}</span>
                <div><div className="text-xs text-white">{p.method}</div><div className="text-[10px] text-white/30">{p.time}</div></div>
              </div>
              <span className="text-xs font-bold text-emerald-400">{p.amount}</span>
            </div>
          ))}
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded p-2.5 flex justify-between items-center">
          <span className="text-[10px] text-emerald-400 uppercase tracking-wider font-medium">Balance</span>
          <span className="text-lg font-bold text-emerald-400">{'₹'}0</span>
        </div>
      </div>
    ),
  },
  {
    title: 'Inventory That Thinks',
    badge: 'MANAGER',
    icon: Package,
    section: 3,
    caption: 'Real-time stock for 100+ EV models. Low stock alerts. Auto reorder. COGS tracked per service ticket.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="text-xs font-bold text-white/70 mb-1">Inventory Alert</div>
        <div className="bg-red-500/5 border border-red-500/20 rounded p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-white">DC-DC Converter 48V</span>
            <span className="text-[9px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded font-bold">LOW STOCK</span>
          </div>
          <div className="text-[10px] text-white/40">HSN: 85044090 | Stock: 2 units | Reorder: 10</div>
          <div className="mt-2 bg-red-500/10 rounded px-2.5 py-1.5 text-[10px] text-red-300">Auto-reorder triggered for 10 units</div>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 bg-zinc-900/60 border border-zinc-700/40 rounded p-2.5 text-center">
            <div className="text-[9px] text-white/30 uppercase tracking-wider">Total SKUs</div>
            <div className="text-lg font-bold text-white">156</div>
          </div>
          <div className="flex-1 bg-zinc-900/60 border border-zinc-700/40 rounded p-2.5 text-center">
            <div className="text-[9px] text-white/30 uppercase tracking-wider">COGS Tracked</div>
            <div className="text-lg font-bold text-[#CBFF00]">{'₹'}2.4L</div>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'Fleet Operations',
    badge: 'FLEET OPERATOR',
    icon: Truck,
    section: 3,
    caption: 'Quick Commerce. FMCG Delivery. Ride-Hailing. India\'s fleet operators manage all vehicles, tickets, and billing in one view. Bulk payment supported.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-white">Delhi EV Fleet Pvt Ltd</div>
          <span className="text-[9px] bg-blue-500/15 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded">AMC ACTIVE</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: 'Vehicles', value: '24', color: '#3b82f6' },
            { label: 'Active Tickets', value: '3', color: '#f59e0b' },
            { label: 'Resolved (Mar)', value: '12', color: '#10b981' },
          ].map((s, i) => (
            <div key={i} className="bg-zinc-900/60 border border-zinc-700/40 rounded p-2.5 text-center">
              <div className="text-lg font-bold" style={{ color: s.color }}>{s.value}</div>
              <div className="text-[9px] text-white/30 uppercase tracking-wider">{s.label}</div>
            </div>
          ))}
        </div>
        <div className="bg-blue-500/5 border border-blue-500/20 rounded p-2.5 text-[10px] text-blue-300">Bulk payment available: {'₹'}1,24,000 for 12 resolved tickets</div>
      </div>
    ),
  },
  {
    title: 'HR & Payroll',
    badge: 'OWNER',
    icon: Users,
    section: 3,
    caption: 'Attendance to payslip. PF, ESI, PT, TDS auto-calculated. Indian labour compliance built in.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-2">
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs font-bold text-white/70">Payroll Summary — March 2026</div>
          <span className="text-[10px] text-white/30">5 employees</span>
        </div>
        <Row label="Gross Salary" value={'₹' + '2,00,000'} />
        <Row label="PF @ 12%" value={'-₹' + '12,000'} />
        <Row label="ESI" value={'-₹' + '1,500'} />
        <Row label="TDS" value={'-₹' + '3,500'} />
        <Row label="Net Payable" value={'₹' + '1,83,000'} bold border />
        <div className="pt-1">
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded p-2 text-center text-[10px] text-emerald-400 font-medium">All statutory deductions auto-calculated</div>
        </div>
      </div>
    ),
  },
  {
    title: 'GST Filing Ready',
    badge: 'ACCOUNTANT',
    icon: FileCheck,
    section: 3,
    caption: 'GSTR-1 and GSTR-3B auto-generated. HSN validated. One-click Tally export. Save 24+ days per year on GST filing.',
    mockup: () => (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4 space-y-3">
        <div className="text-xs font-bold text-white/70 mb-1">GST Dashboard — March 2026</div>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-zinc-900/60 border border-zinc-700/40 rounded p-2.5">
            <div className="text-[9px] text-white/30 uppercase tracking-wider mb-1">GSTR-1</div>
            <div className="text-sm font-bold text-white">42 invoices</div>
            <div className="text-[10px] text-white/40">{'₹'}8,40,000 taxable</div>
          </div>
          <div className="bg-zinc-900/60 border border-zinc-700/40 rounded p-2.5">
            <div className="text-[9px] text-white/30 uppercase tracking-wider mb-1">GSTR-3B</div>
            <div className="text-[10px] text-white/40">Output: {'₹'}1,51,200</div>
            <div className="text-[10px] text-white/40">ITC: {'₹'}48,000</div>
          </div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded p-2.5 flex justify-between items-center">
          <span className="text-[10px] text-amber-400 uppercase tracking-wider font-medium">Net GST Liability</span>
          <span className="text-base font-bold text-amber-400">{'₹'}1,03,200</span>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 bg-zinc-900/60 border border-zinc-700/30 rounded p-2 text-center text-[10px] text-white/40 hover:text-[#CBFF00] cursor-pointer transition">Download JSON</div>
          <div className="flex-1 bg-zinc-900/60 border border-zinc-700/30 rounded p-2 text-center text-[10px] text-white/40 hover:text-[#CBFF00] cursor-pointer transition">Export Tally XML</div>
        </div>
      </div>
    ),
  },
  {
    title: 'EVFI Brain Gets Smarter',
    badge: 'PLATFORM',
    icon: Brain,
    section: 4,
    caption: 'Every resolved ticket makes EVFI smarter. 5 Lakh+ EV technicians needed in India — EVFI gives them expert-level intelligence from day one.',
    mockup: () => (
      <div className="space-y-2.5">
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-bold text-purple-400 tracking-wider">INTELLIGENCE LOOP</span>
          </div>
          <div className="space-y-2">
            {[
              { label: 'Ticket Resolved', icon: '→', desc: 'Failure card created' },
              { label: 'Anonymized', icon: '→', desc: 'Pattern extracted' },
              { label: 'EVFI Updated', icon: '✓', desc: 'All technicians benefit' },
            ].map((s, i) => (
              <div key={i} className="flex items-center gap-3 bg-zinc-900/60 rounded p-2.5 border border-zinc-700/40">
                <span className="text-purple-400 text-sm w-4 text-center">{s.icon}</span>
                <div>
                  <div className="text-xs text-white/70 font-medium">{s.label}</div>
                  <div className="text-[10px] text-white/30">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 bg-purple-500/10 border border-purple-500/20 rounded p-2.5 text-center">
            <div className="text-[9px] text-purple-400 uppercase tracking-wider">Patterns</div>
            <div className="text-lg font-bold text-purple-300">990+</div>
          </div>
          <div className="flex-1 bg-purple-500/10 border border-purple-500/20 rounded p-2.5 text-center">
            <div className="text-[9px] text-purple-400 uppercase tracking-wider">Knowledge</div>
            <div className="text-lg font-bold text-purple-300">795+</div>
          </div>
        </div>
      </div>
    ),
  },
  {
    title: 'Your Complete EV Service OS',
    badge: 'ALL AUDIENCES',
    icon: LayoutGrid,
    section: 4,
    isFinal: true,
    caption: '₹25,000 Cr EV aftermarket by 2030. Is your service & maintenance business ready? 16 modules. 3 portals. One subscription.',
    mockup: () => {
      const mods = [
        'Tickets & SLA', 'Invoicing', 'Estimates', 'Inventory',
        'GST Compliance', 'Accounting', 'HR & Payroll', 'EVFI™ AI',
        'Credit Notes', 'Period Locking', 'Reports', 'AMC Contracts',
        'Customer Portal', 'Tech Portal', 'Fleet Portal', 'Projects',
      ];
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-1.5">
            {mods.map((m, i) => (
              <div key={i} className="bg-zinc-800 border border-zinc-700/50 rounded p-2 text-center hover:border-[#CBFF00]/30 hover:bg-[#CBFF00]/5 transition">
                <div className="text-[10px] text-white/60 leading-tight">{m}</div>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            {[
              { label: 'Modules', val: '16', color: '#CBFF00' },
              { label: 'Portals', val: '3', color: '#14b8a6' },
              { label: 'EV Categories', val: '5', color: '#3b82f6' },
            ].map((s, i) => (
              <div key={i} className="flex-1 bg-zinc-900/60 border border-zinc-700/40 rounded p-2 text-center">
                <div className="text-lg font-bold" style={{ color: s.color }}>{s.val}</div>
                <div className="text-[9px] text-white/30 uppercase tracking-wider">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      );
    },
  },
];

export default function ProductTour({ isOpen, onClose, onStartTrial, startStep = 0 }) {
  const [step, setStep] = useState(0);

  const goNext = useCallback(() => setStep(s => Math.min(s + 1, STEPS.length - 1)), []);
  const goPrev = useCallback(() => setStep(s => Math.max(s - 1, 0)), []);

  useEffect(() => {
    if (!isOpen) return;
    setStep(Math.min(Math.max(startStep, 0), STEPS.length - 1));
  }, [isOpen, startStep]);

  useEffect(() => {
    if (!isOpen) return;
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
  const currentSection = SECTIONS[current.section];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4" data-testid="product-tour-overlay">
      <div className="bg-zinc-900 border border-white/10 rounded-lg max-w-lg w-full shadow-2xl overflow-hidden" data-testid="product-tour-card">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.07]">
          <div className="flex items-center gap-2.5">
            <Icon className="w-4 h-4" style={{ color: currentSection.accent }} />
            <span className="text-sm font-bold text-white">{current.title}</span>
            <B color={currentSection.accent}>{current.badge}</B>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white transition" data-testid="product-tour-close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mockup */}
        <div className="px-6 py-5 min-h-[280px]">
          {current.mockup()}
        </div>

        {/* Caption + Nav */}
        <div className="px-6 pb-5 space-y-4">
          <p className="text-sm text-white/50 leading-relaxed">{current.caption}</p>

          <div className="flex items-center justify-between">
            {/* Grouped dots */}
            <div className="flex items-center gap-3">
              {SECTIONS.map((sec, si) => (
                <div key={si} className="flex flex-col items-center gap-1">
                  <div className="flex gap-1">
                    {sec.steps.map(i => (
                      <button
                        key={i}
                        onClick={() => setStep(i)}
                        className="rounded-full transition"
                        style={{
                          width: i === step ? 10 : 6,
                          height: i === step ? 10 : 6,
                          background: i === step ? sec.accent : current.section === si ? `${sec.accent}44` : 'rgba(255,255,255,0.12)',
                        }}
                        data-testid={`tour-dot-${i}`}
                      />
                    ))}
                  </div>
                </div>
              ))}
              <span className="text-[10px] text-white/25 font-mono ml-1">{step + 1}/{STEPS.length}</span>
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
                  Start Free Trial <ArrowRight className="w-3.5 h-3.5" />
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
