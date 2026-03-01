import React, { useState, useEffect, useRef } from 'react';
import { Building2, ChevronDown, Check, Plus, Settings, Users, Shield } from 'lucide-react';
import { toast } from 'sonner';
import { useOrganization } from '@/App';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PLAN_BADGE = {
  free:         { bg: "rgba(244,246,240,0.08)", text: "rgba(244,246,240,0.35)", label: "FREE" },
  starter:      { bg: "rgb(var(--bw-blue) / 0.15)",  text: "rgb(var(--bw-blue))",     label: "STARTER" },
  professional: { bg: "rgb(var(--bw-amber) / 0.15)", text: "rgb(var(--bw-amber))",    label: "PROFESSIONAL" },
  enterprise:   { bg: "rgb(var(--bw-volt) / 0.10)",  text: "rgb(var(--bw-volt))",     label: "ENTERPRISE" },
};

function getPlanBadge(planType) {
  return PLAN_BADGE[(planType || "free").toLowerCase()] || PLAN_BADGE.free;
}

const OrganizationSwitcher = ({ onSwitch, user }) => {
  // ── ALL HOOKS FIRST — no conditionals before this block ─────────────────────
  const currentOrg = useOrganization();
  const [isOpen, setIsOpen] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);

  const isPlatformAdmin = user?.is_platform_admin || false;

  useEffect(() => {
    if (!isPlatformAdmin) fetchOrganizations();
  }, [isPlatformAdmin]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  // ── END HOOKS ────────────────────────────────────────────────────────────────

  const fetchOrganizations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/organizations/my-organizations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setOrganizations(data.organizations || []);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const handleSwitch = async (org) => {
    if (org.organization_id === currentOrg?.organization_id) {
      setIsOpen(false);
      return;
    }
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/auth/switch-organization`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ organization_id: org.organization_id })
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        localStorage.setItem('organization', JSON.stringify(data.organization));
        toast.success(`Switched to ${org.name}`);
        setIsOpen(false);
        if (onSwitch) onSwitch(data.organization);
        window.location.reload();
      } else {
        toast.error('Failed to switch organization');
      }
    } catch {
      toast.error('Network error');
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'owner':   return 'bg-purple-500/20 text-purple-400';
      case 'admin':   return 'bg-blue-500/20 text-blue-400';
      case 'manager': return 'bg-emerald-500/20 text-emerald-400';
      default:        return 'bg-slate-500/20 text-slate-400';
    }
  };

  // ── Platform Admin display ───────────────────────────────────────────────────
  if (isPlatformAdmin) {
    return (
      <div
        className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg border border-bw-volt/20"
        data-testid="org-switcher-platform-admin"
      >
        <div className="w-8 h-8 bg-bw-volt/[0.08] rounded-lg flex items-center justify-center">
          <Shield className="w-4 h-4 text-bw-volt" />
        </div>
        <div className="hidden sm:block">
          <p className="text-sm font-medium text-white" data-testid="org-switcher-name">
            Platform Admin
          </p>
          <span
            className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
            style={{ background: "rgb(var(--bw-volt) / 0.10)", color: "rgb(var(--bw-volt))" }}
            data-testid="org-switcher-plan-badge"
          >
            SYSTEM
          </span>
        </div>
      </div>
    );
  }

  // ── Single org (no switcher needed) ─────────────────────────────────────────
  if (organizations.length <= 1) {
    const badge = getPlanBadge(currentOrg?.plan_type);
    return (
      <div
        className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg border border-white/[0.07]"
        data-testid="org-switcher-single"
      >
        <div className="w-8 h-8 bg-bw-volt/[0.08] rounded-lg flex items-center justify-center">
          <Building2 className="w-4 h-4 text-bw-volt" />
        </div>
        <div className="hidden sm:block">
          <p className="text-sm font-medium text-white truncate max-w-[150px]" data-testid="org-switcher-name">
            {currentOrg?.name || 'Organization'}
          </p>
          <span
            className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
            style={{ background: badge.bg, color: badge.text }}
            data-testid="org-switcher-plan-badge"
          >
            {badge.label}
          </span>
        </div>
      </div>
    );
  }

  // ── Multi-org switcher dropdown ──────────────────────────────────────────────
  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg border border-white/[0.07] transition"
        data-testid="org-switcher-btn"
      >
        <div className="w-8 h-8 bg-bw-volt/[0.08] rounded-lg flex items-center justify-center">
          {currentOrg?.logo_url
            ? <img src={currentOrg.logo_url} alt="" className="w-6 h-6 rounded" />
            : <Building2 className="w-4 h-4 text-bw-volt" />}
        </div>
        <div className="hidden sm:block text-left">
          <p className="text-sm font-medium text-white truncate max-w-[150px]" data-testid="org-switcher-name">
            {currentOrg?.name || 'Select Organization'}
          </p>
          {(() => {
            const badge = getPlanBadge(currentOrg?.plan_type);
            return (
              <span
                className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                style={{ background: badge.bg, color: badge.text }}
                data-testid="org-switcher-plan-badge"
              >
                {badge.label}
              </span>
            );
          })()}
        </div>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-72 bg-slate-800 border border-white/[0.07] rounded-xl z-50 overflow-hidden">
          <div className="p-2 border-b border-white/[0.07]">
            <p className="text-xs font-medium text-slate-400 px-2 py-1">YOUR ORGANIZATIONS</p>
          </div>
          <div className="max-h-64 overflow-y-auto py-1">
            {organizations.map((org) => (
              <button
                key={org.organization_id}
                onClick={() => handleSwitch(org)}
                disabled={isLoading}
                className={`w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-700/50 transition ${
                  org.organization_id === currentOrg?.organization_id ? 'bg-slate-700/30' : ''
                }`}
              >
                <div className="w-10 h-10 bg-bw-volt/[0.08] rounded-lg flex items-center justify-center flex-shrink-0">
                  {org.logo_url
                    ? <img src={org.logo_url} alt="" className="w-8 h-8 rounded" />
                    : <Building2 className="w-5 h-5 text-bw-volt" />}
                </div>
                <div className="flex-1 text-left min-w-0">
                  <p className="text-sm font-medium text-white truncate">{org.name}</p>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleColor(org.role)}`}>
                      {org.role}
                    </span>
                    {(() => {
                      const b = getPlanBadge(org.plan_type);
                      return (
                        <span className="text-[10px] font-semibold px-1.5 rounded" style={{ background: b.bg, color: b.text }}>
                          {b.label}
                        </span>
                      );
                    })()}
                  </div>
                </div>
                {org.organization_id === currentOrg?.organization_id && (
                  <Check className="w-4 h-4 text-bw-volt flex-shrink-0" />
                )}
              </button>
            ))}
          </div>
          <div className="p-2 border-t border-white/[0.07] space-y-1">
            <a href="/organization-settings" className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-lg transition">
              <Settings className="w-4 h-4" />
              Organization Settings
            </a>
            <a href="/team" className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-lg transition">
              <Users className="w-4 h-4" />
              Manage Team
            </a>
            <a href="/subscription" className="flex items-center gap-2 px-3 py-2 text-sm text-bw-volt hover:bg-bw-volt/[0.08] rounded-lg transition">
              <Plus className="w-4 h-4" />
              Upgrade Plan
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrganizationSwitcher;
