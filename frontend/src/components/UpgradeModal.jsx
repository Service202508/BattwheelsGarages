import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { X, Zap, ArrowRight, Star } from "lucide-react";

/**
 * Global Upgrade Modal
 * Shown when the API returns a 403 feature_not_available error.
 * Triggered via a custom DOM event: "feature_not_available"
 */

const PLAN_DESCRIPTIONS = {
  starter: "Advanced Reports, EFI Intelligence, AMC",
  professional: "Payroll, Projects, E-Invoice, Accounting, HR",
  enterprise: "Multi-Warehouse, Stock Transfers, SSO, White-Label",
};

export default function UpgradeModal() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [featureInfo, setFeatureInfo] = useState(null);

  useEffect(() => {
    const handleEvent = (e) => {
      setFeatureInfo(e.detail);
      setIsOpen(true);
    };
    window.addEventListener("feature_not_available", handleEvent);
    return () => window.removeEventListener("feature_not_available", handleEvent);
  }, []);

  if (!isOpen || !featureInfo) return null;

  const { feature, current_plan, required_plan, message, upgrade_url } = featureInfo;
  const reqPlanDisplay = required_plan
    ? required_plan.charAt(0).toUpperCase() + required_plan.slice(1)
    : "a higher plan";
  const currentPlanDisplay = current_plan
    ? current_plan.charAt(0).toUpperCase() + current_plan.slice(1)
    : "Free";

  const handleViewPlans = () => {
    setIsOpen(false);
    navigate(upgrade_url || "/settings/billing");
  };

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      data-testid="upgrade-modal-overlay"
      onClick={(e) => e.target === e.currentTarget && setIsOpen(false)}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
        data-testid="upgrade-modal"
      >
        {/* Accent bar */}
        <div className="h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500" />

        {/* Close button */}
        <button
          onClick={() => setIsOpen(false)}
          className="absolute top-4 right-4 text-slate-500 hover:text-white transition p-1 rounded-lg hover:bg-slate-800"
          data-testid="upgrade-modal-close"
        >
          <X size={18} />
        </button>

        <div className="p-6">
          {/* Icon + Title */}
          <div className="flex items-start gap-4 mb-5">
            <div className="flex-shrink-0 w-12 h-12 bg-amber-500/20 rounded-xl flex items-center justify-center border border-amber-500/30">
              <Zap size={22} className="text-amber-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-lg leading-snug" data-testid="upgrade-modal-title">
                Feature Not Available
              </h2>
              <p className="text-slate-400 text-sm mt-0.5">
                <span className="text-amber-400 font-medium">{feature}</span> requires {reqPlanDisplay} plan
              </p>
            </div>
          </div>

          {/* Plan comparison */}
          <div className="bg-slate-800/60 rounded-xl p-4 mb-5 border border-slate-700/50">
            <div className="flex items-center justify-between text-sm mb-3">
              <div className="text-center">
                <p className="text-slate-400 text-xs mb-1">Current Plan</p>
                <span className="px-3 py-1 bg-slate-700 text-slate-300 rounded-full text-xs font-medium capitalize">
                  {currentPlanDisplay}
                </span>
              </div>
              <ArrowRight size={16} className="text-slate-600" />
              <div className="text-center">
                <p className="text-slate-400 text-xs mb-1">Required Plan</p>
                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-medium capitalize">
                  {reqPlanDisplay}
                </span>
              </div>
            </div>
            <p className="text-slate-400 text-xs text-center leading-relaxed">
              {PLAN_DESCRIPTIONS[required_plan] || message || `Upgrade to ${reqPlanDisplay} to access ${feature}`}
            </p>
          </div>

          {/* Message */}
          <p className="text-slate-300 text-sm mb-5 leading-relaxed text-center">
            {message || `Upgrade your plan to unlock ${feature} and many more premium features.`}
          </p>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => setIsOpen(false)}
              className="flex-1 px-4 py-2.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 text-sm transition"
              data-testid="upgrade-modal-dismiss"
            >
              Maybe Later
            </button>
            <button
              onClick={handleViewPlans}
              className="flex-1 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition flex items-center justify-center gap-2"
              data-testid="upgrade-modal-view-plans"
            >
              <Star size={15} />
              View Plans
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
