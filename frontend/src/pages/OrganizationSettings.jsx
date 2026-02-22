import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { 
  Building2, Settings, Users, Shield, Bell, Package, Receipt, 
  Brain, Clock, MapPin, Save, Plus, Trash2, Edit2, 
  UserPlus, Mail, Phone, Globe, IndianRupee, Calendar,
  AlertTriangle, CheckCircle, Loader2, RefreshCw, Download, Upload,
  CreditCard, Eye, EyeOff, Link2, ExternalLink
} from "lucide-react";
import { API } from "@/App";

// Role badge colors
const roleBadgeColors = {
  owner: "bg-[rgba(139,92,246,0.20)] text-purple-400 border-purple-500/30",
  admin: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  manager: "bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30",
  dispatcher: "bg-[rgba(234,179,8,0.20)] text-yellow-400 border-yellow-500/30",
  technician: "bg-[rgba(255,140,0,0.20)] text-orange-400 border-orange-500/30",
  accountant: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  viewer: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

// Status badge colors
const statusBadgeColors = {
  active: "bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30",
  invited: "bg-[rgba(234,179,8,0.20)] text-yellow-400 border-yellow-500/30",
  suspended: "bg-[rgba(255,59,47,0.20)] text-red-400 border-red-500/30",
  deactivated: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

export default function OrganizationSettings({ user }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [organization, setOrganization] = useState(null);
  const [settings, setSettings] = useState(null);
  const [members, setMembers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [activeTab, setActiveTab] = useState("general");
  
  // Edit states
  const [editingOrg, setEditingOrg] = useState(false);
  const [orgForm, setOrgForm] = useState({});
  const [settingsForm, setSettingsForm] = useState({});
  
  // Add member dialog
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [newMemberRole, setNewMemberRole] = useState("viewer");
  const [addingMember, setAddingMember] = useState(false);
  
  // Import/Export state
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  
  // Razorpay state
  const [razorpayConfig, setRazorpayConfig] = useState({
    key_id: "",
    key_secret: "",
    webhook_secret: "",
    test_mode: true
  });
  const [razorpayConfigured, setRazorpayConfigured] = useState(false);
  const [showSecrets, setShowSecrets] = useState(false);
  const [savingRazorpay, setSavingRazorpay] = useState(false);
  const [testingRazorpay, setTestingRazorpay] = useState(false);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, []);

  // Export settings
  const exportSettings = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${API}/org/settings/export`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `org-settings-${organization?.slug || "export"}-${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Settings exported successfully");
      } else {
        toast.error("Failed to export settings");
      }
    } catch (error) {
      toast.error("Failed to export settings");
    } finally {
      setExporting(false);
    }
  };

  // Import settings
  const importSettings = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    setImporting(true);
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      const res = await fetch(`${API}/org/settings/import`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      
      if (res.ok) {
        toast.success("Settings imported successfully");
        fetchData(); // Refresh data
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to import settings");
      }
    } catch (error) {
      toast.error("Invalid settings file format");
    } finally {
      setImporting(false);
      event.target.value = ""; // Reset file input
    }
  };

  // Fetch organization data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [orgRes, settingsRes, membersRes, rolesRes, razorpayRes] = await Promise.all([
        fetch(`${API}/org`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/settings`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/users`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/roles`, { headers: getAuthHeaders() }),
        fetch(`${API}/payments/config`, { headers: getAuthHeaders() }),
      ]);

      if (orgRes.ok) {
        const orgData = await orgRes.json();
        setOrganization(orgData);
        setOrgForm(orgData);
      }

      if (settingsRes.ok) {
        const settingsData = await settingsRes.json();
        setSettings(settingsData);
        setSettingsForm(settingsData);
      }

      if (membersRes.ok) {
        const membersData = await membersRes.json();
        setMembers(membersData.users || []);
      }

      if (rolesRes.ok) {
        const rolesData = await rolesRes.json();
        setRoles(rolesData.roles || []);
      }
      
      if (razorpayRes.ok) {
        const rpData = await razorpayRes.json();
        setRazorpayConfigured(rpData.configured || false);
        if (rpData.configured) {
          setRazorpayConfig(prev => ({
            ...prev,
            test_mode: rpData.test_mode ?? true
          }));
        }
      }
    } catch (error) {
      toast.error("Failed to load organization data");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Save organization info
  const saveOrganization = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/org`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name: orgForm.name,
          phone: orgForm.phone,
          email: orgForm.email,
          website: orgForm.website,
          address: orgForm.address,
          city: orgForm.city,
          state: orgForm.state,
          pincode: orgForm.pincode,
          gstin: orgForm.gstin,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setOrganization(data);
        setEditingOrg(false);
        toast.success("Organization updated successfully");
      } else {
        toast.error("Failed to update organization");
      }
    } catch (error) {
      toast.error("Failed to update organization");
    } finally {
      setSaving(false);
    }
  };

  // Save settings
  const saveSettings = async (section, data) => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/org/settings`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify(section ? { [section]: data } : data),
      });

      if (res.ok) {
        const updatedSettings = await res.json();
        setSettings(updatedSettings);
        setSettingsForm(updatedSettings);
        toast.success("Settings saved successfully");
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

  // Add member to organization
  const addMember = async () => {
    if (!newMemberEmail) {
      toast.error("Please enter an email address");
      return;
    }

    setAddingMember(true);
    try {
      const res = await fetch(`${API}/org/users`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          email: newMemberEmail,
          role: newMemberRole,
          send_invite: true,
        }),
      });

      if (res.ok) {
        toast.success("User added to organization");
        setAddMemberOpen(false);
        setNewMemberEmail("");
        setNewMemberRole("viewer");
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to add user");
      }
    } catch (error) {
      toast.error("Failed to add user");
    } finally {
      setAddingMember(false);
    }
  };

  // Update member role
  const updateMemberRole = async (userId, newRole) => {
    try {
      const res = await fetch(`${API}/org/users/${userId}`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ role: newRole }),
      });

      if (res.ok) {
        toast.success("Role updated successfully");
        fetchData();
      } else {
        toast.error("Failed to update role");
      }
    } catch (error) {
      toast.error("Failed to update role");
    }
  };

  // Remove member
  const removeMember = async (userId) => {
    if (!confirm("Are you sure you want to remove this user from the organization?")) {
      return;
    }

    try {
      const res = await fetch(`${API}/org/users/${userId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (res.ok) {
        toast.success("User removed from organization");
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to remove user");
      }
    } catch (error) {
      toast.error("Failed to remove user");
    }
  };

  // Save Razorpay configuration
  const saveRazorpayConfig = async () => {
    if (!razorpayConfig.key_id || !razorpayConfig.key_secret) {
      toast.error("Please enter both Key ID and Key Secret");
      return;
    }
    
    if (razorpayConfig.key_id.length < 10 || razorpayConfig.key_secret.length < 10) {
      toast.error("Invalid API credentials. Please check your Razorpay dashboard.");
      return;
    }
    
    setSavingRazorpay(true);
    try {
      const res = await fetch(`${API}/payments/config`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(razorpayConfig),
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success("Razorpay configuration saved successfully!");
        setRazorpayConfigured(true);
        // Clear sensitive data from state after save
        setRazorpayConfig(prev => ({
          ...prev,
          key_secret: "",
          webhook_secret: ""
        }));
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to save Razorpay configuration");
      }
    } catch (error) {
      toast.error("Failed to save Razorpay configuration");
    } finally {
      setSavingRazorpay(false);
    }
  };
  
  // Remove Razorpay configuration
  const removeRazorpayConfig = async () => {
    if (!confirm("Are you sure you want to remove Razorpay configuration? This will disable online payments.")) {
      return;
    }
    
    try {
      const res = await fetch(`${API}/payments/config`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      
      if (res.ok) {
        toast.success("Razorpay configuration removed");
        setRazorpayConfigured(false);
        setRazorpayConfig({
          key_id: "",
          key_secret: "",
          webhook_secret: "",
          test_mode: true
        });
      } else {
        toast.error("Failed to remove Razorpay configuration");
      }
    } catch (error) {
      toast.error("Failed to remove Razorpay configuration");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="organization-settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-primary" />
            Organization Settings
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage your organization profile, settings, and team members
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Import Settings */}
          <input
            type="file"
            id="import-settings-file"
            accept=".json"
            onChange={importSettings}
            className="hidden"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => document.getElementById("import-settings-file")?.click()}
            disabled={importing}
            data-testid="import-settings-btn"
          >
            {importing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Upload className="h-4 w-4 mr-2" />
            )}
            Import
          </Button>
          
          {/* Export Settings */}
          <Button
            variant="outline"
            size="sm"
            onClick={exportSettings}
            disabled={exporting}
            data-testid="export-settings-btn"
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Export
          </Button>
          
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Organization Info Card */}
      <Card className="border-primary/20">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">{organization?.name}</CardTitle>
            <CardDescription>Organization ID: {organization?.organization_id}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-primary/10">
              {organization?.plan_type?.toUpperCase()}
            </Badge>
            <Badge variant="outline" className={organization?.is_active ? "bg-[rgba(34,197,94,0.10)] text-green-400" : "bg-[rgba(255,59,47,0.10)] text-red-400"}>
              {organization?.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="general" className="gap-2">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline">General</span>
          </TabsTrigger>
          <TabsTrigger value="team" className="gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Team</span>
          </TabsTrigger>
          <TabsTrigger value="operations" className="gap-2">
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">Operations</span>
          </TabsTrigger>
          <TabsTrigger value="finance" className="gap-2">
            <Receipt className="h-4 w-4" />
            <span className="hidden sm:inline">Finance</span>
          </TabsTrigger>
          <TabsTrigger value="efi" className="gap-2">
            <Brain className="h-4 w-4" />
            <span className="hidden sm:inline">EFI</span>
          </TabsTrigger>
        </TabsList>

        {/* General Tab */}
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Organization Profile</CardTitle>
                <CardDescription>Basic information about your organization</CardDescription>
              </div>
              {!editingOrg ? (
                <Button variant="outline" size="sm" onClick={() => setEditingOrg(true)}>
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setEditingOrg(false)}>
                    Cancel
                  </Button>
                  <Button size="sm" onClick={saveOrganization} disabled={saving}>
                    {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Organization Name</Label>
                  <Input 
                    value={orgForm.name || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Slug</Label>
                  <Input value={organization?.slug || ""} disabled className="bg-muted" />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input 
                    type="email"
                    value={orgForm.email || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, email: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input 
                    value={orgForm.phone || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, phone: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Website</Label>
                  <Input 
                    value={orgForm.website || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, website: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
                <div className="space-y-2">
                  <Label>GSTIN</Label>
                  <Input 
                    value={orgForm.gstin || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, gstin: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Address</Label>
                <Textarea 
                  value={orgForm.address || ""} 
                  onChange={(e) => setOrgForm({ ...orgForm, address: e.target.value })}
                  disabled={!editingOrg}
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>City</Label>
                  <Input 
                    value={orgForm.city || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, city: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
                <div className="space-y-2">
                  <Label>State</Label>
                  <Input 
                    value={orgForm.state || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, state: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Pincode</Label>
                  <Input 
                    value={orgForm.pincode || ""} 
                    onChange={(e) => setOrgForm({ ...orgForm, pincode: e.target.value })}
                    disabled={!editingOrg}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* General Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Regional Settings</CardTitle>
              <CardDescription>Currency, timezone, and date format preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Currency</Label>
                  <Select 
                    value={settingsForm.currency || "INR"} 
                    onValueChange={(v) => {
                      setSettingsForm({ ...settingsForm, currency: v });
                      saveSettings(null, { currency: v });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="INR">INR (₹)</SelectItem>
                      <SelectItem value="USD">USD ($)</SelectItem>
                      <SelectItem value="EUR">EUR (€)</SelectItem>
                      <SelectItem value="GBP">GBP (£)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Select 
                    value={settingsForm.timezone || "Asia/Kolkata"} 
                    onValueChange={(v) => {
                      setSettingsForm({ ...settingsForm, timezone: v });
                      saveSettings(null, { timezone: v });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Kolkata">Asia/Kolkata (IST)</SelectItem>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">America/New York</SelectItem>
                      <SelectItem value="Europe/London">Europe/London</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Date Format</Label>
                  <Select 
                    value={settingsForm.date_format || "DD/MM/YYYY"} 
                    onValueChange={(v) => {
                      setSettingsForm({ ...settingsForm, date_format: v });
                      saveSettings(null, { date_format: v });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                      <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                      <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Service Radius (km)</Label>
                  <Input 
                    type="number"
                    value={settingsForm.service_radius_km || 50}
                    onChange={(e) => {
                      const v = parseInt(e.target.value) || 50;
                      setSettingsForm({ ...settingsForm, service_radius_km: v });
                    }}
                    onBlur={() => saveSettings(null, { service_radius_km: settingsForm.service_radius_km })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Fiscal Year Start</Label>
                  <Select 
                    value={settingsForm.fiscal_year_start || "04-01"} 
                    onValueChange={(v) => {
                      setSettingsForm({ ...settingsForm, fiscal_year_start: v });
                      saveSettings(null, { fiscal_year_start: v });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="01-01">January 1</SelectItem>
                      <SelectItem value="04-01">April 1 (India)</SelectItem>
                      <SelectItem value="07-01">July 1</SelectItem>
                      <SelectItem value="10-01">October 1</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Team Tab */}
        <TabsContent value="team" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Team Members</CardTitle>
                <CardDescription>{members.length} members in your organization</CardDescription>
              </div>
              <Dialog open={addMemberOpen} onOpenChange={setAddMemberOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <UserPlus className="h-4 w-4 mr-2" />
                    Add Member
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Team Member</DialogTitle>
                    <DialogDescription>
                      Add a user to your organization by their email address
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>Email Address</Label>
                      <Input 
                        type="email"
                        placeholder="user@example.com"
                        value={newMemberEmail}
                        onChange={(e) => setNewMemberEmail(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Role</Label>
                      <Select value={newMemberRole} onValueChange={setNewMemberRole}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {roles.filter(r => r.role !== 'owner').map((role) => (
                            <SelectItem key={role.role} value={role.role}>
                              {role.name} ({role.permissions.length} permissions)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setAddMemberOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={addMember} disabled={addingMember}>
                      {addingMember && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      Add Member
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {members.map((member) => (
                    <div 
                      key={member.membership?.membership_id}
                      className="flex items-center justify-between p-3 rounded-lg border bg-card/50"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarImage src={member.user?.picture} />
                          <AvatarFallback>
                            {member.user?.name?.charAt(0) || member.user?.email?.charAt(0) || "?"}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{member.user?.name || "Unknown"}</p>
                          <p className="text-sm text-muted-foreground">{member.user?.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={`${roleBadgeColors[member.membership?.role]} border`}>
                          {member.membership?.role}
                        </Badge>
                        <Badge className={`${statusBadgeColors[member.membership?.status]} border`}>
                          {member.membership?.status}
                        </Badge>
                        {member.membership?.role !== 'owner' && (
                          <div className="flex items-center gap-1">
                            <Select 
                              value={member.membership?.role}
                              onValueChange={(v) => updateMemberRole(member.membership?.user_id, v)}
                            >
                              <SelectTrigger className="w-[120px] h-8">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {roles.filter(r => r.role !== 'owner').map((role) => (
                                  <SelectItem key={role.role} value={role.role}>
                                    {role.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                              onClick={() => removeMember(member.membership?.user_id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Roles Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Role Permissions</CardTitle>
              <CardDescription>Understanding role-based access control</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {roles.map((role) => (
                  <div key={role.role} className="p-3 rounded-lg border bg-card/50">
                    <div className="flex items-center justify-between mb-2">
                      <Badge className={`${roleBadgeColors[role.role]} border`}>
                        {role.name}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {role.permissions.length} permissions
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {role.permissions.slice(0, 5).map((perm, i) => (
                        <span key={i} className="text-xs px-1.5 py-0.5 bg-muted rounded">
                          {perm.split(":")[0]}
                        </span>
                      ))}
                      {role.permissions.length > 5 && (
                        <span className="text-xs px-1.5 py-0.5 bg-muted rounded">
                          +{role.permissions.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Operations Tab */}
        <TabsContent value="operations" className="space-y-4">
          {/* Ticket Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Ticket Settings
              </CardTitle>
              <CardDescription>Configure ticket workflows and SLA timers</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Default Priority</Label>
                  <Select 
                    value={settingsForm.tickets?.default_priority || "medium"} 
                    onValueChange={(v) => {
                      const updated = { ...settingsForm.tickets, default_priority: v };
                      setSettingsForm({ ...settingsForm, tickets: updated });
                      saveSettings("tickets", { default_priority: v });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Auto-Assign Tickets</Label>
                    <p className="text-xs text-muted-foreground">Automatically assign to available technicians</p>
                  </div>
                  <Switch 
                    checked={settingsForm.tickets?.auto_assign_enabled ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.tickets, auto_assign_enabled: v };
                      setSettingsForm({ ...settingsForm, tickets: updated });
                      saveSettings("tickets", { auto_assign_enabled: v });
                    }}
                  />
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm font-medium mb-3 block">SLA Response Times (hours)</Label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {["low", "medium", "high", "critical"].map((priority) => (
                    <div key={priority} className="space-y-1">
                      <Label className="text-xs capitalize">{priority}</Label>
                      <Input 
                        type="number"
                        value={settingsForm.tickets?.[`sla_hours_${priority}`] || ""}
                        onChange={(e) => {
                          const v = parseInt(e.target.value) || 0;
                          const updated = { ...settingsForm.tickets, [`sla_hours_${priority}`]: v };
                          setSettingsForm({ ...settingsForm, tickets: updated });
                        }}
                        onBlur={() => {
                          saveSettings("tickets", { 
                            [`sla_hours_${priority}`]: settingsForm.tickets?.[`sla_hours_${priority}`] 
                          });
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border">
                <div>
                  <Label>Require Approval for Close</Label>
                  <p className="text-xs text-muted-foreground">Manager approval needed to close tickets</p>
                </div>
                <Switch 
                  checked={settingsForm.tickets?.require_approval_for_close ?? false}
                  onCheckedChange={(v) => {
                    const updated = { ...settingsForm.tickets, require_approval_for_close: v };
                    setSettingsForm({ ...settingsForm, tickets: updated });
                    saveSettings("tickets", { require_approval_for_close: v });
                  }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Inventory Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Package className="h-4 w-4" />
                Inventory Settings
              </CardTitle>
              <CardDescription>Configure inventory tracking and thresholds</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Inventory Tracking</Label>
                    <p className="text-xs text-muted-foreground">Track stock levels for items</p>
                  </div>
                  <Switch 
                    checked={settingsForm.inventory?.tracking_enabled ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.inventory, tracking_enabled: v };
                      setSettingsForm({ ...settingsForm, inventory: updated });
                      saveSettings("inventory", { tracking_enabled: v });
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Low Stock Threshold</Label>
                  <Input 
                    type="number"
                    value={settingsForm.inventory?.low_stock_threshold || 10}
                    onChange={(e) => {
                      const v = parseInt(e.target.value) || 10;
                      const updated = { ...settingsForm.inventory, low_stock_threshold: v };
                      setSettingsForm({ ...settingsForm, inventory: updated });
                    }}
                    onBlur={() => {
                      saveSettings("inventory", { low_stock_threshold: settingsForm.inventory?.low_stock_threshold });
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Auto-Reorder</Label>
                    <p className="text-xs text-muted-foreground">Create PO when stock is low</p>
                  </div>
                  <Switch 
                    checked={settingsForm.inventory?.auto_reorder_enabled ?? false}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.inventory, auto_reorder_enabled: v };
                      setSettingsForm({ ...settingsForm, inventory: updated });
                      saveSettings("inventory", { auto_reorder_enabled: v });
                    }}
                  />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Serial Tracking</Label>
                    <p className="text-xs text-muted-foreground">Track serial numbers</p>
                  </div>
                  <Switch 
                    checked={settingsForm.inventory?.require_serial_tracking ?? false}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.inventory, require_serial_tracking: v };
                      setSettingsForm({ ...settingsForm, inventory: updated });
                      saveSettings("inventory", { require_serial_tracking: v });
                    }}
                  />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Batch Tracking</Label>
                    <p className="text-xs text-muted-foreground">Track batch numbers</p>
                  </div>
                  <Switch 
                    checked={settingsForm.inventory?.require_batch_tracking ?? false}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.inventory, require_batch_tracking: v };
                      setSettingsForm({ ...settingsForm, inventory: updated });
                      saveSettings("inventory", { require_batch_tracking: v });
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Finance Tab */}
        <TabsContent value="finance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Receipt className="h-4 w-4" />
                Invoice Settings
              </CardTitle>
              <CardDescription>Configure invoice numbering and defaults</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Invoice Prefix</Label>
                  <Input 
                    value={settingsForm.invoices?.invoice_prefix || "INV-"}
                    onChange={(e) => {
                      const updated = { ...settingsForm.invoices, invoice_prefix: e.target.value };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                    }}
                    onBlur={() => {
                      saveSettings("invoices", { invoice_prefix: settingsForm.invoices?.invoice_prefix });
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Estimate Prefix</Label>
                  <Input 
                    value={settingsForm.invoices?.estimate_prefix || "EST-"}
                    onChange={(e) => {
                      const updated = { ...settingsForm.invoices, estimate_prefix: e.target.value };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                    }}
                    onBlur={() => {
                      saveSettings("invoices", { estimate_prefix: settingsForm.invoices?.estimate_prefix });
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Sales Order Prefix</Label>
                  <Input 
                    value={settingsForm.invoices?.salesorder_prefix || "SO-"}
                    onChange={(e) => {
                      const updated = { ...settingsForm.invoices, salesorder_prefix: e.target.value };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                    }}
                    onBlur={() => {
                      saveSettings("invoices", { salesorder_prefix: settingsForm.invoices?.salesorder_prefix });
                    }}
                  />
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Default Payment Terms (days)</Label>
                  <Input 
                    type="number"
                    value={settingsForm.invoices?.default_payment_terms || 30}
                    onChange={(e) => {
                      const v = parseInt(e.target.value) || 30;
                      const updated = { ...settingsForm.invoices, default_payment_terms: v };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                    }}
                    onBlur={() => {
                      saveSettings("invoices", { default_payment_terms: settingsForm.invoices?.default_payment_terms });
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Default Tax Rate (%)</Label>
                  <Input 
                    type="number"
                    step="0.01"
                    value={settingsForm.invoices?.default_tax_rate || 18}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value) || 18;
                      const updated = { ...settingsForm.invoices, default_tax_rate: v };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                    }}
                    onBlur={() => {
                      saveSettings("invoices", { default_tax_rate: settingsForm.invoices?.default_tax_rate });
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>GST Enabled</Label>
                    <p className="text-xs text-muted-foreground">Apply GST to invoices</p>
                  </div>
                  <Switch 
                    checked={settingsForm.invoices?.gst_enabled ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.invoices, gst_enabled: v };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                      saveSettings("invoices", { gst_enabled: v });
                    }}
                  />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Auto-Numbering</Label>
                    <p className="text-xs text-muted-foreground">Auto-generate invoice numbers</p>
                  </div>
                  <Switch 
                    checked={settingsForm.invoices?.auto_number_enabled ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.invoices, auto_number_enabled: v };
                      setSettingsForm({ ...settingsForm, invoices: updated });
                      saveSettings("invoices", { auto_number_enabled: v });
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Bell className="h-4 w-4" />
                Notification Settings
              </CardTitle>
              <CardDescription>Configure notification channels and triggers</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Email Notifications</Label>
                  </div>
                  <Switch 
                    checked={settingsForm.notifications?.email_enabled ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.notifications, email_enabled: v };
                      setSettingsForm({ ...settingsForm, notifications: updated });
                      saveSettings("notifications", { email_enabled: v });
                    }}
                  />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>SMS Notifications</Label>
                  </div>
                  <Switch 
                    checked={settingsForm.notifications?.sms_enabled ?? false}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.notifications, sms_enabled: v };
                      setSettingsForm({ ...settingsForm, notifications: updated });
                      saveSettings("notifications", { sms_enabled: v });
                    }}
                  />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>WhatsApp Notifications</Label>
                  </div>
                  <Switch 
                    checked={settingsForm.notifications?.whatsapp_enabled ?? false}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.notifications, whatsapp_enabled: v };
                      setSettingsForm({ ...settingsForm, notifications: updated });
                      saveSettings("notifications", { whatsapp_enabled: v });
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Razorpay Payment Gateway Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <CreditCard className="h-4 w-4" />
                Payment Gateway (Razorpay)
                {razorpayConfigured && (
                  <Badge className="ml-2 bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Configured
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Connect your Razorpay account to accept online payments for invoices
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {razorpayConfigured ? (
                <>
                  <div className="p-4 bg-[rgba(34,197,94,0.08)] rounded-lg border border-green-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-5 w-5 text-green-400" />
                      <span className="font-medium text-green-400">Razorpay is connected</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Your customers can now pay invoices online via UPI, Cards, Net Banking, and Wallets.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <Badge variant="outline" className={razorpayConfig.test_mode ? "text-yellow-400" : "text-green-400"}>
                        {razorpayConfig.test_mode ? "Test Mode" : "Live Mode"}
                      </Badge>
                      <a 
                        href="https://dashboard.razorpay.com/" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Open Razorpay Dashboard
                      </a>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 rounded-lg border">
                    <div>
                      <Label>Test Mode</Label>
                      <p className="text-xs text-muted-foreground">Use test credentials for testing</p>
                    </div>
                    <Switch 
                      checked={razorpayConfig.test_mode}
                      onCheckedChange={(v) => {
                        setRazorpayConfig({ ...razorpayConfig, test_mode: v });
                      }}
                    />
                  </div>
                  
                  <Separator />
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setRazorpayConfigured(false)}
                    >
                      <Edit2 className="h-4 w-4 mr-2" />
                      Update Credentials
                    </Button>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={removeRazorpayConfig}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Disconnect
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div className="p-4 bg-[rgba(234,179,8,0.08)] rounded-lg border border-yellow-500/20 mb-4">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5" />
                      <div>
                        <span className="font-medium text-yellow-400">Payment gateway not configured</span>
                        <p className="text-sm text-muted-foreground mt-1">
                          To collect online payments, connect your Razorpay account. 
                          Get your API keys from{" "}
                          <a 
                            href="https://dashboard.razorpay.com/app/keys" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                          >
                            Razorpay Dashboard → Settings → API Keys
                          </a>
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Key ID *</Label>
                      <Input 
                        placeholder="rzp_test_REDACTED or rzp_live_REDACTED"
                        value={razorpayConfig.key_id}
                        onChange={(e) => setRazorpayConfig({ ...razorpayConfig, key_id: e.target.value })}
                        data-testid="razorpay-key-id-input"
                      />
                      <p className="text-xs text-muted-foreground">
                        Starts with <code className="bg-muted px-1 rounded">rzp_test_</code> or <code className="bg-muted px-1 rounded">rzp_live_</code>
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label>Key Secret *</Label>
                      <div className="relative">
                        <Input 
                          type={showSecrets ? "text" : "password"}
                          placeholder="Your Razorpay Key Secret"
                          value={razorpayConfig.key_secret}
                          onChange={(e) => setRazorpayConfig({ ...razorpayConfig, key_secret: e.target.value })}
                          data-testid="razorpay-key-secret-input"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="absolute right-1 top-1 h-7 w-7"
                          onClick={() => setShowSecrets(!showSecrets)}
                        >
                          {showSecrets ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Webhook Secret (Optional)</Label>
                    <Input 
                      type={showSecrets ? "text" : "password"}
                      placeholder="Webhook secret for verifying payment notifications"
                      value={razorpayConfig.webhook_secret}
                      onChange={(e) => setRazorpayConfig({ ...razorpayConfig, webhook_secret: e.target.value })}
                      data-testid="razorpay-webhook-secret-input"
                    />
                    <p className="text-xs text-muted-foreground">
                      Create a webhook at Razorpay Dashboard → Settings → Webhooks pointing to your callback URL
                    </p>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 rounded-lg border">
                    <div>
                      <Label>Test Mode</Label>
                      <p className="text-xs text-muted-foreground">Enable for testing with test credentials</p>
                    </div>
                    <Switch 
                      checked={razorpayConfig.test_mode}
                      onCheckedChange={(v) => setRazorpayConfig({ ...razorpayConfig, test_mode: v })}
                    />
                  </div>
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={saveRazorpayConfig}
                      disabled={savingRazorpay || !razorpayConfig.key_id || !razorpayConfig.key_secret}
                      data-testid="save-razorpay-btn"
                    >
                      {savingRazorpay ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4 mr-2" />
                      )}
                      Connect Razorpay
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* EFI Tab */}
        <TabsContent value="efi" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="h-4 w-4" />
                EV Failure Intelligence Settings
              </CardTitle>
              <CardDescription>Configure AI-powered diagnostics and learning</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Failure Learning</Label>
                    <p className="text-xs text-muted-foreground">Learn from resolved tickets</p>
                  </div>
                  <Switch 
                    checked={settingsForm.efi?.failure_learning_enabled ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.efi, failure_learning_enabled: v };
                      setSettingsForm({ ...settingsForm, efi: updated });
                      saveSettings("efi", { failure_learning_enabled: v });
                    }}
                  />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Auto-Suggest Diagnosis</Label>
                    <p className="text-xs text-muted-foreground">AI suggests diagnostic steps</p>
                  </div>
                  <Switch 
                    checked={settingsForm.efi?.auto_suggest_diagnosis ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.efi, auto_suggest_diagnosis: v };
                      setSettingsForm({ ...settingsForm, efi: updated });
                      saveSettings("efi", { auto_suggest_diagnosis: v });
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Minimum Confidence Threshold</Label>
                  <Input 
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={settingsForm.efi?.min_confidence_threshold || 0.7}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value) || 0.7;
                      const updated = { ...settingsForm.efi, min_confidence_threshold: v };
                      setSettingsForm({ ...settingsForm, efi: updated });
                    }}
                    onBlur={() => {
                      saveSettings("efi", { min_confidence_threshold: settingsForm.efi?.min_confidence_threshold });
                    }}
                  />
                  <p className="text-xs text-muted-foreground">Only show suggestions above this confidence level (0-1)</p>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label>Require Checklist Completion</Label>
                    <p className="text-xs text-muted-foreground">Force diagnostic checklist before resolution</p>
                  </div>
                  <Switch 
                    checked={settingsForm.efi?.require_checklist_completion ?? true}
                    onCheckedChange={(v) => {
                      const updated = { ...settingsForm.efi, require_checklist_completion: v };
                      setSettingsForm({ ...settingsForm, efi: updated });
                      saveSettings("efi", { require_checklist_completion: v });
                    }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border">
                <div>
                  <Label>Capture Diagnostic Photos</Label>
                  <p className="text-xs text-muted-foreground">Require photos during diagnostic process</p>
                </div>
                <Switch 
                  checked={settingsForm.efi?.capture_diagnostic_photos ?? true}
                  onCheckedChange={(v) => {
                    const updated = { ...settingsForm.efi, capture_diagnostic_photos: v };
                    setSettingsForm({ ...settingsForm, efi: updated });
                    saveSettings("efi", { capture_diagnostic_photos: v });
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
