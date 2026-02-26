import { useState } from "react";
import { Link, useLocation, useNavigate, Outlet } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  Ticket,
  Clock,
  Calendar,
  Wallet,
  TrendingUp,
  Bot,
  LogOut,
  Menu,
  X,
  Bell,
  Zap,
  ChevronRight
} from "lucide-react";

const technicianNavItems = [
  { path: "/technician", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { path: "/technician/tickets", icon: Ticket, label: "My Tickets" },
  { path: "/technician/attendance", icon: Clock, label: "Attendance" },
  { path: "/technician/leave", icon: Calendar, label: "Leave Requests" },
  { path: "/technician/payroll", icon: Wallet, label: "Payroll" },
  { path: "/technician/productivity", icon: TrendingUp, label: "My Performance" },
  { path: "/technician/ai-assist", icon: Bot, label: "AI Assistant" },
];

export default function TechnicianLayout({ children, user, onLogout }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await onLogout();
    navigate("/login");
  };

  const getInitials = (name) => {
    if (!name) return "T";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const isActive = (path, exact = false) => {
    if (exact) {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-950" data-testid="technician-layout">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-slate-900 border-b border-[rgba(255,255,255,0.07)] border-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-400 hover:text-white"
          >
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-green-500" />
            <span className="font-bold text-lg text-white">Battwheels OS</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="relative text-slate-400 hover:text-white">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-2 w-2 bg-[rgba(255,59,47,0.08)]0 rounded-full"></span>
          </button>
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.picture} />
            <AvatarFallback className="bg-[rgba(34,197,94,0.08)]0/20 text-green-400">
              {getInitials(user?.name)}
            </AvatarFallback>
          </Avatar>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          fixed lg:sticky top-0 left-0 z-40 h-screen w-64 bg-slate-900 border-r border-[rgba(255,255,255,0.07)] border-800
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="hidden lg:flex items-center gap-3 px-6 py-5 border-b border-[rgba(255,255,255,0.07)] border-800">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg text-white">Battwheels OS</h1>
                <p className="text-xs text-slate-500">Technician Portal</p>
              </div>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
              <nav className="space-y-1">
                {technicianNavItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path, item.exact);
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`
                        group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                        transition-all duration-200
                        ${active 
                          ? 'bg-[rgba(34,197,94,0.08)]0/10 text-green-400 border border-green-500/20' 
                          : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                        }
                      `}
                    >
                      <Icon className={`h-5 w-5 ${active ? 'text-green-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                      <span className="flex-1">{item.label}</span>
                      {active && <ChevronRight className="h-4 w-4 text-green-400" />}
                    </Link>
                  );
                })}
              </nav>

              {/* Quick Status */}
              <div className="mt-6 pt-6 border-t border-[rgba(255,255,255,0.07)] border-800">
                <div className="px-3 py-3 rounded-lg bg-slate-800/50">
                  <p className="text-xs font-medium text-slate-400 mb-2">Today's Status</p>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-[rgba(34,197,94,0.08)]0 animate-pulse"></div>
                    <span className="text-sm text-white">On Duty</span>
                  </div>
                </div>
              </div>
            </ScrollArea>

            {/* User Info & Logout */}
            <div className="border-t border-[rgba(255,255,255,0.07)] border-800 p-4">
              <div className="flex items-center gap-3 mb-3 px-2">
                <Avatar className="h-10 w-10 ring-2 ring-green-500/20">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-[rgba(34,197,94,0.08)]0/20 text-green-400">
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{user?.name}</p>
                  <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                </div>
              </div>
              <Button 
                variant="outline" 
                className="w-full justify-start border-[rgba(255,255,255,0.07)] border-700 text-slate-400 hover:text-red-400 hover:border-red-500/30 hover:bg-[rgba(255,59,47,0.08)]0/10"
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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 min-h-screen">
          <div className="p-4 lg:p-6">
            {children || <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
}
