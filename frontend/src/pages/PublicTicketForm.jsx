import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { 
  Car, User, AlertCircle, MapPin, Upload, X, FileText, 
  Phone, Mail, Search, Zap, Building2, IndianRupee, CreditCard,
  CheckCircle, Loader2, Bike, Truck, Bus
} from "lucide-react";
import LocationPicker from "@/components/LocationPicker";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Customer types
const customerTypes = [
  { value: "individual", label: "Individual", icon: User, description: "Personal vehicle owner" },
  { value: "business", label: "Business/OEM/Fleet Operator", icon: Building2, description: "Company, fleet operator, or OEM" },
];

// Resolution types
const resolutionTypes = [
  { value: "workshop", label: "Workshop Visit", description: "Bring your vehicle to our service center" },
  { value: "onsite", label: "On-Site Resolution", description: "We come to your location" },
  { value: "pickup", label: "Pickup & Drop", description: "We pick up and deliver your vehicle" },
  { value: "remote", label: "Remote Diagnosis", description: "Software/OTA fix remotely" },
];

// Priority levels
const priorities = [
  { value: "low", label: "Low - Can wait a few days", color: "bg-green-500" },
  { value: "medium", label: "Medium - Within 24-48 hours", color: "bg-yellow-500" },
  { value: "high", label: "High - Urgent, within 24 hours", color: "bg-orange-500" },
  { value: "critical", label: "Critical - Vehicle not operational", color: "bg-red-500" },
];

// Category icons
const categoryIcons = {
  "2W_EV": Bike,
  "3W_EV": Truck,
  "4W_EV": Car,
  "COMM_EV": Bus,
  "LEV": Bike,
};

