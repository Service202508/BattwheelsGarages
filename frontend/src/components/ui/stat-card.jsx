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
    card: "bg-[#111820] border-[rgba(255,255,255,0.07)]",
    iconContainer: "bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.15)]",
    icon: "text-[#C8FF00]",
    value: "text-[#C8FF00]"
  },
  success: {
    card: "bg-[#111820] border-[rgba(34,197,94,0.25)]",
    iconContainer: "bg-[rgba(34,197,94,0.1)] border border-[rgba(34,197,94,0.2)]",
    icon: "text-[#22C55E]",
    value: "text-[#22C55E]"
  },
  warning: {
    card: "bg-[#111820] border-[rgba(255,140,0,0.25)]",
    iconContainer: "bg-[rgba(255,140,0,0.1)] border border-[rgba(255,140,0,0.2)]",
    icon: "text-[#FF8C00]",
    value: "text-[#FF8C00]"
  },
  danger: {
    card: "bg-[#111820] border-[rgba(255,59,47,0.25)]",
    iconContainer: "bg-[rgba(255,59,47,0.1)] border border-[rgba(255,59,47,0.2)]",
    icon: "text-[#FF3B2F]",
    value: "text-[#FF3B2F]"
  },
  info: {
    card: "bg-[#111820] border-[rgba(59,158,255,0.25)]",
    iconContainer: "bg-[rgba(59,158,255,0.1)] border border-[rgba(59,158,255,0.2)]",
    icon: "text-[#3B9EFF]",
    value: "text-[#3B9EFF]"
  },
  purple: {
    card: "bg-[#111820] border-[rgba(139,92,246,0.25)]",
    iconContainer: "bg-[rgba(139,92,246,0.1)] border border-[rgba(139,92,246,0.2)]",
    icon: "text-[#8B5CF6]",
    value: "text-[#8B5CF6]"
  },
  teal: {
    card: "bg-[#111820] border-[rgba(20,184,166,0.25)]",
    iconContainer: "bg-[rgba(20,184,166,0.1)] border border-[rgba(20,184,166,0.2)]",
    icon: "text-[#14B8A6]",
    value: "text-[#14B8A6]"
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

  if (loading) {
    return (
      <Card ref={ref} className={cn(variantStyles.card, className)} {...props}>
        <CardContent className="pt-4 pb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-16" />
              {subtitle && <Skeleton className="h-3 w-20" />}
            </div>
            <Skeleton className="h-10 w-10 rounded-lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn(variantStyles.card, className)} {...props}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs sm:text-sm text-muted-foreground font-medium truncate">
              {title}
            </p>
            <p 
              className={cn(
                "text-lg sm:text-xl md:text-2xl font-bold mt-1 truncate",
                variantStyles.value
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
  className,
  ...props
}, ref) => {
  if (loading) {
    return (
      <Card ref={ref} className={cn("metric-card", className)} {...props}>
        <CardContent className="p-4 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-10 w-20" />
              {subtitle && <Skeleton className="h-3 w-24" />}
            </div>
            <Skeleton className="h-10 w-10 rounded-lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn("metric-card card-hover", className)} {...props}>
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
});
MetricCard.displayName = "MetricCard";

/**
 * GradientStatCard - Card with gradient background for analytics
 */
const GradientStatCard = React.forwardRef(({
  title,
  value,
  subtitle,
  icon: Icon,
  gradient = "from-blue-500 to-blue-600",
  loading = false,
  className,
  ...props
}, ref) => {
  if (loading) {
    return (
      <Card ref={ref} className={cn(`bg-gradient-to-br ${gradient} text-white`, className)} {...props}>
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-3 w-24 bg-white/20" />
              <Skeleton className="h-7 w-20 bg-white/20" />
              {subtitle && <Skeleton className="h-3 w-16 bg-white/20" />}
            </div>
            <Skeleton className="h-10 w-10 rounded-full bg-white/20" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn(`bg-gradient-to-br ${gradient} text-white`, className)} {...props}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs opacity-80">{title}</p>
            <p 
              className="text-lg sm:text-xl md:text-2xl font-bold mt-1 truncate"
              title={typeof value === 'string' ? value : undefined}
            >
              {value}
            </p>
            {subtitle && (
              <p className="text-xs opacity-70 mt-1">{subtitle}</p>
            )}
          </div>
          {Icon && (
            <Icon className="h-8 w-8 sm:h-10 sm:w-10 shrink-0 opacity-60" />
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
      <div ref={ref} className={cn("flex items-center gap-2 p-2 rounded-lg", variantStyles.card, className)} {...props}>
        <Skeleton className="h-6 w-6 rounded" />
        <div className="space-y-1">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-4 w-8" />
        </div>
      </div>
    );
  }

  return (
    <div ref={ref} className={cn("flex items-center gap-2 p-2 rounded-lg", variantStyles.card, className)} {...props}>
      {Icon && (
        <div className={cn("p-1.5 rounded", variantStyles.iconContainer)}>
          <Icon className={cn("h-4 w-4", variantStyles.icon)} />
        </div>
      )}
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={cn("text-sm font-bold", variantStyles.value)}>{value}</p>
      </div>
    </div>
  );
});
MiniStatCard.displayName = "MiniStatCard";

export { StatCard, MetricCard, GradientStatCard, StatCardGrid, MiniStatCard };
