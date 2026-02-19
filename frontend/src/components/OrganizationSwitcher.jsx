import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Building2, 
  ChevronDown, 
  Check, 
  Plus, 
  Settings,
  Loader2 
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { API } from "@/App";

// Role badge colors
const roleBadgeColors = {
  owner: "bg-purple-500/20 text-purple-400",
  admin: "bg-blue-500/20 text-blue-400",
  manager: "bg-green-500/20 text-green-400",
  dispatcher: "bg-yellow-500/20 text-yellow-400",
  technician: "bg-orange-500/20 text-orange-400",
  accountant: "bg-cyan-500/20 text-cyan-400",
  viewer: "bg-gray-500/20 text-gray-400",
};

export default function OrganizationSwitcher({ compact = false }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [open, setOpen] = useState(false);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, []);

  // Fetch organizations
  const fetchOrganizations = useCallback(async () => {
    try {
      const [currentRes, listRes] = await Promise.all([
        fetch(`${API}/org`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/list`, { headers: getAuthHeaders() }),
      ]);

      if (currentRes.ok) {
        const currentData = await currentRes.json();
        setCurrentOrg(currentData);
      }

      if (listRes.ok) {
        const listData = await listRes.json();
        setOrganizations(listData.organizations || []);
      }
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  // Switch organization
  const switchOrganization = async (orgId) => {
    if (currentOrg?.organization_id === orgId) {
      setOpen(false);
      return;
    }

    setSwitching(true);
    try {
      const res = await fetch(`${API}/org/switch/${orgId}`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(`Switched to ${data.organization_name}`);
        
        // Refresh page to reload all data with new org context
        window.location.reload();
      } else {
        toast.error("Failed to switch organization");
      }
    } catch (error) {
      toast.error("Failed to switch organization");
    } finally {
      setSwitching(false);
      setOpen(false);
    }
  };

  // Get initials for avatar
  const getInitials = (name) => {
    if (!name) return "?";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  // Get current user's role in current org
  const getCurrentRole = () => {
    const org = organizations.find(o => o.organization_id === currentOrg?.organization_id);
    return org?.role || "viewer";
  };

  if (loading) {
    return (
      <Button variant="ghost" size="sm" disabled className="gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        {!compact && <span className="text-sm">Loading...</span>}
      </Button>
    );
  }

  // If only one organization, show simple display
  if (organizations.length <= 1) {
    return (
      <div className="flex items-center gap-2 px-2">
        <Avatar className="h-6 w-6">
          <AvatarImage src={currentOrg?.logo_url} />
          <AvatarFallback className="text-xs bg-primary/20">
            {getInitials(currentOrg?.name)}
          </AvatarFallback>
        </Avatar>
        {!compact && (
          <div className="flex flex-col">
            <span className="text-sm font-medium truncate max-w-[120px]">
              {currentOrg?.name}
            </span>
            <span className="text-xs text-muted-foreground capitalize">
              {getCurrentRole()}
            </span>
          </div>
        )}
      </div>
    );
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="gap-2 hover:bg-primary/10 transition-colors"
          data-testid="org-switcher-trigger"
        >
          <Avatar className="h-6 w-6">
            <AvatarImage src={currentOrg?.logo_url} />
            <AvatarFallback className="text-xs bg-primary/20">
              {getInitials(currentOrg?.name)}
            </AvatarFallback>
          </Avatar>
          {!compact && (
            <>
              <div className="flex flex-col items-start">
                <span className="text-sm font-medium truncate max-w-[120px]">
                  {currentOrg?.name}
                </span>
                <span className="text-xs text-muted-foreground capitalize">
                  {getCurrentRole()}
                </span>
              </div>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[280px]">
        <DropdownMenuLabel className="flex items-center gap-2">
          <Building2 className="h-4 w-4" />
          Switch Organization
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {/* Organization List */}
        <div className="max-h-[300px] overflow-y-auto">
          {organizations.map((org) => (
            <DropdownMenuItem
              key={org.organization_id}
              onClick={() => switchOrganization(org.organization_id)}
              disabled={switching}
              className="flex items-center gap-3 py-2 cursor-pointer"
              data-testid={`org-option-${org.organization_id}`}
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs bg-primary/20">
                  {getInitials(org.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col flex-1 min-w-0">
                <span className="text-sm font-medium truncate">{org.name}</span>
                <div className="flex items-center gap-2">
                  <Badge className={`${roleBadgeColors[org.role]} text-[10px] px-1.5 py-0`}>
                    {org.role}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground">
                    {org.slug}
                  </span>
                </div>
              </div>
              {currentOrg?.organization_id === org.organization_id && (
                <Check className="h-4 w-4 text-primary flex-shrink-0" />
              )}
            </DropdownMenuItem>
          ))}
        </div>

        <DropdownMenuSeparator />
        
        {/* Actions */}
        <DropdownMenuItem
          onClick={() => {
            setOpen(false);
            navigate("/organization-settings");
          }}
          className="gap-2"
        >
          <Settings className="h-4 w-4" />
          Organization Settings
        </DropdownMenuItem>
        
        {/* Only show create option for admins/owners */}
        {["owner", "admin"].includes(getCurrentRole()) && (
          <DropdownMenuItem
            onClick={() => {
              setOpen(false);
              toast.info("Create organization coming soon");
            }}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Create Organization
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
