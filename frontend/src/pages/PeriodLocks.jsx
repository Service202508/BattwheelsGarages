import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Lock, Unlock, Clock, ShieldCheck, AlertTriangle, RefreshCw, Calendar } from "lucide-react";
import { API } from "@/App";
import { apiGet, apiPost } from "@/utils/api";

const STATUS_CONFIG = {
  locked: { label: "Locked", class: "bg-red-500/15 text-red-400 border border-red-500/25", icon: Lock },
  unlocked_amendment: { label: "Amendment", class: "bg-amber-500/15 text-amber-400 border border-amber-500/25", icon: Clock },
  unlocked: { label: "Open", class: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25", icon: Unlock },
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

function formatPeriod(period) {
  if (!period) return "";
  const [y, m] = period.split("-");
  return `${MONTHS[parseInt(m, 10) - 1]} ${y}`;
}

function timeRemaining(expiresAt) {
  if (!expiresAt) return "";
  const diff = new Date(expiresAt) - new Date();
  if (diff <= 0) return "Expired";
  const hrs = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  return `${hrs}h ${mins}m remaining`;
}

export default function PeriodLocks({ user }) {
  const [locks, setLocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [yearFilter, setYearFilter] = useState(new Date().getFullYear());
  const [showLockDialog, setShowLockDialog] = useState(false);
  const [showUnlockDialog, setShowUnlockDialog] = useState(false);
  const [showFYDialog, setShowFYDialog] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [lockForm, setLockForm] = useState({ period: "", reason: "" });
  const [unlockForm, setUnlockForm] = useState({ reason: "", window_hours: 72 });
  const [fyForm, setFyForm] = useState({ year: new Date().getFullYear() - 1, start_month: 4 });
  const [actionLoading, setActionLoading] = useState(false);

  const fetchLocks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiGet(`${API}/period-locks?year=${yearFilter}`);
      if (res.ok) {
        const data = await res.json();
        setLocks(data.locks || []);
      }
    } catch (err) {
      toast.error("Failed to load period locks");
    } finally {
      setLoading(false);
    }
  }, [yearFilter]);

  useEffect(() => { fetchLocks(); }, [fetchLocks]);

  const handleLock = async () => {
    if (!lockForm.period) { toast.error("Select a period"); return; }
    setActionLoading(true);
    try {
      const res = await apiPost(`${API}/period-locks/lock`, {
        period: lockForm.period, reason: lockForm.reason,
      });
      if (res.ok) {
        toast.success(`Period ${formatPeriod(lockForm.period)} locked`);
        setShowLockDialog(false);
        setLockForm({ period: "", reason: "" });
        fetchLocks();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to lock period");
      }
    } catch { toast.error("Network error"); }
    finally { setActionLoading(false); }
  };

  const handleUnlock = async () => {
    if (!unlockForm.reason || unlockForm.reason.length < 10) {
      toast.error("Reason must be at least 10 characters"); return;
    }
    setActionLoading(true);
    try {
      const res = await apiPost(`${API}/period-locks/unlock?period=${selectedPeriod}`, {
        reason: unlockForm.reason, window_hours: unlockForm.window_hours,
      });
      if (res.ok) {
        toast.success(`Period ${formatPeriod(selectedPeriod)} unlocked for amendment`);
        setShowUnlockDialog(false);
        setUnlockForm({ reason: "", window_hours: 72 });
        fetchLocks();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to unlock");
      }
    } catch { toast.error("Network error"); }
    finally { setActionLoading(false); }
  };

  const handleExtend = async (period) => {
    setActionLoading(true);
    try {
      const res = await apiPost(`${API}/period-locks/extend?period=${period}`, {
        additional_hours: 72,
      });
      if (res.ok) {
        toast.success("Unlock window extended by 72 hours");
        fetchLocks();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to extend");
      }
    } catch { toast.error("Network error"); }
    finally { setActionLoading(false); }
  };

  const handleLockFY = async () => {
    setActionLoading(true);
    try {
      const res = await apiPost(`${API}/period-locks/lock-fiscal-year`, {
        year: fyForm.year, fiscal_year_start_month: fyForm.start_month,
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        setShowFYDialog(false);
        fetchLocks();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to lock fiscal year");
      }
    } catch { toast.error("Network error"); }
    finally { setActionLoading(false); }
  };

  const handleAutoRelock = async () => {
    try {
      const res = await apiPost(`${API}/period-locks/auto-relock`, {});
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchLocks();
      }
    } catch { toast.error("Auto-relock failed"); }
  };

  // Build a full 12-month grid for the selected year
  const monthGrid = Array.from({ length: 12 }, (_, i) => {
    const period = `${yearFilter}-${String(i + 1).padStart(2, "0")}`;
    const lock = locks.find((l) => l.period === period);
    const status = lock?.status || "unlocked";
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.unlocked;
    return { period, month: MONTHS[i], lock, status, config };
  });

  const lockedCount = monthGrid.filter((m) => m.status === "locked").length;
  const amendmentCount = monthGrid.filter((m) => m.status === "unlocked_amendment").length;

  const userRole = user?.role || "";
  const canLock = ["admin", "owner", "accountant"].includes(userRole);
  const canUnlock = ["admin", "owner"].includes(userRole);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto" data-testid="period-locks-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-[#C8FF00]" />
            Period Locking
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Lock accounting periods to prevent unauthorized modifications
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={String(yearFilter)} onValueChange={(v) => setYearFilter(Number(v))}>
            <SelectTrigger className="w-28 bg-zinc-800 border-zinc-700 text-white" data-testid="year-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[2024, 2025, 2026, 2027].map((y) => (
                <SelectItem key={y} value={String(y)}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {canUnlock && (
            <Button variant="outline" size="sm" onClick={handleAutoRelock}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800" data-testid="auto-relock-btn">
              <RefreshCw className="w-4 h-4 mr-1" /> Auto-Relock
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-500/10"><Lock className="w-5 h-5 text-red-400" /></div>
            <div>
              <p className="text-2xl font-bold text-white" data-testid="locked-count">{lockedCount}</p>
              <p className="text-xs text-zinc-400">Locked Periods</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10"><Clock className="w-5 h-5 text-amber-400" /></div>
            <div>
              <p className="text-2xl font-bold text-white" data-testid="amendment-count">{amendmentCount}</p>
              <p className="text-xs text-zinc-400">In Amendment</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10"><Unlock className="w-5 h-5 text-emerald-400" /></div>
            <div>
              <p className="text-2xl font-bold text-white" data-testid="open-count">{12 - lockedCount - amendmentCount}</p>
              <p className="text-xs text-zinc-400">Open Periods</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      {canLock && (
        <div className="flex gap-2">
          <Button onClick={() => setShowLockDialog(true)}
            className="bg-red-600 hover:bg-red-700 text-white" data-testid="lock-period-btn">
            <Lock className="w-4 h-4 mr-1" /> Lock Period
          </Button>
          <Button variant="outline" onClick={() => setShowFYDialog(true)}
            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800" data-testid="lock-fy-btn">
            <Calendar className="w-4 h-4 mr-1" /> Lock Fiscal Year
          </Button>
        </div>
      )}

      {/* Month Grid */}
      <div className="grid grid-cols-4 gap-3" data-testid="period-grid">
        {monthGrid.map(({ period, month, lock, status, config }) => {
          const StatusIcon = config.icon;
          return (
            <Card key={period}
              className={`bg-zinc-900 border-zinc-800 transition-all hover:border-zinc-600 ${
                status === "locked" ? "ring-1 ring-red-500/20" : ""
              }`}
              data-testid={`period-card-${period}`}
            >
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white text-sm">{month}</span>
                  <Badge className={config.class + " text-xs px-2 py-0.5"} data-testid={`period-status-${period}`}>
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {config.label}
                  </Badge>
                </div>
                <p className="text-xs text-zinc-500">{period}</p>

                {status === "unlocked_amendment" && lock?.unlock_expires_at && (
                  <div className="flex items-center gap-1 text-xs text-amber-400">
                    <AlertTriangle className="w-3 h-3" />
                    {timeRemaining(lock.unlock_expires_at)}
                  </div>
                )}

                {lock?.locked_by && status === "locked" && (
                  <p className="text-xs text-zinc-500 truncate">
                    Locked by: {lock.locked_by === "system_auto_relock" ? "Auto" : lock.locked_by.slice(0, 12)}
                  </p>
                )}

                {/* Actions per card */}
                <div className="flex gap-1 pt-1">
                  {status === "unlocked" && canLock && (
                    <Button size="sm" variant="ghost"
                      className="text-xs h-7 text-zinc-400 hover:text-red-400 hover:bg-red-500/10"
                      onClick={() => { setLockForm({ period, reason: "" }); setShowLockDialog(true); }}
                      data-testid={`lock-btn-${period}`}
                    >
                      <Lock className="w-3 h-3 mr-1" /> Lock
                    </Button>
                  )}
                  {status === "locked" && canUnlock && (
                    <Button size="sm" variant="ghost"
                      className="text-xs h-7 text-zinc-400 hover:text-amber-400 hover:bg-amber-500/10"
                      onClick={() => { setSelectedPeriod(period); setUnlockForm({ reason: "", window_hours: 72 }); setShowUnlockDialog(true); }}
                      data-testid={`unlock-btn-${period}`}
                    >
                      <Unlock className="w-3 h-3 mr-1" /> Unlock
                    </Button>
                  )}
                  {status === "unlocked_amendment" && canUnlock && (
                    <Button size="sm" variant="ghost"
                      className="text-xs h-7 text-zinc-400 hover:text-blue-400 hover:bg-blue-500/10"
                      onClick={() => handleExtend(period)}
                      disabled={actionLoading}
                      data-testid={`extend-btn-${period}`}
                    >
                      <Clock className="w-3 h-3 mr-1" /> Extend
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Lock Period Dialog */}
      <Dialog open={showLockDialog} onOpenChange={setShowLockDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-red-400" /> Lock Period
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-zinc-300">Period</Label>
              <Select value={lockForm.period} onValueChange={(v) => setLockForm({ ...lockForm, period: v })}>
                <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white mt-1" data-testid="lock-period-select">
                  <SelectValue placeholder="Select month" />
                </SelectTrigger>
                <SelectContent>
                  {monthGrid.filter((m) => m.status === "unlocked").map((m) => (
                    <SelectItem key={m.period} value={m.period}>{m.month} {yearFilter}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-zinc-300">Reason (optional)</Label>
              <Input className="bg-zinc-800 border-zinc-700 text-white mt-1"
                value={lockForm.reason}
                onChange={(e) => setLockForm({ ...lockForm, reason: e.target.value })}
                placeholder="e.g., Month-end close"
                data-testid="lock-reason-input"
              />
            </div>
            <Button onClick={handleLock} disabled={actionLoading}
              className="w-full bg-red-600 hover:bg-red-700" data-testid="confirm-lock-btn">
              {actionLoading ? "Locking..." : "Lock Period"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Unlock Dialog */}
      <Dialog open={showUnlockDialog} onOpenChange={setShowUnlockDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Unlock className="w-5 h-5 text-amber-400" /> Unlock Period — {selectedPeriod && formatPeriod(selectedPeriod)}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-sm text-amber-300">
              <AlertTriangle className="w-4 h-4 inline mr-1" />
              This will open a temporary amendment window. The period will auto-relock after the window expires.
            </div>
            <div>
              <Label className="text-zinc-300">Reason (required, min 10 characters)</Label>
              <Textarea className="bg-zinc-800 border-zinc-700 text-white mt-1"
                value={unlockForm.reason}
                onChange={(e) => setUnlockForm({ ...unlockForm, reason: e.target.value })}
                placeholder="e.g., GSTR-1 amendment for invoice INV-001"
                rows={3}
                data-testid="unlock-reason-input"
              />
              {unlockForm.reason.length > 0 && unlockForm.reason.length < 10 && (
                <p className="text-xs text-red-400 mt-1">{10 - unlockForm.reason.length} more characters needed</p>
              )}
            </div>
            <div>
              <Label className="text-zinc-300">Amendment Window</Label>
              <Select value={String(unlockForm.window_hours)}
                onValueChange={(v) => setUnlockForm({ ...unlockForm, window_hours: Number(v) })}>
                <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white mt-1" data-testid="window-hours-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24">24 hours</SelectItem>
                  <SelectItem value="48">48 hours</SelectItem>
                  <SelectItem value="72">72 hours (default)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleUnlock} disabled={actionLoading || unlockForm.reason.length < 10}
              className="w-full bg-amber-600 hover:bg-amber-700" data-testid="confirm-unlock-btn">
              {actionLoading ? "Unlocking..." : "Unlock for Amendment"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Lock Fiscal Year Dialog */}
      <Dialog open={showFYDialog} onOpenChange={setShowFYDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-red-400" /> Lock Fiscal Year
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-zinc-300">Fiscal Year Starting</Label>
              <Select value={String(fyForm.year)} onValueChange={(v) => setFyForm({ ...fyForm, year: Number(v) })}>
                <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white mt-1" data-testid="fy-year-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[2023, 2024, 2025, 2026].map((y) => (
                    <SelectItem key={y} value={String(y)}>FY {y}-{y + 1}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-xs text-zinc-400">
              This will lock all 12 months from April {fyForm.year} to March {fyForm.year + 1}
            </p>
            <Button onClick={handleLockFY} disabled={actionLoading}
              className="w-full bg-red-600 hover:bg-red-700" data-testid="confirm-lock-fy-btn">
              {actionLoading ? "Locking..." : `Lock FY ${fyForm.year}-${fyForm.year + 1}`}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
