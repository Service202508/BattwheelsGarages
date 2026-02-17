import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
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
  Menu,
  X,
  FileText,
  TrendingUp,
  ShoppingCart,
  Receipt,
  Calculator,
  Truck,
  Building2,
  DollarSign,
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
  CheckSquare
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import NotificationBell from "@/components/NotificationBell";

const navItems = [
  { section: "Intelligence", items: [
    { name: "Failure Intelligence", path: "/failure-intelligence", icon: Brain },
    { name: "Fault Tree Import", path: "/fault-tree-import", icon: FileText },
  ]},
  { section: "General", items: [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Data Insights", path: "/insights", icon: TrendingUp },
  ]},
  { section: "Operations", items: [
    { name: "New Ticket", path: "/tickets/new", icon: Ticket },
    { name: "Complaint Dashboard", path: "/tickets", icon: FileText },
    { name: "Predictive Maintenance", path: "/ai-assistant", icon: Bot },
    { name: "Vehicles", path: "/vehicles", icon: Car },
    { name: "AMC Management", path: "/amc", icon: Shield },
    { name: "Alerts", path: "/alerts", icon: Bell },
  ]},
  { section: "Projects & Time", items: [
    { name: "Projects", path: "/projects", icon: FolderKanban },
  ]},
  { section: "Catalog & Inventory", items: [
    { name: "Items", path: "/items", icon: Tag },
    { name: "Services & Parts", path: "/inventory", icon: Package },
    { name: "Price Lists", path: "/price-lists", icon: List },
    { name: "Inventory Adjustments", path: "/inventory-adjustments", icon: ClipboardList },
  ]},
  { section: "HR & Payroll", items: [
    { name: "Employees", path: "/employees", icon: Users },
    { name: "Technician Productivity", path: "/productivity", icon: BarChart3 },
    { name: "Attendance", path: "/attendance", icon: Clock },
    { name: "Leave Management", path: "/leave", icon: Calendar },
    { name: "Payroll", path: "/payroll", icon: Wallet },
  ]},
  { section: "Sales", items: [
    { name: "Customers", path: "/customers", icon: Users },
    { name: "Quotes", path: "/quotes", icon: FileText },
    { name: "Sales Orders", path: "/sales", icon: ShoppingCart },
    { name: "Delivery Challans", path: "/delivery-challans", icon: Truck },
    { name: "Invoices", path: "/invoices", icon: Receipt },
    { name: "Recurring Invoices", path: "/recurring-transactions", icon: Repeat },
    { name: "Credit Notes", path: "/credit-notes", icon: FileText },
  ]},
  { section: "Purchases", items: [
    { name: "Vendors", path: "/suppliers", icon: Building2 },
    { name: "Purchase Orders", path: "/purchases", icon: Truck },
    { name: "Bills", path: "/bills", icon: Receipt },
    { name: "Vendor Credits", path: "/vendor-credits", icon: CreditCard },
  ]},
  { section: "Finance", items: [
    { name: "Expenses", path: "/expenses", icon: Receipt },
    { name: "Recurring Expenses", path: "/recurring-expenses", icon: Repeat },
    { name: "Banking", path: "/banking", icon: Wallet },
    { name: "Chart of Accounts", path: "/chart-of-accounts", icon: Layers },
    { name: "Journal Entries", path: "/journal-entries", icon: BookOpen },
    { name: "Opening Balances", path: "/opening-balances", icon: Landmark },
    { name: "Exchange Rates", path: "/exchange-rates", icon: ArrowRightLeft },
    { name: "Reports", path: "/reports", icon: BarChart3 },
    { name: "GST Returns", path: "/gst-reports", icon: FileText },
    { name: "Accounting", path: "/accounting", icon: Calculator },
  ]},
  { section: "Projects", items: [
    { name: "Projects", path: "/projects", icon: FolderKanban },
    { name: "Project Tasks", path: "/project-tasks", icon: CheckSquare },
  ]},
  { section: "Administration", items: [
    { name: "Taxes", path: "/taxes", icon: Percent, adminOnly: true },
    { name: "Users", path: "/users", icon: Users, adminOnly: true },
    { name: "Activity Logs", path: "/activity-logs", icon: Activity, adminOnly: true },
    { name: "Data Migration", path: "/data-migration", icon: Database, adminOnly: true },
  ]},
];

