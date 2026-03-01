import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Format currency with appropriate abbreviation for large numbers (Indian numbering)
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

/**
 * Format number with abbreviation
 */
export function formatNumberCompact(num) {
  if (num === null || num === undefined) return "0";
  if (num >= 10000000) return `${(num / 10000000).toFixed(1)}Cr`;
  if (num >= 100000) return `${(num / 100000).toFixed(1)}L`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toLocaleString("en-IN");
}

// Variant configurations - Dark Volt Theme
const variants = {
  default: {
    card: "bg-bw-panel border-white/[0.07]",
    iconContainer: "bg-bw-volt/[0.08] border border-bw-volt/15",
    icon: "text-bw-volt",
    value: "text-bw-volt"
  },
  success: {
    card: "bg-bw-panel border-bw-green/25",
    iconContainer: "bg-bw-green/10 border border-bw-green/20",
    icon: "text-bw-green",
    value: "text-bw-green"
  },
  warning: {
    card: "bg-bw-panel border-bw-orange/25",
    iconContainer: "bg-bw-orange/10 border border-bw-orange/20",
    icon: "text-bw-orange",
    value: "text-bw-orange"
  },
  danger: {
    card: "bg-bw-panel border-bw-red/25",
    iconContainer: "bg-bw-red/10 border border-bw-red/20",
    icon: "text-bw-red",
    value: "text-bw-red"
  },
  info: {
    card: "bg-bw-panel border-bw-blue/25",
    iconContainer: "bg-bw-blue/10 border border-bw-blue/20",
    icon: "text-bw-blue",
    value: "text-bw-blue"
  },
  purple: {
    card: "bg-bw-panel border-bw-purple/25",
    iconContainer: "bg-bw-purple/10 border border-bw-purple/20",
    icon: "text-bw-purple",
    value: "text-bw-purple"
  },
  teal: {
    card: "bg-bw-panel border-bw-teal/25",
    iconContainer: "bg-bw-teal/10 border border-bw-teal/20",
    icon: "text-bw-teal",
    value: "text-bw-teal"
  }
};

/**
 * StatCard - Unified stat card component
 * A reusable card component for displaying statistics and KPIs
 */
const StatCard = React.forwardRef(({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = "default",
  trend,
  trendValue,
  loading = false,
  className,
  ...props
}, ref) => {
  const variantStyles = variants[variant] || variants.default;
  const isZeroValue = value === 0 || value === "0" || value === "₹0";

  if (loading) {
    return (
      <Card ref={ref} className={cn("border rounded", variantStyles.card, className)} {...props}>
        <CardContent className="pt-4 pb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-24 bg-white/5" />
              <Skeleton className="h-7 w-16 bg-white/5" />
              {subtitle && <Skeleton className="h-3 w-20 bg-white/5" />}
            </div>
            <Skeleton className="h-10 w-10 rounded bg-white/5" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn("border rounded card-hover", variantStyles.card, className)} {...props}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] text-bw-white/[0.45] font-medium uppercase tracking-[0.08em] truncate">
              {title}
            </p>
            <p 
              className={cn(
                "text-lg sm:text-xl md:text-2xl font-bold mt-1 truncate",
                isZeroValue ? "text-bw-white/20" : variantStyles.value,
                !isZeroValue && variant === "default" && "text-shadow-volt"
              )}
              style={!isZeroValue && variant === "default" ? { textShadow: '0 0 24px rgba(200,255,0,0.25)' } : undefined}
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className="text-[11px] text-bw-white/25 mt-1 truncate">
                {subtitle}
              </p>
            )}
            {trend && (
              <div className={cn(
                "flex items-center gap-1 mt-1 text-xs",
                trend === "up" ? "text-bw-green" : "text-bw-red"
              )}>
                {trend === "up" ? "↑" : "↓"} {trendValue}
              </div>
            )}
          </div>
          {Icon && (
            <div className={cn(
              "h-9 w-9 sm:h-10 sm:w-10 rounded flex items-center justify-center shrink-0 opacity-70",
              variantStyles.iconContainer
            )}>
              <Icon className={cn("h-4 w-4 sm:h-5 sm:w-5", variantStyles.icon)} strokeWidth={1.5} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
});
StatCard.displayName = "StatCard";

/**
 * MetricCard - Larger metric card for prominent displays
 */
