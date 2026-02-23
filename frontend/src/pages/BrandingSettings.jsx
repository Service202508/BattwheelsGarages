import { useState, useEffect, useRef, useCallback } from "react";
import { API, getAuthHeaders } from "@/App";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
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
  Sparkles,
  AlertCircle,
  Trash2,
  Info
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

const ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "bmp"];
const MAX_FILE_SIZE = 1 * 1024 * 1024; // 1MB

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
  const [uploadProgress, setUploadProgress] = useState({});
  const [dragOver, setDragOver] = useState({});
  
  const mainLogoRef = useRef(null);
  const darkLogoRef = useRef(null);
  const faviconRef = useRef(null);

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
        setOriginalBranding({ ...branding });
        setHasChanges(false);
        toast.success("Branding saved successfully!");
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

  const validateFile = (file) => {
    // Check extension
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      toast.error(`Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return false;
    }
    
    // Check size
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`File too large. Maximum size: 1MB`);
      return false;
    }
    
    return true;
  };

  const uploadLogo = async (file, logoType) => {
    if (!validateFile(file)) return;
    
    setUploadProgress(prev => ({ ...prev, [logoType]: 0 }));
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => ({
          ...prev,
          [logoType]: Math.min((prev[logoType] || 0) + 10, 90)
        }));
      }, 100);
      
      const response = await fetch(`${API}/uploads/logo?logo_type=${logoType}`, {
        method: "POST",
        headers: {
          "Authorization": getAuthHeaders()["Authorization"],
          "X-Organization-ID": getAuthHeaders()["X-Organization-ID"]
        },
        body: formData
      });
      
      clearInterval(progressInterval);
      setUploadProgress(prev => ({ ...prev, [logoType]: 100 }));
      
      if (response.ok) {
        const data = await response.json();
        
        // Update branding state with new URL
        const fieldMap = {
          main: "logo_url",
          dark: "logo_dark_url",
          favicon: "favicon_url"
        };
        
        setBranding(prev => ({
          ...prev,
          [fieldMap[logoType]]: data.file_url
        }));
        
        toast.success(`${logoType === 'main' ? 'Logo' : logoType === 'dark' ? 'Dark logo' : 'Favicon'} uploaded!`);
        
        // Show dimensions info
        if (data.dimensions) {
          const { width, height } = data.dimensions;
          if (width !== 240 || height !== 240) {
            toast.info(`Image dimensions: ${width}x${height}px. Recommended: 240x240px`);
          }
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || "Upload failed");
      }
    } catch (error) {
      toast.error("Upload failed");
    } finally {
      setTimeout(() => {
        setUploadProgress(prev => ({ ...prev, [logoType]: undefined }));
      }, 1000);
    }
  };

  const deleteLogo = async (logoType) => {
    if (!confirm(`Delete ${logoType} logo?`)) return;
    
    try {
      const response = await fetch(`${API}/uploads/logo/${logoType}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const fieldMap = {
          main: "logo_url",
          dark: "logo_dark_url",
          favicon: "favicon_url"
        };
        
        setBranding(prev => ({
          ...prev,
          [fieldMap[logoType]]: ""
        }));
        
        toast.success("Logo deleted");
      }
    } catch (error) {
      toast.error("Failed to delete logo");
    }
  };

  const handleDrop = useCallback((e, logoType) => {
    e.preventDefault();
    setDragOver(prev => ({ ...prev, [logoType]: false }));
    
    const file = e.dataTransfer.files[0];
    if (file) {
      uploadLogo(file, logoType);
    }
  }, []);

  const handleDragOver = useCallback((e, logoType) => {
    e.preventDefault();
    setDragOver(prev => ({ ...prev, [logoType]: true }));
  }, []);

  const handleDragLeave = useCallback((e, logoType) => {
    e.preventDefault();
    setDragOver(prev => ({ ...prev, [logoType]: false }));
  }, []);

  const handleFileSelect = (e, logoType) => {
    const file = e.target.files[0];
    if (file) {
      uploadLogo(file, logoType);
    }
    e.target.value = ""; // Reset input
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
      {description && <p className="text-xs text-[rgba(244,246,240,0.45)]">{description}</p>}
    </div>
  );

  const LogoUploader = ({ logoType, label, description, bgColor = "white", currentUrl, inputRef }) => {
    const isUploading = uploadProgress[logoType] !== undefined;
    const isDragging = dragOver[logoType];
    
    return (
      <div className="space-y-3">
        <Label>{label}</Label>
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-all ${
            isDragging ? "border-[rgba(200,255,0,0.50)] bg-[rgba(200,255,0,0.08)]" : "border-[rgba(255,255,255,0.07)]"
          }`}
          style={{ backgroundColor: bgColor === "dark" ? "#1e293b" : "#fff" }}
          onDrop={(e) => handleDrop(e, logoType)}
          onDragOver={(e) => handleDragOver(e, logoType)}
          onDragLeave={(e) => handleDragLeave(e, logoType)}
        >
          {isUploading ? (
            <div className="space-y-3">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-[#C8FF00] text-500" />
              <Progress value={uploadProgress[logoType]} className="w-32 mx-auto" />
              <p className="text-sm text-[rgba(244,246,240,0.45)]">Uploading...</p>
            </div>
          ) : currentUrl ? (
            <div className="space-y-3">
              <img 
                src={currentUrl.startsWith("/api") ? `${API.replace("/api", "")}${currentUrl}` : currentUrl}
                alt={label}
                className="max-h-20 mx-auto object-contain"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
              <div className="flex justify-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => inputRef.current?.click()}
                >
                  <Upload className="h-4 w-4 mr-1" />
                  Replace
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="text-red-500 hover:text-red-600"
                  onClick={() => deleteLogo(logoType)}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Remove
                </Button>
              </div>
            </div>
          ) : (
            <div 
              className="space-y-2 cursor-pointer" 
              onClick={() => inputRef.current?.click()}
            >
              <Upload className={`h-10 w-10 mx-auto ${bgColor === "dark" ? "text-[rgba(244,246,240,0.45)]" : "text-[rgba(244,246,240,0.20)]"}`} />
              <p className={`text-sm ${bgColor === "dark" ? "text-[rgba(244,246,240,0.20)]" : "text-[rgba(244,246,240,0.35)]"}`}>
                <span className="text-[#C8FF00] text-500 font-medium">Click to upload</span> or drag and drop
              </p>
              <p className={`text-xs ${bgColor === "dark" ? "text-[rgba(244,246,240,0.45)]" : "text-[rgba(244,246,240,0.45)]"}`}>
                {description}
              </p>
            </div>
          )}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.gif,.bmp"
          className="hidden"
          onChange={(e) => handleFileSelect(e, logoType)}
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-[rgba(244,246,240,0.45)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="branding-settings">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#F4F6F0]">Brand Settings</h1>
          <p className="text-[rgba(244,246,240,0.45)] mt-1">Customize your organization's appearance</p>
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

      <Tabs defaultValue="logos" className="space-y-4">
        <TabsList>
          <TabsTrigger value="logos">
            <Image className="h-4 w-4 mr-2" />
            Logos
          </TabsTrigger>
          <TabsTrigger value="colors">
            <Palette className="h-4 w-4 mr-2" />
            Colors
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

        {/* Logos Tab */}
        <TabsContent value="logos" className="space-y-6">
          {/* Requirements Info */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="pt-4">
              <div className="flex gap-3">
                <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Logo Requirements</p>
                  <ul className="space-y-1 text-[#3B9EFF]">
                    <li>• Preferred dimensions: <strong>240 x 240 pixels</strong> @ 72 DPI</li>
                    <li>• Supported formats: <strong>JPG, JPEG, PNG, GIF, BMP</strong></li>
                    <li>• Maximum file size: <strong>1MB</strong></li>
                    <li>• Logo will appear in PDFs, emails, and app header</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Organization Logo</CardTitle>
              <CardDescription>Upload your company logo</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Main Logo */}
                <LogoUploader
                  logoType="main"
                  label="Main Logo (Light Background)"
                  description="For white/light backgrounds"
                  bgColor="white"
                  currentUrl={branding.logo_url}
                  inputRef={mainLogoRef}
                />

                {/* Dark Logo */}
                <LogoUploader
                  logoType="dark"
                  label="Logo for Dark Background"
                  description="For dark/sidebar backgrounds"
                  bgColor="dark"
                  currentUrl={branding.logo_dark_url}
                  inputRef={darkLogoRef}
                />
              </div>

              {/* Favicon */}
              <div className="pt-4 border-t">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <Label>Favicon (Browser Tab Icon)</Label>
                    <div className="flex gap-4 items-start">
                      <div 
                        className={`w-16 h-16 border-2 border-dashed rounded-lg flex items-center justify-center bg-[#111820] cursor-pointer transition-all ${
                          dragOver.favicon ? "border-[rgba(200,255,0,0.50)] bg-[rgba(200,255,0,0.08)]" : "border-[rgba(255,255,255,0.07)]"
                        }`}
                        onClick={() => faviconRef.current?.click()}
                        onDrop={(e) => handleDrop(e, "favicon")}
                        onDragOver={(e) => handleDragOver(e, "favicon")}
                        onDragLeave={(e) => handleDragLeave(e, "favicon")}
                      >
                        {uploadProgress.favicon !== undefined ? (
                          <RefreshCw className="h-5 w-5 animate-spin text-[#C8FF00] text-500" />
                        ) : branding.favicon_url ? (
                          <img 
                            src={branding.favicon_url.startsWith("/api") ? `${API.replace("/api", "")}${branding.favicon_url}` : branding.favicon_url}
                            alt="Favicon" 
                            className="w-10 h-10 object-contain"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <Image className="h-6 w-6 text-[rgba(244,246,240,0.20)]" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-[rgba(244,246,240,0.35)] mb-2">
                          Small icon shown in browser tabs. Recommended: 32x32 or 64x64 pixels.
                        </p>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => faviconRef.current?.click()}>
                            <Upload className="h-4 w-4 mr-1" />
                            Upload
                          </Button>
                          {branding.favicon_url && (
                            <Button 
                              variant="ghost" 
                              size="sm"
                              className="text-red-500"
                              onClick={() => deleteLogo("favicon")}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                    <input
                      ref={faviconRef}
                      type="file"
                      accept=".jpg,.jpeg,.png,.gif,.bmp,.ico"
                      className="hidden"
                      onChange={(e) => handleFileSelect(e, "favicon")}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

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
                <p className="text-xs text-[rgba(244,246,240,0.45)]">Displayed below your logo in some areas</p>
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
                <p className="text-xs text-[rgba(244,246,240,0.45)]">Appears at the bottom of automated emails</p>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <Label>Show "Powered by Battwheels"</Label>
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">Display our branding in your portal</p>
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
                <p className="text-xs text-[rgba(244,246,240,0.45)]">
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
                    <img 
                      src={branding.logo_dark_url.startsWith("/api") ? `${API.replace("/api", "")}${branding.logo_dark_url}` : branding.logo_dark_url}
                      alt="Logo" 
                      className="h-8 object-contain"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : branding.logo_url ? (
                    <img 
                      src={branding.logo_url.startsWith("/api") ? `${API.replace("/api", "")}${branding.logo_url}` : branding.logo_url}
                      alt="Logo" 
                      className="h-8 object-contain"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <div className="h-8 w-24 bg-[#111820] rounded flex items-center justify-center text-[rgba(244,246,240,0.45)] text-xs">
                      Logo
                    </div>
                  )}
                  {branding.company_tagline && (
                    <span className="text-[rgba(244,246,240,0.45)] text-sm">{branding.company_tagline}</span>
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
                  <div className="p-3 text-center text-xs text-[rgba(244,246,240,0.45)] border-t">
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
