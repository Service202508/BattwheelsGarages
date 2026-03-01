import * as React from "react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * ResponsiveTable - Wrapper for tables with mobile scroll and overflow handling
 */
const ResponsiveTable = React.forwardRef(({ 
  children, 
  className, 
  maxHeight,
  ...props 
}, ref) => {
  return (
    <div 
      ref={ref}
      className={cn(
        "bg-bw-panel rounded-lg border overflow-hidden",
        className
      )}
      {...props}
    >
      <div 
        className={cn(
          "overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100",
          maxHeight && "overflow-y-auto"
        )}
        style={maxHeight ? { maxHeight } : undefined}
      >
        <table className="w-full min-w-[640px]">
          {children}
        </table>
      </div>
    </div>
  );
});
ResponsiveTable.displayName = "ResponsiveTable";

/**
 * TableSkeleton - Loading skeleton for table rows
 */
const TableSkeleton = React.forwardRef(({ 
  columns = 5, 
  rows = 5,
  className,
  ...props 
}, ref) => {
  return (
    <div ref={ref} className={cn("bg-bw-panel rounded-lg border overflow-hidden", className)} {...props}>
      {/* Header */}
      <div className="bg-bw-panel border-b px-4 py-3">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1 max-w-[120px]" />
          ))}
        </div>
      </div>
      {/* Rows */}
      <div className="divide-y">
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <div key={rowIdx} className="px-4 py-3">
            <div className="flex items-center gap-4">
              {Array.from({ length: columns }).map((_, colIdx) => (
                <Skeleton 
                  key={colIdx} 
                  className={cn(
                    "h-4 flex-1",
                    colIdx === 0 ? "max-w-[180px]" : "max-w-[100px]"
                  )} 
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});
TableSkeleton.displayName = "TableSkeleton";

/**
 * CardSkeleton - Loading skeleton for cards
 */
const CardSkeleton = React.forwardRef(({ 
  lines = 3,
  className,
  ...props 
}, ref) => {
  return (
    <Card ref={ref} className={className} {...props}>
      <CardContent className="pt-4 space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton 
            key={i} 
            className={cn("h-4", i === 0 ? "w-3/4" : i === lines - 1 ? "w-1/2" : "w-full")} 
          />
        ))}
      </CardContent>
    </Card>
  );
});
CardSkeleton.displayName = "CardSkeleton";

/**
 * PageSkeleton - Full page loading skeleton
 */
const PageSkeleton = React.forwardRef(({ 
  showStats = true,
  showTable = true,
  statsCount = 6,
  className,
  ...props 
}, ref) => {
  return (
    <div ref={ref} className={cn("space-y-6", className)} {...props}>
      {/* Header Skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-32" />
        </div>
      </div>

      {/* Stats Skeleton */}
      {showStats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: statsCount }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-7 w-16" />
                  </div>
                  <Skeleton className="h-10 w-10 rounded-lg" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Table Skeleton */}
      {showTable && <TableSkeleton columns={6} rows={8} />}
    </div>
  );
});
PageSkeleton.displayName = "PageSkeleton";

/**
 * EmptyState - Display when no data is available
 */
const EmptyState = React.forwardRef(({ 
  icon: Icon, 
  title = "No data found",
  description = "Get started by creating your first item.",
  actionLabel,
  onAction,
  actionIcon: ActionIcon,
  variant = "default",
  className,
  ...props 
}, ref) => {
  const variantStyles = {
    default: {
      iconBg: "bg-white/5",
      iconColor: "text-bw-white/[0.45]"
    },
    success: {
      iconBg: "bg-green-100",
      iconColor: "text-green-500"
    },
    warning: {
      iconBg: "bg-orange-100",
      iconColor: "text-orange-500"
    },
    info: {
      iconBg: "bg-blue-100",
      iconColor: "text-blue-500"
    }
  };

  const styles = variantStyles[variant] || variantStyles.default;

  return (
    <div 
      ref={ref} 
      className={cn("flex flex-col items-center justify-center py-12 sm:py-16 px-4", className)} 
      {...props}
    >
      {Icon && (
        <div className={cn("w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center mb-4", styles.iconBg)}>
          <Icon className={cn("h-7 w-7 sm:h-8 sm:w-8", styles.iconColor)} strokeWidth={1.5} />
        </div>
      )}
      <h3 className="text-base sm:text-lg font-semibold text-bw-white mb-1 text-center">
        {title}
      </h3>
      <p className="text-sm text-bw-white/[0.45] text-center max-w-sm mb-6">
        {description}
      </p>
      {actionLabel && onAction && (
        <Button 
          onClick={onAction} 
          className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover font-semibold"
        >
          {ActionIcon && <ActionIcon className="h-4 w-4 mr-2" />}
          {actionLabel}
        </Button>
      )}
    </div>
  );
});
EmptyState.displayName = "EmptyState";

/**
 * DataTable - Combined wrapper with empty state and loading support
 */
const DataTable = React.forwardRef(({ 
  children,
  loading = false,
  empty = false,
  emptyIcon,
  emptyTitle,
  emptyDescription,
  emptyAction,
  onEmptyAction,
  columns = 5,
  rows = 5,
  className,
  ...props 
}, ref) => {
  if (loading) {
    return <TableSkeleton columns={columns} rows={rows} className={className} {...props} />;
  }

  if (empty) {
    return (
      <Card className={className} {...props}>
        <EmptyState 
          icon={emptyIcon}
          title={emptyTitle}
          description={emptyDescription}
          actionLabel={emptyAction}
          onAction={onEmptyAction}
        />
      </Card>
    );
  }

  return (
    <ResponsiveTable ref={ref} className={className} {...props}>
      {children}
    </ResponsiveTable>
  );
});
DataTable.displayName = "DataTable";

export { 
  ResponsiveTable, 
  TableSkeleton, 
  CardSkeleton, 
  PageSkeleton, 
  EmptyState,
  DataTable
};
