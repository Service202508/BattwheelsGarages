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
  CreditCard, Eye, EyeOff, Link2, ExternalLink, FileCheck, Info,
  Image, X, BarChart2
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
  viewer: "bg-[rgba(17,24,32,0.2)] text-[rgba(244,246,240,0.45)] border-[rgba(255,255,255,0.07)]",
};

// Status badge colors
const statusBadgeColors = {
  active: "bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30",
  invited: "bg-[rgba(234,179,8,0.20)] text-yellow-400 border-yellow-500/30",
  suspended: "bg-[rgba(255,59,47,0.20)] text-red-400 border-red-500/30",
  deactivated: "bg-[rgba(17,24,32,0.2)] text-[rgba(244,246,240,0.45)] border-[rgba(255,255,255,0.07)]",
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

  // E-Invoice state
  const [einvoiceConfig, setEinvoiceConfig] = useState({
    gstin: "",
    legal_name: "",
    irp_username: "",
    irp_password: "",
    client_id: "",
    client_secret: "",
    is_sandbox: true,
    enabled: false,
    turnover_threshold_met: false
  });
  const [einvoiceConfigured, setEinvoiceConfigured] = useState(false);
  const [einvoiceEnabled, setEinvoiceEnabled] = useState(false);
  const [showEinvoiceSecrets, setShowEinvoiceSecrets] = useState(false);
  const [savingEinvoice, setSavingEinvoice] = useState(false);
  const [testingEinvoice, setTestingEinvoice] = useState(false);
  const [einvoiceTestResult, setEinvoiceTestResult] = useState(null);
  const [gstinValid, setGstinValid] = useState(null);

  // SLA config state
  const DEFAULT_SLA_TIERS = {
    CRITICAL: { response_hours: 1, resolution_hours: 4 },
    HIGH: { response_hours: 4, resolution_hours: 8 },
    MEDIUM: { response_hours: 8, resolution_hours: 24 },
    LOW: { response_hours: 24, resolution_hours: 72 },
  };
  const [slaConfig, setSlaConfig] = useState({
    ...DEFAULT_SLA_TIERS,
    auto_reassign_on_breach: false,
    reassignment_delay_minutes: 30,
  });
  const [savingSla, setSavingSla] = useState(false);

  // Logo upload state
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoPreview, setLogoPreview] = useState(null);

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
      const [orgRes, settingsRes, membersRes, rolesRes, razorpayRes, einvoiceRes, slaRes] = await Promise.all([
        fetch(`${API}/org`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/settings`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/users`, { headers: getAuthHeaders() }),
        fetch(`${API}/org/roles`, { headers: getAuthHeaders() }),
        fetch(`${API}/payments/config`, { headers: getAuthHeaders() }),
        fetch(`${API}/einvoice/config`, { headers: getAuthHeaders() }),
        fetch(`${API}/sla/config`, { headers: getAuthHeaders() }),
      ]);

      let orgData = null;
      if (orgRes.ok) {
        orgData = await orgRes.json();
        setOrganization(orgData);
        setOrgForm(orgData);
        // Set logo preview immediately
        if (orgData.logo_url) {
          setLogoPreview(orgData.logo_url);
        }
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
      
      if (einvoiceRes.ok) {
        const eiData = await einvoiceRes.json();
        setEinvoiceConfigured(eiData.configured || false);
        setEinvoiceEnabled(eiData.enabled || false);
        if (eiData.configured) {
          setEinvoiceConfig(prev => ({
            ...prev,
            gstin: eiData.gstin || "",
            irp_username: eiData.irp_username || "",
            client_id: eiData.client_id || "",
            is_sandbox: eiData.is_sandbox ?? true,
            enabled: eiData.enabled || false,
            turnover_threshold_met: eiData.turnover_threshold_met || false
          }));
          if (eiData.gstin) setGstinValid(true);
        }
      }

      if (slaRes && slaRes.ok) {
        const slaData = await slaRes.json();
        if (slaData.sla_config) {
          setSlaConfig(prev => ({ ...prev, ...slaData.sla_config }));
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

  // E-Invoice GSTIN validation
  const validateGstin = (gstin) => {
    if (!gstin || gstin.length !== 15) return false;
    const pattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return pattern.test(gstin.toUpperCase());
  };

  const handleGstinChange = (value) => {
    const upperValue = value.toUpperCase();
    setEinvoiceConfig(prev => ({ ...prev, gstin: upperValue }));
    if (upperValue.length === 15) {
      setGstinValid(validateGstin(upperValue));
    } else {
      setGstinValid(null);
    }
  };

  // Save E-Invoice configuration
  const saveEinvoiceConfig = async () => {
    if (!einvoiceConfig.gstin || !validateGstin(einvoiceConfig.gstin)) {
      toast.error("Please enter a valid 15-character GSTIN");
      return;
    }
    if (!einvoiceConfig.irp_username || !einvoiceConfig.irp_password) {
      toast.error("IRP Username and Password are required");
      return;
    }
    if (!einvoiceConfig.client_id || !einvoiceConfig.client_secret) {
      toast.error("Client ID and Client Secret are required");
      return;
    }
    
    setSavingEinvoice(true);
    try {
      const res = await fetch(`${API}/einvoice/config`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          ...einvoiceConfig,
          enabled: einvoiceEnabled
        }),
      });
      
      if (res.ok) {
        toast.success("E-Invoice configuration saved successfully!");
        setEinvoiceConfigured(true);
        // Clear sensitive data from state after save
        setEinvoiceConfig(prev => ({
          ...prev,
          irp_password: "",
          client_secret: ""
        }));
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to save E-Invoice configuration");
      }
    } catch (error) {
      toast.error("Failed to save E-Invoice configuration");
    } finally {
      setSavingEinvoice(false);
    }
  };

  // Test E-Invoice IRP connection
  const testEinvoiceConnection = async () => {
    setTestingEinvoice(true);
    setEinvoiceTestResult(null);
    try {
      const res = await fetch(`${API}/einvoice/eligibility`, { headers: getAuthHeaders() });
      const data = await res.json();
      
      if (data.eligible) {
        setEinvoiceTestResult({ success: true, message: "Connected to IRP successfully" });
      } else if (data.configured) {
        setEinvoiceTestResult({ success: false, message: data.reason || "Connection test failed" });
      } else {
        setEinvoiceTestResult({ success: false, message: "E-Invoice not configured. Save settings first." });
      }
    } catch (error) {
      setEinvoiceTestResult({ success: false, message: "Connection test failed: Network error" });
    } finally {
      setTestingEinvoice(false);
    }
  };

  // Remove E-Invoice configuration
  const removeEinvoiceConfig = async () => {
    if (!confirm("Are you sure you want to remove E-Invoice configuration? IRN generation will be disabled.")) {
      return;
    }
    
    try {
      const res = await fetch(`${API}/einvoice/config`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      
      if (res.ok) {
        toast.success("E-Invoice configuration removed");
        setEinvoiceConfigured(false);
        setEinvoiceEnabled(false);
        setEinvoiceConfig({
          gstin: "",
          legal_name: "",
          irp_username: "",
          irp_password: "",
          client_id: "",
          client_secret: "",
          is_sandbox: true,
          enabled: false,
          turnover_threshold_met: false
        });
        setGstinValid(null);
        setEinvoiceTestResult(null);
      } else {
        toast.error("Failed to remove E-Invoice configuration");
      }
    } catch (error) {
      toast.error("Failed to remove E-Invoice configuration");
    }
  };

  // Save SLA configuration
  const saveSlaConfig = async () => {
    setSavingSla(true);
    try {
      const res = await fetch(`${API}/sla/config`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(slaConfig),
      });
      if (res.ok) {
        toast.success("SLA configuration saved");
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to save SLA config");
      }
    } catch {
      toast.error("Failed to save SLA config");
    } finally {
      setSavingSla(false);
    }
  };

  // Handle logo upload
  const handleLogoUpload = async (file) => {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      toast.error("Logo must be under 2MB");
      return;
    }
    setLogoUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("logo_type", "main");
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/uploads/logo`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        const logoUrl = data.file_url || data.logo_url;
        setLogoPreview(logoUrl);
        setOrganization(prev => ({ ...prev, logo_url: logoUrl }));
        toast.success("Logo uploaded successfully");
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Failed to upload logo");
      }
    } catch {
      toast.error("Failed to upload logo");
    } finally {
      setLogoUploading(false);
    }
  };

  // Remove logo
  const handleLogoRemove = async () => {
    try {
      const res = await fetch(`${API}/uploads/logo/main`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        setLogoPreview(null);
        setOrganization(prev => ({ ...prev, logo_url: null }));
        toast.success("Logo removed");
      }
    } catch {
      toast.error("Failed to remove logo");
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

          {/* Logo Upload Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Image className="h-4 w-4" />
                Organization Logo
              </CardTitle>
              <CardDescription>Used in email communications and documents. PNG, JPG, or SVG. Max 2MB. Recommended: 200×60px.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-6">
                {/* Preview */}
                <div className="w-48 h-16 rounded border border-white/10 bg-black/30 flex items-center justify-center overflow-hidden flex-shrink-0">
                  {logoPreview ? (
                    <img src={logoPreview} alt="Logo" className="max-h-12 max-w-full object-contain" />
                  ) : (
                    <span className="text-xs text-muted-foreground">No logo</span>
                  )}
                </div>
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">How your logo appears in emails</p>
                  <div className="flex gap-2">
                    <label htmlFor="logo-upload-input">
                      <Button variant="outline" size="sm" asChild disabled={logoUploading}>
                        <span className="cursor-pointer">
                          {logoUploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
                          Upload Logo
                        </span>
                      </Button>
                    </label>
                    <input
                      id="logo-upload-input"
                      type="file"
                      accept="image/png,image/jpeg,image/svg+xml"
                      className="hidden"
                      onChange={(e) => handleLogoUpload(e.target.files?.[0])}
                    />
                    {logoPreview && (
                      <Button variant="ghost" size="sm" onClick={handleLogoRemove} className="text-red-400 hover:text-red-300">
                        <X className="h-4 w-4 mr-1" />
                        Remove
                      </Button>
                    )}
                  </div>
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

          {/* SLA Configuration Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart2 className="h-4 w-4" />
                SLA Configuration
              </CardTitle>
              <CardDescription>Define response and resolution SLA targets per ticket priority</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Tiers Table */}
              <div>
                <div className="grid grid-cols-3 gap-2 mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  <span>Priority</span>
                  <span>Response (hrs)</span>
                  <span>Resolution (hrs)</span>
                </div>
                {[
                  { key: "CRITICAL", label: "Critical", color: "text-red-400" },
                  { key: "HIGH", label: "High", color: "text-orange-400" },
                  { key: "MEDIUM", label: "Medium", color: "text-yellow-400" },
                  { key: "LOW", label: "Low", color: "text-green-400" },
                ].map(({ key, label, color }) => (
                  <div key={key} className="grid grid-cols-3 gap-2 mb-2 items-center">
                    <span className={`text-sm font-medium ${color}`}>{label}</span>
                    <Input
                      type="number"
                      min="0.5"
                      step="0.5"
                      value={slaConfig[key]?.response_hours ?? ""}
                      onChange={(e) => setSlaConfig(prev => ({
                        ...prev,
                        [key]: { ...(prev[key] || {}), response_hours: parseFloat(e.target.value) || 0 }
                      }))}
                      className="h-8 text-sm"
                      data-testid={`sla-response-${key.toLowerCase()}`}
                    />
                    <Input
                      type="number"
                      min="0.5"
                      step="0.5"
                      value={slaConfig[key]?.resolution_hours ?? ""}
                      onChange={(e) => setSlaConfig(prev => ({
                        ...prev,
                        [key]: { ...(prev[key] || {}), resolution_hours: parseFloat(e.target.value) || 0 }
                      }))}
                      className="h-8 text-sm"
                      data-testid={`sla-resolution-${key.toLowerCase()}`}
                    />
                  </div>
                ))}
              </div>

              <Separator />

              {/* Auto-reassignment toggle */}
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <Label className="font-medium">Auto-reassign on SLA breach</Label>
                    <p className="text-xs text-muted-foreground">Automatically move tickets to the least-busy technician after breach</p>
                  </div>
                  <Switch
                    checked={slaConfig.auto_reassign_on_breach ?? false}
                    onCheckedChange={(v) => setSlaConfig(prev => ({ ...prev, auto_reassign_on_breach: v }))}
                    data-testid="sla-auto-reassign-toggle"
                  />
                </div>

                {slaConfig.auto_reassign_on_breach && (
                  <>
                    {/* Warning banner */}
                    <div style={{ background: "rgba(234,179,8,0.08)", borderLeft: "3px solid #EAB308" }} className="p-3 rounded-r-lg">
                      <p className="text-xs text-yellow-300">
                        <strong>Warning:</strong> Auto-reassignment will move tickets without manual approval. Ensure all technicians are properly onboarded before enabling this feature.
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Label className="text-sm whitespace-nowrap">Reassign after</Label>
                      <Input
                        type="number"
                        min="5"
                        step="5"
                        value={slaConfig.reassignment_delay_minutes ?? 30}
                        onChange={(e) => setSlaConfig(prev => ({ ...prev, reassignment_delay_minutes: parseInt(e.target.value) || 30 }))}
                        className="w-24 h-8 text-sm"
                        data-testid="sla-reassign-delay-input"
                      />
                      <Label className="text-sm text-muted-foreground">minutes past breach</Label>
                    </div>
                  </>
                )}
              </div>

              <Button onClick={saveSlaConfig} disabled={savingSla} size="sm" data-testid="save-sla-config-btn">
                {savingSla ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                Save SLA Configuration
              </Button>
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
          
          {/* E-Invoice (IRN) Settings Card */}
          <Card className="bg-[#111820] border-[rgba(255,255,255,0.07)]">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileCheck className="h-4 w-4 text-[#C8FF00]" />
                    E-Invoice (IRN) Settings
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Mandatory for GST-registered businesses above ₹5 Crore annual turnover
                  </CardDescription>
                </div>
                {/* Status Badge */}
                {einvoiceConfigured && einvoiceEnabled ? (
                  <Badge className="bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30">
                    ACTIVE
                  </Badge>
                ) : einvoiceConfigured ? (
                  <Badge className="bg-[rgba(128,128,128,0.20)] text-[rgba(244,246,240,0.45)] border-[rgba(255,255,255,0.15)]">
                    DISABLED
                  </Badge>
                ) : (
                  <Badge className="bg-[rgba(234,179,8,0.20)] text-yellow-400 border-yellow-500/30">
                    NOT CONFIGURED
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Enable/Disable Toggle */}
              <div className="flex items-center justify-between p-4 rounded-lg border border-[rgba(255,255,255,0.07)] bg-[rgba(200,255,0,0.02)]">
                <div>
                  <Label className="text-sm font-medium">Enable E-Invoice Generation</Label>
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">
                    When enabled, finalized B2B invoices will require IRN registration before they can be sent to customers
                  </p>
                </div>
                <Switch 
                  checked={einvoiceEnabled}
                  onCheckedChange={setEinvoiceEnabled}
                  className="data-[state=checked]:bg-[#C8FF00]"
                  data-testid="einvoice-enable-toggle"
                />
              </div>
              
              {/* Credentials Form - shown when enabled */}
              {einvoiceEnabled && (
                <>
                  <Separator className="bg-[rgba(255,255,255,0.07)]" />
                  
                  {/* Row 1: GSTIN and Legal Name */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                        GSTIN *
                      </Label>
                      <div className="relative">
                        <Input 
                          placeholder="22AAAAA0000A1Z5"
                          value={einvoiceConfig.gstin}
                          onChange={(e) => handleGstinChange(e.target.value)}
                          maxLength={15}
                          className="bg-[#111820] border-[rgba(255,255,255,0.13)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)] font-mono uppercase"
                          data-testid="einvoice-gstin-input"
                        />
                        {gstinValid !== null && (
                          <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            {gstinValid ? (
                              <CheckCircle className="h-4 w-4 text-green-400" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-red-400" />
                            )}
                          </div>
                        )}
                      </div>
                      {gstinValid === false && (
                        <p className="text-xs text-red-400">Invalid GSTIN format</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                        Legal Business Name
                      </Label>
                      <Input 
                        placeholder="As registered on GST portal"
                        value={einvoiceConfig.legal_name}
                        onChange={(e) => setEinvoiceConfig({ ...einvoiceConfig, legal_name: e.target.value })}
                        className="bg-[#111820] border-[rgba(255,255,255,0.13)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)]"
                      />
                    </div>
                  </div>
                  
                  {/* Row 2: IRP Username and Password */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                        IRP Username *
                      </Label>
                      <Input 
                        placeholder="Your IRP portal username"
                        value={einvoiceConfig.irp_username}
                        onChange={(e) => setEinvoiceConfig({ ...einvoiceConfig, irp_username: e.target.value })}
                        className="bg-[#111820] border-[rgba(255,255,255,0.13)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)]"
                        data-testid="einvoice-username-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                        IRP Password *
                      </Label>
                      <div className="relative">
                        <Input 
                          type={showEinvoiceSecrets ? "text" : "password"}
                          placeholder="Your IRP portal password"
                          value={einvoiceConfig.irp_password}
                          onChange={(e) => setEinvoiceConfig({ ...einvoiceConfig, irp_password: e.target.value })}
                          className="bg-[#111820] border-[rgba(255,255,255,0.13)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)] pr-10"
                          data-testid="einvoice-password-input"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="absolute right-1 top-1 h-7 w-7 text-[rgba(244,246,240,0.45)]"
                          onClick={() => setShowEinvoiceSecrets(!showEinvoiceSecrets)}
                        >
                          {showEinvoiceSecrets ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Row 3: Client ID and Secret */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                        Client ID *
                      </Label>
                      <Input 
                        placeholder="IRP API Client ID"
                        value={einvoiceConfig.client_id}
                        onChange={(e) => setEinvoiceConfig({ ...einvoiceConfig, client_id: e.target.value })}
                        className="bg-[#111820] border-[rgba(255,255,255,0.13)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)] font-mono"
                        data-testid="einvoice-client-id-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                        Client Secret *
                      </Label>
                      <div className="relative">
                        <Input 
                          type={showEinvoiceSecrets ? "text" : "password"}
                          placeholder="IRP API Client Secret"
                          value={einvoiceConfig.client_secret}
                          onChange={(e) => setEinvoiceConfig({ ...einvoiceConfig, client_secret: e.target.value })}
                          className="bg-[#111820] border-[rgba(255,255,255,0.13)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)] pr-10 font-mono"
                          data-testid="einvoice-client-secret-input"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="absolute right-1 top-1 h-7 w-7 text-[rgba(244,246,240,0.45)]"
                          onClick={() => setShowEinvoiceSecrets(!showEinvoiceSecrets)}
                        >
                          {showEinvoiceSecrets ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Row 4: Environment Selector */}
                  <div className="space-y-3">
                    <Label className="text-[10px] uppercase tracking-wider text-[rgba(244,246,240,0.45)] font-mono">
                      Environment
                    </Label>
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => setEinvoiceConfig({ ...einvoiceConfig, is_sandbox: true })}
                        className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                          einvoiceConfig.is_sandbox 
                            ? "bg-[rgba(234,179,8,0.10)] text-[#EAB308] border border-[rgba(234,179,8,0.25)]" 
                            : "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.45)] border border-[rgba(255,255,255,0.10)]"
                        }`}
                        data-testid="einvoice-sandbox-btn"
                      >
                        SANDBOX
                      </button>
                      <button
                        type="button"
                        onClick={() => setEinvoiceConfig({ ...einvoiceConfig, is_sandbox: false })}
                        className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                          !einvoiceConfig.is_sandbox 
                            ? "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]" 
                            : "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.45)] border border-[rgba(255,255,255,0.10)]"
                        }`}
                        data-testid="einvoice-production-btn"
                      >
                        PRODUCTION
                      </button>
                    </div>
                    
                    {/* Production Warning */}
                    {!einvoiceConfig.is_sandbox && (
                      <div className="p-3 bg-[rgba(255,59,47,0.08)] border border-[rgba(255,59,47,0.20)] border-l-[3px] border-l-[#FF3B2F] rounded">
                        <p className="text-sm text-[rgba(244,246,240,0.70)] flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-[#FF3B2F] mt-0.5 flex-shrink-0" />
                          <span>
                            Production mode will submit real IRNs to the government IRP. Ensure all credentials are correct before enabling.
                          </span>
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <Separator className="bg-[rgba(255,255,255,0.07)]" />
                  
                  {/* Connection Test Button */}
                  <div className="space-y-3">
                    <Button 
                      variant="ghost"
                      onClick={testEinvoiceConnection}
                      disabled={testingEinvoice || !einvoiceConfigured}
                      className="text-[rgba(244,246,240,0.65)] hover:text-[#F4F6F0] hover:bg-[rgba(255,255,255,0.05)]"
                      data-testid="test-einvoice-btn"
                    >
                      {testingEinvoice ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4 mr-2" />
                      )}
                      Test IRP Connection
                    </Button>
                    
                    {/* Test Result */}
                    {einvoiceTestResult && (
                      <div className={`p-3 rounded border ${
                        einvoiceTestResult.success 
                          ? "bg-[rgba(34,197,94,0.08)] border-[rgba(34,197,94,0.25)]" 
                          : "bg-[rgba(255,59,47,0.08)] border-[rgba(255,59,47,0.25)]"
                      }`}>
                        <p className={`text-sm flex items-center gap-2 ${
                          einvoiceTestResult.success ? "text-[#22C55E]" : "text-[#FF3B2F]"
                        }`}>
                          {einvoiceTestResult.success ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <AlertTriangle className="h-4 w-4" />
                          )}
                          {einvoiceTestResult.success ? "✓ " : "✗ "}{einvoiceTestResult.message}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* Save Button */}
                  <div className="flex gap-3">
                    <Button 
                      onClick={saveEinvoiceConfig}
                      disabled={savingEinvoice || gstinValid === false}
                      className="bg-[#C8FF00] hover:bg-[#a8d900] text-[#080C0F]"
                      data-testid="save-einvoice-btn"
                    >
                      {savingEinvoice ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4 mr-2" />
                      )}
                      Save E-Invoice Settings
                    </Button>
                    
                    {einvoiceConfigured && (
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={removeEinvoiceConfig}
                        className="bg-[rgba(255,59,47,0.15)] hover:bg-[rgba(255,59,47,0.25)] text-[#FF3B2F] border-none"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Remove Configuration
                      </Button>
                    )}
                  </div>
                </>
              )}
              
              {/* E-Invoice Applicability Info Card */}
              <div className="p-4 bg-[rgba(200,255,0,0.04)] border border-[rgba(200,255,0,0.12)] border-l-[3px] border-l-[rgba(200,255,0,0.30)] rounded">
                <div className="flex items-start gap-3">
                  <Info className="h-5 w-5 text-[#C8FF00] mt-0.5 flex-shrink-0" />
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-[#C8FF00] font-mono">E-Invoice Applicability</h4>
                    <p className="text-xs text-[rgba(244,246,240,0.65)] leading-relaxed">
                      E-invoicing is mandatory under GST for businesses with aggregate annual turnover exceeding ₹5 Crore (as per CBIC notification). Invoices issued without IRN to eligible businesses are not valid GST invoices.
                    </p>
                    <div className="grid grid-cols-2 gap-4 pt-2 text-xs">
                      <div>
                        <span className="text-[rgba(244,246,240,0.45)]">Applicable from:</span>
                        <p className="text-[#F4F6F0] font-medium mt-0.5">₹5 Crore turnover</p>
                      </div>
                      <div>
                        <span className="text-[rgba(244,246,240,0.45)]">Penalty for non-compliance:</span>
                        <p className="text-[#FF3B2F] font-medium mt-0.5">Invoice invalid + ITC denial to buyer</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
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
