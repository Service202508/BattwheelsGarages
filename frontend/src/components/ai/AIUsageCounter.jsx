import { useState, useEffect, useCallback } from "react";
import { Zap } from "lucide-react";
import { API } from "@/App";

const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function AIUsageCounter({ compact = false, className = "", onUsageLoaded }) {
  const [usage, setUsage] = useState(null);

  const fetchUsage = useCallback(async () => {
    try {
      const res = await fetch(`${API}/subscriptions/current`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      });
      if (!res.ok) return;
      const data = await res.json();
      const used = data?.usage?.ai_calls_made ?? 0;
      const limit = data?.limits?.ai_calls_per_month ?? 0;
      const isUnlimited = limit === -1;
      const remaining = isUnlimited ? Infinity : Math.max(0, limit - used);
      const percent = isUnlimited ? 0 : limit > 0 ? (used / limit) * 100 : 100;
      const state = { used, limit, isUnlimited, remaining, percent };
      setUsage(state);
      onUsageLoaded?.(state);
    } catch { /* silent */ }
  }, [onUsageLoaded]);

  useEffect(() => { fetchUsage(); }, [fetchUsage]);

  // Expose refresh via custom event
  useEffect(() => {
    const handler = () => fetchUsage();
    window.addEventListener("ai-usage-refresh", handler);
    return () => window.removeEventListener("ai-usage-refresh", handler);
  }, [fetchUsage]);

  if (!usage) return null;

  const { used, limit, isUnlimited, percent } = usage;

  // Color coding: green >50% remaining, amber 25-50%, red <25%
  const remainingPct = 100 - percent;
  const color =
    isUnlimited ? "text-green-400" :
    remainingPct > 50 ? "text-green-400" :
    remainingPct > 25 ? "text-amber-400" :
    "text-red-400";

  const bgColor =
    isUnlimited ? "bg-green-500/10 border-green-500/20" :
    remainingPct > 50 ? "bg-green-500/10 border-green-500/20" :
    remainingPct > 25 ? "bg-amber-500/10 border-amber-500/20" :
    "bg-red-500/10 border-red-500/20";

  const barColor =
    isUnlimited ? "bg-green-500" :
    remainingPct > 50 ? "bg-green-500" :
    remainingPct > 25 ? "bg-amber-500" :
    "bg-red-500";

  const limitText = isUnlimited ? "Unlimited" : limit;

  if (compact) {
    return (
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border ${bgColor} ${className}`}
        data-testid="ai-usage-counter-compact"
        title={`AI calls: ${used}/${limitText}`}
      >
        <Zap className={`h-3.5 w-3.5 ${color}`} />
        <span className={`text-xs font-mono font-medium ${color}`}>
          {used}/{isUnlimited ? "\u221E" : limit}
        </span>
      </div>
    );
  }

  return (
    <div
      className={`flex items-center gap-3 px-3 py-2 rounded-lg border ${bgColor} ${className}`}
      data-testid="ai-usage-counter"
    >
      <Zap className={`h-4 w-4 ${color} shrink-0`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-bw-white/70">AI Calls</span>
          <span className={`text-xs font-mono font-semibold ${color}`}>
            {used}/{limitText}
          </span>
        </div>
        {!isUnlimited && (
          <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${barColor}`}
              style={{ width: `${Math.min(percent, 100)}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
