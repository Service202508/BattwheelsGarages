import { useState, useEffect, useRef } from "react";
import { API, getAuthHeaders } from "@/App";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Palette, 
  Image, 
  Type, 
  RotateCcw, 
  Save, 
  Eye,
  Upload,
  RefreshCw,
  Check,
  X,
  Sparkles
} from "lucide-react";
import { toast } from "sonner";

const DEFAULT_COLORS = {
  primary_color: "#10b981",
  secondary_color: "#059669",
  accent_color: "#f59e0b",
  text_color: "#111827",
  background_color: "#ffffff",
  sidebar_color: "#1e293b"
};

const COLOR_PRESETS = [
  { name: "Emerald (Default)", primary: "#10b981", secondary: "#059669", accent: "#f59e0b" },
  { name: "Blue Ocean", primary: "#3b82f6", secondary: "#2563eb", accent: "#f97316" },
  { name: "Purple Royal", primary: "#8b5cf6", secondary: "#7c3aed", accent: "#ec4899" },
  { name: "Rose Gold", primary: "#f43f5e", secondary: "#e11d48", accent: "#fbbf24" },
  { name: "Teal Fresh", primary: "#14b8a6", secondary: "#0d9488", accent: "#a855f7" },
  { name: "Indigo Pro", primary: "#6366f1", secondary: "#4f46e5", accent: "#22c55e" }
];

