import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import FeatureGateBanner from "./FeatureGateBanner";
import OrganizationSwitcher from "./OrganizationSwitcher";
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
  Scale
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import NotificationBell from "@/components/NotificationBell";

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
      { name: "AI Assistant", path: "/ai-assistant", icon: Bot },
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
      { name: "Fixed Assets", path: "/fixed-assets", icon: Package },
      { name: "Chart of Accounts", path: "/chart-of-accounts", icon: Layers },
      { name: "Journal Entries", path: "/journal-entries", icon: BookOpen },
      { name: "Trial Balance", path: "/trial-balance", icon: Scale },
      { name: "Opening Balances", path: "/opening-balances", icon: Landmark },
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
      { name: "All Settings", path: "/all-settings", icon: Settings, adminOnly: true },
      { name: "Organization", path: "/organization-settings", icon: Building2, adminOnly: true },
      { name: "Data Management", path: "/data-management", icon: Database, adminOnly: true },
      { name: "Documents", path: "/documents", icon: FolderOpen, adminOnly: true },
      { name: "Taxes", path: "/taxes", icon: Percent, adminOnly: true },
      { name: "Users", path: "/users", icon: Users, adminOnly: true },
      { name: "Custom Modules", path: "/custom-modules", icon: Database, adminOnly: true },
      { name: "Activity Logs", path: "/activity-logs", icon: Activity, adminOnly: true },
      { name: "Zoho Sync", path: "/zoho-sync", icon: CloudDownload, adminOnly: true },
      { name: "Exchange Rates", path: "/exchange-rates", icon: ArrowRightLeft },
      { name: "Customer Portal", path: "/customer-portal", icon: Building2 },
    ]
  },
];

