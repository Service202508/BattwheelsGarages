import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ProfitLoss() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState(`${new Date().getFullYear()}-01-01`);
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState('');

  const fetchReport = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const orgId = localStorage.getItem('organization_id') || '';
      const res = await fetch(
        `${API}/api/v1/journal-entries/reports/profit-loss?start_date=${startDate}&end_date=${endDate}`,
        { headers: { Authorization: `Bearer ${token}`, 'X-Organization-ID': orgId } }
      );
      if (!res.ok) throw new Error('Failed to load P&L report');
      const result = await res.json();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReport(); }, []);

  const Section = ({ title, items, color }) => {
    const total = items?.reduce((sum, a) => sum + (a.balance || a.amount || 0), 0) || 0;
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-xs uppercase tracking-wider text-[rgba(244,246,240,0.4)] pb-1 border-b border-[rgba(244,246,240,0.06)]">
          <span>{title}</span>
          <span className={`font-mono ${color}`}>{total.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</span>
        </div>
        {items && items.length > 0 ? items.map((item, i) => (
          <div key={i} className="flex justify-between py-1 text-sm">
            <span className="text-[rgba(244,246,240,0.6)] pl-3">{item.account_name || item.name || 'Unknown'}</span>
            <span className="font-mono text-[rgba(244,246,240,0.8)]">{(item.balance || item.amount || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</span>
          </div>
        )) : (
          <p className="text-xs text-[rgba(244,246,240,0.25)] pl-3 py-1">No entries</p>
        )}
      </div>
    );
  };

  const revenue = data?.revenue || data?.income || [];
  const cogs = data?.cost_of_goods_sold || data?.cogs || [];
  const expenses = data?.expenses || data?.operating_expenses || [];
  const totalRevenue = revenue.reduce((s, a) => s + (a.balance || a.amount || 0), 0);
  const totalCogs = cogs.reduce((s, a) => s + (a.balance || a.amount || 0), 0);
  const totalExpenses = expenses.reduce((s, a) => s + (a.balance || a.amount || 0), 0);
  const grossProfit = totalRevenue - totalCogs;
  const netProfit = grossProfit - totalExpenses;

  return (
    <div data-testid="profit-loss-page" className="min-h-screen bg-[#0B0B0F] text-[#F4F6F0] p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-[#C8FF00]" />
          <h1 className="text-2xl font-bold tracking-tight">Profit & Loss</h1>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-[rgba(244,246,240,0.5)]" />
          <Input type="date" data-testid="start-date" value={startDate} onChange={e => setStartDate(e.target.value)} className="w-36 bg-[#0D0D14] border-[rgba(244,246,240,0.12)] text-[#F4F6F0] text-sm" />
          <span className="text-[rgba(244,246,240,0.3)] text-sm">to</span>
          <Input type="date" data-testid="end-date" value={endDate} onChange={e => setEndDate(e.target.value)} className="w-36 bg-[#0D0D14] border-[rgba(244,246,240,0.12)] text-[#F4F6F0] text-sm" />
          <Button data-testid="refresh-pl-btn" onClick={fetchReport} className="bg-[#C8FF00] text-black hover:bg-[#B8EF00] text-sm font-semibold">Refresh</Button>
        </div>
      </div>

      {error && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

      {loading ? (
        <div className="text-center py-12 text-[rgba(244,246,240,0.4)]">Loading P&L report...</div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: 'Revenue', value: totalRevenue, icon: TrendingUp, color: 'text-[#C8FF00]' },
              { label: 'COGS', value: totalCogs, icon: DollarSign, color: 'text-orange-400' },
              { label: 'Gross Profit', value: grossProfit, icon: TrendingUp, color: grossProfit >= 0 ? 'text-emerald-400' : 'text-red-400' },
              { label: 'Net Profit', value: netProfit, icon: netProfit >= 0 ? TrendingUp : TrendingDown, color: netProfit >= 0 ? 'text-emerald-400' : 'text-red-400' },
            ].map((c, i) => (
              <Card key={i} className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
                <CardContent className="py-3 px-4">
                  <div className="flex items-center gap-2 mb-1">
                    <c.icon className={`w-3.5 h-3.5 ${c.color}`} />
                    <span className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.4)]">{c.label}</span>
                  </div>
                  <span data-testid={`pl-${c.label.toLowerCase().replace(/\s/g, '-')}`} className={`text-lg font-mono font-bold ${c.color}`}>
                    {c.value.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Detail Sections */}
          <Card className="bg-[#14141B] border-[rgba(244,246,240,0.08)]">
            <CardContent className="space-y-6 pt-6">
              <Section title="Revenue" items={revenue} color="text-[#C8FF00]" />
              <Section title="Cost of Goods Sold" items={cogs} color="text-orange-400" />
              <div className="flex justify-between py-2 border-y border-[rgba(244,246,240,0.1)] text-sm font-semibold">
                <span>Gross Profit</span>
                <span className={grossProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}>{grossProfit.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</span>
              </div>
              <Section title="Operating Expenses" items={expenses} color="text-red-400" />
              <div className="flex justify-between py-3 border-t-2 border-[#C8FF00]/30 text-base font-bold">
                <span>Net Profit</span>
                <span data-testid="net-profit" className={netProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                  {netProfit.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
                </span>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
