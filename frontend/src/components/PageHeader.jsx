import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

/**
 * Standardized Page Header Component
 * Provides consistent styling across all pages
 * 
 * @param {string} title - Main page title
 * @param {string} description - Optional subtitle/description
 * @param {React.ReactNode} icon - Optional icon component
 * @param {React.ReactNode} actions - Optional action buttons (right side)
 * @param {boolean} showBack - Show back button
 * @param {string} backPath - Custom back navigation path
 * @param {React.ReactNode} badges - Optional badges to show after title
 */
export default function PageHeader({ 
  title, 
  description, 
  icon: Icon, 
  actions, 
  showBack = false,
  backPath,
  badges,
  children 
}) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (backPath) {
      navigate(backPath);
    } else {
      navigate(-1);
    }
  };

  return (
    <div className="mb-6 lg:mb-8">
      {/* Back Button */}
      {showBack && (
        <button
          onClick={handleBack}
          className="flex items-center gap-1 text-sm text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] mb-3 transition-colors group"
        >
          <ChevronLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
          <span>Back</span>
        </button>
      )}

      {/* Main Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        {/* Left Side - Title & Description */}
        <div className="flex items-start gap-4">
          {/* Icon */}
          {Icon && (
            <div className="hidden sm:flex h-12 w-12 rounded-xl bg-gradient-to-br from-[#C8FF00]/10 to-[#C8FF00]/5 items-center justify-center flex-shrink-0 shadow-sm border border-[#C8FF00]/10">
              <Icon className="h-6 w-6 text-[#C8FF00]" strokeWidth={1.5} />
            </div>
          )}
          
          {/* Text Content */}
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl lg:text-3xl font-bold text-[#F4F6F0] tracking-tight">
                {title}
              </h1>
              {badges && (
                <div className="flex items-center gap-2">
                  {badges}
                </div>
              )}
            </div>
            {description && (
              <p className="text-[rgba(244,246,240,0.45)] mt-1 text-sm lg:text-base max-w-2xl">
                {description}
              </p>
            )}
          </div>
        </div>

        {/* Right Side - Actions */}
        {actions && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {actions}
          </div>
        )}
      </div>

      {/* Optional Additional Content (tabs, filters, etc.) */}
      {children && (
        <div className="mt-4">
          {children}
        </div>
      )}
    </div>
  );
}

/**
 * Page Header with Stats
 * Extended version with summary statistics
 */
export function PageHeaderWithStats({ 
  title, 
  description, 
  icon, 
  actions, 
  stats = [],
  ...props 
}) {
  return (
    <div className="mb-6 lg:mb-8">
      <PageHeader 
        title={title} 
        description={description} 
        icon={icon} 
        actions={actions}
        {...props}
      />
      
      {stats.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          {stats.map((stat, index) => (
            <div 
              key={index}
              className="bg-[#111820] rounded-xl p-4 border border-[rgba(255,255,255,0.07)] hover:border-[rgba(255,255,255,0.12)] transition-all"
            >
              <div className="flex items-center gap-3">
                {stat.icon && (
                  <div className={`p-2 rounded-lg ${stat.iconBg || 'bg-[rgba(255,255,255,0.05)]'}`}>
                    <stat.icon className={`h-5 w-5 ${stat.iconColor || 'text-[rgba(244,246,240,0.35)]'}`} />
                  </div>
                )}
                <div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)] font-medium uppercase tracking-wide">
                    {stat.label}
                  </p>
                  <p className="text-xl font-bold text-[#F4F6F0]">
                    {stat.value}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Empty State Component
 * Use when no data is available
 */
export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  actionLabel, 
  onAction,
  actionIcon: ActionIcon
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-[rgba(255,255,255,0.05)] flex items-center justify-center mb-4">
          <Icon className="h-8 w-8 text-[rgba(244,246,240,0.45)]" strokeWidth={1.5} />
        </div>
      )}
      <h3 className="text-lg font-semibold text-[#F4F6F0] mb-1">
        {title || "No data found"}
      </h3>
      <p className="text-[rgba(244,246,240,0.45)] text-center max-w-sm mb-6">
        {description || "Get started by creating your first item."}
      </p>
      {actionLabel && onAction && (
        <Button onClick={onAction} className="bg-[#C8FF00] text-[#F4F6F0] hover:bg-[#d4ff1a] font-semibold">
          {ActionIcon && <ActionIcon className="h-4 w-4 mr-2" />}
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

/**
 * Section Header Component
 * For sub-sections within a page
 */
export function SectionHeader({ title, description, actions }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <h2 className="text-lg font-semibold text-[#F4F6F0]">{title}</h2>
        {description && (
          <p className="text-sm text-[rgba(244,246,240,0.45)]">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  );
}
