import { useLocation, useNavigate } from "react-router-dom";
import { Lock } from "lucide-react";
import { useOrganization } from "@/App";

// Map of route prefix -> feature key
const ROUTE_FEATURES = {
  "/payroll":               "PAYROLL",
  "/projects":              "PROJECT_MANAGEMENT",
  "/reports/technician":    "ADVANCED_REPORTS",
  "/reports/profit":        "ADVANCED_REPORTS",
  "/reports/gst":           "ADVANCED_REPORTS",
  "/gst-reports":           "ADVANCED_REPORTS",
  "/reports-advanced":      "ADVANCED_REPORTS",
  "/productivity":          "ADVANCED_REPORTS",
  "/inventory/warehouses":  "MULTI_WAREHOUSE",
  "/einvoice":              "EINVOICE",
  "/banking":               "ACCOUNTING_MODULE",
  "/finance/journal":       "ACCOUNTING_MODULE",
  "/journal-entries":       "ACCOUNTING_MODULE",
  "/efi":                   "EFI_INTELLIGENCE",
  "/failure-intelligence":  "EFI_INTELLIGENCE",
};

// Minimum plan required per feature key
const FEATURE_PLANS = {
  PAYROLL:            "professional",
  PROJECT_MANAGEMENT: "professional",
  ADVANCED_REPORTS:   "starter",
  MULTI_WAREHOUSE:    "enterprise",
  EINVOICE:           "professional",
  ACCOUNTING_MODULE:  "professional",
  EFI_INTELLIGENCE:   "starter",
};

const FEATURE_NAMES = {
  PAYROLL:            "Payroll",
  PROJECT_MANAGEMENT: "Project Management",
  ADVANCED_REPORTS:   "Advanced Reports",
  MULTI_WAREHOUSE:    "Multi-Warehouse Inventory",
  EINVOICE:           "E-Invoice",
  ACCOUNTING_MODULE:  "Accounting Module",
  EFI_INTELLIGENCE:   "EFI Intelligence",
};

const PLAN_HIERARCHY = ["free", "starter", "professional", "enterprise"];

function planCovers(currentPlan, requiredPlan) {
  const cur = PLAN_HIERARCHY.indexOf((currentPlan || "free").toLowerCase());
  const req = PLAN_HIERARCHY.indexOf((requiredPlan || "free").toLowerCase());
  return cur >= req;
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

/**
 * Wraps page content. When the current route requires a higher plan,
 * renders an amber banner above a blurred/disabled content area.
 */
export default function FeatureGateBanner({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const currentOrg = useOrganization();

  // No org context = platform admin or unauthenticated → no banner
  if (!currentOrg) return <>{children}</>;

  const planType = (currentOrg.plan_type || "free").toLowerCase();
  const pathname = location.pathname;

  // Find which feature this route maps to (longest prefix match)
  let matchedFeature = null;
  let matchedRoute = null;
  for (const [route, feature] of Object.entries(ROUTE_FEATURES)) {
    if (pathname === route || pathname.startsWith(route + "/")) {
      if (!matchedRoute || route.length > matchedRoute.length) {
        matchedRoute = route;
        matchedFeature = feature;
      }
    }
  }

  // No feature gate for this route
  if (!matchedFeature) return <>{children}</>;

  const requiredPlan = FEATURE_PLANS[matchedFeature];
  const hasAccess = planCovers(planType, requiredPlan);

  // User's plan covers this feature → no banner
  if (hasAccess) return <>{children}</>;

  const featureLabel = FEATURE_NAMES[matchedFeature] || matchedFeature;
  const requiredLabel = capitalize(requiredPlan);
  const currentLabel = capitalize(planType);

  return (
    <div className="relative" data-testid="feature-gate-wrapper">
      {/* ── Banner ── */}
      <div
        className="sticky top-0 z-30 w-full flex items-center justify-between px-6 py-3 border-b-2"
        style={{
          background: "rgba(234,179,8,0.08)",
          borderBottomColor: "#EAB308",
        }}
        data-testid="feature-gate-banner"
      >
        {/* Left */}
        <div className="flex items-center gap-3 min-w-0">
          <Lock
            size={16}
            className="flex-shrink-0"
            style={{ color: "#EAB308" }}
          />
          <div className="min-w-0">
            <p className="text-sm font-medium text-[#F4F6F0] leading-tight">
              <span style={{ color: "#EAB308" }}>{featureLabel}</span>
              {" "}is available on{" "}
              <span className="font-semibold">{requiredLabel} plan</span>
              {" "}and above.
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.45)] mt-0.5">
              Your current plan:{" "}
              <span className="text-[rgba(244,246,240,0.7)]">{currentLabel}</span>
            </p>
          </div>
        </div>

        {/* Right */}
        <button
          onClick={() => navigate("/subscription")}
          className="flex-shrink-0 ml-4 text-sm font-semibold px-4 py-2 rounded transition-opacity hover:opacity-90 active:opacity-80"
          style={{
            background: "#EAB308",
            color: "#080C0F",
            fontFamily: "'JetBrains Mono', monospace",
          }}
          data-testid="feature-gate-upgrade-btn"
        >
          Upgrade to {requiredLabel} →
        </button>
      </div>

      {/* ── Blurred content ── */}
      <div
        style={{ filter: "blur(4px)", pointerEvents: "none", userSelect: "none" }}
        aria-hidden="true"
        data-testid="feature-gate-blurred-content"
      >
        {children}
      </div>
    </div>
  );
}
