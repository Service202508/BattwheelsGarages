import React, { useState, useEffect } from 'react';
import { Zap, ChevronDown, ChevronUp, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';
import { API } from '../App';

const ConfidenceBadge = ({ level }) => {
  const colors = {
    high: 'bg-green-900/50 text-green-400 border-green-700',
    medium: 'bg-amber-900/50 text-amber-400 border-amber-700',
    low: 'bg-red-900/50 text-red-400 border-red-700',
  };
  const style = colors[level?.toLowerCase()] || colors.low;
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded border ${style}`}>
      {level || 'Unknown'}
    </span>
  );
};

const TicketEFIPanel = ({ ticketId, orgId }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [matches, setMatches] = useState([]);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCard, setExpandedCard] = useState(null);

  useEffect(() => {
    if (!ticketId) return;
    const headers = {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
      "Content-Type": "application/json",
    };
    const orgParam = orgId ? `?org_id=${encodeURIComponent(orgId)}` : "";
    const fetchEfiData = async () => {
      setLoading(true);
      try {
        const [matchRes, sessionRes] = await Promise.allSettled([
          fetch(`${API}/efi-guided/suggestions/${ticketId}${orgParam}`, { headers }).then(r => r.ok ? r.json() : null),
          fetch(`${API}/efi-guided/session/ticket/${ticketId}${orgParam}`, { headers }).then(r => r.ok ? r.json() : null),
        ]);
        if (matchRes.status === 'fulfilled' && matchRes.value) {
          setMatches(matchRes.value?.suggested_paths || matchRes.value?.matches || []);
        }
        if (sessionRes.status === 'fulfilled' && sessionRes.value) {
          setSession(sessionRes.value);
        }
      } catch (err) {
        console.error('EVFI panel error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchEfiData();
  }, [ticketId, orgId]);

  return (
    <div className="mt-4 rounded-lg border border-zinc-700 bg-zinc-900 overflow-hidden">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-4 py-3 bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-teal-400" />
          <span className="text-sm font-semibold text-teal-400">Battwheels EVFI™</span>
          <span className="text-xs text-zinc-500">AI-powered diagnostic intelligence</span>
        </div>
        {collapsed ? <ChevronDown className="w-4 h-4 text-zinc-400" /> : <ChevronUp className="w-4 h-4 text-zinc-400" />}
      </button>
      {!collapsed && (
        <div className="p-4 space-y-4">
          {loading ? (
            <div className="text-sm text-zinc-500 text-center py-4">Loading EVFI intelligence...</div>
          ) : (
            <>
              {matches.length > 0 ? (
                <div className="space-y-2" style={{ userSelect: 'none', WebkitUserSelect: 'none' }}>
                  <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Matched Failure Patterns</h4>
                  {matches.map((match, idx) => (
                    <div key={match._id || idx} className="rounded border border-zinc-700 bg-zinc-800/50 p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-zinc-200">{match.failure_title || match.title || 'Unknown Failure'}</span>
                        <ConfidenceBadge level={match.confidence || match.confidence_level} />
                      </div>
                      {match.vehicle_model && <p className="text-xs text-zinc-500 mb-1">{match.vehicle_model}</p>}
                      {match.root_cause && <p className="text-xs text-zinc-400">{match.root_cause}</p>}
                      {match.resolution_steps && (
                        <button onClick={() => setExpandedCard(expandedCard === idx ? null : idx)} className="text-xs text-teal-400 mt-1 hover:underline">
                          {expandedCard === idx ? 'Hide details' : 'View details'}
                        </button>
                      )}
                      {expandedCard === idx && match.resolution_steps && (
                        <div className="mt-2 text-xs text-zinc-400 bg-zinc-900 rounded p-2">
                          {Array.isArray(match.resolution_steps)
                            ? match.resolution_steps.map((step, i) => <p key={i} className="mb-1">{i + 1}. {step}</p>)
                            : match.resolution_steps}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <AlertTriangle className="w-5 h-5 text-zinc-600 mx-auto mb-2" />
                  <p className="text-sm text-zinc-500">No matching patterns found</p>
                </div>
              )}
              <div className="border-t border-zinc-700 pt-3">
                {session ? (
                  <a href={`/ai-diagnostic?ticket=${ticketId}`} className="flex items-center justify-center gap-2 w-full py-2 rounded bg-teal-600/20 text-teal-400 text-sm font-medium hover:bg-teal-600/30 transition-colors">
                    <CheckCircle className="w-4 h-4" />Continue Diagnosis<ArrowRight className="w-4 h-4" />
                  </a>
                ) : (
                  <a href={`/ai-diagnostic?ticket=${ticketId}`} className="flex items-center justify-center gap-2 w-full py-2 rounded bg-teal-600/20 text-teal-400 text-sm font-medium hover:bg-teal-600/30 transition-colors">
                    <Zap className="w-4 h-4" />{`Start EVFI™ Diagnosis`}<ArrowRight className="w-4 h-4" />
                  </a>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default TicketEFIPanel;
