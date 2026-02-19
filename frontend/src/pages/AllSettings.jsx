import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Search, Building2, Users, Receipt, Palette, Zap, Settings2, 
  Plug, Code, ChevronRight, Save, RefreshCw, FileText, Bell,
  Car, Ticket, Wrench, Package, UserCircle, CreditCard, Brain,
  Globe, Key, Webhook, ShieldCheck, MapPin, Percent, IndianRupee
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
  "#10B981": "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  "#3B82F6": "bg-blue-500/10 text-blue-500 border-blue-500/20",
  "#F59E0B": "bg-amber-500/10 text-amber-500 border-amber-500/20",
  "#8B5CF6": "bg-violet-500/10 text-violet-500 border-violet-500/20",
  "#EF4444": "bg-red-500/10 text-red-500 border-red-500/20",
  "#06B6D4": "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
  "#EC4899": "bg-pink-500/10 text-pink-500 border-pink-500/20",
  "#6366F1": "bg-indigo-500/10 text-indigo-500 border-indigo-500/20"
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
                {selectedItem && (
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
function SettingsPanel({ item, settings, onUpdate, onSave }) {
  switch (item.id) {
    case "profile":
      return <OrganizationProfilePanel settings={settings.organization || {}} onUpdate={(data) => onUpdate("organization", data)} />;
    case "branding":
      return <BrandingPanel settings={settings.branding || {}} onUpdate={(data) => onUpdate("branding", data)} />;
    case "locations":
      return <LocationsPanel settings={settings.locations || []} onUpdate={(data) => onUpdate("locations", data)} />;
    case "gst":
      return <GSTSettingsPanel settings={settings.gst || {}} onUpdate={(data) => onUpdate("gst", data)} />;
    case "tds":
      return <TDSSettingsPanel settings={settings.tds || {}} onUpdate={(data) => onUpdate("tds", data)} />;
    case "msme":
      return <MSMESettingsPanel settings={settings.msme || {}} onUpdate={(data) => onUpdate("msme", data)} />;
    case "vehicles":
      return <VehicleSettingsPanel settings={settings.vehicles || {}} onUpdate={(data) => onUpdate("vehicles", data)} />;
    case "tickets":
      return <TicketSettingsPanel settings={settings.tickets || {}} onUpdate={(data) => onUpdate("tickets", data)} />;
    case "inventory":
      return <InventorySettingsPanel settings={settings.inventory || {}} onUpdate={(data) => onUpdate("inventory", data)} />;
    case "billing":
      return <BillingSettingsPanel settings={settings.billing || {}} onUpdate={(data) => onUpdate("billing", data)} />;
    case "custom-fields":
      return <CustomFieldsPanel settings={settings.custom_fields || []} onUpdate={(data) => onUpdate("custom_fields", data)} />;
    case "workflows":
      return <WorkflowsPanel settings={settings.workflow_rules || []} onUpdate={(data) => onUpdate("workflow_rules", data)} />;
    default:
      return <ComingSoonPanel item={item} />;
  }
}

// Individual Settings Panels
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
      <div className="flex items-center gap-4 p-4 border rounded-lg bg-emerald-500/5">
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

function CustomFieldsPanel({ settings }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-medium">Custom Fields</h3>
        <Button size="sm"><FileText className="h-4 w-4 mr-2" />Add Field</Button>
      </div>
      <p className="text-sm text-muted-foreground">
        Create custom fields for Vehicles, Tickets, Work Orders, and other modules.
        Fields support text, numbers, dates, dropdowns, and more.
      </p>
      {settings.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
          No custom fields defined. Click "Add Field" to create your first custom field.
        </div>
      ) : (
        <div className="space-y-2">
          {settings.map((field, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <div className="font-medium">{field.label}</div>
                <div className="text-sm text-muted-foreground">{field.module} - {field.data_type}</div>
              </div>
              {field.is_required && <Badge variant="outline">Required</Badge>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WorkflowsPanel({ settings }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-medium">Workflow Rules</h3>
        <Button size="sm"><Zap className="h-4 w-4 mr-2" />Add Rule</Button>
      </div>
      <p className="text-sm text-muted-foreground">
        Automate actions based on triggers. Send emails, update fields, call webhooks, or run custom functions.
      </p>
      {settings.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
          No workflow rules defined. Click "Add Rule" to automate your operations.
        </div>
      ) : (
        <div className="space-y-2">
          {settings.map((rule, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <div className="font-medium">{rule.name}</div>
                <div className="text-sm text-muted-foreground">{rule.module} - {rule.trigger_type}</div>
              </div>
              <Badge variant={rule.is_active ? "default" : "secondary"}>
                {rule.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
          ))}
        </div>
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
