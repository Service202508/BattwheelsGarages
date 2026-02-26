import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  ArrowLeft, Send, Car, User, AlertCircle, MapPin, 
  Upload, X, FileText, Phone, Mail, Search, Bike, Truck, Bus, Loader2
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// Fallback static data (in case API fails)
const fallbackIssueTypes = [
  { value: "battery", label: "Battery Issues" },
  { value: "motor", label: "Motor Problems" },
  { value: "charging", label: "Charging System" },
  { value: "controller", label: "Controller/BMS" },
  { value: "electrical", label: "Electrical Wiring" },
  { value: "suspension", label: "Suspension" },
  { value: "brakes", label: "Brakes" },
  { value: "tyre", label: "Tyre/Wheel" },
  { value: "body", label: "Body Damage" },
  { value: "software", label: "Software/Display" },
  { value: "noise", label: "Unusual Noise" },
  { value: "performance", label: "Performance Issue" },
  { value: "other", label: "Other" },
];

const customerTypes = [
  { value: "individual", label: "Individual" },
  { value: "business", label: "Business/OEM/Fleet Operator" },
];

const priorities = [
  { value: "low", label: "Low - Can wait a few days", color: "text-green-500" },
  { value: "medium", label: "Medium - Within 24-48 hours", color: "text-yellow-500" },
  { value: "high", label: "High - Urgent, within 24 hours", color: "text-orange-500" },
  { value: "critical", label: "Critical - Vehicle not operational", color: "text-red-500" },
];

// Category icons mapping
const categoryIcons = {
  "2W_EV": Bike,
  "3W_EV": Truck,
  "4W_EV": Car,
  "COMM_EV": Bus,
  "LEV": Bike,
};

