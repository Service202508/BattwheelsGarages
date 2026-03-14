import { useState, useCallback, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import FeatureGateBanner from "./FeatureGateBanner";
import UpgradePrompt from "./UpgradePrompt";
import OrganizationSwitcher from "./OrganizationSwitcher";
import { isModuleAccessible } from "../config/planConfig";
import { useOrganization } from "@/App";
import { 
  LayoutDashboard, 
  Ticket, 
  Package, 
  Bot, 
  Users, 
  Car, 
  Bell, 
  Settings, 
  LogOut, 
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Menu,
  X,
  FileText,
  TrendingUp,
  ShoppingCart,
  Receipt,
  Calculator,
  Truck,
  Building2,
  Database,
  Clock,
  Calendar,
  Wallet,
  Brain,
  Shield,
  BarChart3,
  Repeat,
  FolderKanban,
  Percent,
  BookOpen,
  Layers,
  CreditCard,
  Tag,
  List,
  ClipboardList,
  ArrowRightLeft,
  Activity,
  Landmark,
  CheckSquare,
  CloudDownload,
  Warehouse,
  Search,
  Zap,
  PieChart,
  Banknote,
  UserCircle,
  Briefcase,
  LayoutGrid,
  Hash,
  Home,
  Timer,
  FolderOpen,
  Palette,
  Scale,
  Lock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import NotificationBell from "@/components/NotificationBell";
import AIUsageCounter from "@/components/ai/AIUsageCounter";

// Reorganized & cleaned navigation - removed legacy items and duplicates
const navItems = [
  { 
    section: "Home", 
    icon: Home,
    defaultOpen: true,
    items: [
      { name: "Financial Overview", path: "/home", icon: Home },
      { name: "Workshop Dashboard", path: "/dashboard", icon: LayoutDashboard },
      { name: "Data Insights", path: "/insights", icon: TrendingUp },
    ]
  },
  { 
    section: "Intelligence", 
    icon: Brain,
    defaultOpen: false,
    items: [
      { name: "Failure Intelligence", path: "/failure-intelligence", icon: Brain },
      { name: "EVFI\u2122 Knowledge Brain", path: "/knowledge-brain", icon: Brain },
      { name: "EVFI\u2122 AI Assistant", path: "/ai-assistant", icon: Bot },
      { name: "Fault Tree Import", path: "/fault-tree-import", icon: FileText },
    ]
  },
  { 
    section: "Operations", 
    icon: Ticket,
    defaultOpen: false,
    items: [
      { name: "New Ticket", path: "/tickets/new", icon: Ticket },
      { name: "All Tickets", path: "/tickets", icon: FileText },
      { name: "Vehicles", path: "/vehicles", icon: Car },
      { name: "AMC Management", path: "/amc", icon: Shield },
      { name: "Time Tracking", path: "/time-tracking", icon: Timer },
      { name: "Alerts", path: "/alerts", icon: Bell },
    ]
  },
  { 
    section: "Contacts", 
    icon: Users,
    defaultOpen: false,
    items: [
      { name: "All Contacts", path: "/contacts", icon: Users },
    ]
  },
  { 
    section: "Sales", 
    icon: ShoppingCart,
    defaultOpen: false,
    items: [
      { name: "Estimates", path: "/estimates", icon: FileText },
      { name: "Sales Orders", path: "/sales-orders", icon: ShoppingCart },
      { name: "Invoices", path: "/invoices-enhanced", icon: Receipt },
      { name: "Payments Received", path: "/payments-received", icon: CreditCard },
      { name: "Invoice Automation", path: "/invoice-settings", icon: Settings },
      { name: "Recurring Invoices", path: "/recurring-transactions", icon: Repeat },
      { name: "Credit Notes", path: "/credit-notes", icon: FileText },
      { name: "Delivery Challans", path: "/delivery-challans", icon: Truck },
    ]
  },
  { 
    section: "Purchases", 
    icon: Truck,
    defaultOpen: false,
    items: [
      { name: "Purchase Orders", path: "/purchases", icon: Truck },
      { name: "Bills", path: "/bills-enhanced", icon: Receipt },
      { name: "Recurring Bills", path: "/recurring-bills", icon: Repeat },
      { name: "Vendor Credits", path: "/vendor-credits", icon: CreditCard },
    ]
  },
  { 
    section: "Inventory", 
    icon: Package,
    defaultOpen: false,
    items: [
      { name: "Items & Products", path: "/items", icon: Tag },
      { name: "Composite Items", path: "/composite-items", icon: Layers },
      { name: "Stock Management", path: "/inventory-enhanced", icon: Warehouse },
      { name: "Stock Transfers", path: "/stock-transfers", icon: ArrowRightLeft },
      { name: "Price Lists", path: "/price-lists", icon: List },
      { name: "Adjustments", path: "/inventory-adjustments", icon: ClipboardList },
      { name: "Serial & Batch", path: "/serial-batch-tracking", icon: Hash },
    ]
  },
  { 
    section: "Finance", 
    icon: Banknote,
    defaultOpen: false,
    items: [
      { name: "Expenses", path: "/expenses", icon: Receipt },
      { name: "Recurring Expenses", path: "/recurring-expenses", icon: Repeat },
      { name: "Banking", path: "/banking", icon: Wallet },
      { name: "Accountant", path: "/accountant", icon: Calculator },
      { name: "Chart of Accounts", path: "/chart-of-accounts", icon: Layers },
      { name: "Journal Entries", path: "/journal-entries", icon: BookOpen },
      { name: "Trial Balance", path: "/trial-balance", icon: Scale },
      { name: "Opening Balances", path: "/opening-balances", icon: Landmark },
      { name: "Period Locks", path: "/period-locks", icon: Lock },
      { name: "Balance Sheet", path: "/balance-sheet", icon: FileText },
      { name: "Profit & Loss", path: "/profit-loss", icon: BarChart3 },
    ]
  },
  { 
    section: "Reports", 
    icon: PieChart,
    defaultOpen: false,
    items: [
      { name: "Analytics Dashboard", path: "/reports-advanced", icon: BarChart3 },
      { name: "Financial Reports", path: "/reports", icon: BarChart3 },
      { name: "GST Returns", path: "/gst-reports", icon: FileText },
      { name: "Accounting", path: "/accounting", icon: Calculator },
    ]
  },
  { 
    section: "Projects", 
    icon: FolderKanban,
    defaultOpen: false,
    items: [
      { name: "All Projects", path: "/projects", icon: FolderKanban },
      { name: "Project Tasks", path: "/project-tasks", icon: CheckSquare },
    ]
  },
  { 
    section: "HR & Payroll", 
    icon: Briefcase,
    defaultOpen: false,
    items: [
      { name: "HR Dashboard", path: "/hr", icon: Briefcase },
      { name: "Employees", path: "/employees", icon: Users },
      { name: "Attendance", path: "/attendance", icon: Clock },
      { name: "Leave Management", path: "/leave", icon: Calendar },
      { name: "Payroll", path: "/payroll", icon: Wallet },
      { name: "Productivity", path: "/productivity", icon: BarChart3 },
    ]
  },
  { 
    section: "Settings", 
    icon: Settings,
    defaultOpen: false,
    items: [
      { name: "Subscription & Billing", path: "/subscription", icon: CreditCard, adminOnly: true },
      { name: "Team Management", path: "/team", icon: Users, adminOnly: true },
      { name: "Branding", path: "/branding", icon: Palette, adminOnly: true },
      { name: "Organization", path: "/organization-settings", icon: Building2, adminOnly: true },
      { name: "Data Management", path: "/data-management", icon: Database, adminOnly: true },
      { name: "Documents", path: "/documents", icon: FolderOpen, adminOnly: true },
      { name: "Customer Portal", path: "/customer-portal", icon: Building2 },
    ]
  },
];

// Collapsible Navigation Section Component
const NavSection = ({ section, user, collapsed, onClose, openSections, toggleSection, currentPlan, onLockedClick }) => {
  const location = useLocation();
  const SectionIcon = section.icon;
  const isOpen = openSections[section.section] ?? section.defaultOpen;
  
  // Check if any item in this section is active
  const hasActiveItem = section.items.some(item => location.pathname === item.path);
  
  // Filter out admin-only items for non-admin users
  // Also filter sections by role: HR only sees HR & Payroll section
  const userRole = user?.role || "";
  const isAdminLevel = ["owner", "org_admin", "admin"].includes(userRole);
  const isHR = userRole === "hr";
  
  // HR role: only show HR & Payroll section (+ Settings limited)
  if (isHR) {
    const hrSections = ["HR & Payroll"];
    if (!hrSections.includes(section.section) && section.section !== "Settings") return null;
  }
  
  const visibleItems = section.items.filter(item => !item.adminOnly || isAdminLevel);
  
  if (visibleItems.length === 0) return null;

  if (collapsed) {
    // In collapsed mode, show only the first item or section icon
    return (
      <div className="space-y-1">
        {visibleItems.slice(0, 3).map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          const accessible = isModuleAccessible(item.path, currentPlan);
          return (
            <Link
              key={item.path}
              to={accessible ? item.path : "#"}
              onClick={(e) => {
                if (!accessible) {
                  e.preventDefault();
                  onLockedClick?.(item.path);
                } else {
                  onClose?.();
                }
              }}
              title={item.name + (!accessible ? " (Locked)" : "")}
              className={`relative flex items-center justify-center p-2.5 rounded transition-all duration-200 ${
                isActive && accessible
                  ? "bg-bw-volt/[0.12] text-bw-volt border-l-2 border-bw-volt"
                  : accessible
                    ? "text-bw-white/[0.65] hover:text-bw-white hover:bg-bw-volt/[0.06]"
                    : "text-bw-white/[0.25] cursor-pointer hover:bg-white/[0.03]"
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive && accessible ? "text-bw-volt" : !accessible ? "text-bw-white/25" : ""}`} strokeWidth={1.5} />
              {!accessible && (
                <Lock className="absolute -top-0.5 -right-0.5 h-3 w-3 text-amber-500/70" strokeWidth={2} />
              )}
            </Link>
          );
        })}
      </div>
    );
  }

  return (
    <Collapsible open={isOpen} onOpenChange={() => toggleSection(section.section)}>
      <CollapsibleTrigger className="w-full">
        <div className={`flex items-center justify-between px-3 py-2.5 rounded transition-all duration-200 group cursor-pointer ${
          hasActiveItem 
            ? "bg-bw-volt/[0.08] text-bw-white" 
            : "text-bw-white/[0.65] hover:bg-bw-volt/[0.06]"
        }`}>
          <div className="flex items-center gap-3">
            <div className={`p-1.5 rounded transition-colors ${
              hasActiveItem ? "bg-bw-volt/[0.12]" : "bg-bw-panel group-hover:bg-bw-volt/[0.08]"
            }`}>
              <SectionIcon className={`h-4 w-4 ${hasActiveItem ? "text-bw-volt" : "text-bw-white/45"}`} strokeWidth={1.5} />
            </div>
            <span className={`text-sm font-medium nav-section-label ${hasActiveItem ? "text-bw-white !text-sm !tracking-normal !normal-case !font-medium" : ""}`} style={{ fontFamily: hasActiveItem ? 'Manrope, sans-serif' : undefined }}>
              {section.section}
            </span>
          </div>
          <ChevronDown className={`h-4 w-4 text-bw-white/25 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
        </div>
      </CollapsibleTrigger>
      
      <CollapsibleContent className="overflow-hidden data-[state=open]:animate-slideDown data-[state=closed]:animate-slideUp">
        <div className="ml-4 pl-4 border-l border-white/[0.07] mt-1 space-y-0.5">
          {visibleItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            const accessible = isModuleAccessible(item.path, currentPlan);
            return (
              <Link
                key={item.path}
                to={accessible ? item.path : "#"}
                onClick={(e) => {
                  if (!accessible) {
                    e.preventDefault();
                    onLockedClick?.(item.path);
                  } else {
                    onClose?.();
                  }
                }}
                data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={`flex items-center gap-3 px-3 py-2 rounded transition-all duration-200 ${
                  isActive && accessible
                    ? "bg-bw-volt/[0.12] text-bw-volt font-semibold border-l-2 border-bw-volt rounded-l-none"
                    : accessible
                      ? "text-bw-white/[0.75] hover:text-bw-white hover:bg-bw-volt/[0.06]"
                      : "text-bw-white/[0.30] cursor-pointer hover:bg-white/[0.03]"
                }`}
              >
                <Icon className={`h-4 w-4 flex-shrink-0 ${isActive && accessible ? "text-bw-volt" : !accessible ? "text-bw-white/25" : "text-bw-white/50"}`} strokeWidth={1.5} />
                <span className="text-sm flex-1">{item.name}</span>
                {!accessible && (
                  <Lock className="h-3 w-3 text-amber-500/60 flex-shrink-0 ml-auto" strokeWidth={2} data-testid={`lock-icon-${item.path.slice(1)}`} />
                )}
              </Link>
            );
          })}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

const SidebarContent = ({ user, collapsed, setCollapsed, onLogout, onClose, currentPlan, onLockedClick }) => {
  const [openSections, setOpenSections] = useState({});
  
  const toggleSection = (sectionName) => {
    setOpenSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }));
  };

  return (
    <div className="flex flex-col h-full bg-bw-black">
      {/* Header with Logo */}
      <div className="p-4 border-b border-white/[0.07]">
        <div className="flex items-center justify-between">
          {!collapsed ? (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-bw-volt flex items-center justify-center">
                <Zap className="h-5 w-5 text-bw-black" strokeWidth={2} />
              </div>
              <div>
                <h1 className="text-lg font-extrabold text-bw-white tracking-tight" data-testid="sidebar-title">
                  Battwheels OS
                </h1>
                <p className="text-[9px] text-bw-white/35 font-medium tracking-[0.2em] uppercase font-mono">EV Intelligence</p>
              </div>
            </div>
          ) : (
            <div className="w-9 h-9 rounded bg-bw-volt flex items-center justify-center mx-auto">
              <Zap className="h-5 w-5 text-bw-black" strokeWidth={2} />
            </div>
          )}
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => setCollapsed?.(!collapsed)}
            className="text-bw-white/35 hover:text-bw-white hover:bg-bw-volt/[0.06] hidden lg:flex h-8 w-8"
            data-testid="collapse-sidebar-btn"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Quick Search (Desktop only, expanded) */}
      {!collapsed && (
        <div className="px-4 py-3 border-b border-white/[0.07]">
          <button 
            onClick={() => {
              // Dispatch keyboard event to open command palette
              document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
            }}
            className="w-full flex items-center gap-2 px-3 py-2 bg-bw-panel border border-white/[0.07] rounded text-bw-white/25 text-sm cursor-pointer hover:border-bw-volt/20 transition-colors"
            data-testid="quick-search-btn"
          >
            <Search className="h-4 w-4" />
            <span>Quick search...</span>
            <kbd className="ml-auto text-[10px] bg-white/5 text-bw-white/30 px-1.5 py-0.5 rounded border border-white/[0.07] font-mono">⌘K</kbd>
          </button>
        </div>
      )}

      {/* Navigation */}
      <ScrollArea className="flex-1 py-3">
        <nav className={`space-y-1 ${collapsed ? "px-2" : "px-3"}`}>
          {navItems.map((section) => (
            <NavSection
              key={section.section}
              section={section}
              user={user}
              collapsed={collapsed}
              onClose={onClose}
              openSections={openSections}
              toggleSection={toggleSection}
              currentPlan={currentPlan}
              onLockedClick={onLockedClick}
            />
          ))}
        </nav>
      </ScrollArea>

      {/* User Profile */}
      <div className="border-t border-white/[0.07] p-4 bg-bw-black">
        {/* AI Usage Counter */}
        {!collapsed ? (
          <div className="mb-3">
            <AIUsageCounter compact={false} className="bg-bw-panel" />
          </div>
        ) : (
          <div className="flex justify-center mb-3">
            <AIUsageCounter compact={true} />
          </div>
        )}
        {!collapsed ? (
          <div className="flex items-center gap-3 p-2 rounded bg-bw-black mb-3">
            <Avatar className="h-10 w-10 ring-1 ring-bw-volt/20">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-bw-volt/[0.12] border border-bw-volt/20 text-bw-volt font-bold text-sm">
                {user?.name?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-semibold truncate text-bw-white">{user?.name || "User"}</p>
              <p className="text-[11px] text-bw-white/35 truncate">{user?.role || "Member"}</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center mb-3">
            <Avatar className="h-10 w-10 ring-1 ring-bw-volt/20">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-bw-volt/[0.12] border border-bw-volt/20 text-bw-volt font-bold text-sm">
                {user?.name?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
          </div>
        )}
        
        <div className={`flex ${collapsed ? "flex-col gap-2 items-center" : "gap-2"}`}>
          <Link 
            to="/settings" 
            onClick={onClose}
            className={`flex items-center gap-2 px-3 py-2 rounded text-bw-white/35 hover:text-bw-white hover:bg-bw-volt/[0.06] transition-all ${collapsed ? "justify-center w-full" : "flex-1"}`}
            data-testid="nav-settings"
          >
            <Settings className="h-4 w-4" strokeWidth={1.5} />
            {!collapsed && <span className="text-sm font-medium">Settings</span>}
          </Link>
          <Button 
            variant="ghost" 
            onClick={() => { onLogout(); onClose?.(); }}
            className={`text-bw-white/35 hover:text-bw-red hover:bg-bw-red/[0.08] ${collapsed ? "w-full justify-center" : ""}`}
            data-testid="logout-btn"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.5} />
            {!collapsed && <span className="ml-2 text-sm font-medium">Logout</span>}
          </Button>
        </div>
        {!collapsed && (
          <p className="text-[10px] text-bw-white/20 text-center mt-2 font-mono" data-testid="version-footer">
            Battwheels OS v2.5.0
          </p>
        )}
      </div>
    </div>
  );
};

export default function Layout({ children, user, onLogout, emailVerified = true }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [resendSent, setResendSent] = useState(false);
  const [lockedModule, setLockedModule] = useState(null);
  const location = useLocation();
  const currentOrg = useOrganization();
  const currentPlan = (currentOrg?.plan_type || "free_trial").toLowerCase();

  // Clear upgrade prompt on route changes
  useEffect(() => {
    setLockedModule(null);
  }, [location.pathname]);

  const handleResendVerification = useCallback(async () => {
    try {
      const API = window.location.origin;
      await fetch(`${API}/api/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user?.email }),
      });
      setResendSent(true);
    } catch { /* silent */ }
  }, [user?.email]);

  // Mobile bottom tab items
  const MOBILE_TABS = [
    { name: "Home", icon: LayoutDashboard, path: "/dashboard" },
    { name: "Tickets", icon: Ticket, path: "/tickets" },
    { name: "Contacts", icon: Users, path: "/contacts" },
    { name: "Inventory", icon: Package, path: "/items" },
  ];

  return (
    <div className="min-h-screen bg-bw-off-black flex">{/* Desktop Sidebar */}
      <aside 
        className={`hidden lg:flex flex-col fixed left-0 top-0 h-screen bg-bw-black border-r border-white/[0.07] transition-all duration-300 z-50 ${
          collapsed ? "w-[72px]" : "w-72"
        }`}
        data-testid="desktop-sidebar"
      >
        <SidebarContent 
          user={user} 
          collapsed={collapsed} 
          setCollapsed={setCollapsed} 
          onLogout={onLogout}
          currentPlan={currentPlan}
          onLockedClick={(path) => { setLockedModule(path); }}
        />
      </aside>

      {/* Mobile Sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-80 bg-bw-black border-r border-white/[0.07]">
          <SidebarContent 
            user={user} 
            onLogout={onLogout}
            onClose={() => setMobileOpen(false)}
            currentPlan={currentPlan}
            onLockedClick={(path) => { setLockedModule(path); setMobileOpen(false); }}
          />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <main 
        className={`flex-1 min-w-0 overflow-x-hidden transition-all duration-300 ${
          collapsed ? "lg:ml-[72px]" : "lg:ml-72"
        }`}
      >
        {/* Top Header Bar */}
        <header className="sticky top-0 z-40 bg-bw-black/90 backdrop-blur-md border-b border-white/[0.07]">
          <div className="flex items-center justify-between px-4 lg:px-8 h-16">
            {/* Left side - Mobile menu button */}
            <div className="lg:hidden">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setMobileOpen(true)}
                className="h-10 w-10 bg-bw-panel hover:bg-bw-volt/[0.08] border border-white/[0.07] rounded"
                data-testid="mobile-menu-btn"
              >
                <Menu className="h-5 w-5 text-bw-white/70" />
              </Button>
            </div>
            
            {/* Left side desktop - Organization Switcher */}
            <div className="hidden lg:flex items-center">
              <OrganizationSwitcher user={user} />
            </div>
            
            {/* Center - Spacer */}
            <div className="flex-1" />
            
            {/* Right side - Actions */}
            <div className="flex items-center gap-3">
              <NotificationBell />
              <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-white/[0.07]">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-bw-volt/[0.12] border border-bw-volt/20 text-bw-volt text-xs font-bold">
                    {user?.name?.charAt(0) || "U"}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium text-bw-white">{user?.name?.split(' ')[0]}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Email Verification Banner */}
        {!emailVerified && (
          <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 lg:px-8 py-3 flex items-center justify-between" data-testid="email-verify-banner">
            <span className="text-amber-400 text-sm">
              Please verify your email to unlock all features. Check your inbox for the verification link.
            </span>
            <button
              onClick={handleResendVerification}
              disabled={resendSent}
              className="text-amber-400 text-sm underline ml-4 hover:text-amber-300 transition whitespace-nowrap disabled:opacity-50"
              data-testid="resend-verification-btn"
            >
              {resendSent ? "Email sent!" : "Resend email"}
            </button>
          </div>
        )}

        {/* Page Content - wrapped in FeatureGateBanner for plan-gated routes */}
        <div className="p-4 pb-[76px] lg:p-8 lg:pb-8">
          {lockedModule ? (
            <UpgradePrompt
              modulePath={lockedModule}
              currentPlan={currentPlan}
              onClose={() => setLockedModule(null)}
            />
          ) : (
            <FeatureGateBanner>
              {children}
            </FeatureGateBanner>
          )}
        </div>
      </main>

      {/* ── MOBILE BOTTOM TAB BAR ── */}
      <nav
        data-testid="mobile-bottom-nav"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around"
        style={{
          height: "60px",
          background: "rgb(var(--bw-black))",
          borderTop: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        {MOBILE_TABS.map((tab) => {
          const isActive =
            location.pathname === tab.path ||
            location.pathname.startsWith(tab.path + "/");
          const { icon: Icon } = tab;
          return (
            <Link
              key={tab.path}
              to={tab.path}
              data-testid={`mobile-tab-${tab.name.toLowerCase()}`}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "3px",
                flex: 1,
                height: "60px",
                textDecoration: "none",
                color: isActive ? "rgb(var(--bw-volt))" : "rgba(244,246,240,0.40)",
                transition: "color 0.15s",
              }}
            >
              <Icon style={{ width: "20px", height: "20px" }} />
              <span
                style={{
                  fontSize: "10px",
                  fontFamily: "Syne, sans-serif",
                  fontWeight: isActive ? 600 : 400,
                  letterSpacing: "0.02em",
                }}
              >
                {tab.name}
              </span>
            </Link>
          );
        })}
        {/* More button opens sidebar sheet */}
        <button
          data-testid="mobile-tab-more"
          onClick={() => setMobileOpen(true)}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "3px",
            flex: 1,
            height: "60px",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "rgb(var(--bw-white) / 0.40)",
            transition: "color 0.15s",
          }}
        >
          <Menu style={{ width: "20px", height: "20px" }} />
          <span style={{ fontSize: "10px", fontFamily: "Syne, sans-serif" }}>More</span>
        </button>
      </nav>
    </div>
  );
}
