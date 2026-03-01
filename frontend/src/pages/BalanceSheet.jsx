import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { FileText, TrendingUp, TrendingDown, Equal, Calendar } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function BalanceSheet() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState('');

  const fetchReport = async (date) => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const orgId = localStorage.getItem('organization_id') || '';
      const res = await fetch(
        `${API}/api/v1/journal-entries/reports/balance-sheet?as_of_date=${date}`,
        { headers: { Authorization: `Bearer ${token}`, 'X-Organization-ID': orgId } }
      );
      if (!res.ok) throw new Error('Failed to load balance sheet');
      const result = await res.json();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReport(asOfDate); }, []);

  const Section = ({ title, items, icon: Icon, color }) => (
    <Card className="bg-bw-panel border-bw-white/[0.08]">
      <CardHeader className="pb-2 border-b border-bw-white/[0.06]">
        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-bw-white/70">
          <Icon className={`w-4 h-4 ${color}`} /> {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-3">
        {items && items.length > 0 ? items.map((item, i) => (
          <div key={i} className="flex justify-between py-1.5 text-sm border-b border-bw-white/[0.03] last:border-0">
            <span className="text-bw-white/70">{item.account_name || item.name || 'Unknown'}</span>
            <span className="font-mono text-bw-white">
              {(item.balance || item.amount || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}
            </span>
          </div>
        )) : (
          <p className="text-sm text-bw-white/30 py-2">No data for this section</p>
        )}
      </CardContent>
    </Card>
  );

  // Handle both API formats: { accounts: [], total: } or direct array
  const getAccounts = (section) => Array.isArray(section) ? section : (section?.accounts || []);
  const getTotal = (section, accounts) => section?.total ?? accounts.reduce((sum, a) => sum + (a.balance || a.amount || 0), 0);
  
  const assetsAccounts = getAccounts(data?.assets);
  const liabilitiesAccounts = getAccounts(data?.liabilities);
  const equityAccounts = getAccounts(data?.equity);
  
  const totalAssets = getTotal(data?.assets, assetsAccounts);
  const totalLiabilities = getTotal(data?.liabilities, liabilitiesAccounts);
  const totalEquity = getTotal(data?.equity, equityAccounts) + (data?.equity?.retained_earnings || 0);
  const isBalanced = data?.is_balanced ?? Math.abs(totalAssets - (totalLiabilities + totalEquity)) < 0.01;

  return (
    <div data-testid="balance-sheet-page" className="min-h-screen bg-bw-black text-bw-white p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-bw-volt" />
          <h1 className="text-2xl font-bold tracking-tight">Balance Sheet</h1>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-bw-white/50" />
          <Input
            data-testid="as-of-date-input"
            type="date"
            value={asOfDate}
            onChange={e => setAsOfDate(e.target.value)}
            className="w-40 bg-bw-black border-bw-white/[0.12] text-bw-white text-sm"
          />
          <Button
            data-testid="refresh-btn"
            onClick={() => fetchReport(asOfDate)}
            className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover text-sm font-semibold"
          >Refresh</Button>
        </div>
      </div>

      {error && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

      {loading ? (
        <div className="text-center py-12 text-bw-white/40">Loading balance sheet...</div>
      ) : (
        <>
          {/* Accounting Equation */}
          <Card className={`${isBalanced ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
            <CardContent className="py-4">
              <div data-testid="accounting-equation" className="flex items-center justify-center gap-4 text-lg font-mono">
                <span className="text-bw-volt">{totalAssets.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</span>
                <Equal className="w-5 h-5 text-bw-white/50" />
                <span className="text-orange-400">{totalLiabilities.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</span>
                <span className="text-bw-white/30">+</span>
                <span className="text-blue-400">{totalEquity.toLocaleString('en-IN', { style: 'currency', currency: 'INR' })}</span>
                <span className={`text-xs ml-2 px-2 py-0.5 rounded ${isBalanced ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {isBalanced ? 'BALANCED' : 'UNBALANCED'}
                </span>
              </div>
              <p className="text-center text-xs text-bw-white/30 mt-1">Assets = Liabilities + Equity</p>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Section title="Assets" items={assetsAccounts} icon={TrendingUp} color="text-bw-volt" />
            <Section title="Liabilities" items={liabilitiesAccounts} icon={TrendingDown} color="text-orange-400" />
            <Section title="Equity" items={equityAccounts} icon={FileText} color="text-blue-400" />
          </div>
        </>
      )}
    </div>
  );
}