export default function NewTicket({ user }) {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [searchingLocation, setSearchingLocation] = useState(false);
  
  // Master data from backend
  const [categories, setCategories] = useState([]);
  const [models, setModels] = useState([]);
  const [modelsByOem, setModelsByOem] = useState({});
  const [issueSuggestions, setIssueSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const [formData, setFormData] = useState({
    // Vehicle Info
    vehicle_category: "",
    vehicle_model_id: "",
    vehicle_model_name: "",
    vehicle_oem: "",
    vehicle_number: "",
    // Customer Details
    customer_type: "individual",
    customer_name: "",
    contact_number: "",
    email: "",
    // Complaint Specifics
    title: "",
    issue_type: "general",
    priority: "medium",
    description: "",
    // Location
    incident_location: "",
    location_coordinates: null,
  });

  useEffect(() => {
    fetchMasterData();
    fetchCustomers();
  }, []);

  // Fetch vehicle models when category changes
  useEffect(() => {
    if (formData.vehicle_category) {
      fetchModels(formData.vehicle_category);
      fetchIssueSuggestions(formData.vehicle_category);
    }
  }, [formData.vehicle_category]);

  const fetchMasterData = async () => {
    try {
      const res = await fetch(`${API}/master-data/vehicle-categories?active_only=true`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
      }
    } catch (error) {
      console.error("Failed to fetch vehicle categories:", error);
    }
  };

  const fetchModels = async (categoryCode) => {
    try {
      const res = await fetch(`${API}/master-data/vehicle-models?category_code=${categoryCode}&active_only=true`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
        setModelsByOem(data.by_oem || {});
      }
    } catch (error) {
      console.error("Failed to fetch vehicle models:", error);
    }
  };

  const fetchIssueSuggestions = async (categoryCode, modelId = null) => {
    try {
      let url = `${API}/master-data/issue-suggestions?category_code=${categoryCode}`;
      if (modelId) url += `&model_id=${modelId}`;
      
      const res = await fetch(url, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setIssueSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error("Failed to fetch issue suggestions:", error);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await fetch(`${API}/customers`, {
        credentials: "include",
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setCustomers(data);
      }
    } catch (error) {
      console.error("Failed to fetch customers:", error);
    }
  };

  const handleModelSelect = (modelId) => {
    const model = models.find(m => m.model_id === modelId);
    if (model) {
      setFormData(prev => ({
        ...prev,
        vehicle_model_id: modelId,
        vehicle_model_name: model.name,
        vehicle_oem: model.oem
      }));
      fetchIssueSuggestions(formData.vehicle_category, modelId);
    }
  };

  const handleSuggestionSelect = (suggestion) => {
    setFormData(prev => ({
      ...prev,
      title: suggestion.title,
      issue_type: suggestion.issue_type || "general"
    }));
    setShowSuggestions(false);
    
    // Increment usage count for analytics
    fetch(`${API}/master-data/issue-suggestions/${suggestion.suggestion_id}/increment-usage`, {
      method: "POST",
      headers: getAuthHeaders()
    }).catch(() => {});
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    const newAttachments = files.map(file => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    }));
    setAttachments(prev => [...prev, ...newAttachments]);
  };

  const removeAttachment = (id) => {
    setAttachments(prev => {
      const attachment = prev.find(a => a.id === id);
      if (attachment?.preview) {
        URL.revokeObjectURL(attachment.preview);
      }
      return prev.filter(a => a.id !== id);
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleLocationSearch = async () => {
    if (!formData.incident_location) return;
    setSearchingLocation(true);
    // Simulate location search - in production, integrate with Google Maps API
    setTimeout(() => {
      toast.success("Location found: " + formData.incident_location);
      setSearchingLocation(false);
    }, 1000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.vehicle_category || !formData.vehicle_number) {
      toast.error("Please fill in vehicle information");
      return;
    }
    if (!formData.customer_name || !formData.contact_number) {
      toast.error("Please fill in customer details");
      return;
    }
    if (!formData.title || !formData.description) {
      toast.error("Please fill in complaint specifics");
      return;
    }

    setLoading(true);

    try {
      // Create ticket data
      const ticketData = {
        title: formData.title,
        description: formData.description,
        category: formData.issue_type,
        priority: formData.priority,
        // Vehicle info - unified
        vehicle_type: formData.vehicle_category,
        vehicle_category: formData.vehicle_category,
        vehicle_model: formData.vehicle_model_name || formData.vehicle_oem,
        vehicle_model_id: formData.vehicle_model_id,
        vehicle_oem: formData.vehicle_oem,
        vehicle_number: formData.vehicle_number,
        // Customer info
        customer_type: formData.customer_type,
        customer_name: formData.customer_name,
        contact_number: formData.contact_number,
        customer_email: formData.email,
        // Service details
        issue_type: formData.issue_type,
        incident_location: formData.incident_location,
        attachments_count: attachments.length,
      };

      const response = await fetch(`${API}/tickets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        credentials: "include",
        body: JSON.stringify(ticketData),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success("Service ticket submitted successfully!");
        navigate("/tickets");
      } else {
        const data = await response.json();
        toast.error(data.detail || "Failed to create ticket");
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="new-ticket-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => navigate(-1)}
          data-testid="back-btn"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Submit a Service Ticket</h1>
          <p className="text-muted-foreground mt-1">Please provide detailed information about the issue.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="border-white/10 bg-card/50">
          <CardHeader>
            <CardTitle>New Service Ticket</CardTitle>
            <CardDescription>Fill out the form below to report an issue or request service.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            
            {/* Vehicle Information */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <Car className="h-5 w-5 text-primary" />
                <span>Vehicle Information</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="vehicle_category">Vehicle Category *</Label>
                  <Select
                    value={formData.vehicle_category}
                    onValueChange={(value) => setFormData({ 
                      ...formData, 
                      vehicle_category: value,
                      vehicle_model_id: "",
                      vehicle_model_name: "",
                      vehicle_oem: ""
                    })}
                  >
                    <SelectTrigger className="bg-background/50" data-testid="vehicle-category-select">
                      <SelectValue placeholder="Select vehicle category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((cat) => {
                        const Icon = categoryIcons[cat.code] || Car;
                        return (
                          <SelectItem key={cat.code} value={cat.code}>
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4" />
                              {cat.name}
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vehicle_model">Vehicle Model (OEM)</Label>
                  <Select
                    value={formData.vehicle_model_id}
                    onValueChange={handleModelSelect}
                    disabled={!formData.vehicle_category}
                  >
                    <SelectTrigger className="bg-background/50" data-testid="vehicle-model-select">
                      <SelectValue placeholder={formData.vehicle_category ? "Select model" : "Select category first"} />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(modelsByOem).map(([oem, oemModels]) => (
                        <div key={oem}>
                          <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground bg-muted">{oem}</div>
                          {oemModels.map((model) => (
                            <SelectItem key={model.model_id} value={model.model_id}>
                              {model.name} {model.range_km && `(${model.range_km} km range)`}
                            </SelectItem>
                          ))}
                        </div>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vehicle_number">Vehicle Number *</Label>
                  <Input
                    id="vehicle_number"
                    placeholder="e.g., MH12AB1234"
                    className="bg-background/50 uppercase"
                    value={formData.vehicle_number}
                    onChange={(e) => setFormData({ ...formData, vehicle_number: e.target.value.toUpperCase() })}
                    data-testid="vehicle-number-input"
                  />
                </div>
              </div>
            </div>

            {/* Customer Details */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <User className="h-5 w-5 text-primary" />
                <span>Customer Details</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="customer_type">Customer Type</Label>
                  <Select
                    value={formData.customer_type}
                    onValueChange={(value) => setFormData({ ...formData, customer_type: value })}
                  >
                    <SelectTrigger className="bg-background/50" data-testid="customer-type-select">
                      <SelectValue placeholder="Select customer type" />
                    </SelectTrigger>
                    <SelectContent>
                      {customerTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="customer_name">Full Name *</Label>
                  <Input
                    id="customer_name"
                    placeholder="Customer name"
                    className="bg-background/50"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                    data-testid="customer-name-input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="contact_number">Contact Number *</Label>
                  <div className="flex">
                    <div className="flex items-center px-3 bg-muted border border-r-0 rounded-l-md text-sm text-muted-foreground">
                      +91
                    </div>
                    <Input
                      id="contact_number"
                      placeholder="98765 43210"
                      className="bg-background/50 rounded-l-none"
                      value={formData.contact_number}
                      onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })}
                      data-testid="contact-number-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="email@example.com"
                      className="bg-background/50 pl-10"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      data-testid="email-input"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Complaint Specifics */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <AlertCircle className="h-5 w-5 text-primary" />
                <span>Complaint Specifics</span>
              </div>
              <div className="space-y-2 relative">
                <Label htmlFor="title">Issue Title *</Label>
                <Input
                  id="title"
                  placeholder="e.g., Battery not charging properly"
                  className="bg-background/50"
                  value={formData.title}
                  onChange={(e) => {
                    setFormData({ ...formData, title: e.target.value });
                    setShowSuggestions(true);
                  }}
                  onFocus={() => setShowSuggestions(true)}
                  data-testid="title-input"
                />
                {/* Issue Suggestions Dropdown */}
                {showSuggestions && issueSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-popover border border-[rgba(255,255,255,0.13)] rounded max-h-60 overflow-auto">
                    <div className="p-2 text-xs text-muted-foreground border-b">
                      Common EV issues for your vehicle:
                    </div>
                    {issueSuggestions.slice(0, 8).map((suggestion) => (
                      <div
                        key={suggestion.suggestion_id || suggestion.failure_id}
                        className="px-3 py-2 hover:bg-accent cursor-pointer"
                        onClick={() => handleSuggestionSelect(suggestion)}
                      >
                        <p className="text-sm font-medium">{suggestion.title}</p>
                        {suggestion.common_symptoms?.length > 0 && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {suggestion.common_symptoms.slice(0, 2).join(", ")}
                          </p>
                        )}
                        {suggestion.source === "efi" && (
                          <Badge variant="outline" className="text-xs mt-1">From EFI Database</Badge>
                        )}
                      </div>
                    ))}
                    <div 
                      className="px-3 py-2 text-xs text-muted-foreground hover:bg-accent cursor-pointer border-t"
                      onClick={() => setShowSuggestions(false)}
                    >
                      Close suggestions
                    </div>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="issue_type">Issue Type</Label>
                  <Select
                    value={formData.issue_type}
                    onValueChange={(value) => setFormData({ ...formData, issue_type: value })}
                  >
                    <SelectTrigger className="bg-background/50" data-testid="issue-type-select">
                      <SelectValue placeholder="Select issue type" />
                    </SelectTrigger>
                    <SelectContent>
                      {fallbackIssueTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <Select
                    value={formData.priority}
                    onValueChange={(value) => setFormData({ ...formData, priority: value })}
                  >
                    <SelectTrigger className="bg-background/50" data-testid="priority-select">
                      <SelectValue placeholder="Set priority level" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorities.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          <span className={p.color}>{p.label}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Detailed Issue Description *</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the issue in detail - when it started, symptoms, error codes if any..."
                  className="bg-background/50 min-h-[120px]"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  data-testid="description-input"
                />
              </div>
            </div>

            {/* Location (for on-site service) */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 text-lg font-semibold">
                  <MapPin className="h-5 w-5 text-primary" />
                  <span>Service Location</span>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="incident_location">Location Address</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="incident_location"
                        placeholder="Type an address or landmark..."
                        className="bg-background/50 pl-10"
                        value={formData.incident_location}
                        onChange={(e) => setFormData({ ...formData, incident_location: e.target.value })}
                        data-testid="location-input"
                      />
                    </div>
                    <Button 
                      type="button" 
                      variant="outline"
                      onClick={handleLocationSearch}
                      disabled={searchingLocation}
                    >
                      {searchingLocation ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirm"}
                    </Button>
                  </div>
                </div>
                
                {/* Map Placeholder */}
                <div className="h-48 bg-muted/50 rounded-lg border border-dashed border-white/10 flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <MapPin className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Map integration available</p>
                    <p className="text-xs">Enter address above</p>
                  </div>
                </div>
              </div>
            )}

            {/* File Attachments */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <Upload className="h-5 w-5 text-primary" />
                <span>Attach Documents or Images</span>
              </div>
              
              <div className="space-y-4">
                <div 
                  className="border-2 border-dashed border-white/10 rounded-lg p-6 text-center hover:border-primary/50 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    You can upload multiple files (e.g., photos of damage, previous receipts).
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*,.pdf,.doc,.docx"
                    className="hidden"
                    onChange={handleFileChange}
                    data-testid="file-input"
                  />
                </div>

                {/* Attached Files */}
                {attachments.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {attachments.map((attachment) => (
                      <div 
                        key={attachment.id}
                        className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg"
                      >
                        {attachment.preview ? (
                          <img 
                            src={attachment.preview} 
                            alt={attachment.name}
                            className="h-12 w-12 object-cover rounded"
                          />
                        ) : (
                          <div className="h-12 w-12 bg-muted rounded flex items-center justify-center">
                            <FileText className="h-6 w-6 text-muted-foreground" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{attachment.name}</p>
                          <p className="text-xs text-muted-foreground">{formatFileSize(attachment.size)}</p>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => removeAttachment(attachment.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex gap-4 pt-4 border-t border-white/10">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(-1)}
                className="border-white/10"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="glow-primary flex-1"
                disabled={loading}
                data-testid="submit-ticket-btn"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                {loading ? "Submitting..." : "Submit Ticket"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