export default function BrandingSettings({ user }) {
  const [branding, setBranding] = useState({
    logo_url: "",
    logo_dark_url: "",
    favicon_url: "",
    primary_color: "#10b981",
    secondary_color: "#059669",
    accent_color: "#f59e0b",
    text_color: "#111827",
    background_color: "#ffffff",
    sidebar_color: "#1e293b",
    company_tagline: "",
    custom_css: "",
    email_footer: "",
    show_powered_by: true
  });
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalBranding, setOriginalBranding] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchBranding();
  }, []);

  useEffect(() => {
    if (originalBranding) {
      const changed = JSON.stringify(branding) !== JSON.stringify(originalBranding);
      setHasChanges(changed);
    }
  }, [branding, originalBranding]);

  const fetchBranding = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/organizations/me/branding`, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        const brandingData = data.branding || {};
        setBranding(prev => ({ ...prev, ...brandingData }));
        setOriginalBranding({ ...branding, ...brandingData });
        setOrgName(data.organization_name || "");
      }
    } catch (error) {
      console.error("Failed to fetch branding:", error);
      toast.error("Failed to load branding settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/organizations/me/branding`, {
        method: "PUT",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify(branding)
      });

      if (response.ok) {
        const data = await response.json();
        setOriginalBranding({ ...branding });
        setHasChanges(false);
        toast.success("Branding saved successfully!");
        
        // Apply branding to current page
        applyBranding(branding);
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save branding");
      }
    } catch (error) {
      toast.error("Failed to save branding");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("Reset all branding to defaults? This cannot be undone.")) return;
    
    try {
      const response = await fetch(`${API}/organizations/me/branding/reset`, {
        method: "POST",
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setBranding(data.branding);
        setOriginalBranding(data.branding);
        setHasChanges(false);
        toast.success("Branding reset to defaults");
        applyBranding(data.branding);
      }
    } catch (error) {
      toast.error("Failed to reset branding");
    }
  };

  const applyBranding = (b) => {
    const root = document.documentElement;
    root.style.setProperty('--brand-primary', b.primary_color);
    root.style.setProperty('--brand-secondary', b.secondary_color);
    root.style.setProperty('--brand-accent', b.accent_color);
  };

  const applyPreset = (preset) => {
    setBranding(prev => ({
      ...prev,
      primary_color: preset.primary,
      secondary_color: preset.secondary,
      accent_color: preset.accent
    }));
  };

  const handleColorChange = (field, value) => {
    setBranding(prev => ({ ...prev, [field]: value }));
  };

  const ColorInput = ({ label, field, description }) => (
    <div className="space-y-2">
      <Label htmlFor={field}>{label}</Label>
      <div className="flex gap-2">
        <div 
          className="w-12 h-10 rounded-md border cursor-pointer relative overflow-hidden"
          style={{ backgroundColor: branding[field] }}
        >
          <input
            type="color"
            value={branding[field]}
            onChange={(e) => handleColorChange(field, e.target.value)}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
        </div>
        <Input
          id={field}
          value={branding[field]}
          onChange={(e) => handleColorChange(field, e.target.value)}
          placeholder="#10b981"
          className="flex-1 font-mono"
        />
      </div>
      {description && <p className="text-xs text-gray-500">{description}</p>}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="branding-settings">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Brand Settings</h1>
          <p className="text-gray-500 mt-1">Customize your organization's appearance</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button onClick={handleSave} disabled={saving || !hasChanges}>
            {saving ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {hasChanges && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2 text-amber-800">
          <Sparkles className="h-4 w-4" />
          <span className="text-sm">You have unsaved changes</span>
        </div>
      )}

      <Tabs defaultValue="colors" className="space-y-4">
        <TabsList>
          <TabsTrigger value="colors">
            <Palette className="h-4 w-4 mr-2" />
            Colors
          </TabsTrigger>
          <TabsTrigger value="logos">
            <Image className="h-4 w-4 mr-2" />
            Logos
          </TabsTrigger>
          <TabsTrigger value="content">
            <Type className="h-4 w-4 mr-2" />
            Content
          </TabsTrigger>
          <TabsTrigger value="preview">
            <Eye className="h-4 w-4 mr-2" />
            Preview
          </TabsTrigger>
        </TabsList>

        {/* Colors Tab */}
        <TabsContent value="colors" className="space-y-6">
          {/* Presets */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Color Presets</CardTitle>
              <CardDescription>Quick-apply a color theme</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {COLOR_PRESETS.map((preset) => (
                  <button
                    key={preset.name}
                    onClick={() => applyPreset(preset)}
                    className="p-3 border rounded-lg hover:border-gray-400 transition-colors text-left"
                  >
                    <div className="flex gap-1 mb-2">
                      <div className="w-6 h-6 rounded" style={{ backgroundColor: preset.primary }} />
                      <div className="w-6 h-6 rounded" style={{ backgroundColor: preset.secondary }} />
                      <div className="w-6 h-6 rounded" style={{ backgroundColor: preset.accent }} />
                    </div>
                    <span className="text-xs font-medium">{preset.name}</span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Custom Colors */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Custom Colors</CardTitle>
              <CardDescription>Fine-tune your brand colors</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <ColorInput 
                  label="Primary Color" 
                  field="primary_color" 
                  description="Main brand color for buttons and accents"
                />
                <ColorInput 
                  label="Secondary Color" 
                  field="secondary_color" 
                  description="Secondary actions and hover states"
                />
                <ColorInput 
                  label="Accent Color" 
                  field="accent_color" 
                  description="Highlights and notifications"
                />
                <ColorInput 
                  label="Text Color" 
                  field="text_color" 
                  description="Primary text color"
                />
                <ColorInput 
                  label="Background Color" 
                  field="background_color" 
                  description="Page background"
                />
                <ColorInput 
                  label="Sidebar Color" 
                  field="sidebar_color" 
                  description="Navigation sidebar background"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logos Tab */}
        <TabsContent value="logos" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Logo Images</CardTitle>
              <CardDescription>Upload your organization's logos</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Main Logo */}
                <div className="space-y-3">
                  <Label>Main Logo (Light Background)</Label>
                  <div className="border-2 border-dashed rounded-lg p-6 text-center bg-white">
                    {branding.logo_url ? (
                      <div className="space-y-3">
                        <img 
                          src={branding.logo_url} 
                          alt="Logo" 
                          className="max-h-16 mx-auto object-contain"
                        />
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => setBranding(prev => ({ ...prev, logo_url: "" }))}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="h-8 w-8 mx-auto text-gray-400" />
                        <p className="text-sm text-gray-500">Paste image URL below</p>
                      </div>
                    )}
                  </div>
                  <Input
                    placeholder="https://example.com/logo.png"
                    value={branding.logo_url || ""}
                    onChange={(e) => setBranding(prev => ({ ...prev, logo_url: e.target.value }))}
                  />
                </div>

                {/* Dark Logo */}
                <div className="space-y-3">
                  <Label>Logo for Dark Background</Label>
                  <div className="border-2 border-dashed rounded-lg p-6 text-center bg-gray-900">
                    {branding.logo_dark_url ? (
                      <div className="space-y-3">
                        <img 
                          src={branding.logo_dark_url} 
                          alt="Logo Dark" 
                          className="max-h-16 mx-auto object-contain"
                        />
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-white hover:text-gray-200"
                          onClick={() => setBranding(prev => ({ ...prev, logo_dark_url: "" }))}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="h-8 w-8 mx-auto text-gray-500" />
                        <p className="text-sm text-gray-400">Paste image URL below</p>
                      </div>
                    )}
                  </div>
                  <Input
                    placeholder="https://example.com/logo-white.png"
                    value={branding.logo_dark_url || ""}
                    onChange={(e) => setBranding(prev => ({ ...prev, logo_dark_url: e.target.value }))}
                  />
                </div>
              </div>

              {/* Favicon */}
              <div className="space-y-3">
                <Label>Favicon</Label>
                <div className="flex gap-4 items-center">
                  <div className="w-12 h-12 border rounded-lg flex items-center justify-center bg-gray-50">
                    {branding.favicon_url ? (
                      <img src={branding.favicon_url} alt="Favicon" className="w-8 h-8 object-contain" />
                    ) : (
                      <Image className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <Input
                    placeholder="https://example.com/favicon.ico"
                    value={branding.favicon_url || ""}
                    onChange={(e) => setBranding(prev => ({ ...prev, favicon_url: e.target.value }))}
                    className="flex-1"
                  />
                </div>
                <p className="text-xs text-gray-500">Recommended: 32x32 or 64x64 pixels, .ico or .png format</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Brand Content</CardTitle>
              <CardDescription>Customize text and messaging</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="tagline">Company Tagline</Label>
                <Input
                  id="tagline"
                  placeholder="Your trusted EV service partner"
                  value={branding.company_tagline || ""}
                  onChange={(e) => setBranding(prev => ({ ...prev, company_tagline: e.target.value }))}
                />
                <p className="text-xs text-gray-500">Displayed below your logo in some areas</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email_footer">Email Footer</Label>
                <Textarea
                  id="email_footer"
                  placeholder="123 Main Street, City&#10;Phone: +91 12345 67890"
                  value={branding.email_footer || ""}
                  onChange={(e) => setBranding(prev => ({ ...prev, email_footer: e.target.value }))}
                  rows={3}
                />
                <p className="text-xs text-gray-500">Appears at the bottom of automated emails</p>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <Label>Show "Powered by Battwheels"</Label>
                  <p className="text-sm text-gray-500">Display our branding in your portal</p>
                </div>
                <Switch
                  checked={branding.show_powered_by}
                  onCheckedChange={(checked) => setBranding(prev => ({ ...prev, show_powered_by: checked }))}
                />
              </div>
            </CardContent>
          </Card>

          {/* Advanced */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Advanced</CardTitle>
              <CardDescription>For power users only</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="custom_css">Custom CSS</Label>
                <Textarea
                  id="custom_css"
                  placeholder=".my-class { color: red; }"
                  value={branding.custom_css || ""}
                  onChange={(e) => setBranding(prev => ({ ...prev, custom_css: e.target.value }))}
                  rows={5}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500">
                  Add custom CSS to override styles. Use with caution - may break layouts.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Live Preview</CardTitle>
              <CardDescription>See how your branding looks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg overflow-hidden">
                {/* Mock Header */}
                <div 
                  className="p-4 flex items-center gap-4"
                  style={{ backgroundColor: branding.sidebar_color }}
                >
                  {branding.logo_dark_url ? (
                    <img src={branding.logo_dark_url} alt="Logo" className="h-8 object-contain" />
                  ) : (
                    <div className="h-8 w-24 bg-gray-700 rounded flex items-center justify-center text-gray-400 text-xs">
                      Logo
                    </div>
                  )}
                  {branding.company_tagline && (
                    <span className="text-gray-400 text-sm">{branding.company_tagline}</span>
                  )}
                </div>

                {/* Mock Content */}
                <div 
                  className="p-6 space-y-4"
                  style={{ backgroundColor: branding.background_color }}
                >
                  <h2 style={{ color: branding.text_color }} className="text-xl font-semibold">
                    Welcome to {orgName || "Your Organization"}
                  </h2>
                  <p style={{ color: branding.text_color }} className="opacity-70">
                    This is a preview of how your branding will look throughout the application.
                  </p>
                  <div className="flex gap-3">
                    <button
                      className="px-4 py-2 rounded-lg text-white font-medium"
                      style={{ backgroundColor: branding.primary_color }}
                    >
                      Primary Button
                    </button>
                    <button
                      className="px-4 py-2 rounded-lg text-white font-medium"
                      style={{ backgroundColor: branding.secondary_color }}
                    >
                      Secondary
                    </button>
                    <button
                      className="px-4 py-2 rounded-lg text-white font-medium"
                      style={{ backgroundColor: branding.accent_color }}
                    >
                      Accent
                    </button>
                  </div>
                  <div 
                    className="p-3 rounded-lg border-l-4"
                    style={{ borderColor: branding.accent_color, backgroundColor: `${branding.accent_color}15` }}
                  >
                    <p className="text-sm" style={{ color: branding.text_color }}>
                      This is an accent notification using your brand colors.
                    </p>
                  </div>
                </div>

                {/* Mock Footer */}
                {branding.show_powered_by && (
                  <div className="p-3 text-center text-xs text-gray-400 border-t">
                    Powered by Battwheels OS
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
