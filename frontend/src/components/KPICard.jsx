import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * KPICard - A reusable card component for displaying key performance indicators
 * Handles overflow gracefully with responsive font sizing and text truncation
 */
export function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconClassName = "",
  iconContainerClassName = "",
  className = "",
  variant = "default",
  trend,
  trendValue,
  "data-testid": testId
}) {
  // Variant styles
  const variants = {
    default: "bg-card",
    success: "bg-green-50 border-green-200",
    warning: "bg-orange-50 border-orange-200",
    danger: "bg-red-50 border-red-200",
    info: "bg-blue-50 border-blue-200",
    purple: "bg-purple-50 border-purple-200"
  };

  const iconVariants = {
    default: "bg-primary/10 text-primary",
    success: "bg-green-100 text-green-600",
    warning: "bg-orange-100 text-orange-600",
    danger: "bg-red-100 text-red-600",
    info: "bg-blue-100 text-blue-600",
    purple: "bg-purple-100 text-purple-600"
  };

  const valueVariants = {
    default: "text-foreground",
    success: "text-green-700",
    warning: "text-orange-700",
    danger: "text-red-700",
    info: "text-blue-700",
    purple: "text-purple-700"
  };

  return (
    <Card className={cn(variants[variant], className)} data-testid={testId}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs sm:text-sm text-muted-foreground font-medium truncate">
              {title}
            </p>
            <p 
              className={cn(
                "text-lg sm:text-xl md:text-2xl font-bold mt-1 truncate",
                valueVariants[variant]
              )}
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1 truncate">
                {subtitle}
              </p>
            )}
            {trend && (
              <div className={cn(
                "flex items-center gap-1 mt-1 text-xs",
                trend === "up" ? "text-green-600" : "text-red-600"
              )}>
                {trend === "up" ? "↑" : "↓"} {trendValue}
              </div>
            )}
          </div>
          {Icon && (
            <div className={cn(
              "h-9 w-9 sm:h-10 sm:w-10 rounded-lg flex items-center justify-center shrink-0",
              iconVariants[variant],
              iconContainerClassName
            )}>
              <Icon className={cn("h-4 w-4 sm:h-5 sm:w-5", iconClassName)} strokeWidth={1.5} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * MetricCard - A larger metric card for dashboard-style displays
 * Used for primary KPIs with more visual prominence
 */
export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconClassName = "",
  className = "",
  "data-testid": testId
}) {
  return (
    <Card className={cn("metric-card card-hover", className)} data-testid={testId}>
      <CardContent className="p-4 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs sm:text-sm text-muted-foreground font-medium">
              {title}
            </p>
            <p 
              className="text-2xl sm:text-3xl lg:text-4xl font-bold mt-2 mono truncate"
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">
                {subtitle}
              </p>
            )}
          </div>
          {Icon && (
            <div className={cn(
              "h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0",
              iconClassName
            )}>
              <Icon className="h-5 w-5 text-primary" strokeWidth={1.5} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * GradientKPICard - A KPI card with gradient background
 * Used for prominent metrics in reports/analytics
 */
export function GradientKPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  gradient = "from-blue-500 to-blue-600",
  textColor = "text-white",
  subtitleColor = "text-white/80",
  iconColor = "text-white/60",
  className = "",
  "data-testid": testId
}) {
  return (
    <Card className={cn(`bg-gradient-to-br ${gradient} ${textColor}`, className)} data-testid={testId}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className={cn("text-xs opacity-80", subtitleColor)}>{title}</p>
            <p 
              className="text-lg sm:text-xl md:text-2xl font-bold mt-1 truncate"
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className={cn("text-xs mt-1", subtitleColor)}>{subtitle}</p>
            )}
          </div>
          {Icon && (
            <Icon className={cn("h-8 w-8 sm:h-10 sm:w-10 shrink-0", iconColor)} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Format currency with appropriate abbreviation for large numbers
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency symbol (default: ₹)
 * @param {boolean} abbreviate - Whether to abbreviate large numbers
 * @returns {string} Formatted currency string
 */
export function formatCurrencyCompact(amount, currency = "₹", abbreviate = true) {
  if (amount === null || amount === undefined) return `${currency}0`;
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? "-" : "";
  
  if (!abbreviate || absAmount < 100000) {
    return `${sign}${currency}${absAmount.toLocaleString("en-IN")}`;
  }
  
  // Indian numbering system abbreviations
  if (absAmount >= 10000000) {
    // Crores
    return `${sign}${currency}${(absAmount / 10000000).toFixed(1)}Cr`;
  } else if (absAmount >= 100000) {
    // Lakhs
    return `${sign}${currency}${(absAmount / 100000).toFixed(1)}L`;
  }
  
  return `${sign}${currency}${absAmount.toLocaleString("en-IN")}`;
}

export default KPICard;
