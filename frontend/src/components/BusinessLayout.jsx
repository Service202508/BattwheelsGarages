import { useState } from "react";
import { Link, useLocation, useNavigate, Outlet } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  Ticket,
  Car,
  FileText,
  CreditCard,
  Shield,
  BarChart3,
  LogOut,
  Menu,
  X,
  Bell,
  Building2,
  ChevronRight,
  Plus
} from "lucide-react";

const businessNavItems = [
  { path: "/business", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { path: "/business/fleet", icon: Car, label: "Fleet Management" },
  { path: "/business/tickets", icon: Ticket, label: "Service Tickets" },
  { path: "/business/invoices", icon: FileText, label: "Invoices" },
  { path: "/business/payments", icon: CreditCard, label: "Payments" },
  { path: "/business/amc", icon: Shield, label: "AMC Contracts" },
  { path: "/business/reports", icon: BarChart3, label: "Reports" },
];

export default function BusinessLayout({ children, user, onLogout }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await onLogout();
    navigate("/login");
  };

  const getInitials = (name) => {
    if (!name) return "B";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const isActive = (path, exact = false) => {
    if (exact) {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" data-testid="business-layout">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-[#111820] border-b border-[rgba(255,255,255,0.07)] border-200 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-600 hover:text-slate-900"
          >
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <div className="flex items-center gap-2">
            <Building2 className="h-6 w-6 text-indigo-600" />
            <span className="font-bold text-lg text-slate-900">Business Portal</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="relative text-slate-500 hover:text-slate-700">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-2 w-2 bg-[rgba(255,59,47,0.08)]0 rounded-full"></span>
          </button>
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.picture} />
            <AvatarFallback className="bg-indigo-100 text-indigo-600">
              {getInitials(user?.name)}
            </AvatarFallback>
          </Avatar>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          fixed lg:sticky top-0 left-0 z-40 h-screen w-72 bg-[#111820] border-r border-[rgba(255,255,255,0.07)] border-200
          transform transition-transform duration-200 ease-in-out lg:shadow-none
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <div className="flex flex-col h-full">
            {/* Logo & Business Info */}
            <div className="hidden lg:block px-6 py-5 border-b border-[rgba(255,255,255,0.07)] border-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Building2 className="h-7 w-7 text-white" />
                </div>
                <div>
                  <h1 className="font-bold text-lg text-slate-900">Business Portal</h1>
                  <p className="text-xs text-slate-500">Fleet Management</p>
                </div>
              </div>
              {/* Business Name Badge */}
              <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-100">
                <p className="text-xs text-indigo-600 font-medium">Organization</p>
                <p className="text-sm text-slate-900 font-semibold truncate">{user?.organization || user?.name}</p>
              </div>
            </div>

            {/* Quick Action */}
            <div className="px-4 py-3 border-b border-[rgba(255,255,255,0.07)] border-200">
              <Link to="/business/tickets/new">
                <Button className="w-full bg-indigo-600 hover:bg-indigo-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Raise Service Ticket
                </Button>
              </Link>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
              <nav className="space-y-1">
                {businessNavItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path, item.exact);
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`
                        group flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium
                        transition-all duration-200
                        ${active 
                          ? 'bg-indigo-50 text-indigo-700 shadow-sm' 
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                        }
                      `}
                    >
                      <div className={`
                        p-2 rounded-lg transition-colors
                        ${active ? 'bg-indigo-100' : 'bg-[rgba(255,255,255,0.05)] group-hover:bg-slate-200'}
                      `}>
                        <Icon className={`h-5 w-5 ${active ? 'text-indigo-600' : 'text-slate-500'}`} />
                      </div>
                      <span className="flex-1">{item.label}</span>
                      {active && <ChevronRight className="h-4 w-4 text-indigo-400" />}
                    </Link>
                  );
                })}
              </nav>
            </ScrollArea>

            {/* User Info & Logout */}
            <div className="border-t border-[rgba(255,255,255,0.07)] border-200 p-4 bg-slate-50">
              <div className="flex items-center gap-3 mb-3 px-2">
                <Avatar className="h-10 w-10 ring-2 ring-indigo-100">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-indigo-100 text-indigo-600">
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
                  <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                </div>
              </div>
              <Button 
                variant="outline" 
                className="w-full justify-start border-[rgba(255,255,255,0.07)] border-300 text-slate-600 hover:text-red-600 hover:border-red-200 hover:bg-[rgba(255,59,47,0.08)]"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 min-h-screen">
          <div className="p-6 lg:p-8 max-w-7xl mx-auto">
            {children || <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
}
