import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { 
  Bell, Check, CheckCheck, FileText, AlertTriangle, 
  Package, Wrench, Clock, IndianRupee
} from "lucide-react";
import { API } from "@/App";

const notificationIcons = {
  invoice_sent: FileText,
  invoice_paid: IndianRupee,
  invoice_overdue: AlertTriangle,
  amc_expiring: Clock,
  low_stock: Package,
  ticket_update: Wrench,
};

const priorityColors = {
  low: "bg-bw-white/5 text-bw-white/35 border border-white/[0.08]",
  normal: "bg-blue-100 text-bw-blue",
  high: "bg-orange-100 text-bw-orange",
  urgent: "bg-bw-red/10 text-bw-red border border-bw-red/25",
};

export default function NotificationBell({ user }) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const role = user?.role || "";
      const userId = user?.user_id || "";
      
      const res = await fetch(
        `${API}/notifications?role=${role}&user_id=${userId}&per_page=20`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchNotifications();
    // Poll for new notifications every 60 seconds
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/notifications/${notificationId}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchNotifications();
    } catch (error) {
      console.error("Failed to mark as read:", error);
    }
  };

  const markAllRead = async () => {
    try {
      const token = localStorage.getItem("token");
      const role = user?.role || "";
      const userId = user?.user_id || "";
      
      await fetch(`${API}/notifications/mark-all-read?role=${role}&user_id=${userId}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchNotifications();
    } catch (error) {
      console.error("Failed to mark all as read:", error);
    }
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative"
          data-testid="notification-bell"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-bw-red/[0.08]0 text-white text-xs flex items-center justify-center font-medium">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-0" align="end">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={markAllRead}
              className="text-xs text-bw-white/[0.45] hover:text-bw-white"
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          )}
        </div>
        
        <ScrollArea className="h-96">
          {loading ? (
            <div className="p-8 text-center text-bw-white/[0.45]">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center text-bw-white/[0.45]">
              <Bell className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>No notifications</p>
            </div>
          ) : (
            <div className="divide-y">
              {notifications.map((notif) => {
                const Icon = notificationIcons[notif.notification_type] || Bell;
                return (
                  <div
                    key={notif.notification_id}
                    className={`p-4 hover:bg-bw-panel cursor-pointer transition-colors ${
                      !notif.is_read ? "bg-blue-50/50" : ""
                    }`}
                    onClick={() => !notif.is_read && markAsRead(notif.notification_id)}
                  >
                    <div className="flex gap-3">
                      <div className={`p-2 rounded-full ${priorityColors[notif.priority] || priorityColors.normal}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className={`text-sm ${!notif.is_read ? "font-semibold" : "font-medium"}`}>
                            {notif.title}
                          </p>
                          {!notif.is_read && (
                            <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0 mt-1.5" />
                          )}
                        </div>
                        <p className="text-sm text-bw-white/35 line-clamp-2 mt-0.5">
                          {notif.message}
                        </p>
                        <p className="text-xs text-bw-white/[0.45] mt-1">
                          {formatTime(notif.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
        
        {notifications.length > 0 && (
          <div className="p-3 border-t text-center">
            <Button variant="ghost" size="sm" className="text-xs text-bw-white/[0.45]">
              View all notifications
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