// Collapsible Navigation Section Component
const NavSection = ({ section, user, collapsed, onClose, openSections, toggleSection }) => {
  const location = useLocation();
  const SectionIcon = section.icon;
  const isOpen = openSections[section.section] ?? section.defaultOpen;
  
  // Check if any item in this section is active
  const hasActiveItem = section.items.some(item => location.pathname === item.path);
  
  // Filter out admin-only items for non-admin users
  const visibleItems = section.items.filter(item => !item.adminOnly || user?.role === "admin");
  
  if (visibleItems.length === 0) return null;

  if (collapsed) {
    // In collapsed mode, show only the first item or section icon
    return (
      <div className="space-y-1">
        {visibleItems.slice(0, 3).map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onClose}
              title={item.name}
              className={`flex items-center justify-center p-2.5 rounded transition-all duration-200 ${
                isActive
                  ? "bg-[rgba(200,255,0,0.12)] text-[#C8FF00] border-l-2 border-[#C8FF00]"
                  : "text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive ? "text-[#C8FF00]" : ""}`} strokeWidth={1.5} />
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
            ? "bg-[rgba(200,255,0,0.08)] text-[#F4F6F0]" 
            : "text-[rgba(244,246,240,0.45)] hover:bg-[rgba(200,255,0,0.06)]"
        }`}>
          <div className="flex items-center gap-3">
            <div className={`p-1.5 rounded transition-colors ${
              hasActiveItem ? "bg-[rgba(200,255,0,0.12)]" : "bg-[#111820] group-hover:bg-[rgba(200,255,0,0.08)]"
            }`}>
              <SectionIcon className={`h-4 w-4 ${hasActiveItem ? "text-[#C8FF00]" : "text-[rgba(244,246,240,0.3)]"}`} strokeWidth={1.5} />
            </div>
            <span className={`text-sm font-medium nav-section-label ${hasActiveItem ? "text-[#F4F6F0] !text-sm !tracking-normal !normal-case !font-medium" : ""}`} style={{ fontFamily: hasActiveItem ? 'Manrope, sans-serif' : undefined }}>
              {section.section}
            </span>
          </div>
          <ChevronDown className={`h-4 w-4 text-[rgba(244,246,240,0.25)] transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
        </div>
      </CollapsibleTrigger>
      
      <CollapsibleContent className="overflow-hidden data-[state=open]:animate-slideDown data-[state=closed]:animate-slideUp">
        <div className="ml-4 pl-4 border-l border-[rgba(255,255,255,0.07)] mt-1 space-y-0.5">
          {visibleItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={`flex items-center gap-3 px-3 py-2 rounded transition-all duration-200 ${
                  isActive
                    ? "bg-[rgba(200,255,0,0.12)] text-[#C8FF00] font-semibold border-l-2 border-[#C8FF00] rounded-l-none"
                    : "text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"
                }`}
              >
                <Icon className={`h-4 w-4 flex-shrink-0 ${isActive ? "text-[#C8FF00]" : "text-[rgba(244,246,240,0.3)]"}`} strokeWidth={1.5} />
                <span className="text-sm">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

const SidebarContent = ({ user, collapsed, setCollapsed, onLogout, onClose }) => {
  const [openSections, setOpenSections] = useState({});
  
  const toggleSection = (sectionName) => {
    setOpenSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }));
  };

  return (
    <div className="flex flex-col h-full bg-[#080C0F]">
      {/* Header with Logo */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.07)]">
        <div className="flex items-center justify-between">
          {!collapsed ? (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-[#C8FF00] flex items-center justify-center">
                <Zap className="h-5 w-5 text-[#080C0F]" strokeWidth={2} />
              </div>
              <div>
                <h1 className="text-lg font-extrabold text-[#F4F6F0] tracking-tight" data-testid="sidebar-title">
                  Battwheels OS
                </h1>
                <p className="text-[9px] text-[rgba(244,246,240,0.35)] font-medium tracking-[0.2em] uppercase font-mono">EV Intelligence</p>
              </div>
            </div>
          ) : (
            <div className="w-9 h-9 rounded bg-[#C8FF00] flex items-center justify-center mx-auto">
              <Zap className="h-5 w-5 text-[#080C0F]" strokeWidth={2} />
            </div>
          )}
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => setCollapsed?.(!collapsed)}
            className="text-[rgba(244,246,240,0.35)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)] hidden lg:flex h-8 w-8"
            data-testid="collapse-sidebar-btn"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
          {onClose && (
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={onClose}
              className="text-[rgba(244,246,240,0.35)] hover:text-[#F4F6F0] lg:hidden h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Quick Search (Desktop only, expanded) */}
      {!collapsed && (
        <div className="px-4 py-3 border-b border-[rgba(255,255,255,0.07)]">
          <button 
            onClick={() => {
              // Dispatch keyboard event to open command palette
              document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
            }}
            className="w-full flex items-center gap-2 px-3 py-2 bg-[#111820] border border-[rgba(255,255,255,0.07)] rounded text-[rgba(244,246,240,0.25)] text-sm cursor-pointer hover:border-[rgba(200,255,0,0.2)] transition-colors"
            data-testid="quick-search-btn"
          >
            <Search className="h-4 w-4" />
            <span>Quick search...</span>
            <kbd className="ml-auto text-[10px] bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.3)] px-1.5 py-0.5 rounded border border-[rgba(255,255,255,0.07)] font-mono">⌘K</kbd>
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
            />
          ))}
        </nav>
      </ScrollArea>

      {/* User Profile */}
      <div className="border-t border-[rgba(255,255,255,0.07)] p-4 bg-[#080C0F]">
        {!collapsed ? (
          <div className="flex items-center gap-3 p-2 rounded bg-[#080C0F] mb-3">
            <Avatar className="h-10 w-10 ring-1 ring-[rgba(200,255,0,0.2)]">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-[rgba(200,255,0,0.12)] border border-[rgba(200,255,0,0.2)] text-[#C8FF00] font-bold text-sm">
                {user?.name?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-semibold truncate text-[#F4F6F0]">{user?.name || "User"}</p>
              <p className="text-[11px] text-[rgba(244,246,240,0.35)] truncate">{user?.role || "Member"}</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center mb-3">
            <Avatar className="h-10 w-10 ring-1 ring-[rgba(200,255,0,0.2)]">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-[rgba(200,255,0,0.12)] border border-[rgba(200,255,0,0.2)] text-[#C8FF00] font-bold text-sm">
                {user?.name?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
          </div>
        )}
        
        <div className={`flex ${collapsed ? "flex-col gap-2 items-center" : "gap-2"}`}>
          <Link 
            to="/settings" 
            onClick={onClose}
            className={`flex items-center gap-2 px-3 py-2 rounded text-[rgba(244,246,240,0.35)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)] transition-all ${collapsed ? "justify-center w-full" : "flex-1"}`}
            data-testid="nav-settings"
          >
            <Settings className="h-4 w-4" strokeWidth={1.5} />
            {!collapsed && <span className="text-sm font-medium">Settings</span>}
          </Link>
          <Button 
            variant="ghost" 
            onClick={() => { onLogout(); onClose?.(); }}
            className={`text-[rgba(244,246,240,0.35)] hover:text-[#FF3B2F] hover:bg-[rgba(255,59,47,0.08)] ${collapsed ? "w-full justify-center" : ""}`}
            data-testid="logout-btn"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.5} />
            {!collapsed && <span className="ml-2 text-sm font-medium">Logout</span>}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default function Layout({ children, user, onLogout }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Mobile bottom tab items
  const MOBILE_TABS = [
    { name: "Home", icon: LayoutDashboard, path: "/dashboard" },
    { name: "Tickets", icon: Ticket, path: "/tickets" },
    { name: "Contacts", icon: Users, path: "/contacts" },
    { name: "Inventory", icon: Package, path: "/items" },
  ];

  return (
    <div className="min-h-screen bg-[#0D1317] flex">{/* Desktop Sidebar */}
      <aside 
        className={`hidden lg:flex flex-col fixed left-0 top-0 h-screen bg-[#080C0F] border-r border-[rgba(255,255,255,0.07)] transition-all duration-300 z-50 ${
          collapsed ? "w-[72px]" : "w-72"
        }`}
        data-testid="desktop-sidebar"
      >
        <SidebarContent 
          user={user} 
          collapsed={collapsed} 
          setCollapsed={setCollapsed} 
          onLogout={onLogout} 
        />
      </aside>

      {/* Mobile Sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-80 bg-[#080C0F] border-r border-[rgba(255,255,255,0.07)]">
          <SidebarContent 
            user={user} 
            onLogout={onLogout}
            onClose={() => setMobileOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <main 
        className={`flex-1 transition-all duration-300 ${
          collapsed ? "lg:ml-[72px]" : "lg:ml-72"
        }`}
      >
        {/* Top Header Bar */}
        <header className="sticky top-0 z-40 bg-[#080C0F]/90 backdrop-blur-md border-b border-[rgba(255,255,255,0.07)]">
          <div className="flex items-center justify-between px-4 lg:px-8 h-16">
            {/* Left side - Mobile menu button */}
            <div className="lg:hidden">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setMobileOpen(true)}
                className="h-10 w-10 bg-[#111820] hover:bg-[rgba(200,255,0,0.08)] border border-[rgba(255,255,255,0.07)] rounded"
                data-testid="mobile-menu-btn"
              >
                <Menu className="h-5 w-5 text-[rgba(244,246,240,0.7)]" />
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
              <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-[rgba(255,255,255,0.07)]">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-[rgba(200,255,0,0.12)] border border-[rgba(200,255,0,0.2)] text-[#C8FF00] text-xs font-bold">
                    {user?.name?.charAt(0) || "U"}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium text-[#F4F6F0]">{user?.name?.split(' ')[0]}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content — wrapped in FeatureGateBanner for plan-gated routes */}
        <div className="p-4 lg:p-8">
          <FeatureGateBanner>
            {children}
          </FeatureGateBanner>
        </div>
      </main>
    </div>
  );
}