const MetricCard = React.forwardRef(({
  title,
  value,
  subtitle,
  icon: Icon,
  iconClassName = "",
  loading = false,
  featured = false,
  className,
  ...props
}, ref) => {
  const isZeroValue = value === 0 || value === "0" || value === "₹0";

  if (loading) {
    return (
      <Card ref={ref} className={cn("metric-card", className)} {...props}>
        <CardContent className="p-4 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-32 bg-white/5" />
              <Skeleton className="h-10 w-20 bg-white/5" />
              {subtitle && <Skeleton className="h-3 w-24 bg-white/5" />}
            </div>
            <Skeleton className="h-10 w-10 rounded bg-white/5" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn("metric-card card-hover", featured && "metric-card-featured", className)} {...props}>
      <CardContent className="p-4 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="metric-card-title">
              {title}
            </p>
            <p 
              className={cn(
                "text-2xl sm:text-3xl lg:text-4xl font-bold mt-2 mono truncate",
                isZeroValue ? "metric-card-value-zero" : "metric-card-value",
                featured && !isZeroValue && "text-[48px]"
              )}
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className="metric-card-subtitle mt-1">
                {subtitle}
              </p>
            )}
          </div>
          {Icon && (
            <div className={cn(
              "h-10 w-10 rounded metric-card-icon flex items-center justify-center shrink-0",
              iconClassName
            )}>
              <Icon className="h-5 w-5 text-bw-volt" strokeWidth={1.5} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
});
MetricCard.displayName = "MetricCard";

/**
 * GradientStatCard - Card with accent styling for analytics
 */
const GradientStatCard = React.forwardRef(({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = "volt",
  loading = false,
  className,
  ...props
}, ref) => {
  const gradientStyles = {
    volt: "bg-bw-volt/[0.08] border border-bw-volt/20 text-bw-volt",
    blue: "bg-bw-blue/[0.08] border border-bw-blue/20 text-bw-blue",
    green: "bg-bw-green/[0.08] border border-bw-green/20 text-bw-green",
    orange: "bg-bw-orange/[0.08] border border-bw-orange/20 text-bw-orange"
  };

  const currentStyle = gradientStyles[variant] || gradientStyles.volt;

  if (loading) {
    return (
      <Card ref={ref} className={cn(currentStyle, "rounded", className)} {...props}>
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-3 w-24 bg-white/10" />
              <Skeleton className="h-7 w-20 bg-white/10" />
              {subtitle && <Skeleton className="h-3 w-16 bg-white/10" />}
            </div>
            <Skeleton className="h-10 w-10 rounded-full bg-white/10" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn(currentStyle, "rounded", className)} {...props}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs opacity-60">{title}</p>
            <p 
              className="text-lg sm:text-xl md:text-2xl font-bold mt-1 truncate"
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className="text-xs opacity-50 mt-1">{subtitle}</p>
            )}
          </div>
          {Icon && (
            <Icon className="h-8 w-8 sm:h-10 sm:w-10 shrink-0 opacity-50" />
          )}
        </div>
      </CardContent>
    </Card>
  );
});
GradientStatCard.displayName = "GradientStatCard";

/**
 * StatCardGrid - Container for stat cards with responsive layout
 */
const StatCardGrid = React.forwardRef(({
  children,
  columns = 6,
  className,
  ...props
}, ref) => {
  const colClasses = {
    2: "grid-cols-2",
    3: "grid-cols-2 md:grid-cols-3",
    4: "grid-cols-2 md:grid-cols-4",
    5: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5",
    6: "grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
  };

  return (
    <div 
      ref={ref} 
      className={cn("grid gap-3 sm:gap-4", colClasses[columns] || colClasses[6], className)} 
      {...props}
    >
      {children}
    </div>
  );
});
StatCardGrid.displayName = "StatCardGrid";

/**
 * MiniStatCard - Compact stat display for tight spaces
 */
const MiniStatCard = React.forwardRef(({
  label,
  value,
  icon: Icon,
  variant = "default",
  loading = false,
  className,
  ...props
}, ref) => {
  const variantStyles = variants[variant] || variants.default;

  if (loading) {
    return (
      <div ref={ref} className={cn("flex items-center gap-2 p-2 rounded border", variantStyles.card, className)} {...props}>
        <Skeleton className="h-6 w-6 rounded bg-white/5" />
        <div className="space-y-1">
          <Skeleton className="h-3 w-12 bg-white/5" />
          <Skeleton className="h-4 w-8 bg-white/5" />
        </div>
      </div>
    );
  }

  return (
    <div ref={ref} className={cn("flex items-center gap-2 p-2 rounded border", variantStyles.card, className)} {...props}>
      {Icon && (
        <div className={cn("p-1.5 rounded", variantStyles.iconContainer)}>
          <Icon className={cn("h-4 w-4", variantStyles.icon)} />
        </div>
      )}
      <div>
        <p className="text-xs text-bw-white/[0.45]">{label}</p>
        <p className={cn("text-sm font-bold", variantStyles.value)}>{value}</p>
      </div>
    </div>
  );
});
MiniStatCard.displayName = "MiniStatCard";

export { StatCard, MetricCard, GradientStatCard, StatCardGrid, MiniStatCard };
