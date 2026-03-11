import { useNavigate } from "react-router-dom";
import { Lock, ArrowRight } from "lucide-react";
import { getModuleDescription, getPlanDetails, getMinPlan } from "../config/planConfig";

export default function UpgradePrompt({ modulePath, currentPlan, onClose }) {
  const navigate = useNavigate();
  const moduleInfo = getModuleDescription(modulePath);
  const currentPlanDetails = getPlanDetails(currentPlan);
  const requiredPlanId = moduleInfo?.minPlan || getMinPlan(modulePath);
  const requiredPlanDetails = getPlanDetails(requiredPlanId);

  const title = moduleInfo?.title || "Premium Feature";
  const description = moduleInfo?.description || "This feature requires a higher plan. Upgrade to unlock it.";

  return (
    <div className="flex items-center justify-center min-h-[60vh] px-6" data-testid="upgrade-prompt-wrapper">
      <div className="max-w-lg w-full bg-[#0f1419] rounded-2xl border border-white/10 p-8 text-center">
        {/* Lock icon */}
        <div className="w-16 h-16 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <Lock className="w-8 h-8 text-amber-400" data-testid="upgrade-prompt-lock-icon" />
        </div>

        {/* Module title */}
        <h2 className="text-2xl font-bold text-white mb-2" data-testid="upgrade-prompt-title">
          {title}
        </h2>

        {/* Description */}
        <p className="text-gray-400 mb-6 leading-relaxed" data-testid="upgrade-prompt-description">
          {description}
        </p>

        {/* Plan comparison */}
        <div className="bg-white/5 rounded-xl p-4 mb-6 border border-white/5" data-testid="upgrade-prompt-plan-comparison">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-gray-500 text-xs">Your Plan</p>
              <p className="text-white font-medium">{currentPlanDetails.name}</p>
            </div>
            <ArrowRight className="w-5 h-5 text-[#CBFF00]" />
            <div>
              <p className="text-gray-500 text-xs">Required</p>
              <p className="text-[#CBFF00] font-medium">
                {requiredPlanDetails.name}
                {requiredPlanDetails.price > 0 && (
                  <span className="text-gray-500 text-sm ml-1">
                    &#8377;{requiredPlanDetails.price}/mo
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate("/subscription")}
          className="w-full bg-[#CBFF00] text-[#0a0e12] font-bold py-3 rounded-lg hover:bg-[#d4ff33] transition-colors mb-3"
          data-testid="upgrade-prompt-upgrade-btn"
        >
          UPGRADE TO {requiredPlanDetails.name.toUpperCase()} &rarr;
        </button>

        <button
          onClick={onClose || (() => navigate(-1))}
          className="text-gray-500 text-sm hover:text-gray-300 transition-colors"
          data-testid="upgrade-prompt-back-btn"
        >
          &larr; Go back
        </button>
      </div>
    </div>
  );
}
