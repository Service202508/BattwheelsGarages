import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Lock, Unlock, AlertTriangle, Calendar, Shield } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

export default function PeriodLocks({ user }) {
  const [locks, setLocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [locking, setLocking] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [lockReason, setLockReason] = useState('');
  const [error, setError] = useState('');

  const fetchLocks = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/finance/period-locks`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      const data = await res.json();
      setLocks(data.data || []);
    } catch {
      setError('Failed to load period locks');
    } finally {
      setLoading(false);
    }
  }, [user?.token]);

  useEffect(() => { fetchLocks(); }, [fetchLocks]);

  const handleLock = async () => {
    setLocking(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/v1/finance/period-locks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: JSON.stringify({ period_month: selectedMonth, period_year: selectedYear, lock_reason: lockReason })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to lock period');
      setShowConfirm(false);
      setLockReason('');
      fetchLocks();
    } catch (e) {
      setError(e.message);
    } finally {
      setLocking(false);
    }
  };

  const activeLocks = locks.filter(l => !l.unlocked_at);
  const isLocked = (m, y) => activeLocks.some(l => l.period_month === m && l.period_year === y);

  return (
    <div data-testid="period-locks-page" className="min-h-screen bg-bw-black text-bw-white p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-bw-volt" />
          <h1 className="text-2xl font-bold tracking-tight">Period Locks</h1>
        </div>
        {(user?.role === 'owner' || user?.role === 'admin') && (
          <Button
            data-testid="lock-period-btn"
            onClick={() => setShowConfirm(true)}
            className="bg-bw-volt text-black hover:bg-bw-volt-hover font-semibold"
          >
            <Lock className="w-4 h-4 mr-2" /> Lock a Period
          </Button>
        )}
      </div>

      <p className="text-sm text-bw-white/50">
        Locked periods prevent any financial transactions from being created, modified, or deleted within that timeframe.
      </p>

      {error && (
        <div data-testid="period-lock-error" className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Lock Dialog */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <Card data-testid="lock-confirm-dialog" className="bg-bw-panel border-bw-white/10 w-full max-w-md">
            <CardHeader className="border-b border-bw-white/[0.06]">
              <CardTitle className="text-bw-white flex items-center gap-2 text-lg">
                <AlertTriangle className="w-5 h-5 text-amber-400" /> Confirm Period Lock
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="flex gap-3">
                <select
                  data-testid="lock-month-select"
                  value={selectedMonth}
                  onChange={e => setSelectedMonth(Number(e.target.value))}
                  className="flex-1 bg-bw-black border border-bw-white/[0.12] rounded-md px-3 py-2 text-bw-white text-sm"
                >
                  {MONTHS.map((m, i) => (
                    <option key={i} value={i + 1} disabled={isLocked(i + 1, selectedYear)}>{m}</option>
                  ))}
                </select>
                <select
                  data-testid="lock-year-select"
                  value={selectedYear}
                  onChange={e => setSelectedYear(Number(e.target.value))}
                  className="w-24 bg-bw-black border border-bw-white/[0.12] rounded-md px-3 py-2 text-bw-white text-sm"
                >
                  {[2024, 2025, 2026, 2027].map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
              <input
                data-testid="lock-reason-input"
                type="text"
                placeholder="Reason (optional)"
                value={lockReason}
                onChange={e => setLockReason(e.target.value)}
                className="w-full bg-bw-black border border-bw-white/[0.12] rounded-md px-3 py-2 text-bw-white text-sm placeholder:text-bw-white/30"
              />
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/15 text-amber-300 text-xs leading-relaxed">
                Locking <strong>{MONTHS[selectedMonth - 1]} {selectedYear}</strong> is irreversible by org users.
                All financial transactions in this period will be frozen. Only a platform administrator can unlock.
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button
                  data-testid="lock-cancel-btn"
                  variant="outline"
                  onClick={() => { setShowConfirm(false); setError(''); }}
                  className="border-bw-white/15 text-bw-white hover:bg-bw-white/5"
                >Cancel</Button>
                <Button
                  data-testid="lock-confirm-btn"
                  onClick={handleLock}
                  disabled={locking || isLocked(selectedMonth, selectedYear)}
                  className="bg-red-600 text-white hover:bg-red-700 font-semibold"
                >
                  {locking ? 'Locking...' : 'Lock Period'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Locks Table */}
      <Card className="bg-bw-panel border-bw-white/[0.08]">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-bw-white/40">Loading...</div>
          ) : activeLocks.length === 0 ? (
            <div data-testid="no-locks-message" className="p-12 text-center">
              <Unlock className="w-10 h-10 mx-auto mb-3 text-bw-white/20" />
              <p className="text-bw-white/40 text-sm">No periods are locked. All financial periods are open for transactions.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-bw-white/[0.06] text-bw-white/50 text-xs uppercase tracking-wider">
                  <th className="text-left px-4 py-3">Period</th>
                  <th className="text-left px-4 py-3">Locked By</th>
                  <th className="text-left px-4 py-3">Locked Date</th>
                  <th className="text-left px-4 py-3">Reason</th>
                  <th className="text-left px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {activeLocks.map(lock => (
                  <tr key={lock.lock_id} data-testid={`lock-row-${lock.lock_id}`} className="border-b border-bw-white/[0.04] hover:bg-bw-white/[0.02]">
                    <td className="px-4 py-3 font-medium flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-bw-volt" />
                      {MONTHS[lock.period_month - 1]} {lock.period_year}
                    </td>
                    <td className="px-4 py-3 text-bw-white/70">{lock.locked_by_name || lock.locked_by}</td>
                    <td className="px-4 py-3 text-bw-white/50">{new Date(lock.locked_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-bw-white/50">{lock.lock_reason || '—'}</td>
                    <td className="px-4 py-3">
                      <Badge className="bg-red-500/15 text-red-400 border-0 text-[10px] uppercase tracking-wider">
                        <Lock className="w-3 h-3 mr-1" /> Locked
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
