import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { 
  LayoutDashboard, FileText, Users, Car, Package, Receipt, ShoppingCart, 
  Truck, Brain, Bot, Ticket, Calculator, Wallet, BarChart3, Settings,
  Plus, Search, Clock, Star, Zap, Shield, Bell, Calendar, Activity
} from "lucide-react";

// Navigation items for quick access
const navigationItems = [
  { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard, keywords: ["home", "overview", "main"] },
  { name: "All Tickets", path: "/tickets", icon: Ticket, keywords: ["complaints", "issues", "service"] },
  { name: "New Ticket", path: "/tickets/new", icon: Plus, keywords: ["create ticket", "add complaint"] },
  { name: "Estimates", path: "/estimates", icon: FileText, keywords: ["quotes", "quotations"] },
  { name: "Invoices", path: "/invoices-enhanced", icon: Receipt, keywords: ["bills", "payments"] },
  { name: "Sales Orders", path: "/sales-orders", icon: ShoppingCart, keywords: ["orders", "sales"] },
  { name: "Purchase Orders", path: "/purchases", icon: Truck, keywords: ["po", "procurement"] },
  { name: "Contacts", path: "/contacts", icon: Users, keywords: ["customers", "vendors", "clients"] },
  { name: "Items & Products", path: "/items", icon: Package, keywords: ["inventory", "stock", "products"] },
  { name: "Inventory", path: "/inventory-enhanced", icon: Package, keywords: ["stock management", "warehouse"] },
  { name: "Vehicles", path: "/vehicles", icon: Car, keywords: ["ev", "electric vehicles", "cars"] },
  { name: "Failure Intelligence", path: "/failure-intelligence", icon: Brain, keywords: ["efi", "diagnostics", "ai"] },
  { name: "AI Assistant", path: "/ai-assistant", icon: Bot, keywords: ["chat", "help", "assistant"] },
  { name: "Banking", path: "/banking", icon: Wallet, keywords: ["accounts", "bank", "transactions"] },
  { name: "Expenses", path: "/expenses", icon: Receipt, keywords: ["costs", "spending"] },
  { name: "Reports", path: "/reports", icon: BarChart3, keywords: ["analytics", "insights"] },
  { name: "GST Reports", path: "/gst-reports", icon: Calculator, keywords: ["tax", "gst", "returns"] },
  { name: "AMC Management", path: "/amc", icon: Shield, keywords: ["contracts", "maintenance"] },
  { name: "Employees", path: "/employees", icon: Users, keywords: ["staff", "team", "hr"] },
  { name: "Attendance", path: "/attendance", icon: Clock, keywords: ["time", "checkin", "checkout"] },
  { name: "Leave Management", path: "/leave", icon: Calendar, keywords: ["pto", "vacation", "absence"] },
  { name: "Settings", path: "/settings", icon: Settings, keywords: ["preferences", "config", "options"] },
  { name: "Activity Logs", path: "/activity-logs", icon: Activity, keywords: ["audit", "history", "logs"] },
];

// Quick actions
const quickActions = [
  { name: "Create New Estimate", action: "create_estimate", icon: Plus, keywords: ["new quote", "add estimate"] },
  { name: "Create New Invoice", action: "create_invoice", icon: Plus, keywords: ["new bill", "add invoice"] },
  { name: "Create New Ticket", action: "create_ticket", icon: Plus, keywords: ["new complaint", "add ticket"] },
  { name: "Add New Contact", action: "create_contact", icon: Plus, keywords: ["new customer", "add client"] },
  { name: "Record Expense", action: "create_expense", icon: Plus, keywords: ["add expense", "new cost"] },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const navigate = useNavigate();

  // Listen for Cmd+K / Ctrl+K
  useEffect(() => {
    const down = (e) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("recentSearches");
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load recent searches:", e);
      }
    }
  }, []);

  const handleSelect = useCallback((item) => {
    // Add to recent searches
    const newRecent = [item, ...recentSearches.filter(r => r.path !== item.path)].slice(0, 5);
    setRecentSearches(newRecent);
    localStorage.setItem("recentSearches", JSON.stringify(newRecent));
    
    // Navigate
    setOpen(false);
    navigate(item.path);
  }, [navigate, recentSearches]);

  const handleAction = useCallback((action) => {
    setOpen(false);
    
    // Navigate to the appropriate page with action parameter
    switch (action) {
      case "create_estimate":
        navigate("/estimates?action=create");
        break;
      case "create_invoice":
        navigate("/invoices-enhanced?action=create");
        break;
      case "create_ticket":
        navigate("/tickets/new");
        break;
      case "create_contact":
        navigate("/contacts?action=create");
        break;
      case "create_expense":
        navigate("/expenses?action=create");
        break;
      default:
        break;
    }
  }, [navigate]);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search pages, actions, or type a command..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        
        {/* Recent Searches */}
        {recentSearches.length > 0 && (
          <>
            <CommandGroup heading="Recent">
              {recentSearches.map((item) => {
                const Icon = navigationItems.find(n => n.path === item.path)?.icon || FileText;
                return (
                  <CommandItem
                    key={`recent-${item.path}`}
                    value={`recent ${item.name}`}
                    onSelect={() => handleSelect(item)}
                    className="cursor-pointer"
                  >
                    <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{item.name}</span>
                  </CommandItem>
                );
              })}
            </CommandGroup>
            <CommandSeparator />
          </>
        )}
        
        {/* Quick Actions */}
        <CommandGroup heading="Quick Actions">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <CommandItem
                key={action.action}
                value={`${action.name} ${action.keywords.join(" ")}`}
                onSelect={() => handleAction(action.action)}
                className="cursor-pointer"
              >
                <Icon className="mr-2 h-4 w-4 text-green-600" />
                <span>{action.name}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>
        
        <CommandSeparator />
        
        {/* Navigation */}
        <CommandGroup heading="Pages">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <CommandItem
                key={item.path}
                value={`${item.name} ${item.keywords.join(" ")}`}
                onSelect={() => handleSelect(item)}
                className="cursor-pointer"
              >
                <Icon className="mr-2 h-4 w-4" />
                <span>{item.name}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>
      </CommandList>
      
      {/* Footer with keyboard hints */}
      <div className="flex items-center justify-between px-3 py-2 border-t text-xs text-muted-foreground bg-muted/30">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px]">↑↓</kbd>
            Navigate
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px]">↵</kbd>
            Select
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px]">esc</kbd>
            Close
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Zap className="h-3 w-3 text-bw-volt" />
          <span>Powered by Battwheels OS</span>
        </div>
      </div>
    </CommandDialog>
  );
}