const SidebarContent = ({ user, collapsed, setCollapsed, onLogout, onClose }) => {
  const location = useLocation();

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <h1 className="text-xl font-bold text-gray-900 tracking-tight" data-testid="sidebar-title">
              Battwheels OS
            </h1>
          )}
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => setCollapsed?.(!collapsed)}
            className="text-gray-500 hover:text-gray-900 hover:bg-gray-100 hidden lg:flex"
            data-testid="collapse-sidebar-btn"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
          {onClose && (
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={onClose}
              className="text-gray-500 hover:text-gray-900 lg:hidden"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-4">
        <nav className="space-y-6 px-3">
          {navItems.map((section) => (
            <div key={section.section}>
              {!collapsed && (
                <p className="text-xs uppercase tracking-widest text-gray-400 mb-3 px-3 font-medium">
                  {section.section}
                </p>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  if (item.adminOnly && user?.role !== "admin") return null;
                  const isActive = location.pathname === item.path;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                        isActive
                          ? "bg-[#22EDA9]/15 text-gray-900 font-medium"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                      } ${collapsed ? "justify-center" : ""}`}
                    >
                      <Icon className={`h-5 w-5 flex-shrink-0 ${isActive ? "text-[#22EDA9]" : ""}`} strokeWidth={1.5} />
                      {!collapsed && <span className="text-sm">{item.name}</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* User Profile */}
      <div className="border-t border-gray-200 p-4">
        {!collapsed ? (
          <div className="flex items-center gap-3 mb-4">
            <Avatar className="h-10 w-10">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-[#22EDA9] text-black font-semibold">
                {user?.name?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-gray-900">{user?.name || "User"}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center mb-4">
            <Avatar className="h-10 w-10">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-[#22EDA9] text-black font-semibold">
                {user?.name?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
          </div>
        )}
        
        <div className={`flex ${collapsed ? "flex-col gap-2 items-center" : "gap-2"}`}>
          <Link 
            to="/settings" 
            onClick={onClose}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors ${collapsed ? "justify-center w-full" : "flex-1"}`}
            data-testid="nav-settings"
          >
            <Settings className="h-4 w-4" strokeWidth={1.5} />
            {!collapsed && <span className="text-sm">Settings</span>}
          </Link>
          <Button 
            variant="ghost" 
            onClick={() => { onLogout(); onClose?.(); }}
            className={`text-gray-600 hover:text-gray-900 hover:bg-gray-100 ${collapsed ? "w-full justify-center" : ""}`}
            data-testid="logout-btn"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.5} />
            {!collapsed && <span className="ml-2 text-sm">Logout</span>}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default function Layout({ children, user, onLogout }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Desktop Sidebar */}
      <aside 
        className={`hidden lg:flex flex-col fixed left-0 top-0 h-screen bg-white border-r border-gray-200 transition-all duration-300 z-50 ${
          collapsed ? "w-20" : "w-64"
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

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 z-40 shadow-sm">
        <div className="flex items-center">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-gray-600 hover:text-gray-900" data-testid="mobile-menu-btn">
                <Menu className="h-6 w-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0 bg-white border-r border-gray-200">
              <SidebarContent 
                user={user} 
                collapsed={false} 
                onLogout={onLogout}
                onClose={() => setMobileOpen(false)}
              />
            </SheetContent>
          </Sheet>
          <h1 className="ml-4 text-lg font-bold text-gray-900">Battwheels OS</h1>
        </div>
        <NotificationBell user={user} />
      </div>

      {/* Desktop Top Bar (optional - for notifications) */}
      <div className="hidden lg:flex fixed top-4 right-6 z-30">
        <NotificationBell user={user} />
      </div>

      {/* Main Content */}
      <main 
        className={`flex-1 transition-all duration-300 ${
          collapsed ? "lg:ml-20" : "lg:ml-64"
        } mt-16 lg:mt-0`}
      >
        <div className="p-6 md:p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