export default function PublicTicketForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fileInputRef = useRef(null);
  
  // Form state
  const [step, setStep] = useState(1); // 1: Form, 2: Payment, 3: Success
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Master data
  const [categories, setCategories] = useState([]);
  const [models, setModels] = useState([]);
  const [modelsByOem, setModelsByOem] = useState({});
  const [issueSuggestions, setIssueSuggestions] = useState([]);
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [serviceCharges, setServiceCharges] = useState({ visit_fee: 299, diagnostic_fee: 199 });
  
  // Form data
  const [formData, setFormData] = useState({
    // Vehicle
    vehicle_category: "",
    vehicle_model_id: "",
    vehicle_model_name: "",
    vehicle_oem: "",
    vehicle_number: "",
    // Customer
    customer_type: "individual",
    customer_name: "",
    contact_number: "",
    email: "",
    business_name: "",
    gst_number: "",
    // Issue
    title: "",
    description: "",
    issue_type: "general",
    priority: "medium",
    // Resolution
    resolution_type: "workshop",
    // Location
    incident_location: "",
    location_lat: null,
    location_lng: null,
    // Payment
    include_visit_fee: true,
    include_diagnostic_fee: false,
  });
  
  // Payment state
  const [paymentDetails, setPaymentDetails] = useState(null);
  const [ticketResult, setTicketResult] = useState(null);
  
  // File attachments
  const [attachments, setAttachments] = useState([]);
  
  // Search states
  const [searchingLocation, setSearchingLocation] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAiSuggestions, setShowAiSuggestions] = useState(false);

  // AI suggestion debounce
  const aiDebounceRef = useRef(null);

  // Load master data on mount
  useEffect(() => {
    fetchMasterData();
  }, []);

  // Load models when category changes
  useEffect(() => {
    if (formData.vehicle_category) {
      fetchModels(formData.vehicle_category);
      fetchIssueSuggestions(formData.vehicle_category);
    }
  }, [formData.vehicle_category]);

  const fetchMasterData = async () => {
    try {
      const [catRes, chargesRes] = await Promise.all([
        fetch(`${API}/public/vehicle-categories`),
        fetch(`${API}/public/service-charges`)
      ]);
      
      if (catRes.ok) {
        const catData = await catRes.json();
        setCategories(catData.categories || []);
      }
      
      if (chargesRes.ok) {
        const chargesData = await chargesRes.json();
        setServiceCharges({
          visit_fee: chargesData.visit_fee?.amount || 299,
          diagnostic_fee: chargesData.diagnostic_fee?.amount || 199
        });
      }
    } catch (error) {
      console.error("Failed to fetch master data:", error);
    }
  };

  const fetchModels = async (categoryCode) => {
    try {
      const res = await fetch(`${API}/public/vehicle-models?category_code=${categoryCode}`);
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
        setModelsByOem(data.by_oem || {});
      }
    } catch (error) {
      console.error("Failed to fetch models:", error);
    }
  };

  const fetchIssueSuggestions = async (categoryCode, modelId = null) => {
    try {
      let url = `${API}/public/issue-suggestions?category_code=${categoryCode}`;
      if (modelId) url += `&model_id=${modelId}`;
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setIssueSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error("Failed to fetch suggestions:", error);
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
    setShowAiSuggestions(false);
  };

  // Fetch AI-powered suggestions
  const fetchAiSuggestions = async (userInput) => {
    if (!userInput || userInput.length < 3 || !formData.vehicle_category) return;
    
    setAiLoading(true);
    try {
      const res = await fetch(`${API}/public/ai/issue-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vehicle_category: formData.vehicle_category,
          vehicle_model: formData.vehicle_model_name || null,
          vehicle_oem: formData.vehicle_oem || null,
          user_input: userInput
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setAiSuggestions(data.suggestions || []);
        if (data.suggestions && data.suggestions.length > 0) {
          setShowAiSuggestions(true);
        }
      }
    } catch (error) {
      console.error("Failed to fetch AI suggestions:", error);
    } finally {
      setAiLoading(false);
    }
  };

  // Debounced AI suggestion handler
  const handleTitleChange = (value) => {
    setFormData(prev => ({ ...prev, title: value }));
    
    // Clear previous timeout
    if (aiDebounceRef.current) {
      clearTimeout(aiDebounceRef.current);
    }
    
    // Set new timeout for AI suggestions (500ms debounce)
    if (value.length >= 3) {
      aiDebounceRef.current = setTimeout(() => {
        fetchAiSuggestions(value);
      }, 500);
    } else {
      setShowAiSuggestions(false);
    }
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
      if (attachment?.preview) URL.revokeObjectURL(attachment.preview);
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
    
    // Simple geocoding simulation - in production, use a real geocoding service
    setTimeout(() => {
      toast.success("Location saved: " + formData.incident_location);
      setSearchingLocation(false);
    }, 1000);
  };

  const validateForm = () => {
    if (!formData.vehicle_category) {
      toast.error("Please select vehicle category");
      return false;
    }
    if (!formData.vehicle_number) {
      toast.error("Please enter vehicle number");
      return false;
    }
    if (!formData.customer_name) {
      toast.error("Please enter your name");
      return false;
    }
    if (!formData.contact_number) {
      toast.error("Please enter contact number");
      return false;
    }
    if (!formData.title) {
      toast.error("Please describe the issue");
      return false;
    }
    if (!formData.description) {
      toast.error("Please provide issue details");
      return false;
    }
    if (formData.resolution_type === "onsite" && !formData.incident_location) {
      toast.error("Please enter location for on-site service");
      return false;
    }
    return true;
  };

  const requiresPayment = () => {
    return formData.customer_type === "individual" && formData.resolution_type === "onsite";
  };

  const calculateTotal = () => {
    if (!requiresPayment()) return 0;
    let total = serviceCharges.visit_fee; // Always mandatory for onsite
    if (formData.include_diagnostic_fee) {
      total += serviceCharges.diagnostic_fee;
    }
    return total;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setSubmitting(true);
    
    try {
      const submitData = {
        ...formData,
        include_visit_fee: requiresPayment() ? true : false,
      };
      
      const res = await fetch(`${API}/public/tickets/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submitData)
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to submit ticket");
      }
      
      if (data.requires_payment) {
        // Show payment page
        setPaymentDetails(data.payment_details);
        setTicketResult(data);
        setStep(2);
      } else {
        // Ticket created successfully
        setTicketResult(data);
        setStep(3);
        toast.success("Service ticket submitted successfully!");
      }
    } catch (error) {
      toast.error(error.message || "Failed to submit ticket");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePayment = async () => {
    if (!paymentDetails) return;
    
    // For mock payments (when Razorpay not configured), simulate success
    if (paymentDetails.is_mock) {
      try {
        const verifyRes = await fetch(`${API}/public/tickets/verify-payment`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ticket_id: ticketResult.ticket_id,
            razorpay_order_id: paymentDetails.order_id,
            razorpay_payment_id: `pay_mock_${Date.now()}`,
            razorpay_signature: "mock_signature"
          })
        });
        
        if (verifyRes.ok) {
          setStep(3);
          toast.success("Payment successful! Ticket submitted.");
        }
      } catch (error) {
        toast.error("Payment verification failed");
      }
      return;
    }
    
    // Real Razorpay integration
    const options = {
      key: paymentDetails.key_id,
      amount: paymentDetails.amount_paise,
      currency: "INR",
      name: "Battwheels Services",
      description: "Service Ticket Charges",
      order_id: paymentDetails.order_id,
      handler: async function(response) {
        try {
          const verifyRes = await fetch(`${API}/public/tickets/verify-payment`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              ticket_id: ticketResult.ticket_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            })
          });
          
          if (verifyRes.ok) {
            setStep(3);
            toast.success("Payment successful! Ticket submitted.");
          } else {
            toast.error("Payment verification failed");
          }
        } catch (error) {
          toast.error("Payment verification failed");
        }
      },
      prefill: {
        name: formData.customer_name,
        email: formData.email,
        contact: formData.contact_number
      },
      theme: { color: "#22c55e" }
    };
    
    // @ts-ignore
    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  // Step 1: Form
  if (step === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
        <div className="max-w-3xl mx-auto space-y-6" data-testid="public-ticket-form">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Zap className="h-10 w-10 text-green-500" />
              <h1 className="text-3xl font-bold text-white">Battwheels Service</h1>
            </div>
            <p className="text-slate-400">Submit your EV service request</p>
          </div>

          <Card className="border-slate-700 bg-slate-800/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="text-white">New Service Ticket</CardTitle>
              <CardDescription>Fill out the form below to request EV service</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              
              {/* Customer Type Selection */}
              <div className="space-y-4">
                <Label className="text-white text-lg font-semibold flex items-center gap-2">
                  <User className="h-5 w-5 text-green-500" />
                  Customer Type
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {customerTypes.map((type) => {
                    const Icon = type.icon;
                    const isSelected = formData.customer_type === type.value;
                    return (
                      <div
                        key={type.value}
                        onClick={() => setFormData(prev => ({ ...prev, customer_type: type.value }))}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isSelected 
                            ? "border-green-500 bg-green-500/10" 
                            : "border-slate-600 hover:border-slate-500"
                        }`}
                        data-testid={`customer-type-${type.value}`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className={`h-6 w-6 ${isSelected ? "text-green-500" : "text-slate-400"}`} />
                          <div>
                            <p className={`font-medium ${isSelected ? "text-green-500" : "text-white"}`}>{type.label}</p>
                            <p className="text-sm text-slate-400">{type.description}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Vehicle Information */}
              <div className="space-y-4">
                <Label className="text-white text-lg font-semibold flex items-center gap-2">
                  <Car className="h-5 w-5 text-green-500" />
                  Vehicle Information
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Vehicle Category *</Label>
                    <Select
                      value={formData.vehicle_category}
                      onValueChange={(value) => setFormData(prev => ({ 
                        ...prev, 
                        vehicle_category: value,
                        vehicle_model_id: "",
                        vehicle_model_name: "",
                        vehicle_oem: ""
                      }))}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="vehicle-category-select">
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
                    <Label className="text-slate-300">Vehicle Model (OEM)</Label>
                    <Select
                      value={formData.vehicle_model_id}
                      onValueChange={handleModelSelect}
                      disabled={!formData.vehicle_category}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="vehicle-model-select">
                        <SelectValue placeholder="Select vehicle model" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(modelsByOem).map(([oem, oemModels]) => (
                          <div key={oem}>
                            <div className="px-2 py-1.5 text-xs font-semibold text-slate-400 bg-slate-800">{oem}</div>
                            {oemModels.map((model) => (
                              <SelectItem key={model.model_id} value={model.model_id}>
                                {model.name} {model.range_km && `(${model.range_km} km)`}
                              </SelectItem>
                            ))}
                          </div>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Vehicle Number *</Label>
                  <Input
                    placeholder="e.g., MH12AB1234"
                    className="bg-slate-700/50 border-slate-600 uppercase"
                    value={formData.vehicle_number}
                    onChange={(e) => setFormData(prev => ({ ...prev, vehicle_number: e.target.value.toUpperCase() }))}
                    data-testid="vehicle-number-input"
                  />
                </div>
              </div>

              {/* Customer Details */}
              <div className="space-y-4">
                <Label className="text-white text-lg font-semibold flex items-center gap-2">
                  <User className="h-5 w-5 text-green-500" />
                  Customer Details
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Full Name *</Label>
                    <Input
                      placeholder="Your name"
                      className="bg-slate-700/50 border-slate-600"
                      value={formData.customer_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, customer_name: e.target.value }))}
                      data-testid="customer-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Contact Number *</Label>
                    <div className="flex">
                      <div className="flex items-center px-3 bg-slate-700 border border-r-0 border-slate-600 rounded-l-md text-sm text-slate-400">
                        +91
                      </div>
                      <Input
                        placeholder="98765 43210"
                        className="bg-slate-700/50 border-slate-600 rounded-l-none"
                        value={formData.contact_number}
                        onChange={(e) => setFormData(prev => ({ ...prev, contact_number: e.target.value }))}
                        data-testid="contact-number-input"
                      />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Email Address</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input
                        type="email"
                        placeholder="your@email.com"
                        className="bg-slate-700/50 border-slate-600 pl-10"
                        value={formData.email}
                        onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                        data-testid="email-input"
                      />
                    </div>
                  </div>
                  {formData.customer_type === "business" && (
                    <div className="space-y-2">
                      <Label className="text-slate-300">Business Name</Label>
                      <Input
                        placeholder="Company name"
                        className="bg-slate-700/50 border-slate-600"
                        value={formData.business_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, business_name: e.target.value }))}
                        data-testid="business-name-input"
                      />
                    </div>
                  )}
                </div>
                {formData.customer_type === "business" && (
                  <div className="space-y-2">
                    <Label className="text-slate-300">GST Number</Label>
                    <Input
                      placeholder="22AAAAA0000A1Z5"
                      className="bg-slate-700/50 border-slate-600 uppercase"
                      value={formData.gst_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, gst_number: e.target.value.toUpperCase() }))}
                      data-testid="gst-number-input"
                    />
                  </div>
                )}
              </div>

              {/* Issue Details */}
              <div className="space-y-4">
                <Label className="text-white text-lg font-semibold flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-green-500" />
                  Issue Details
                </Label>
                <div className="space-y-2 relative">
                  <Label className="text-slate-300">Issue Title *</Label>
                  <Input
                    placeholder="Describe the issue briefly..."
                    className="bg-slate-700/50 border-slate-600"
                    value={formData.title}
                    onChange={(e) => {
                      setFormData(prev => ({ ...prev, title: e.target.value }));
                      setShowSuggestions(true);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    data-testid="issue-title-input"
                  />
                  {/* Issue Suggestions Dropdown */}
                  {showSuggestions && issueSuggestions.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg max-h-60 overflow-auto">
                      <div className="p-2 text-xs text-slate-400 border-b border-slate-700">
                        Common EV issues for your vehicle:
                      </div>
                      {issueSuggestions.slice(0, 8).map((suggestion) => (
                        <div
                          key={suggestion.suggestion_id}
                          className="px-3 py-2 hover:bg-slate-700 cursor-pointer"
                          onClick={() => handleSuggestionSelect(suggestion)}
                        >
                          <p className="text-white text-sm">{suggestion.title}</p>
                          {suggestion.common_symptoms?.length > 0 && (
                            <p className="text-xs text-slate-400 mt-0.5">
                              {suggestion.common_symptoms.slice(0, 2).join(", ")}
                            </p>
                          )}
                        </div>
                      ))}
                      <div 
                        className="px-3 py-2 text-xs text-slate-500 hover:bg-slate-700 cursor-pointer"
                        onClick={() => setShowSuggestions(false)}
                      >
                        Close suggestions
                      </div>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Detailed Description *</Label>
                  <Textarea
                    placeholder="Describe the issue in detail - when it started, symptoms, error codes if any..."
                    className="bg-slate-700/50 border-slate-600 min-h-[100px]"
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    data-testid="description-input"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Priority</Label>
                    <Select
                      value={formData.priority}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, priority: value }))}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="priority-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {priorities.map((p) => (
                          <SelectItem key={p.value} value={p.value}>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${p.color}`} />
                              {p.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Resolution Type *</Label>
                    <Select
                      value={formData.resolution_type}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, resolution_type: value }))}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="resolution-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {resolutionTypes.map((r) => (
                          <SelectItem key={r.value} value={r.value}>
                            <div>
                              <p>{r.label}</p>
                              <p className="text-xs text-slate-400">{r.description}</p>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Location (for onsite) */}
              {formData.resolution_type === "onsite" && (
                <div className="space-y-4">
                  <Label className="text-white text-lg font-semibold flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-green-500" />
                    Service Location
                  </Label>
                  <LocationPicker
                    value={
                      formData.incident_location 
                        ? { address: formData.incident_location, lat: formData.location_lat, lng: formData.location_lng }
                        : null
                    }
                    onChange={(location) => {
                      setFormData(prev => ({
                        ...prev,
                        incident_location: location.address,
                        location_lat: location.lat,
                        location_lng: location.lng
                      }));
                    }}
                    placeholder="Click to select location on map"
                    buttonText="Open Map"
                  />
                  <p className="text-xs text-slate-400">
                    Select your exact location on the map for accurate on-site service
                  </p>
                </div>
              )}

              {/* Payment Info (Individual + Onsite) */}
              {requiresPayment() && (
                <div className="space-y-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <Label className="text-amber-400 text-lg font-semibold flex items-center gap-2">
                    <IndianRupee className="h-5 w-5" />
                    Service Charges
                  </Label>
                  <p className="text-sm text-slate-400">
                    On-site service requires advance payment of service charges.
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Checkbox checked disabled className="bg-green-500" />
                        <div>
                          <p className="text-white font-medium">Visit Charges</p>
                          <p className="text-xs text-slate-400">Mandatory for on-site service</p>
                        </div>
                      </div>
                      <p className="text-green-400 font-semibold">₹{serviceCharges.visit_fee}</p>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Checkbox 
                          checked={formData.include_diagnostic_fee}
                          onCheckedChange={(checked) => setFormData(prev => ({ ...prev, include_diagnostic_fee: !!checked }))}
                          data-testid="diagnostic-fee-checkbox"
                        />
                        <div>
                          <p className="text-white font-medium">Diagnostic Charges</p>
                          <p className="text-xs text-slate-400">Optional - detailed diagnosis report</p>
                        </div>
                      </div>
                      <p className="text-slate-300 font-semibold">₹{serviceCharges.diagnostic_fee}</p>
                    </div>
                    <div className="flex items-center justify-between pt-3 border-t border-slate-700">
                      <p className="text-white font-semibold">Total Payable</p>
                      <p className="text-green-400 text-xl font-bold">₹{calculateTotal()}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* File Attachments */}
              <div className="space-y-4">
                <Label className="text-white text-lg font-semibold flex items-center gap-2">
                  <Upload className="h-5 w-5 text-green-500" />
                  Attachments (Optional)
                </Label>
                <div 
                  className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-green-500/50 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-8 w-8 mx-auto mb-2 text-slate-400" />
                  <p className="text-sm text-slate-400">Click to upload photos/documents</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*,.pdf,.doc,.docx"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </div>
                {attachments.length > 0 && (
                  <div className="grid grid-cols-2 gap-2">
                    {attachments.map((att) => (
                      <div key={att.id} className="flex items-center gap-2 p-2 bg-slate-700/50 rounded">
                        {att.preview ? (
                          <img src={att.preview} alt="" className="h-10 w-10 object-cover rounded" />
                        ) : (
                          <FileText className="h-10 w-10 text-slate-400" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-white truncate">{att.name}</p>
                          <p className="text-xs text-slate-400">{formatFileSize(att.size)}</p>
                        </div>
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeAttachment(att.id)}>
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="pt-4 border-t border-slate-700">
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="w-full bg-green-600 hover:bg-green-700 text-white h-12 text-lg"
                  data-testid="submit-ticket-btn"
                >
                  {submitting ? (
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  ) : requiresPayment() ? (
                    <>
                      <CreditCard className="h-5 w-5 mr-2" />
                      Proceed to Payment - ₹{calculateTotal()}
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-5 w-5 mr-2" />
                      Submit Service Request
                    </>
                  )}
                </Button>
                
                {formData.customer_type === "business" && (
                  <p className="text-center text-sm text-slate-400 mt-4">
                    Business customers can also access the{" "}
                    <a href="/customer-portal" className="text-green-400 hover:underline">Customer Portal</a>
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center text-sm text-slate-500">
            <p>© 2026 Battwheels Services Pvt Ltd. All rights reserved.</p>
          </div>
        </div>
      </div>
    );
  }

  // Step 2: Payment
  if (step === 2) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4 flex items-center justify-center">
        <Card className="border-slate-700 bg-slate-800/50 backdrop-blur max-w-md w-full">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-green-500/20 rounded-full">
                <CreditCard className="h-8 w-8 text-green-500" />
              </div>
            </div>
            <CardTitle className="text-white">Complete Payment</CardTitle>
            <CardDescription>Pay service charges to confirm your booking</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3 p-4 bg-slate-700/50 rounded-lg">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Ticket ID</span>
                <span className="text-white font-mono">{ticketResult?.ticket_id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Visit Charges</span>
                <span className="text-white">₹{paymentDetails?.visit_fee}</span>
              </div>
              {paymentDetails?.diagnostic_fee > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Diagnostic Charges</span>
                  <span className="text-white">₹{paymentDetails?.diagnostic_fee}</span>
                </div>
              )}
              <div className="flex justify-between pt-3 border-t border-slate-600">
                <span className="text-white font-semibold">Total</span>
                <span className="text-green-400 text-xl font-bold">₹{paymentDetails?.amount}</span>
              </div>
            </div>

            {paymentDetails?.is_mock && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <p className="text-amber-400 text-sm text-center">
                  Test Mode: Payment will be simulated
                </p>
              </div>
            )}

            <Button
              onClick={handlePayment}
              className="w-full bg-green-600 hover:bg-green-700 text-white h-12"
              data-testid="pay-now-btn"
            >
              <IndianRupee className="h-5 w-5 mr-2" />
              Pay ₹{paymentDetails?.amount}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Step 3: Success
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4 flex items-center justify-center">
      <Card className="border-slate-700 bg-slate-800/50 backdrop-blur max-w-md w-full">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-green-500/20 rounded-full">
              <CheckCircle className="h-10 w-10 text-green-500" />
            </div>
          </div>
          <CardTitle className="text-white text-2xl">Ticket Submitted!</CardTitle>
          <CardDescription>Your service request has been received</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="p-4 bg-slate-700/50 rounded-lg text-center">
            <p className="text-slate-400 text-sm">Ticket ID</p>
            <p className="text-green-400 text-2xl font-mono font-bold">{ticketResult?.ticket_id}</p>
          </div>

          <div className="space-y-2 text-sm text-slate-400">
            <p className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Confirmation sent to your phone/email
            </p>
            <p className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Our team will contact you shortly
            </p>
            <p className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Track your ticket status anytime
            </p>
          </div>

          <div className="space-y-3">
            <Button
              onClick={() => navigate(`/track-ticket?id=${ticketResult?.ticket_id}`)}
              className="w-full bg-green-600 hover:bg-green-700"
              data-testid="track-ticket-btn"
            >
              Track Your Ticket
            </Button>
            <Button
              variant="outline"
              onClick={() => { setStep(1); setFormData({ ...formData, title: "", description: "" }); }}
              className="w-full border-slate-600"
            >
              Submit Another Request
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
