import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  LayoutDashboard,
  Car,
  ClipboardList,
  FileText,
  CreditCard,
  Shield,
  LogOut,
  Menu,
  X,
  Phone,
  Calendar
} from "lucide-react";

const customerNavItems = [
  { path: "/customer", icon: LayoutDashboard, label: "Dashboard" },
  { path: "/customer/vehicles", icon: Car, label: "My Vehicles" },
  { path: "/customer/service-history", icon: ClipboardList, label: "Service History" },
  { path: "/customer/invoices", icon: FileText, label: "Invoices" },
  { path: "/customer/payments", icon: CreditCard, label: "Payments Due" },
  { path: "/customer/amc", icon: Shield, label: "AMC Plans" },
];

export default function CustomerLayout({ children, user, onLogout }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await onLogout();
    navigate("/login");
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  return (
    <div className="min-h-screen bg-[#111820]">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-[#111820] border-b border-[rgba(255,255,255,0.07)] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <span className="font-bold text-lg text-[#C8FF00] text-600">Battwheels OS</span>
        </div>
        <Avatar className="h-8 w-8">
          <AvatarImage src={user?.picture} />
          <AvatarFallback className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] text-700">
            {getInitials(user?.name)}
          </AvatarFallback>
        </Avatar>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          fixed lg:sticky top-0 left-0 z-40 h-screen w-64 bg-[#111820] border-r border-[rgba(255,255,255,0.07)]
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="hidden lg:flex items-center gap-3 px-6 py-5 border-b border-[rgba(255,255,255,0.07)]">
              <div className="h-10 w-10 rounded-lg bg-[rgba(200,255,0,0.08)]0 flex items-center justify-center">
                <Car className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg text-[#F4F6F0]">Battwheels OS</h1>
                <p className="text-xs text-[rgba(244,246,240,0.45)]">Customer Portal</p>
              </div>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
              <nav className="space-y-1">
                {customerNavItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path || 
                    (item.path !== "/customer" && location.pathname.startsWith(item.path));
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`
                        flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                        transition-colors duration-150
                        ${isActive 
                          ? 'bg-[rgba(200,255,0,0.08)] text-[#C8FF00] text-700' 
                          : 'text-[rgba(244,246,240,0.35)] hover:bg-[#111820] hover:text-[#F4F6F0]'
                        }
                      `}
                    >
                      <Icon className={`h-5 w-5 ${isActive ? 'text-[#C8FF00] text-600' : 'text-[rgba(244,246,240,0.45)]'}`} />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>

              {/* Quick Actions */}
              <div className="mt-6 pt-6 border-t border-[rgba(255,255,255,0.07)]">
                <p className="px-3 mb-2 text-xs font-semibold text-[rgba(244,246,240,0.45)] uppercase tracking-wider">
                  Quick Actions
                </p>
                <Link
                  to="/customer/request-callback"
                  onClick={() => setSidebarOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[rgba(244,246,240,0.35)] hover:bg-[#111820] hover:text-[#F4F6F0]"
                >
                  <Phone className="h-5 w-5 text-[rgba(244,246,240,0.45)]" />
                  Request Callback
                </Link>
                <Link
                  to="/customer/book-appointment"
                  onClick={() => setSidebarOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[rgba(244,246,240,0.35)] hover:bg-[#111820] hover:text-[#F4F6F0]"
                >
                  <Calendar className="h-5 w-5 text-[rgba(244,246,240,0.45)]" />
                  Book Appointment
                </Link>
              </div>
            </ScrollArea>

            {/* User Info & Logout */}
            <div className="border-t border-[rgba(255,255,255,0.07)] p-4">
              <div className="flex items-center gap-3 mb-3">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] text-700">
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#F4F6F0] truncate">{user?.name}</p>
                  <p className="text-xs text-[rgba(244,246,240,0.45)] truncate">{user?.email}</p>
                </div>
              </div>
              <Button 
                variant="outline" 
                className="w-full justify-start text-[rgba(244,246,240,0.35)] hover:text-red-600 hover:border-red-200"
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
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 min-h-screen">
          <div className="p-4 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
