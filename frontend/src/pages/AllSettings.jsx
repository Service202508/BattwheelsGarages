import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { 
  Search, Building2, Users, Receipt, Palette, Zap, Settings2, 
  Plug, Code, ChevronRight, Save, RefreshCw, FileText, Bell,
  Car, Ticket, Wrench, Package, UserCircle, CreditCard, Brain,
  Globe, Key, Webhook, ShieldCheck, MapPin, Percent, IndianRupee,
  Plus, Pencil, Trash2, Mail, UserPlus, Shield, Check, X,
  AlertCircle, Clock, Play, Pause, Copy, Eye, EyeOff, MoreHorizontal
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// Icon mapping
const iconMap = {
  Building2, Users, Receipt, Palette, Zap, Settings2, Plug, Code,
  Car, Ticket, Wrench, Package, UserCircle, CreditCard, Brain,
  Globe, Key, Webhook, ShieldCheck, MapPin, Percent, IndianRupee
};

// Color classes for categories
const colorClasses = {
  "#10B981": "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border-[rgba(200,255,0,0.20)]",
  "#3B82F6": "bg-blue-500/10 text-blue-500 border-blue-500/20",
  "#F59E0B": "bg-amber-500/10 text-amber-500 border-amber-500/20",
  "#8B5CF6": "bg-violet-500/10 text-violet-500 border-violet-500/20",
  "#EF4444": "bg-[rgba(255,59,47,0.10)] text-red-500 border-red-500/20",
  "#06B6D4": "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
  "#EC4899": "bg-pink-500/10 text-pink-500 border-pink-500/20",
  "#6366F1": "bg-indigo-500/10 text-indigo-500 border-indigo-500/20"
};

// Role permissions map
const ROLE_PERMISSIONS = {
  owner: ["All permissions - Full control over organization"],
  admin: ["Manage users", "Update settings", "View reports", "Manage billing"],
  manager: ["View users", "Update settings", "View reports"],
  dispatcher: ["Manage tickets", "Assign work orders", "View vehicles"],
  technician: ["View tickets", "Update work orders", "View inventory"],
  accountant: ["View billing", "Manage invoices", "View reports"],
  viewer: ["View-only access to all modules"]
};

export default function AllSettings({ user }) {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchCategories();
    fetchAllSettings();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API}/settings/categories`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
        if (data.categories?.length > 0) {
          setSelectedCategory(data.categories[0]);
          if (data.categories[0].items?.length > 0) {
            setSelectedItem(data.categories[0].items[0]);
          }
        }
      }
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  };

  const fetchAllSettings = async () => {
    try {
      const res = await fetch(`${API}/settings`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (error) {
      console.error("Failed to fetch settings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (section, data) => {
    setSaving(true);
    try {
      const endpoint = getEndpointForSection(section);
      const res = await fetch(`${API}/settings/${endpoint}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      if (res.ok) {
        toast.success("Settings saved successfully");
        await fetchAllSettings();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to save settings");
      }
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const getEndpointForSection = (section) => {
    const map = {
      "profile": "organization/profile",
      "branding": "organization/branding",
      "gst": "taxes/gst",
      "tds": "taxes/tds",
      "msme": "taxes/msme",
      "vehicles": "modules/vehicles",
      "tickets": "modules/tickets",
      "work-orders": "modules/work-orders",
      "inventory": "modules/inventory",
      "customers": "modules/customers",
      "billing": "modules/billing",
      "efi": "modules/efi",
      "portal": "modules/portal"
    };
    return map[section] || section;
  };

  // Filter categories and items by search
  const filteredCategories = categories.map(cat => ({
    ...cat,
    items: cat.items.filter(item => 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cat.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })).filter(cat => cat.items.length > 0 || cat.name.toLowerCase().includes(searchTerm.toLowerCase()));

  const IconComponent = ({ name, className }) => {
    const Icon = iconMap[name] || Settings2;
    return <Icon className={className} />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="all-settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">All Settings</h1>
          <p className="text-muted-foreground">
            Configure your organization, modules, and integrations
          </p>
        </div>
        <Button variant="outline" onClick={fetchAllSettings}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search settings..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
          data-testid="settings-search"
        />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left sidebar - Categories */}
        <div className="col-span-12 lg:col-span-4 xl:col-span-3">
          <Card className="sticky top-6">
            <ScrollArea className="h-[calc(100vh-220px)]">
              <div className="p-4 space-y-4">
                {filteredCategories.map((category) => (
                  <div key={category.id}>
                    <button
                      onClick={() => {
                        setSelectedCategory(category);
                        if (category.items?.length > 0) {
                          setSelectedItem(category.items[0]);
                        }
                      }}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                        selectedCategory?.id === category.id
                          ? "bg-primary/10 text-primary"
                          : "hover:bg-muted"
                      }`}
                      data-testid={`category-${category.id}`}
                    >
                      <div className={`p-2 rounded-lg border ${colorClasses[category.color] || "bg-muted"}`}>
                        <IconComponent name={category.icon} className="h-5 w-5" />
                      </div>
                      <div className="text-left flex-1">
                        <div className="font-medium">{category.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {category.items?.length || 0} settings
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </button>

                    {/* Sub-items when category is selected */}
                    {selectedCategory?.id === category.id && (
                      <div className="ml-6 mt-2 space-y-1">
                        {category.items?.map((item) => (
                          <button
                            key={item.id}
                            onClick={() => setSelectedItem(item)}
                            className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                              selectedItem?.id === item.id
                                ? "bg-primary/10 text-primary font-medium"
                                : "hover:bg-muted text-muted-foreground"
                            }`}
                            data-testid={`setting-${item.id}`}
                          >
                            {item.name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>
        </div>

        {/* Right content - Settings panel */}
        <div className="col-span-12 lg:col-span-8 xl:col-span-9">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{selectedItem?.name || "Select a setting"}</CardTitle>
                  <CardDescription>
                    {selectedCategory?.name} / {selectedItem?.name}
                  </CardDescription>
                </div>
                {selectedItem && !["users", "roles", "teams", "custom-fields", "workflows"].includes(selectedItem.id) && (
                  <Button onClick={() => handleSave(selectedItem.id, settings[selectedItem.id])} disabled={saving}>
                    {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                    Save Changes
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {selectedItem ? (
                <SettingsPanel 
                  item={selectedItem}
                  settings={settings}
                  onUpdate={(section, data) => setSettings(prev => ({...prev, [section]: data}))}
                  onSave={handleSave}
                  onRefresh={fetchAllSettings}
                />
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  Select a setting from the sidebar to configure
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Settings Panel Component - renders appropriate form based on selected item
function SettingsPanel({ item, settings, onUpdate, onSave, onRefresh }) {
  switch (item.id) {
    case "profile":
      return <OrganizationProfilePanel settings={settings.organization || {}} onUpdate={(data) => onUpdate("organization", data)} />;
    case "branding":
      return <BrandingPanel settings={settings.branding || {}} onUpdate={(data) => onUpdate("branding", data)} />;
    case "locations":
      return <LocationsPanel settings={settings.locations || []} onUpdate={(data) => onUpdate("locations", data)} />;
    case "users":
      return <UsersPanel onRefresh={onRefresh} />;
    case "roles":
      return <RolesPanel />;
    case "gst":
      return <GSTSettingsPanel settings={settings.gst || {}} onUpdate={(data) => onUpdate("gst", data)} />;
    case "tds":
      return <TDSSettingsPanel settings={settings.tds || {}} onUpdate={(data) => onUpdate("tds", data)} />;
    case "msme":
      return <MSMESettingsPanel settings={settings.msme || {}} onUpdate={(data) => onUpdate("msme", data)} />;
    case "custom-fields":
      return <CustomFieldsBuilderPanel settings={settings.custom_fields || []} onRefresh={onRefresh} />;
    case "workflows":
      return <WorkflowRulesBuilderPanel settings={settings.workflow_rules || []} onRefresh={onRefresh} />;
    case "vehicles":
      return <VehicleSettingsPanel settings={settings.vehicles || {}} onUpdate={(data) => onUpdate("vehicles", data)} />;
    case "tickets":
      return <TicketSettingsPanel settings={settings.tickets || {}} onUpdate={(data) => onUpdate("tickets", data)} />;
    case "work-orders":
      return <WorkOrderSettingsPanel settings={settings.work_orders || {}} onUpdate={(data) => onUpdate("work_orders", data)} />;
    case "inventory":
      return <InventorySettingsPanel settings={settings.inventory || {}} onUpdate={(data) => onUpdate("inventory", data)} />;
    case "customers":
      return <CustomerSettingsPanel settings={settings.customers || {}} onUpdate={(data) => onUpdate("customers", data)} />;
    case "billing":
      return <BillingSettingsPanel settings={settings.billing || {}} onUpdate={(data) => onUpdate("billing", data)} />;
    case "efi":
      return <EFISettingsPanel settings={settings.efi || {}} onUpdate={(data) => onUpdate("efi", data)} />;
    case "portal":
      return <PortalSettingsPanel settings={settings.portal || {}} onUpdate={(data) => onUpdate("portal", data)} />;
    default:
      return <ComingSoonPanel item={item} />;
  }
}

// ==================== USERS & ROLES PANELS ====================

function UsersPanel({ onRefresh }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [inviteForm, setInviteForm] = useState({ email: "", role: "viewer" });
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await fetch(`${API}/org/users`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error("Failed to fetch users:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleInviteUser = async () => {
    try {
      const res = await fetch(`${API}/org/users`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ email: inviteForm.email, role: inviteForm.role })
      });
      if (res.ok) {
        toast.success("User invited successfully");
        setShowInviteDialog(false);
        setInviteForm({ email: "", role: "viewer" });
        fetchUsers();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to invite user");
      }
    } catch (error) {
      toast.error("Failed to invite user");
    }
  };

  const handleUpdateRole = async () => {
    if (!selectedUser) return;
    try {
      const res = await fetch(`${API}/org/users/${selectedUser.membership.user_id}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ role: selectedUser.membership.role })
      });
      if (res.ok) {
        toast.success("User role updated");
        setShowEditDialog(false);
        setSelectedUser(null);
        fetchUsers();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to update role");
      }
    } catch (error) {
      toast.error("Failed to update user");
    }
  };

  const handleRemoveUser = async (userId) => {
    try {
      const res = await fetch(`${API}/org/users/${userId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        toast.success("User removed from organization");
        setDeleteConfirm(null);
        fetchUsers();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to remove user");
      }
    } catch (error) {
      toast.error("Failed to remove user");
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      owner: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
      admin: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
      manager: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
      dispatcher: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
      technician: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
      accountant: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400",
      viewer: "bg-[rgba(255,255,255,0.05)] text-[#F4F6F0] dark:bg-[#080C0F]/30 dark:text-[rgba(244,246,240,0.45)]"
    };
    return colors[role] || colors.viewer;
  };

  if (loading) {
    return <div className="flex items-center justify-center py-8"><RefreshCw className="h-6 w-6 animate-spin" /></div>;
  }

  return (
    <div className="space-y-6" data-testid="users-panel">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            Manage team members and their access to this organization
          </p>
        </div>
        <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
          <DialogTrigger asChild>
            <Button data-testid="invite-user-btn">
              <UserPlus className="h-4 w-4 mr-2" />
              Invite User
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite Team Member</DialogTitle>
              <DialogDescription>
                Send an invitation to add a new member to your organization
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Email Address</Label>
                <Input
                  type="email"
                  placeholder="colleague@company.com"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                  data-testid="invite-email-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={inviteForm.role} onValueChange={(val) => setInviteForm(prev => ({ ...prev, role: val }))}>
                  <SelectTrigger data-testid="invite-role-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                    <SelectItem value="dispatcher">Dispatcher</SelectItem>
                    <SelectItem value="technician">Technician</SelectItem>
                    <SelectItem value="accountant">Accountant</SelectItem>
                    <SelectItem value="viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {ROLE_PERMISSIONS[inviteForm.role]?.[0]}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowInviteDialog(false)}>Cancel</Button>
              <Button onClick={handleInviteUser} data-testid="send-invite-btn">
                <Mail className="h-4 w-4 mr-2" />
                Send Invitation
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Users Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                  No team members yet. Invite your first team member.
                </TableCell>
              </TableRow>
            ) : (
              users.map((item) => (
                <TableRow key={item.membership.user_id} data-testid={`user-row-${item.membership.user_id}`}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        {item.user?.picture ? (
                          <img src={item.user.picture} alt="" className="h-10 w-10 rounded-full" />
                        ) : (
                          <span className="text-primary font-medium">
                            {item.user?.name?.charAt(0) || item.user?.email?.charAt(0) || "?"}
                          </span>
                        )}
                      </div>
                      <div>
                        <div className="font-medium">{item.user?.name || "Unknown"}</div>
                        <div className="text-sm text-muted-foreground">{item.user?.email}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getRoleBadgeColor(item.membership.role)}>
                      {item.membership.role?.charAt(0).toUpperCase() + item.membership.role?.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={item.membership.status === "active" ? "default" : "secondary"}>
                      {item.membership.status || "Active"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {item.membership.joined_at ? new Date(item.membership.joined_at).toLocaleDateString() : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedUser(item);
                          setShowEditDialog(true);
                        }}
                        disabled={item.membership.role === "owner"}
                        data-testid={`edit-user-${item.membership.user_id}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteConfirm(item.membership.user_id)}
                        disabled={item.membership.role === "owner"}
                        className="text-destructive hover:text-destructive"
                        data-testid={`remove-user-${item.membership.user_id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Edit Role Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User Role</DialogTitle>
            <DialogDescription>
              Change the role for {selectedUser?.user?.name || selectedUser?.user?.email}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Role</Label>
              <Select 
                value={selectedUser?.membership?.role || "viewer"} 
                onValueChange={(val) => setSelectedUser(prev => ({ 
                  ...prev, 
                  membership: { ...prev.membership, role: val } 
                }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="dispatcher">Dispatcher</SelectItem>
                  <SelectItem value="technician">Technician</SelectItem>
                  <SelectItem value="accountant">Accountant</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button onClick={handleUpdateRole}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove this user from the organization? They will lose access to all resources.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => handleRemoveUser(deleteConfirm)} className="bg-destructive text-destructive-foreground">
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function RolesPanel() {
  const roles = [
    { id: "owner", name: "Owner", description: "Full control over the organization", permissions: 21, color: "purple" },
    { id: "admin", name: "Admin", description: "Manage users, settings, and billing", permissions: 16, color: "red" },
    { id: "manager", name: "Manager", description: "Manage operations and view reports", permissions: 15, color: "blue" },
    { id: "dispatcher", name: "Dispatcher", description: "Assign tickets and manage work orders", permissions: 9, color: "amber" },
    { id: "technician", name: "Technician", description: "Execute work orders and update status", permissions: 8, color: "green" },
    { id: "accountant", name: "Accountant", description: "Manage billing and financial reports", permissions: 7, color: "cyan" },
    { id: "viewer", name: "Viewer", description: "View-only access to resources", permissions: 6, color: "gray" }
  ];

  const permissionGroups = {
    "Organization": ["org:read", "org:update", "org:settings:read", "org:settings:update"],
    "Users": ["org:users:read", "org:users:create", "org:users:update", "org:users:delete"],
    "Vehicles": ["vehicles:read", "vehicles:create", "vehicles:update", "vehicles:delete"],
    "Tickets": ["tickets:read", "tickets:create", "tickets:update", "tickets:delete", "tickets:assign"],
    "Work Orders": ["work-orders:read", "work-orders:create", "work-orders:update", "work-orders:delete"],
    "Inventory": ["inventory:read", "inventory:create", "inventory:update", "inventory:delete"],
    "Billing": ["billing:read", "billing:create", "billing:update", "billing:delete"],
    "Reports": ["reports:read", "reports:export"]
  };

  const rolePermissions = {
    owner: Object.values(permissionGroups).flat(),
    admin: ["org:read", "org:update", "org:settings:read", "org:settings:update", "org:users:read", "org:users:create", "org:users:update", "org:users:delete", "billing:read", "billing:create", "reports:read", "reports:export"],
    manager: ["org:read", "org:settings:read", "org:users:read", "vehicles:read", "tickets:read", "tickets:update", "tickets:assign", "work-orders:read", "work-orders:update", "inventory:read", "reports:read"],
    dispatcher: ["vehicles:read", "tickets:read", "tickets:create", "tickets:update", "tickets:assign", "work-orders:read", "work-orders:create", "work-orders:update"],
    technician: ["vehicles:read", "tickets:read", "tickets:update", "work-orders:read", "work-orders:update", "inventory:read"],
    accountant: ["billing:read", "billing:create", "billing:update", "reports:read", "reports:export"],
    viewer: ["org:read", "vehicles:read", "tickets:read", "work-orders:read", "inventory:read", "billing:read"]
  };

  const [selectedRole, setSelectedRole] = useState("owner");

  return (
    <div className="space-y-6" data-testid="roles-panel">
      <p className="text-sm text-muted-foreground">
        View predefined roles and their permissions. Custom roles coming soon.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {roles.map((role) => (
          <button
            key={role.id}
            onClick={() => setSelectedRole(role.id)}
            className={`p-4 rounded-lg border text-left transition-all ${
              selectedRole === role.id 
                ? "border-primary bg-primary/5 ring-2 ring-primary/20" 
                : "hover:border-primary/50"
            }`}
            data-testid={`role-${role.id}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <Shield className={`h-5 w-5 text-${role.color}-500`} />
              <span className="font-medium">{role.name}</span>
            </div>
            <p className="text-sm text-muted-foreground mb-2">{role.description}</p>
            <Badge variant="secondary">{role.permissions} permissions</Badge>
          </button>
        ))}
      </div>

      <Separator />

      <div>
        <h3 className="font-medium mb-4">Permissions for {roles.find(r => r.id === selectedRole)?.name}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(permissionGroups).map(([group, perms]) => (
            <div key={group} className="border rounded-lg p-4">
              <h4 className="font-medium mb-3">{group}</h4>
              <div className="space-y-2">
                {perms.map((perm) => {
                  const hasPermission = rolePermissions[selectedRole]?.includes(perm);
                  return (
                    <div key={perm} className="flex items-center gap-2 text-sm">
                      {hasPermission ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <X className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className={hasPermission ? "" : "text-muted-foreground"}>
                        {perm.split(":").pop()}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ==================== CUSTOM FIELDS BUILDER ====================

function CustomFieldsBuilderPanel({ settings, onRefresh }) {
  const [fields, setFields] = useState(settings || []);
  const [showFieldDialog, setShowFieldDialog] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [loading, setLoading] = useState(false);

  const emptyField = {
    module: "vehicles",
    field_name: "",
    label: "",
    data_type: "text",
    description: "",
    placeholder: "",
    is_required: false,
    is_searchable: true,
    is_visible_in_list: true,
    options: []
  };

  const [fieldForm, setFieldForm] = useState(emptyField);

  useEffect(() => {
    setFields(settings || []);
  }, [settings]);

  const handleSaveField = async () => {
    setLoading(true);
    try {
      const url = editingField 
        ? `${API}/settings/custom-fields/${editingField.field_id}`
        : `${API}/settings/custom-fields`;
      
      const method = editingField ? "PATCH" : "POST";
      
      const res = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(fieldForm)
      });

      if (res.ok) {
        toast.success(editingField ? "Field updated" : "Field created");
        setShowFieldDialog(false);
        setFieldForm(emptyField);
        setEditingField(null);
        onRefresh();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to save field");
      }
    } catch (error) {
      toast.error("Failed to save field");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteField = async (fieldId) => {
    try {
      const res = await fetch(`${API}/settings/custom-fields/${fieldId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (res.ok) {
        toast.success("Field deleted");
        setDeleteConfirm(null);
        onRefresh();
      } else {
        toast.error("Failed to delete field");
      }
    } catch (error) {
      toast.error("Failed to delete field");
    }
  };

  const openEditDialog = (field) => {
    setEditingField(field);
    setFieldForm({
      module: field.module,
      field_name: field.field_name,
      label: field.label,
      data_type: field.data_type,
      description: field.description || "",
      placeholder: field.placeholder || "",
      is_required: field.is_required || false,
      is_searchable: field.is_searchable !== false,
      is_visible_in_list: field.is_visible_in_list !== false,
      options: field.options || []
    });
    setShowFieldDialog(true);
  };

  const modules = [
    { value: "vehicles", label: "Vehicles" },
    { value: "tickets", label: "Tickets" },
    { value: "work_orders", label: "Work Orders" },
    { value: "parts_inventory", label: "Parts & Inventory" },
    { value: "customers", label: "Customers" },
    { value: "invoices", label: "Invoices" },
    { value: "quotes", label: "Quotes" }
  ];

  const dataTypes = [
    { value: "text", label: "Text", icon: "Aa" },
    { value: "number", label: "Number", icon: "#" },
    { value: "decimal", label: "Decimal", icon: ".00" },
    { value: "date", label: "Date", icon: "Cal" },
    { value: "datetime", label: "Date & Time", icon: "Time" },
    { value: "boolean", label: "Checkbox", icon: "Check" },
    { value: "dropdown", label: "Dropdown", icon: "List" },
    { value: "multi_select", label: "Multi-Select", icon: "Tags" },
    { value: "email", label: "Email", icon: "@" },
    { value: "phone", label: "Phone", icon: "Tel" },
    { value: "url", label: "URL", icon: "Link" },
    { value: "currency", label: "Currency", icon: "INR" },
    { value: "percent", label: "Percentage", icon: "%" },
    { value: "textarea", label: "Long Text", icon: "Para" }
  ];

  return (
    <div className="space-y-6" data-testid="custom-fields-panel">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Create custom fields for any module. Fields support various data types including dropdowns and formulas.
        </p>
        <Button onClick={() => { setEditingField(null); setFieldForm(emptyField); setShowFieldDialog(true); }} data-testid="add-field-btn">
          <Plus className="h-4 w-4 mr-2" />
          Add Custom Field
        </Button>
      </div>

      {/* Fields grouped by module */}
      {modules.map(mod => {
        const moduleFields = fields.filter(f => f.module === mod.value);
        if (moduleFields.length === 0) return null;

        return (
          <div key={mod.value} className="border rounded-lg">
            <div className="px-4 py-3 bg-muted/50 border-b">
              <h4 className="font-medium">{mod.label}</h4>
            </div>
            <div className="divide-y">
              {moduleFields.map((field) => (
                <div key={field.field_id} className="flex items-center justify-between p-4 hover:bg-muted/30" data-testid={`field-${field.field_id}`}>
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-sm font-mono">
                      {dataTypes.find(d => d.value === field.data_type)?.icon || "?"}
                    </div>
                    <div>
                      <div className="font-medium">{field.label}</div>
                      <div className="text-sm text-muted-foreground">
                        {field.field_name} &bull; {dataTypes.find(d => d.value === field.data_type)?.label || field.data_type}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {field.is_required && <Badge variant="outline">Required</Badge>}
                    <Button variant="ghost" size="sm" onClick={() => openEditDialog(field)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setDeleteConfirm(field.field_id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {fields.length === 0 && (
        <div className="text-center py-12 border-2 border-dashed rounded-lg text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No custom fields defined yet.</p>
          <p className="text-sm">Click "Add Custom Field" to create your first field.</p>
        </div>
      )}

      {/* Add/Edit Field Dialog */}
      <Dialog open={showFieldDialog} onOpenChange={setShowFieldDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingField ? "Edit Custom Field" : "Add Custom Field"}</DialogTitle>
            <DialogDescription>
              Define a custom field to capture additional data in your modules.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Module *</Label>
                <Select value={fieldForm.module} onValueChange={(val) => setFieldForm(prev => ({ ...prev, module: val }))}>
                  <SelectTrigger data-testid="field-module-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {modules.map(m => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Data Type *</Label>
                <Select value={fieldForm.data_type} onValueChange={(val) => setFieldForm(prev => ({ ...prev, data_type: val }))}>
                  <SelectTrigger data-testid="field-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {dataTypes.map(d => (
                      <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Label *</Label>
                <Input
                  placeholder="e.g., Battery Capacity"
                  value={fieldForm.label}
                  onChange={(e) => setFieldForm(prev => ({ 
                    ...prev, 
                    label: e.target.value,
                    field_name: e.target.value.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "")
                  }))}
                  data-testid="field-label-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Field Name (API)</Label>
                <Input
                  value={fieldForm.field_name}
                  onChange={(e) => setFieldForm(prev => ({ ...prev, field_name: e.target.value }))}
                  placeholder="auto_generated_from_label"
                  className="font-mono text-sm"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Input
                placeholder="Help text for this field"
                value={fieldForm.description}
                onChange={(e) => setFieldForm(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label>Placeholder</Label>
              <Input
                placeholder="Placeholder text shown in the input"
                value={fieldForm.placeholder}
                onChange={(e) => setFieldForm(prev => ({ ...prev, placeholder: e.target.value }))}
              />
            </div>

            {/* Dropdown Options */}
            {(fieldForm.data_type === "dropdown" || fieldForm.data_type === "multi_select") && (
              <div className="space-y-2">
                <Label>Options (one per line)</Label>
                <Textarea
                  placeholder="Option 1&#10;Option 2&#10;Option 3"
                  value={fieldForm.options.map(o => o.label || o.value || o).join("\n")}
                  onChange={(e) => {
                    const options = e.target.value.split("\n").filter(Boolean).map((label, i) => ({
                      value: label.toLowerCase().replace(/\s+/g, "_"),
                      label,
                      sort_order: i
                    }));
                    setFieldForm(prev => ({ ...prev, options }));
                  }}
                  rows={4}
                />
              </div>
            )}

            <Separator />

            <div className="space-y-4">
              <h4 className="font-medium">Field Options</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    id="is_required"
                    checked={fieldForm.is_required}
                    onCheckedChange={(checked) => setFieldForm(prev => ({ ...prev, is_required: checked }))}
                  />
                  <Label htmlFor="is_required">Required</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="is_searchable"
                    checked={fieldForm.is_searchable}
                    onCheckedChange={(checked) => setFieldForm(prev => ({ ...prev, is_searchable: checked }))}
                  />
                  <Label htmlFor="is_searchable">Searchable</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="is_visible_in_list"
                    checked={fieldForm.is_visible_in_list}
                    onCheckedChange={(checked) => setFieldForm(prev => ({ ...prev, is_visible_in_list: checked }))}
                  />
                  <Label htmlFor="is_visible_in_list">Show in List</Label>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowFieldDialog(false); setEditingField(null); }}>
              Cancel
            </Button>
            <Button onClick={handleSaveField} disabled={loading || !fieldForm.label}>
              {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
              {editingField ? "Update Field" : "Create Field"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Custom Field</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this field? This action cannot be undone and existing data for this field will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => handleDeleteField(deleteConfirm)} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ==================== WORKFLOW RULES BUILDER ====================

function WorkflowRulesBuilderPanel({ settings, onRefresh }) {
  const [rules, setRules] = useState(settings || []);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [loading, setLoading] = useState(false);

  const emptyRule = {
    module: "tickets",
    name: "",
    description: "",
    trigger_type: "on_create",
    conditions: [],
    actions: [],
    is_active: true
  };

  const [ruleForm, setRuleForm] = useState(emptyRule);

  useEffect(() => {
    setRules(settings || []);
  }, [settings]);

  const modules = [
    { value: "tickets", label: "Tickets" },
    { value: "vehicles", label: "Vehicles" },
    { value: "work_orders", label: "Work Orders" },
    { value: "invoices", label: "Invoices" },
    { value: "quotes", label: "Quotes" },
    { value: "customers", label: "Customers" }
  ];

  const triggerTypes = [
    { value: "on_create", label: "When a record is created" },
    { value: "on_update", label: "When a record is updated" },
    { value: "on_create_or_update", label: "When created or updated" },
    { value: "field_update", label: "When a field changes" },
    { value: "date_based", label: "Based on a date field" }
  ];

  const actionTypes = [
    { value: "email_alert", label: "Send Email", icon: Mail },
    { value: "field_update", label: "Update Field", icon: Pencil },
    { value: "webhook", label: "Call Webhook", icon: Webhook },
    { value: "create_task", label: "Create Task", icon: FileText },
    { value: "assign_user", label: "Assign User", icon: UserPlus }
  ];

  const operators = [
    { value: "equals", label: "equals" },
    { value: "not_equals", label: "does not equal" },
    { value: "contains", label: "contains" },
    { value: "greater_than", label: "is greater than" },
    { value: "less_than", label: "is less than" },
    { value: "is_empty", label: "is empty" },
    { value: "is_not_empty", label: "is not empty" }
  ];

  const handleSaveRule = async () => {
    setLoading(true);
    try {
      const url = editingRule 
        ? `${API}/settings/workflows/${editingRule.rule_id}`
        : `${API}/settings/workflows`;
      
      const method = editingRule ? "PATCH" : "POST";
      
      const res = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(ruleForm)
      });

      if (res.ok) {
        toast.success(editingRule ? "Workflow updated" : "Workflow created");
        setShowRuleDialog(false);
        setRuleForm(emptyRule);
        setEditingRule(null);
        onRefresh();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to save workflow");
      }
    } catch (error) {
      toast.error("Failed to save workflow");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      const res = await fetch(`${API}/settings/workflows/${ruleId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });

      if (res.ok) {
        toast.success("Workflow deleted");
        setDeleteConfirm(null);
        onRefresh();
      } else {
        toast.error("Failed to delete workflow");
      }
    } catch (error) {
      toast.error("Failed to delete workflow");
    }
  };

  const handleToggleRule = async (rule) => {
    try {
      const res = await fetch(`${API}/settings/workflows/${rule.rule_id}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ is_active: !rule.is_active })
      });

      if (res.ok) {
        toast.success(rule.is_active ? "Workflow paused" : "Workflow activated");
        onRefresh();
      }
    } catch (error) {
      toast.error("Failed to update workflow");
    }
  };

  const openEditDialog = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      module: rule.module,
      name: rule.name,
      description: rule.description || "",
      trigger_type: rule.trigger_type,
      conditions: rule.conditions || [],
      actions: rule.actions || [],
      is_active: rule.is_active
    });
    setShowRuleDialog(true);
  };

  const addCondition = () => {
    setRuleForm(prev => ({
      ...prev,
      conditions: [...prev.conditions, { field: "", operator: "equals", value: "", logic: "and" }]
    }));
  };

  const updateCondition = (index, updates) => {
    setRuleForm(prev => ({
      ...prev,
      conditions: prev.conditions.map((c, i) => i === index ? { ...c, ...updates } : c)
    }));
  };

  const removeCondition = (index) => {
    setRuleForm(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }));
  };

  const addAction = () => {
    setRuleForm(prev => ({
      ...prev,
      actions: [...prev.actions, { action_type: "email_alert", name: "", email_alert: { subject: "", body: "", to_emails: [] } }]
    }));
  };

  const updateAction = (index, updates) => {
    setRuleForm(prev => ({
      ...prev,
      actions: prev.actions.map((a, i) => i === index ? { ...a, ...updates } : a)
    }));
  };

  const removeAction = (index) => {
    setRuleForm(prev => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="space-y-6" data-testid="workflows-panel">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Automate actions based on triggers. Send emails, update fields, call webhooks, or assign tasks.
        </p>
        <Button onClick={() => { setEditingRule(null); setRuleForm(emptyRule); setShowRuleDialog(true); }} data-testid="add-workflow-btn">
          <Plus className="h-4 w-4 mr-2" />
          Add Workflow Rule
        </Button>
      </div>

      {/* Rules List */}
      <div className="space-y-4">
        {rules.map((rule) => (
          <div 
            key={rule.rule_id} 
            className={`border rounded-lg p-4 transition-opacity ${rule.is_active ? "" : "opacity-60"}`}
            data-testid={`workflow-${rule.rule_id}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${rule.is_active ? "bg-green-100 text-green-600" : "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.45)]"}`}>
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-medium">{rule.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {modules.find(m => m.value === rule.module)?.label || rule.module} &bull; 
                    {" "}{triggerTypes.find(t => t.value === rule.trigger_type)?.label || rule.trigger_type}
                  </div>
                  {rule.description && (
                    <p className="text-sm text-muted-foreground mt-1">{rule.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span>{rule.conditions?.length || 0} conditions</span>
                    <span>{rule.actions?.length || 0} actions</span>
                    {rule.trigger_count > 0 && (
                      <span>Triggered {rule.trigger_count} times</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={rule.is_active ? "default" : "secondary"}>
                  {rule.is_active ? "Active" : "Paused"}
                </Badge>
                <Button variant="ghost" size="sm" onClick={() => handleToggleRule(rule)}>
                  {rule.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => openEditDialog(rule)}>
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setDeleteConfirm(rule.rule_id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}

        {rules.length === 0 && (
          <div className="text-center py-12 border-2 border-dashed rounded-lg text-muted-foreground">
            <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No workflow rules defined yet.</p>
            <p className="text-sm">Click "Add Workflow Rule" to automate your operations.</p>
          </div>
        )}
      </div>

      {/* Add/Edit Workflow Dialog */}
      <Dialog open={showRuleDialog} onOpenChange={setShowRuleDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? "Edit Workflow Rule" : "Add Workflow Rule"}</DialogTitle>
            <DialogDescription>
              Define triggers, conditions, and actions for automated workflows.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Rule Name *</Label>
                <Input
                  placeholder="e.g., Send welcome email"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm(prev => ({ ...prev, name: e.target.value }))}
                  data-testid="workflow-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Module *</Label>
                <Select value={ruleForm.module} onValueChange={(val) => setRuleForm(prev => ({ ...prev, module: val }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {modules.map(m => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Input
                placeholder="What does this workflow do?"
                value={ruleForm.description}
                onChange={(e) => setRuleForm(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label>Trigger *</Label>
              <Select value={ruleForm.trigger_type} onValueChange={(val) => setRuleForm(prev => ({ ...prev, trigger_type: val }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {triggerTypes.map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator />

            {/* Conditions */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base">Conditions</Label>
                  <p className="text-sm text-muted-foreground">Workflow runs only when conditions are met</p>
                </div>
                <Button variant="outline" size="sm" onClick={addCondition}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Condition
                </Button>
              </div>

              {ruleForm.conditions.length === 0 ? (
                <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg text-center">
                  No conditions. This workflow will run for all records.
                </div>
              ) : (
                <div className="space-y-2">
                  {ruleForm.conditions.map((condition, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-3 border rounded-lg bg-muted/30">
                      {idx > 0 && (
                        <Select value={condition.logic} onValueChange={(val) => updateCondition(idx, { logic: val })}>
                          <SelectTrigger className="w-20">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="and">AND</SelectItem>
                            <SelectItem value="or">OR</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                      <Input
                        placeholder="Field name"
                        value={condition.field}
                        onChange={(e) => updateCondition(idx, { field: e.target.value })}
                        className="flex-1"
                      />
                      <Select value={condition.operator} onValueChange={(val) => updateCondition(idx, { operator: val })}>
                        <SelectTrigger className="w-40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {operators.map(o => (
                            <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {!["is_empty", "is_not_empty"].includes(condition.operator) && (
                        <Input
                          placeholder="Value"
                          value={condition.value}
                          onChange={(e) => updateCondition(idx, { value: e.target.value })}
                          className="flex-1"
                        />
                      )}
                      <Button variant="ghost" size="sm" onClick={() => removeCondition(idx)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Actions */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base">Actions *</Label>
                  <p className="text-sm text-muted-foreground">What happens when the workflow runs</p>
                </div>
                <Button variant="outline" size="sm" onClick={addAction}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Action
                </Button>
              </div>

              {ruleForm.actions.length === 0 ? (
                <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg text-center">
                  Add at least one action for this workflow.
                </div>
              ) : (
                <div className="space-y-4">
                  {ruleForm.actions.map((action, idx) => (
                    <div key={idx} className="p-4 border rounded-lg space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{idx + 1}</Badge>
                          <Select value={action.action_type} onValueChange={(val) => updateAction(idx, { action_type: val })}>
                            <SelectTrigger className="w-48">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {actionTypes.map(a => (
                                <SelectItem key={a.value} value={a.value}>
                                  <div className="flex items-center gap-2">
                                    <a.icon className="h-4 w-4" />
                                    {a.label}
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => removeAction(idx)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </div>

                      {/* Action-specific fields */}
                      {action.action_type === "email_alert" && (
                        <div className="space-y-3">
                          <Input
                            placeholder="Email subject"
                            value={action.email_alert?.subject || ""}
                            onChange={(e) => updateAction(idx, { 
                              email_alert: { ...action.email_alert, subject: e.target.value } 
                            })}
                          />
                          <Textarea
                            placeholder="Email body (supports {{field}} merge tags)"
                            value={action.email_alert?.body || ""}
                            onChange={(e) => updateAction(idx, { 
                              email_alert: { ...action.email_alert, body: e.target.value } 
                            })}
                            rows={3}
                          />
                          <Input
                            placeholder="To emails (comma-separated) or use {{email_field}}"
                            value={action.email_alert?.to_emails?.join(", ") || ""}
                            onChange={(e) => updateAction(idx, { 
                              email_alert: { ...action.email_alert, to_emails: e.target.value.split(",").map(s => s.trim()) } 
                            })}
                          />
                        </div>
                      )}

                      {action.action_type === "field_update" && (
                        <div className="grid grid-cols-3 gap-2">
                          <Input
                            placeholder="Field to update"
                            value={action.field_update?.field || ""}
                            onChange={(e) => updateAction(idx, { 
                              field_update: { ...action.field_update, field: e.target.value } 
                            })}
                          />
                          <Select 
                            value={action.field_update?.update_type || "set_value"} 
                            onValueChange={(val) => updateAction(idx, { 
                              field_update: { ...action.field_update, update_type: val } 
                            })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="set_value">Set to value</SelectItem>
                              <SelectItem value="increment">Increment by</SelectItem>
                              <SelectItem value="clear">Clear field</SelectItem>
                              <SelectItem value="copy_from">Copy from field</SelectItem>
                            </SelectContent>
                          </Select>
                          <Input
                            placeholder="Value"
                            value={action.field_update?.value || ""}
                            onChange={(e) => updateAction(idx, { 
                              field_update: { ...action.field_update, value: e.target.value } 
                            })}
                          />
                        </div>
                      )}

                      {action.action_type === "webhook" && (
                        <div className="space-y-3">
                          <Input
                            placeholder="Webhook URL"
                            value={action.webhook?.url || ""}
                            onChange={(e) => updateAction(idx, { 
                              webhook: { ...action.webhook, url: e.target.value } 
                            })}
                          />
                          <Select 
                            value={action.webhook?.method || "POST"} 
                            onValueChange={(val) => updateAction(idx, { 
                              webhook: { ...action.webhook, method: val } 
                            })}
                          >
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="POST">POST</SelectItem>
                              <SelectItem value="PUT">PUT</SelectItem>
                              <SelectItem value="PATCH">PATCH</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="is_active"
                checked={ruleForm.is_active}
                onCheckedChange={(checked) => setRuleForm(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="is_active">Enable this workflow</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRuleDialog(false); setEditingRule(null); }}>
              Cancel
            </Button>
            <Button onClick={handleSaveRule} disabled={loading || !ruleForm.name || ruleForm.actions.length === 0}>
              {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
              {editingRule ? "Update Workflow" : "Create Workflow"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Workflow Rule</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this workflow? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => handleDeleteRule(deleteConfirm)} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ==================== MODULE SETTINGS PANELS ====================

function OrganizationProfilePanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => {
    setForm(settings);
  }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Organization Name</label>
          <Input value={form.name || ""} onChange={(e) => handleChange("name", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Legal Name</label>
          <Input value={form.legal_name || ""} onChange={(e) => handleChange("legal_name", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Email</label>
          <Input type="email" value={form.email || ""} onChange={(e) => handleChange("email", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Phone</label>
          <Input value={form.phone || ""} onChange={(e) => handleChange("phone", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Website</label>
          <Input value={form.website || ""} onChange={(e) => handleChange("website", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Industry</label>
          <Input value={form.industry || ""} onChange={(e) => handleChange("industry", e.target.value)} />
        </div>
      </div>
      <Separator />
      <h3 className="font-medium">Address</h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="text-sm font-medium">Address</label>
          <Input value={form.address || ""} onChange={(e) => handleChange("address", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">City</label>
          <Input value={form.city || ""} onChange={(e) => handleChange("city", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">State</label>
          <Input value={form.state || ""} onChange={(e) => handleChange("state", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Pincode</label>
          <Input value={form.pincode || ""} onChange={(e) => handleChange("pincode", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Country</label>
          <Input value={form.country || "India"} onChange={(e) => handleChange("country", e.target.value)} />
        </div>
      </div>
      <Separator />
      <h3 className="font-medium">Tax Information</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">GSTIN</label>
          <Input value={form.gstin || ""} onChange={(e) => handleChange("gstin", e.target.value)} placeholder="22AAAAA0000A1Z5" />
        </div>
        <div>
          <label className="text-sm font-medium">PAN</label>
          <Input value={form.pan || ""} onChange={(e) => handleChange("pan", e.target.value)} placeholder="AAAAA0000A" />
        </div>
        <div>
          <label className="text-sm font-medium">CIN</label>
          <Input value={form.cin || ""} onChange={(e) => handleChange("cin", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">MSME Registration</label>
          <Input value={form.msme_registration || ""} onChange={(e) => handleChange("msme_registration", e.target.value)} />
        </div>
      </div>
    </div>
  );
}

function BrandingPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => {
    setForm(settings);
  }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Primary Color</label>
          <div className="flex gap-2">
            <Input type="color" value={form.primary_color || "#10B981"} onChange={(e) => handleChange("primary_color", e.target.value)} className="w-16 h-10" />
            <Input value={form.primary_color || "#10B981"} onChange={(e) => handleChange("primary_color", e.target.value)} />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium">Secondary Color</label>
          <div className="flex gap-2">
            <Input type="color" value={form.secondary_color || "#3B82F6"} onChange={(e) => handleChange("secondary_color", e.target.value)} className="w-16 h-10" />
            <Input value={form.secondary_color || "#3B82F6"} onChange={(e) => handleChange("secondary_color", e.target.value)} />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium">Accent Color</label>
          <div className="flex gap-2">
            <Input type="color" value={form.accent_color || "#F59E0B"} onChange={(e) => handleChange("accent_color", e.target.value)} className="w-16 h-10" />
            <Input value={form.accent_color || "#F59E0B"} onChange={(e) => handleChange("accent_color", e.target.value)} />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium">Logo URL</label>
          <Input value={form.logo_url || ""} onChange={(e) => handleChange("logo_url", e.target.value)} placeholder="https://..." />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <input type="checkbox" id="darkMode" checked={form.dark_mode_enabled !== false} onChange={(e) => handleChange("dark_mode_enabled", e.target.checked)} />
        <label htmlFor="darkMode" className="text-sm">Enable Dark Mode</label>
      </div>
    </div>
  );
}

function LocationsPanel({ settings, onUpdate }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-medium">Locations & Branches</h3>
        <Button size="sm"><MapPin className="h-4 w-4 mr-2" />Add Location</Button>
      </div>
      {settings.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No locations configured. Add your first location to enable multi-branch operations.
        </div>
      ) : (
        <div className="space-y-2">
          {settings.map((loc, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <div className="font-medium">{loc.name}</div>
                <div className="text-sm text-muted-foreground">{loc.city}, {loc.state}</div>
              </div>
              {loc.is_primary && <Badge>Primary</Badge>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GSTSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => {
    setForm(settings);
  }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 p-4 border rounded-lg bg-[rgba(200,255,0,0.05)]">
        <input type="checkbox" id="gstRegistered" checked={form.is_gst_registered !== false} onChange={(e) => handleChange("is_gst_registered", e.target.checked)} />
        <div>
          <label htmlFor="gstRegistered" className="font-medium">GST Registered</label>
          <p className="text-sm text-muted-foreground">Enable GST compliance features</p>
        </div>
      </div>
      {form.is_gst_registered !== false && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">GSTIN</label>
              <Input value={form.gstin || ""} onChange={(e) => handleChange("gstin", e.target.value)} placeholder="22AAAAA0000A1Z5" />
            </div>
            <div>
              <label className="text-sm font-medium">GST Treatment</label>
              <select className="w-full h-10 px-3 border rounded-md" value={form.gst_treatment || ""} onChange={(e) => handleChange("gst_treatment", e.target.value)}>
                <option value="registered_business">Registered Business</option>
                <option value="unregistered">Unregistered</option>
                <option value="consumer">Consumer</option>
                <option value="overseas">Overseas</option>
              </select>
            </div>
          </div>
          <Separator />
          <h3 className="font-medium">E-Invoicing</h3>
          <div className="flex items-center gap-4 p-4 border rounded-lg">
            <input type="checkbox" id="einvoicing" checked={form.e_invoicing_enabled === true} onChange={(e) => handleChange("e_invoicing_enabled", e.target.checked)} />
            <div>
              <label htmlFor="einvoicing" className="font-medium">Enable E-Invoicing</label>
              <p className="text-sm text-muted-foreground">Generate IRN for invoices above threshold</p>
            </div>
          </div>
          {form.e_invoicing_enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">E-Invoice Threshold (INR)</label>
                <Input type="number" value={form.e_invoicing_threshold || 50000000} onChange={(e) => handleChange("e_invoicing_threshold", parseFloat(e.target.value))} />
              </div>
              <div>
                <label className="text-sm font-medium">E-Invoice Username</label>
                <Input value={form.einvoice_username || ""} onChange={(e) => handleChange("einvoice_username", e.target.value)} />
              </div>
            </div>
          )}
          <Separator />
          <h3 className="font-medium">E-Way Bill</h3>
          <div className="flex items-center gap-4 p-4 border rounded-lg">
            <input type="checkbox" id="ewaybill" checked={form.eway_bill_enabled === true} onChange={(e) => handleChange("eway_bill_enabled", e.target.checked)} />
            <div>
              <label htmlFor="ewaybill" className="font-medium">Enable E-Way Bill</label>
              <p className="text-sm text-muted-foreground">Auto-generate E-Way bills for shipments</p>
            </div>
          </div>
          {form.eway_bill_enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">E-Way Bill Threshold (INR)</label>
                <Input type="number" value={form.eway_bill_threshold || 50000} onChange={(e) => handleChange("eway_bill_threshold", parseFloat(e.target.value))} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function TDSSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="tdsApplicable" checked={form.is_tds_applicable === true} onChange={(e) => handleChange("is_tds_applicable", e.target.checked)} />
        <div>
          <label htmlFor="tdsApplicable" className="font-medium">TDS Applicable</label>
          <p className="text-sm text-muted-foreground">Enable TDS deduction on payments</p>
        </div>
      </div>
      {form.is_tds_applicable && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">TAN</label>
            <Input value={form.tan || ""} onChange={(e) => handleChange("tan", e.target.value)} placeholder="AAAA00000A" />
          </div>
          <div>
            <label className="text-sm font-medium">Deductor Type</label>
            <Input value={form.deductor_type || ""} onChange={(e) => handleChange("deductor_type", e.target.value)} />
          </div>
        </div>
      )}
    </div>
  );
}

function MSMESettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 p-4 border rounded-lg bg-blue-500/5">
        <input type="checkbox" id="msmeRegistered" checked={form.is_msme_registered === true} onChange={(e) => handleChange("is_msme_registered", e.target.checked)} />
        <div>
          <label htmlFor="msmeRegistered" className="font-medium">MSME Registered</label>
          <p className="text-sm text-muted-foreground">Enable MSME compliance (45-day payment terms)</p>
        </div>
      </div>
      {form.is_msme_registered && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">Udyam Registration Number</label>
            <Input value={form.udyam_registration || ""} onChange={(e) => handleChange("udyam_registration", e.target.value)} placeholder="UDYAM-XX-00-0000000" />
          </div>
          <div>
            <label className="text-sm font-medium">MSME Type</label>
            <select className="w-full h-10 px-3 border rounded-md" value={form.msme_type || ""} onChange={(e) => handleChange("msme_type", e.target.value)}>
              <option value="">Select Type</option>
              <option value="micro">Micro</option>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Payment Terms (Days)</label>
            <Input type="number" value={form.payment_terms_days || 45} onChange={(e) => handleChange("payment_terms_days", parseInt(e.target.value))} />
          </div>
        </div>
      )}
    </div>
  );
}

function VehicleSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Default Warranty (Months)</label>
          <Input type="number" value={form.default_warranty_months || 24} onChange={(e) => handleChange("default_warranty_months", parseInt(e.target.value))} />
        </div>
        <div>
          <label className="text-sm font-medium">Battery Warranty (Months)</label>
          <Input type="number" value={form.battery_warranty_months || 36} onChange={(e) => handleChange("battery_warranty_months", parseInt(e.target.value))} />
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="vinValidation" checked={form.vin_validation_enabled !== false} onChange={(e) => handleChange("vin_validation_enabled", e.target.checked)} />
        <div>
          <label htmlFor="vinValidation" className="font-medium">VIN Validation</label>
          <p className="text-sm text-muted-foreground">Validate VIN format on vehicle registration</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="autoCreateCustomer" checked={form.auto_create_customer !== false} onChange={(e) => handleChange("auto_create_customer", e.target.checked)} />
        <div>
          <label htmlFor="autoCreateCustomer" className="font-medium">Auto Create Customer</label>
          <p className="text-sm text-muted-foreground">Automatically create customer record from vehicle owner</p>
        </div>
      </div>
    </div>
  );
}

function TicketSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Default Priority</label>
          <select className="w-full h-10 px-3 border rounded-md" value={form.default_priority || "medium"} onChange={(e) => handleChange("default_priority", e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-medium">Escalation Hours</label>
          <Input type="number" value={form.escalation_hours || 24} onChange={(e) => handleChange("escalation_hours", parseInt(e.target.value))} />
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="slaEnabled" checked={form.sla_enabled !== false} onChange={(e) => handleChange("sla_enabled", e.target.checked)} />
        <div>
          <label htmlFor="slaEnabled" className="font-medium">SLA Tracking</label>
          <p className="text-sm text-muted-foreground">Track SLA targets for ticket resolution</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="autoAssign" checked={form.auto_assign_enabled === true} onChange={(e) => handleChange("auto_assign_enabled", e.target.checked)} />
        <div>
          <label htmlFor="autoAssign" className="font-medium">Auto Assignment</label>
          <p className="text-sm text-muted-foreground">Automatically assign tickets to technicians</p>
        </div>
      </div>
    </div>
  );
}

function WorkOrderSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Default Labor Rate (INR/hr)</label>
          <Input type="number" value={form.default_labor_rate || 500} onChange={(e) => handleChange("default_labor_rate", parseFloat(e.target.value))} />
        </div>
        <div>
          <label className="text-sm font-medium">Approval Threshold (INR)</label>
          <Input type="number" value={form.approval_threshold || 10000} onChange={(e) => handleChange("approval_threshold", parseFloat(e.target.value))} />
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="approvalRequired" checked={form.approval_required === true} onChange={(e) => handleChange("approval_required", e.target.checked)} />
        <div>
          <label htmlFor="approvalRequired" className="font-medium">Approval Required</label>
          <p className="text-sm text-muted-foreground">Require manager approval for work orders above threshold</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="checklistRequired" checked={form.checklist_required !== false} onChange={(e) => handleChange("checklist_required", e.target.checked)} />
        <div>
          <label htmlFor="checklistRequired" className="font-medium">Checklist Required</label>
          <p className="text-sm text-muted-foreground">Require technicians to complete service checklist</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="customerSignature" checked={form.customer_signature_required !== false} onChange={(e) => handleChange("customer_signature_required", e.target.checked)} />
        <div>
          <label htmlFor="customerSignature" className="font-medium">Customer Signature Required</label>
          <p className="text-sm text-muted-foreground">Capture customer signature on work order completion</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="autoGenerateInvoice" checked={form.auto_generate_invoice === true} onChange={(e) => handleChange("auto_generate_invoice", e.target.checked)} />
        <div>
          <label htmlFor="autoGenerateInvoice" className="font-medium">Auto Generate Invoice</label>
          <p className="text-sm text-muted-foreground">Automatically create invoice when work order is completed</p>
        </div>
      </div>
    </div>
  );
}

function InventorySettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Tracking Method</label>
          <select className="w-full h-10 px-3 border rounded-md" value={form.tracking_method || "fifo"} onChange={(e) => handleChange("tracking_method", e.target.value)}>
            <option value="fifo">FIFO</option>
            <option value="lifo">LIFO</option>
            <option value="average">Average Cost</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-medium">Low Stock Threshold</label>
          <Input type="number" value={form.low_stock_threshold || 10} onChange={(e) => handleChange("low_stock_threshold", parseInt(e.target.value))} />
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="serialTracking" checked={form.enable_serial_tracking !== false} onChange={(e) => handleChange("enable_serial_tracking", e.target.checked)} />
        <div>
          <label htmlFor="serialTracking" className="font-medium">Serial Number Tracking</label>
          <p className="text-sm text-muted-foreground">Track individual items by serial number</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="batchTracking" checked={form.enable_batch_tracking !== false} onChange={(e) => handleChange("enable_batch_tracking", e.target.checked)} />
        <div>
          <label htmlFor="batchTracking" className="font-medium">Batch Tracking</label>
          <p className="text-sm text-muted-foreground">Track items by batch/lot number with expiry</p>
        </div>
      </div>
    </div>
  );
}

function CustomerSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Default Credit Limit (INR)</label>
          <Input type="number" value={form.default_credit_limit || 50000} onChange={(e) => handleChange("default_credit_limit", parseFloat(e.target.value))} />
        </div>
        <div>
          <label className="text-sm font-medium">Payment Terms (Days)</label>
          <Input type="number" value={form.payment_terms_days || 30} onChange={(e) => handleChange("payment_terms_days", parseInt(e.target.value))} />
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="creditLimit" checked={form.credit_limit_enabled !== false} onChange={(e) => handleChange("credit_limit_enabled", e.target.checked)} />
        <div>
          <label htmlFor="creditLimit" className="font-medium">Credit Limit Enabled</label>
          <p className="text-sm text-muted-foreground">Enforce credit limits for customers</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="portalEnabled" checked={form.portal_enabled !== false} onChange={(e) => handleChange("portal_enabled", e.target.checked)} />
        <div>
          <label htmlFor="portalEnabled" className="font-medium">Customer Portal</label>
          <p className="text-sm text-muted-foreground">Allow customers to access self-service portal</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="loyaltyProgram" checked={form.loyalty_program_enabled === true} onChange={(e) => handleChange("loyalty_program_enabled", e.target.checked)} />
        <div>
          <label htmlFor="loyaltyProgram" className="font-medium">Loyalty Program</label>
          <p className="text-sm text-muted-foreground">Enable customer loyalty rewards</p>
        </div>
      </div>
    </div>
  );
}

function BillingSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Invoice Prefix</label>
          <Input value={form.invoice_prefix || "INV"} onChange={(e) => handleChange("invoice_prefix", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Quote Prefix</label>
          <Input value={form.quote_prefix || "QT"} onChange={(e) => handleChange("quote_prefix", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium">Default Payment Terms (Days)</label>
          <Input type="number" value={form.default_payment_terms || 30} onChange={(e) => handleChange("default_payment_terms", parseInt(e.target.value))} />
        </div>
        <div>
          <label className="text-sm font-medium">Max Discount %</label>
          <Input type="number" value={form.max_discount_percent || 20} onChange={(e) => handleChange("max_discount_percent", parseFloat(e.target.value))} />
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="autoSendReminder" checked={form.auto_send_reminder !== false} onChange={(e) => handleChange("auto_send_reminder", e.target.checked)} />
        <div>
          <label htmlFor="autoSendReminder" className="font-medium">Auto Send Reminders</label>
          <p className="text-sm text-muted-foreground">Automatically send payment reminders</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="lateFee" checked={form.late_fee_enabled === true} onChange={(e) => handleChange("late_fee_enabled", e.target.checked)} />
        <div>
          <label htmlFor="lateFee" className="font-medium">Late Fee</label>
          <p className="text-sm text-muted-foreground">Apply late fee on overdue invoices</p>
        </div>
      </div>
    </div>
  );
}

function EFISettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Configure Failure Intelligence settings for automatic diagnosis and failure pattern detection.
      </p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Repeat Failure Threshold</label>
          <Input type="number" value={form.repeat_failure_threshold || 3} onChange={(e) => handleChange("repeat_failure_threshold", parseInt(e.target.value))} />
          <p className="text-xs text-muted-foreground mt-1">Number of failures before marking as repeat issue</p>
        </div>
        <div>
          <label className="text-sm font-medium">Repeat Failure Window (Days)</label>
          <Input type="number" value={form.repeat_failure_days || 90} onChange={(e) => handleChange("repeat_failure_days", parseInt(e.target.value))} />
          <p className="text-xs text-muted-foreground mt-1">Time window to detect repeat failures</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="aiDiagnosis" checked={form.ai_diagnosis_enabled !== false} onChange={(e) => handleChange("ai_diagnosis_enabled", e.target.checked)} />
        <div>
          <label htmlFor="aiDiagnosis" className="font-medium">AI Diagnosis</label>
          <p className="text-sm text-muted-foreground">Use AI to suggest diagnostic steps and solutions</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="knowledgeBase" checked={form.knowledge_base_suggestions_enabled !== false} onChange={(e) => handleChange("knowledge_base_suggestions_enabled", e.target.checked)} />
        <div>
          <label htmlFor="knowledgeBase" className="font-medium">Knowledge Base Suggestions</label>
          <p className="text-sm text-muted-foreground">Show relevant knowledge base articles for issues</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="partsRecommendation" checked={form.parts_recommendation_enabled !== false} onChange={(e) => handleChange("parts_recommendation_enabled", e.target.checked)} />
        <div>
          <label htmlFor="partsRecommendation" className="font-medium">Parts Recommendations</label>
          <p className="text-sm text-muted-foreground">Suggest required parts based on failure type</p>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <input type="checkbox" id="autoEscalate" checked={form.auto_escalate_repeat_failures !== false} onChange={(e) => handleChange("auto_escalate_repeat_failures", e.target.checked)} />
        <div>
          <label htmlFor="autoEscalate" className="font-medium">Auto Escalate Repeat Failures</label>
          <p className="text-sm text-muted-foreground">Automatically escalate tickets for repeat issues</p>
        </div>
      </div>
    </div>
  );
}

function PortalSettingsPanel({ settings, onUpdate }) {
  const [form, setForm] = useState(settings);

  useEffect(() => { setForm(settings); }, [settings]);

  const handleChange = (field, value) => {
    const updated = { ...form, [field]: value };
    setForm(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 p-4 border rounded-lg bg-blue-500/5">
        <input type="checkbox" id="customerPortalEnabled" checked={form.customer_portal_enabled !== false} onChange={(e) => handleChange("customer_portal_enabled", e.target.checked)} />
        <div>
          <label htmlFor="customerPortalEnabled" className="font-medium">Customer Portal</label>
          <p className="text-sm text-muted-foreground">Allow customers to access self-service portal</p>
        </div>
      </div>
      {form.customer_portal_enabled !== false && (
        <>
          <h4 className="font-medium">Customer Permissions</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2 p-3 border rounded-lg">
              <input type="checkbox" id="canViewInvoices" checked={form.customer_can_view_invoices !== false} onChange={(e) => handleChange("customer_can_view_invoices", e.target.checked)} />
              <label htmlFor="canViewInvoices" className="text-sm">View Invoices</label>
            </div>
            <div className="flex items-center gap-2 p-3 border rounded-lg">
              <input type="checkbox" id="canViewQuotes" checked={form.customer_can_view_quotes !== false} onChange={(e) => handleChange("customer_can_view_quotes", e.target.checked)} />
              <label htmlFor="canViewQuotes" className="text-sm">View Quotes</label>
            </div>
            <div className="flex items-center gap-2 p-3 border rounded-lg">
              <input type="checkbox" id="canAcceptQuotes" checked={form.customer_can_accept_quotes !== false} onChange={(e) => handleChange("customer_can_accept_quotes", e.target.checked)} />
              <label htmlFor="canAcceptQuotes" className="text-sm">Accept Quotes</label>
            </div>
            <div className="flex items-center gap-2 p-3 border rounded-lg">
              <input type="checkbox" id="canPayOnline" checked={form.customer_can_pay_online !== false} onChange={(e) => handleChange("customer_can_pay_online", e.target.checked)} />
              <label htmlFor="canPayOnline" className="text-sm">Pay Online</label>
            </div>
            <div className="flex items-center gap-2 p-3 border rounded-lg">
              <input type="checkbox" id="canRaiseTickets" checked={form.customer_can_raise_tickets !== false} onChange={(e) => handleChange("customer_can_raise_tickets", e.target.checked)} />
              <label htmlFor="canRaiseTickets" className="text-sm">Raise Support Tickets</label>
            </div>
            <div className="flex items-center gap-2 p-3 border rounded-lg">
              <input type="checkbox" id="canTrackService" checked={form.customer_can_track_service !== false} onChange={(e) => handleChange("customer_can_track_service", e.target.checked)} />
              <label htmlFor="canTrackService" className="text-sm">Track Service Status</label>
            </div>
          </div>
          <Separator />
          <div className="flex items-center gap-4 p-4 border rounded-lg">
            <input type="checkbox" id="vendorPortalEnabled" checked={form.vendor_portal_enabled === true} onChange={(e) => handleChange("vendor_portal_enabled", e.target.checked)} />
            <div>
              <label htmlFor="vendorPortalEnabled" className="font-medium">Vendor Portal</label>
              <p className="text-sm text-muted-foreground">Allow vendors to view POs and update delivery status</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function ComingSoonPanel({ item }) {
  return (
    <div className="text-center py-12">
      <Settings2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
      <h3 className="font-medium text-lg">{item.name}</h3>
      <p className="text-muted-foreground mt-2">
        This settings panel is being built. Configuration will be available soon.
      </p>
    </div>
  );
}
