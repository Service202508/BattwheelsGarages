import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  Shield, Users, Settings, Eye, Plus, Edit2, Trash2,
  Check, X, ChevronRight, Loader2, Lock, Unlock,
  LayoutDashboard, Ticket, FileText, Package, Wallet,
  User, Building2, BarChart3, Clock, Bot, Save
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const categoryIcons = {
  core: LayoutDashboard,
  operations: Ticket,
  sales: FileText,
  purchases: Package,
  inventory: Package,
  finance: Wallet,
  hr: User,
  intelligence: Bot,
  admin: Settings,
  reports: BarChart3,
};

const roleColors = {
  admin: "bg-bw-red/10 text-bw-red border border-bw-red/25 border-red-200",
  manager: "bg-purple-100 text-bw-purple border-purple-200",
  technician: "bg-bw-volt/10 text-bw-volt border border-bw-volt/25 border-green-200",
  customer: "bg-blue-100 text-bw-blue border-blue-200",
  business_customer: "bg-indigo-100 text-indigo-700 border-indigo-200",
};

export default function PermissionsManager() {
  const [roles, setRoles] = useState([]);
  const [modules, setModules] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleDescription, setNewRoleDescription] = useState("");

  useEffect(() => {
    fetchRolesAndModules();
  }, []);

  const fetchRolesAndModules = async () => {
    try {
      const [rolesRes, modulesRes] = await Promise.all([
        fetch(`${API}/permissions/roles`, { headers: getAuthHeaders() }),
        fetch(`${API}/permissions/modules`, { headers: getAuthHeaders() })
      ]);
      
      if (rolesRes.ok && modulesRes.ok) {
        const rolesData = await rolesRes.json();
        const modulesData = await modulesRes.json();
        setRoles(rolesData.roles || []);
        setModules(modulesData.modules || []);
        
        // Select first role by default
        if (rolesData.roles?.length > 0 && !selectedRole) {
          fetchRolePermissions(rolesData.roles[0].role);
        }
      }
    } catch (error) {
      console.error("Failed to fetch roles/modules:", error);
      toast.error("Failed to load permissions data");
    } finally {
      setLoading(false);
    }
  };

  const fetchRolePermissions = async (role) => {
    setSelectedRole(role);
    try {
      const res = await fetch(`${API}/permissions/roles/${role}`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setPermissions(data);
      }
    } catch (error) {
      console.error("Failed to fetch permissions:", error);
    }
  };

  const handlePermissionChange = async (moduleId, permissionKey, value) => {
    if (!permissions) return;
    
    // Optimistic update
    const updatedModules = { ...permissions.modules };
    if (!updatedModules[moduleId]) {
      updatedModules[moduleId] = { can_view: false, can_create: false, can_edit: false, can_delete: false };
    }
    updatedModules[moduleId][permissionKey] = value;
    
    setPermissions({ ...permissions, modules: updatedModules });
    
    // Save to backend
    try {
      const res = await fetch(`${API}/permissions/roles/${selectedRole}/module/${moduleId}`, {
        method: "PATCH",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          role: selectedRole,
          module_id: moduleId,
          permission_key: permissionKey,
          value: value
        })
      });
      
      if (!res.ok) {
        toast.error("Failed to update permission");
        // Revert
        fetchRolePermissions(selectedRole);
      }
    } catch (error) {
      toast.error("Failed to update permission");
      fetchRolePermissions(selectedRole);
    }
  };

  const handleSaveRole = async () => {
    if (!permissions) return;
    setSaving(true);
    
    try {
      const modulesList = Object.entries(permissions.modules).map(([moduleId, perms]) => ({
        module_id: moduleId,
        can_view: perms.can_view || false,
        can_create: perms.can_create || false,
        can_edit: perms.can_edit || false,
        can_delete: perms.can_delete || false,
        custom_permissions: perms.custom || {}
      }));
      
      const res = await fetch(`${API}/permissions/roles/${selectedRole}`, {
        method: "PUT",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          role: selectedRole,
          modules: modulesList,
          description: permissions.description
        })
      });
      
      if (res.ok) {
        toast.success("Permissions saved successfully");
      } else {
        toast.error("Failed to save permissions");
      }
    } catch (error) {
      toast.error("Failed to save permissions");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateRole = async () => {
    if (!newRoleName.trim()) {
      toast.error("Please enter a role name");
      return;
    }
    
    try {
      const res = await fetch(`${API}/permissions/roles`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          role: newRoleName.toLowerCase().replace(/\s+/g, '_'),
          description: newRoleDescription,
          modules: []
        })
      });
      
      if (res.ok) {
        toast.success("Role created successfully");
        setShowCreateRole(false);
        setNewRoleName("");
        setNewRoleDescription("");
        fetchRolesAndModules();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to create role");
      }
    } catch (error) {
      toast.error("Failed to create role");
    }
  };

  const handleDeleteRole = async (role) => {
    if (window.confirm(`Are you sure you want to delete the "${role}" role?`)) {
      try {
        const res = await fetch(`${API}/permissions/roles/${role}`, {
          method: "DELETE",
          headers: getAuthHeaders()
        });
        
        if (res.ok) {
          toast.success("Role deleted");
          fetchRolesAndModules();
          if (selectedRole === role) {
            setSelectedRole(null);
            setPermissions(null);
          }
        } else {
          const data = await res.json();
          toast.error(data.detail || "Failed to delete role");
        }
      } catch (error) {
        toast.error("Failed to delete role");
      }
    }
  };

  // Group modules by category
  const modulesByCategory = modules.reduce((acc, mod) => {
    const category = mod.category || "other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(mod);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="permissions-manager">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Role Permissions</h1>
          <p className="text-muted-foreground">Manage access control for different user roles</p>
        </div>
        <Button onClick={() => setShowCreateRole(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Role
        </Button>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Roles List */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Roles
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px]">
              <div className="p-2 space-y-1">
                {roles.map((role) => (
                  <div
                    key={role.role}
                    onClick={() => fetchRolePermissions(role.role)}
                    className={`
                      flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all
                      ${selectedRole === role.role 
                        ? 'bg-primary/10 border border-primary/20' 
                        : 'hover:bg-muted'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${roleColors[role.role] || 'bg-white/5'}`}>
                        {role.is_system ? <Lock className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                      </div>
                      <div>
                        <p className="font-medium capitalize">{role.role.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-[120px]">
                          {role.description || "No description"}
                        </p>
                      </div>
                    </div>
                    {!role.is_system && (
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-7 w-7"
                        onClick={(e) => { e.stopPropagation(); handleDeleteRole(role.role); }}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Permissions Grid */}
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                {selectedRole ? (
                  <span className="capitalize">{selectedRole.replace(/_/g, ' ')} Permissions</span>
                ) : (
                  "Select a Role"
                )}
              </CardTitle>
              <CardDescription>
                {permissions?.description || "Configure module access for this role"}
              </CardDescription>
            </div>
            {selectedRole && (
              <Button onClick={handleSaveRole} disabled={saving} className="gap-2">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save Changes
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {!selectedRole ? (
              <div className="text-center py-12 text-muted-foreground">
                <Shield className="h-16 w-16 mx-auto mb-4 opacity-30" />
                <p>Select a role from the list to manage its permissions</p>
              </div>
            ) : (
              <ScrollArea className="h-[550px] pr-4">
                <div className="space-y-6">
                  {Object.entries(modulesByCategory).map(([category, categoryModules]) => {
                    const CategoryIcon = categoryIcons[category] || Settings;
                    return (
                      <div key={category}>
                        <div className="flex items-center gap-2 mb-3">
                          <CategoryIcon className="h-4 w-4 text-muted-foreground" />
                          <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">
                            {category}
                          </h3>
                        </div>
                        <div className="space-y-2">
                          {categoryModules.map((mod) => {
                            const modPerms = permissions?.modules?.[mod.module_id] || {};
                            return (
                              <div 
                                key={mod.module_id}
                                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <div className="p-2 rounded-lg bg-muted">
                                    <Settings className="h-4 w-4 text-muted-foreground" />
                                  </div>
                                  <span className="font-medium">{mod.name}</span>
                                </div>
                                <div className="flex items-center gap-4">
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">View</span>
                                    <Switch
                                      checked={modPerms.can_view || false}
                                      onCheckedChange={(v) => handlePermissionChange(mod.module_id, "can_view", v)}
                                    />
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">Create</span>
                                    <Switch
                                      checked={modPerms.can_create || false}
                                      onCheckedChange={(v) => handlePermissionChange(mod.module_id, "can_create", v)}
                                    />
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">Edit</span>
                                    <Switch
                                      checked={modPerms.can_edit || false}
                                      onCheckedChange={(v) => handlePermissionChange(mod.module_id, "can_edit", v)}
                                    />
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">Delete</span>
                                    <Switch
                                      checked={modPerms.can_delete || false}
                                      onCheckedChange={(v) => handlePermissionChange(mod.module_id, "can_delete", v)}
                                    />
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Create Role Dialog */}
      <Dialog open={showCreateRole} onOpenChange={setShowCreateRole}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Role</DialogTitle>
            <DialogDescription>
              Create a custom role with specific permissions
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Role Name</Label>
              <Input
                placeholder="e.g., supervisor"
                value={newRoleName}
                onChange={(e) => setNewRoleName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Describe this role's purpose..."
                value={newRoleDescription}
                onChange={(e) => setNewRoleDescription(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateRole(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateRole}>
              Create Role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
