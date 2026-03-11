import { Shield, AlertTriangle, ClipboardList, Wrench, Clock, Package, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";

/**
 * Parse structured EVFI response text into sections.
 * Handles the new Battwheels EVFI™ branded format with emoji markers.
 */
export function parseEVFIResponse(text) {
  if (!text) return { rawText: "", steps: [], rootCauses: [], parts: [] };

  const result = {
    safety: "",
    steps: [],
    rootCauses: [],
    parts: [],
    estimatedTime: "",
    disclaimer: "",
    rawText: text,
  };

  // Extract safety section
  const safetyMatch = text.match(/⚡\s*SAFETY[^\n]*\n([\s\S]*?)(?=📋|🔧|🛒|⏱️|⚠️\s*This|$)/i);
  if (safetyMatch) {
    result.safety = safetyMatch[0].replace(/^⚡\s*SAFETY[^\n]*\n/, "").trim();
  }

  // Extract diagnostic steps
  const stepsMatch = text.match(/📋\s*DIAGNOSTIC STEPS[^\n]*\n([\s\S]*?)(?=🔧|🛒|⏱️|⚠️\s*This|$)/i);
  if (stepsMatch) {
    const stepsBlock = stepsMatch[1];
    const lines = stepsBlock.split("\n").filter((l) => l.trim());
    lines.forEach((line) => {
      const cleaned = line.replace(/^[-•*]\s*/, "").trim();
      if (cleaned) result.steps.push(cleaned);
    });
  }

  // Extract root causes
  const causesMatch = text.match(/🔧\s*PROBABLE ROOT CAUSES[^\n]*\n([\s\S]*?)(?=🛒|⏱️|⚠️\s*This|$)/i);
  if (causesMatch) {
    const lines = causesMatch[1].split("\n").filter((l) => l.trim());
    lines.forEach((line) => {
      const cleaned = line.replace(/^[-•*\d.]+\s*/, "").trim();
      if (cleaned && cleaned.length > 3) result.rootCauses.push(cleaned);
    });
  }

  // Extract parts
  const partsMatch = text.match(/🛒\s*PARTS[^\n]*\n([\s\S]*?)(?=⏱️|⚠️\s*This|$)/i);
  if (partsMatch) {
    const lines = partsMatch[1].split("\n").filter((l) => l.trim());
    lines.forEach((line) => {
      const cleaned = line.replace(/^[-•*]\s*/, "").trim();
      if (cleaned) result.parts.push(cleaned);
    });
  }

  // Extract estimated time
  const timeMatch = text.match(/⏱️\s*ESTIMATED TIME[:\s]*(.*)/i);
  if (timeMatch) {
    result.estimatedTime = timeMatch[1].trim();
  }

  // Extract disclaimer
  const disclaimerMatch = text.match(/⚠️\s*This guidance[\s\S]*/i);
  if (disclaimerMatch) {
    result.disclaimer = disclaimerMatch[0].trim();
  }

  return result;
}

/**
 * Classification badge colors and labels.
 */
const CLASSIFICATION_CONFIG = {
  AI_GUIDED: { dot: "bg-blue-400", bg: "bg-blue-500/15", text: "text-blue-300", border: "border-blue-500/30", label: "Known EV Model" },
  AI_GENERAL: { dot: "bg-amber-400", bg: "bg-amber-500/15", text: "text-amber-300", border: "border-amber-500/30", label: "General Guidance" },
  PATTERN_MATCHED: { dot: "bg-yellow-400", bg: "bg-yellow-500/15", text: "text-yellow-300", border: "border-yellow-500/30", label: "Pattern Matched" },
};

function ClassificationBadge({ classification }) {
  if (!classification?.level) return null;
  const config = CLASSIFICATION_CONFIG[classification.level] || CLASSIFICATION_CONFIG.AI_GENERAL;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium ${config.bg} ${config.text} border ${config.border}`} data-testid="evfi-classification-badge">
      <span className={`w-2 h-2 rounded-full ${config.dot}`} />
      {classification.badge || config.label}
    </span>
  );
}

/**
 * Shared EVFI Response Card — used by EVFIGuidancePanel and TechnicianAIAssistant.
 * Renders the structured, branded EVFI diagnostic response.
 */
export default function EFIResponseCard({
  responseText,
  classification,
  vehicleInfo,
  category,
  description,
  estimatedTime: externalTime,
}) {
  const parsed = parseEVFIResponse(responseText);

  // Extract vehicle/issue from the header block of the response text
  const vehicleLine = responseText?.match(/Vehicle:\s*(.+)/i);
  const issueLine = responseText?.match(/Reported Issue:\s*(.+)/i);

  const vehicleDisplay = vehicleLine?.[1]?.trim() ||
    (vehicleInfo ? `${vehicleInfo.make || ""} ${vehicleInfo.model || ""}`.trim() : "");
  const issueDisplay = issueLine?.[1]?.trim() || description || "";

  const timeDisplay = parsed.estimatedTime || externalTime || "";

  return (
    <div className="space-y-3 w-full max-w-full md:max-w-4xl md:mx-auto overflow-hidden" data-testid="efi-response-card">
      {/* Branded Header */}
      <div className="relative bg-slate-900 border border-[#CBFF00]/20 rounded-xl overflow-hidden" data-testid="efi-branded-header">
        <div className="absolute inset-0 bg-gradient-to-br from-[#CBFF00]/[0.04] to-transparent pointer-events-none" />
        <div className="relative px-3 py-3 sm:px-6 sm:py-4 space-y-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <Zap className="h-5 w-5 text-[#CBFF00] flex-shrink-0" />
              <span className="text-xs sm:text-sm font-bold tracking-wide break-words" style={{ color: "#CBFF00" }}>
                BATTWHEELS EVFI&trade; DIAGNOSTIC REPORT
              </span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {timeDisplay && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-xs text-slate-300" data-testid="efi-time-badge">
                  <Clock className="h-3 w-3 flex-shrink-0" /> {timeDisplay}
                </span>
              )}
              <ClassificationBadge classification={classification} />
            </div>
          </div>
          {vehicleDisplay && (
            <p className="text-sm text-white/80 break-words">
              <span className="text-slate-400">Vehicle:</span> {vehicleDisplay}
              {category && <span className="text-slate-500"> ({category})</span>}
            </p>
          )}
          {issueDisplay && (
            <p className="text-sm text-white/60 break-words">
              <span className="text-slate-400">Issue:</span> {issueDisplay}
            </p>
          )}
        </div>
      </div>

      {/* Safety Precautions */}
      {parsed.safety && (
        <div className="px-3 py-3 sm:px-6 sm:py-4 bg-red-900/20 border border-red-500/40 rounded-xl" data-testid="efi-safety-section">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="h-5 w-5 text-red-400" />
            <span className="text-sm font-semibold text-red-300">Safety Precautions</span>
          </div>
          <div className="text-sm text-red-200/80 whitespace-pre-line leading-relaxed break-words">
            {parsed.safety}
          </div>
        </div>
      )}

      {/* Diagnostic Steps */}
      {parsed.steps.length > 0 && (
        <div className="space-y-2" data-testid="efi-diagnostic-steps">
          <div className="flex items-center gap-2 px-1">
            <ClipboardList className="h-4 w-4 text-[#CBFF00]" />
            <span className="text-sm font-medium text-slate-300">Diagnostic Steps</span>
          </div>
          <div className="space-y-1.5">
            {parsed.steps.map((step, i) => {
              // Try to split "Action — Expected: Result"
              const parts = step.split(/\s*—\s*Expected:\s*/i);
              return (
                <div key={i} className="flex items-start gap-2 sm:gap-3 px-3 py-2 sm:px-4 sm:py-3 bg-slate-800/60 rounded-lg border border-slate-700/50">
                  <span className="w-6 h-6 rounded-full bg-[#CBFF00]/10 text-[#CBFF00] text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white/90 break-words" style={{ overflowWrap: "break-word" }}>{parts[0]}</p>
                    {parts[1] && (
                      <p className="text-xs text-slate-400 mt-1">
                        Expected: <span className="text-emerald-400">{parts[1]}</span>
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Root Causes */}
      {parsed.rootCauses.length > 0 && (
        <div className="px-3 py-3 sm:px-6 sm:py-4 bg-slate-800/50 rounded-xl border border-slate-700/40" data-testid="efi-root-causes">
          <div className="flex items-center gap-2 mb-3">
            <Wrench className="h-4 w-4 text-amber-400" />
            <span className="text-sm font-medium text-slate-300">Probable Root Causes</span>
          </div>
          <div className="space-y-2">
            {parsed.rootCauses.map((cause, i) => (
              <div key={i} className="flex items-start gap-2.5" style={{ opacity: 1 - i * 0.15 }}>
                <span className="w-5 h-5 rounded-full bg-amber-500/15 text-amber-400 text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span className="text-sm text-white/80 break-words min-w-0 flex-1" style={{ overflowWrap: "break-word" }}>{cause}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Parts Needed */}
      {parsed.parts.length > 0 && (
        <div className="px-3 py-3 sm:px-6 sm:py-4 bg-slate-800/50 rounded-xl border border-slate-700/40" data-testid="efi-parts-section">
          <div className="flex items-center gap-2 mb-3">
            <Package className="h-4 w-4 text-blue-400" />
            <span className="text-sm font-medium text-slate-300">Parts That May Be Needed</span>
          </div>
          <div className="space-y-1.5">
            {parsed.parts.map((part, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-white/70">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400/60 flex-shrink-0 mt-1.5" />
                <span className="break-words min-w-0 flex-1" style={{ overflowWrap: "break-word" }}>{part}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      {parsed.disclaimer && (
        <p className="text-xs text-slate-500 px-1 leading-relaxed" data-testid="efi-disclaimer">
          {parsed.disclaimer}
        </p>
      )}

      {/* Fallback: if no sections parsed, show raw text */}
      {!parsed.safety && parsed.steps.length === 0 && parsed.rootCauses.length === 0 && (
        <div className="px-3 py-3 sm:px-6 sm:py-4 bg-slate-800/50 rounded-xl text-sm text-white/70 whitespace-pre-line leading-relaxed break-words overflow-x-auto" style={{ overflowWrap: "break-word" }}>
          {parsed.rawText}
        </div>
      )}
    </div>
  );
}
