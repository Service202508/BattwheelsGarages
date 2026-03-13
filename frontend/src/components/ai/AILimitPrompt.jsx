import { useNavigate } from "react-router-dom";
import { Zap, ArrowRight, X } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * AI Limit Prompt - Shown when user hits their AI call limit (429 response)
 * Displays usage info and prompts to upgrade plan
 */
export default function AILimitPrompt({ message, usageInfo, onClose }) {
  const navigate = useNavigate();

  // Extract usage info from message if not provided directly
  const usageText = usageInfo || message || "You've reached your AI call limit for this billing period.";

  return (
    <div 
      className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/30 rounded-xl p-6 text-center"
      data-testid="ai-limit-prompt"
    >
      {/* Icon */}
      <div className="w-14 h-14 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
        <Zap className="w-7 h-7 text-amber-400" />
      </div>

      {/* Title */}
      <h3 className="text-xl font-bold text-white mb-2" data-testid="ai-limit-title">
        AI Call Limit Reached
      </h3>

      {/* Usage message */}
      <p className="text-gray-400 mb-6 leading-relaxed text-sm" data-testid="ai-limit-message">
        {usageText}
      </p>

      {/* Plan comparison hint */}
      <div className="bg-white/5 rounded-lg p-3 mb-5 border border-white/10">
        <div className="flex items-center justify-center gap-3 text-sm">
          <span className="text-gray-400">Current</span>
          <ArrowRight className="w-4 h-4 text-[#CBFF00]" />
          <span className="text-[#CBFF00] font-medium">Upgrade for more AI calls</span>
        </div>
      </div>

      {/* CTAs */}
      <div className="flex flex-col gap-2">
        <Button
          onClick={() => navigate("/subscription")}
          className="w-full bg-[#CBFF00] text-[#0a0e12] font-bold py-3 hover:bg-[#d4ff33]"
          data-testid="ai-limit-upgrade-btn"
        >
          Upgrade Plan
        </Button>
        
        {onClose && (
          <Button
            variant="ghost"
            onClick={onClose}
            className="text-gray-500 text-sm hover:text-gray-300"
            data-testid="ai-limit-close-btn"
          >
            <X className="w-4 h-4 mr-1" /> Close
          </Button>
        )}
      </div>
    </div>
  );
}
