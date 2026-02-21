import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  Car, User, MapPin, Upload, X, FileText, 
  Phone, Mail, Zap, Building2, IndianRupee, CreditCard,
  CheckCircle, Loader2, Bike, Truck, Bus, ArrowRight, Shield, Clock, Headphones,
  Brain, Sparkles, ChevronRight, Home, Wrench
} from "lucide-react";
import LocationPicker from "@/components/LocationPicker";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Customer types
const customerTypes = [
  { value: "individual", label: "Individual", icon: User, description: "Personal vehicle" },
  { value: "business", label: "Business/Fleet", icon: Building2, description: "Company/OEM" },
];

// Resolution types with better mobile icons
const resolutionTypes = [
  { value: "workshop", label: "Workshop", description: "Visit service center", icon: Wrench },
  { value: "onsite", label: "On-Site", description: "We come to you", icon: MapPin },
  { value: "pickup", label: "Pickup", description: "We handle transport", icon: Truck },
  { value: "remote", label: "Remote", description: "OTA/Software", icon: Zap },
];

// Priority levels
const priorities = [
  { value: "low", label: "Low", color: "bg-emerald-500", textColor: "text-emerald-400" },
  { value: "medium", label: "Medium", color: "bg-amber-500", textColor: "text-amber-400" },
  { value: "high", label: "High", color: "bg-orange-500", textColor: "text-orange-400" },
  { value: "critical", label: "Critical", color: "bg-red-500", textColor: "text-red-400" },
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
  
  const [step, setStep] = useState(1);
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
    vehicle_category: "",
    vehicle_model_id: "",
    vehicle_model_name: "",
    vehicle_oem: "",
    vehicle_number: "",
    customer_type: "individual",
    customer_name: "",
    contact_number: "",
    email: "",
    business_name: "",
    gst_number: "",
    title: "",
    description: "",
    issue_type: "general",
    priority: "medium",
    resolution_type: "workshop",
    incident_location: "",
    location_lat: null,
    location_lng: null,
    include_visit_fee: true,
    include_diagnostic_fee: false,
  });
  
  const [paymentDetails, setPaymentDetails] = useState(null);
  const [ticketResult, setTicketResult] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAiSuggestions, setShowAiSuggestions] = useState(false);
  const aiDebounceRef = useRef(null);

  useEffect(() => {
    fetchMasterData();
  }, []);

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

  const handleTitleChange = (value) => {
    setFormData(prev => ({ ...prev, title: value }));
    
    if (aiDebounceRef.current) {
      clearTimeout(aiDebounceRef.current);
    }
    
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
    let total = serviceCharges.visit_fee;
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
        setPaymentDetails(data.payment_details);
        setTicketResult(data);
        setStep(2);
      } else {
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
          toast.success("Payment successful!");
        }
      } catch (error) {
        toast.error("Payment verification failed");
      }
      return;
    }
    
    const options = {
      key: paymentDetails.key_id,
      amount: paymentDetails.amount_paise,
      currency: "INR",
      name: "Battwheels Garages",
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
            toast.success("Payment successful!");
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
      theme: { color: "#10b981" }
    };
    
    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  // Section Header Component
  const SectionHeader = ({ icon: Icon, title, subtitle }) => (
    <div className="flex items-start gap-3 mb-4">
      <div className="p-2 bg-emerald-500/10 rounded-xl flex-shrink-0">
        <Icon className="h-5 w-5 text-emerald-400" />
      </div>
      <div>
        <h3 className="text-base font-semibold text-white">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );

  // Footer Component
  const Footer = () => (
    <footer className="mt-8 pb-6 text-center space-y-4">
      <div className="flex items-center justify-center gap-2 text-emerald-400/80">
        <Brain className="h-4 w-4" />
        <span className="text-xs font-medium">Powered by EFI Intelligence</span>
        <Sparkles className="h-3 w-3" />
      </div>
      <div className="pt-4 border-t border-slate-800/50">
        <p className="text-[11px] text-slate-600 leading-relaxed">
          © 2026 BATTWHEELS SERVICES PRIVATE LIMITED.
          <br />All rights reserved.
        </p>
      </div>
    </footer>
  );

  // Step 1: Form
  if (step === 1) {
    return (
      <div className="min-h-screen bg-slate-950">
        {/* Mobile-optimized Header */}
        <div className="sticky top-0 z-50 bg-slate-950/95 backdrop-blur-lg border-b border-slate-800/50">
          <div className="px-4 py-3 flex items-center justify-between">
            <img 
              src="/battwheels_garages_logo.png" 
              alt="Battwheels Garages" 
              className="h-8 w-auto"
            />
            <div className="flex items-center gap-1.5 text-emerald-400">
              <Brain className="h-4 w-4" />
              <span className="text-xs font-medium">EFI</span>
            </div>
          </div>
        </div>

        {/* Hero Section - Mobile Optimized */}
        <div className="px-4 pt-6 pb-4">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold text-white">
              EV Service Request
            </h1>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">
              Expert care for your electric vehicle
            </p>
          </div>

          {/* Trust Badges - Horizontal Scroll on Mobile */}
          <div className="flex justify-center gap-4 mt-5 overflow-x-auto pb-2 -mx-4 px-4">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 whitespace-nowrap bg-slate-900/50 px-3 py-2 rounded-full">
              <Shield className="h-3.5 w-3.5 text-emerald-500" />
              <span>Certified</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 whitespace-nowrap bg-slate-900/50 px-3 py-2 rounded-full">
              <Clock className="h-3.5 w-3.5 text-emerald-500" />
              <span>Quick Response</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 whitespace-nowrap bg-slate-900/50 px-3 py-2 rounded-full">
              <Headphones className="h-3.5 w-3.5 text-emerald-500" />
              <span>24/7 Support</span>
            </div>
          </div>
        </div>

        {/* Form Container */}
        <div className="px-4 pb-4" data-testid="public-ticket-form">
          <div className="space-y-5">
            
            {/* Customer Type */}
            <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
              <CardContent className="p-4">
                <SectionHeader icon={User} title="Customer Type" />
                <div className="grid grid-cols-2 gap-3">
                  {customerTypes.map((type) => {
                    const Icon = type.icon;
                    const isSelected = formData.customer_type === type.value;
                    return (
                      <button
                        key={type.value}
                        onClick={() => setFormData(prev => ({ ...prev, customer_type: type.value }))}
                        className={`relative p-4 rounded-xl border-2 transition-all duration-200 text-center ${
                          isSelected 
                            ? "border-emerald-500 bg-emerald-500/10" 
                            : "border-slate-800 bg-slate-800/30 active:scale-[0.98]"
                        }`}
                        data-testid={`customer-type-${type.value}`}
                      >
                        <div className={`mx-auto w-10 h-10 rounded-xl flex items-center justify-center mb-2 ${
                          isSelected ? "bg-emerald-500/20" : "bg-slate-700/50"
                        }`}>
                          <Icon className={`h-5 w-5 ${isSelected ? "text-emerald-400" : "text-slate-400"}`} />
                        </div>
                        <p className={`font-medium text-sm ${isSelected ? "text-emerald-400" : "text-white"}`}>
                          {type.label}
                        </p>
                        <p className="text-[10px] text-slate-500 mt-0.5">{type.description}</p>
                        {isSelected && (
                          <div className="absolute top-2 right-2">
                            <CheckCircle className="h-4 w-4 text-emerald-500" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Vehicle Information */}
            <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
              <CardContent className="p-4">
                <SectionHeader icon={Car} title="Vehicle Information" subtitle="Select your EV details" />
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Category <span className="text-emerald-500">*</span></Label>
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
                      <SelectTrigger className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base" data-testid="vehicle-category-select">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {categories.map((cat) => {
                          const Icon = categoryIcons[cat.code] || Car;
                          return (
                            <SelectItem key={cat.code} value={cat.code} className="py-3">
                              <div className="flex items-center gap-2">
                                <Icon className="h-4 w-4 text-emerald-500" />
                                {cat.name}
                              </div>
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Model (OEM)</Label>
                    <Select
                      value={formData.vehicle_model_id}
                      onValueChange={handleModelSelect}
                      disabled={!formData.vehicle_category}
                    >
                      <SelectTrigger className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base disabled:opacity-50" data-testid="vehicle-model-select">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700 max-h-60">
                        {Object.entries(modelsByOem).map(([oem, oemModels]) => (
                          <div key={oem}>
                            <div className="px-2 py-2 text-xs font-semibold text-emerald-400 bg-slate-900/80 sticky top-0">{oem}</div>
                            {oemModels.map((model) => (
                              <SelectItem key={model.model_id} value={model.model_id} className="py-3">
                                {model.name}
                              </SelectItem>
                            ))}
                          </div>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Vehicle Number <span className="text-emerald-500">*</span></Label>
                    <Input
                      placeholder="MH12AB1234"
                      className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base uppercase tracking-wider"
                      value={formData.vehicle_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, vehicle_number: e.target.value.toUpperCase() }))}
                      data-testid="vehicle-number-input"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Your Details */}
            <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
              <CardContent className="p-4">
                <SectionHeader icon={User} title="Your Details" subtitle="How can we reach you?" />
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Full Name <span className="text-emerald-500">*</span></Label>
                    <Input
                      placeholder="Your name"
                      className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base"
                      value={formData.customer_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, customer_name: e.target.value }))}
                      data-testid="customer-name-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Phone Number <span className="text-emerald-500">*</span></Label>
                    <div className="flex">
                      <div className="flex items-center px-4 bg-slate-800 border border-r-0 border-slate-700/50 rounded-l-xl text-sm text-slate-400 font-medium">
                        +91
                      </div>
                      <Input
                        type="tel"
                        placeholder="98765 43210"
                        className="h-12 bg-slate-800/50 border-slate-700/50 rounded-l-none rounded-r-xl text-base"
                        value={formData.contact_number}
                        onChange={(e) => setFormData(prev => ({ ...prev, contact_number: e.target.value }))}
                        data-testid="contact-number-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Email <span className="text-slate-500 text-xs">(Optional)</span></Label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <Input
                        type="email"
                        placeholder="your@email.com"
                        className="h-12 bg-slate-800/50 border-slate-700/50 pl-11 rounded-xl text-base"
                        value={formData.email}
                        onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                        data-testid="email-input"
                      />
                    </div>
                  </div>

                  {formData.customer_type === "business" && (
                    <>
                      <div className="space-y-2">
                        <Label className="text-slate-300 text-sm">Business Name</Label>
                        <Input
                          placeholder="Company name"
                          className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base"
                          value={formData.business_name}
                          onChange={(e) => setFormData(prev => ({ ...prev, business_name: e.target.value }))}
                          data-testid="business-name-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-slate-300 text-sm">GSTIN</Label>
                        <Input
                          placeholder="22AAAAA0000A1Z5"
                          className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base uppercase"
                          value={formData.gst_number}
                          onChange={(e) => setFormData(prev => ({ ...prev, gst_number: e.target.value.toUpperCase() }))}
                          data-testid="gst-number-input"
                        />
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Issue Details */}
            <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
              <CardContent className="p-4">
                <SectionHeader 
                  icon={Brain} 
                  title="What's the Issue?" 
                  subtitle="AI will suggest solutions"
                />
                <div className="space-y-4">
                  <div className="space-y-2 relative">
                    <div className="flex items-center justify-between">
                      <Label className="text-slate-300 text-sm">Issue <span className="text-emerald-500">*</span></Label>
                      {aiLoading && (
                        <span className="text-xs text-emerald-400 flex items-center gap-1">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Analyzing...
                        </span>
                      )}
                    </div>
                    <Input
                      placeholder="Describe the issue..."
                      className="h-12 bg-slate-800/50 border-slate-700/50 rounded-xl text-base"
                      value={formData.title}
                      onChange={(e) => handleTitleChange(e.target.value)}
                      onFocus={() => {
                        if (issueSuggestions.length > 0) setShowSuggestions(true);
                        if (aiSuggestions.length > 0) setShowAiSuggestions(true);
                      }}
                      data-testid="issue-title-input"
                    />
                    
                    {/* AI Suggestions Dropdown */}
                    {showAiSuggestions && aiSuggestions.length > 0 && (
                      <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-emerald-500/30 rounded-xl shadow-xl overflow-hidden">
                        <div className="p-2.5 text-xs text-emerald-400 border-b border-slate-700/50 flex items-center gap-2 bg-emerald-500/5">
                          <Brain className="h-3.5 w-3.5" />
                          <span className="font-medium">AI Suggestions</span>
                          <Sparkles className="h-3 w-3" />
                        </div>
                        <div className="max-h-48 overflow-y-auto">
                          {aiSuggestions.slice(0, 4).map((suggestion, idx) => (
                            <button
                              key={idx}
                              className="w-full px-4 py-3 text-left hover:bg-emerald-500/10 active:bg-emerald-500/20 border-b border-slate-700/30 last:border-b-0"
                              onClick={() => handleSuggestionSelect(suggestion)}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-white text-sm font-medium flex-1">{suggestion.title}</p>
                                <ChevronRight className="h-4 w-4 text-slate-500" />
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Details <span className="text-emerald-500">*</span></Label>
                    <Textarea
                      placeholder="When did it start? Any error codes?"
                      className="min-h-[100px] bg-slate-800/50 border-slate-700/50 rounded-xl text-base resize-none"
                      value={formData.description}
                      onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      data-testid="description-input"
                    />
                  </div>

                  {/* Priority - Horizontal Pills */}
                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">Priority</Label>
                    <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
                      {priorities.map((p) => {
                        const isSelected = formData.priority === p.value;
                        return (
                          <button
                            key={p.value}
                            onClick={() => setFormData(prev => ({ ...prev, priority: p.value }))}
                            className={`flex-shrink-0 px-4 py-2.5 rounded-full border-2 transition-all text-sm font-medium ${
                              isSelected 
                                ? `${p.color} border-transparent text-white` 
                                : `border-slate-700 bg-slate-800/30 ${p.textColor}`
                            }`}
                          >
                            {p.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Service Type */}
            <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
              <CardContent className="p-4">
                <SectionHeader icon={Wrench} title="Service Type" subtitle="How should we help?" />
                <div className="grid grid-cols-2 gap-3">
                  {resolutionTypes.map((r) => {
                    const Icon = r.icon;
                    const isSelected = formData.resolution_type === r.value;
                    return (
                      <button
                        key={r.value}
                        onClick={() => setFormData(prev => ({ ...prev, resolution_type: r.value }))}
                        className={`p-4 rounded-xl border-2 transition-all text-center ${
                          isSelected 
                            ? "border-emerald-500 bg-emerald-500/10" 
                            : "border-slate-800 bg-slate-800/30 active:scale-[0.98]"
                        }`}
                        data-testid={`resolution-${r.value}`}
                      >
                        <div className={`mx-auto w-10 h-10 rounded-xl flex items-center justify-center mb-2 ${
                          isSelected ? "bg-emerald-500/20" : "bg-slate-700/50"
                        }`}>
                          <Icon className={`h-5 w-5 ${isSelected ? "text-emerald-400" : "text-slate-400"}`} />
                        </div>
                        <p className={`font-medium text-sm ${isSelected ? "text-emerald-400" : "text-white"}`}>
                          {r.label}
                        </p>
                        <p className="text-[10px] text-slate-500 mt-0.5">{r.description}</p>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Location (for onsite) */}
            {formData.resolution_type === "onsite" && (
              <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
                <CardContent className="p-4">
                  <SectionHeader icon={MapPin} title="Your Location" subtitle="Where should we come?" />
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
                    placeholder="Tap to select location"
                    buttonText="Open Map"
                  />
                </CardContent>
              </Card>
            )}

            {/* Payment Info */}
            {requiresPayment() && (
              <Card className="border-0 bg-gradient-to-br from-amber-500/10 to-orange-500/5 rounded-2xl overflow-hidden">
                <CardContent className="p-4">
                  <SectionHeader icon={IndianRupee} title="Service Charges" />
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <Checkbox checked disabled className="bg-emerald-500 border-emerald-500" />
                        <span className="text-sm text-white">Visit Charges</span>
                      </div>
                      <span className="text-emerald-400 font-semibold">₹{serviceCharges.visit_fee}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <Checkbox 
                          checked={formData.include_diagnostic_fee}
                          onCheckedChange={(checked) => setFormData(prev => ({ ...prev, include_diagnostic_fee: !!checked }))}
                          className="border-slate-600"
                          data-testid="diagnostic-fee-checkbox"
                        />
                        <span className="text-sm text-white">Diagnostic Report</span>
                      </div>
                      <span className="text-slate-300 font-semibold">₹{serviceCharges.diagnostic_fee}</span>
                    </div>
                    <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
                      <span className="text-white font-semibold">Total</span>
                      <span className="text-emerald-400 text-xl font-bold">₹{calculateTotal()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Attachments */}
            <Card className="border-0 bg-slate-900/60 rounded-2xl overflow-hidden">
              <CardContent className="p-4">
                <SectionHeader icon={Upload} title="Photos" subtitle="Optional - helps diagnose faster" />
                <button 
                  className="w-full border-2 border-dashed border-slate-700/50 rounded-xl p-6 text-center active:scale-[0.99] active:bg-slate-800/30 transition-all"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-6 w-6 mx-auto mb-2 text-slate-500" />
                  <p className="text-sm text-slate-400">Tap to upload</p>
                  <p className="text-xs text-slate-600 mt-1">PNG, JPG up to 10MB</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </button>
                {attachments.length > 0 && (
                  <div className="grid grid-cols-3 gap-2 mt-3">
                    {attachments.map((att) => (
                      <div key={att.id} className="relative aspect-square rounded-lg overflow-hidden bg-slate-800">
                        {att.preview ? (
                          <img src={att.preview} alt="" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <FileText className="h-6 w-6 text-slate-400" />
                          </div>
                        )}
                        <button 
                          className="absolute top-1 right-1 p-1 bg-black/60 rounded-full"
                          onClick={() => removeAttachment(att.id)}
                        >
                          <X className="h-3 w-3 text-white" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Submit Button - Sticky on Mobile */}
            <div className="sticky bottom-0 -mx-4 px-4 py-3 bg-gradient-to-t from-slate-950 via-slate-950 to-transparent">
              <Button
                onClick={handleSubmit}
                disabled={submitting}
                className="w-full h-14 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-base font-semibold rounded-xl shadow-lg shadow-emerald-900/30 active:scale-[0.98] transition-all"
                data-testid="submit-ticket-btn"
              >
                {submitting ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : requiresPayment() ? (
                  <>
                    <CreditCard className="h-5 w-5 mr-2" />
                    Pay ₹{calculateTotal()}
                    <ArrowRight className="h-5 w-5 ml-2" />
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-5 w-5 mr-2" />
                    Submit Request
                    <ArrowRight className="h-5 w-5 ml-2" />
                  </>
                )}
              </Button>
            </div>

            {/* Quick Links */}
            <div className="flex items-center justify-center gap-4 text-xs text-slate-500 pt-2">
              <a href="/track-ticket" className="hover:text-emerald-400 active:text-emerald-500 transition-colors flex items-center gap-1">
                Track Ticket
                <ChevronRight className="h-3 w-3" />
              </a>
              <span className="text-slate-700">|</span>
              <a href="/login" className="hover:text-emerald-400 active:text-emerald-500 transition-colors flex items-center gap-1">
                Customer Portal
                <ChevronRight className="h-3 w-3" />
              </a>
            </div>

            <Footer />
          </div>
        </div>
      </div>
    );
  }

  // Step 2: Payment
  if (step === 2) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col">
        <div className="sticky top-0 z-50 bg-slate-950/95 backdrop-blur-lg border-b border-slate-800/50">
          <div className="px-4 py-3 flex items-center justify-center">
            <img 
              src="/battwheels_garages_logo.png" 
              alt="Battwheels Garages" 
              className="h-8 w-auto"
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center p-4">
          <Card className="border-0 bg-slate-900/80 rounded-2xl w-full max-w-sm overflow-hidden">
            <CardContent className="p-6 text-center space-y-6">
              <div className="inline-flex p-4 bg-emerald-500/20 rounded-2xl">
                <CreditCard className="h-10 w-10 text-emerald-400" />
              </div>
              
              <div>
                <h2 className="text-xl font-bold text-white">Complete Payment</h2>
                <p className="text-sm text-slate-400 mt-1">Confirm your service booking</p>
              </div>

              <div className="space-y-3 p-4 bg-slate-800/50 rounded-xl text-left">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Ticket ID</span>
                  <span className="text-emerald-400 font-mono font-medium">{ticketResult?.ticket_id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Visit Charges</span>
                  <span className="text-white">₹{paymentDetails?.visit_fee}</span>
                </div>
                {paymentDetails?.diagnostic_fee > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Diagnostic</span>
                    <span className="text-white">₹{paymentDetails?.diagnostic_fee}</span>
                  </div>
                )}
                <div className="flex justify-between pt-3 border-t border-slate-700/50">
                  <span className="text-white font-semibold">Total</span>
                  <span className="text-emerald-400 text-2xl font-bold">₹{paymentDetails?.amount}</span>
                </div>
              </div>

              {paymentDetails?.is_mock && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                  <p className="text-amber-400 text-xs">Test Mode - Payment simulated</p>
                </div>
              )}

              <Button
                onClick={handlePayment}
                className="w-full h-14 bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-base font-semibold rounded-xl active:scale-[0.98]"
                data-testid="pay-now-btn"
              >
                <IndianRupee className="h-5 w-5 mr-2" />
                Pay ₹{paymentDetails?.amount}
              </Button>
            </CardContent>
          </Card>
        </div>

        <Footer />
      </div>
    );
  }

  // Step 3: Success
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <div className="sticky top-0 z-50 bg-slate-950/95 backdrop-blur-lg border-b border-slate-800/50">
        <div className="px-4 py-3 flex items-center justify-center">
          <img 
            src="/battwheels_garages_logo.png" 
            alt="Battwheels Garages" 
            className="h-8 w-auto"
          />
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="border-0 bg-slate-900/80 rounded-2xl w-full max-w-sm overflow-hidden">
          {/* Success Header */}
          <div className="bg-gradient-to-br from-emerald-500/20 to-teal-500/10 p-8 text-center">
            <div className="inline-flex p-4 bg-emerald-500/30 rounded-full mb-4">
              <CheckCircle className="h-12 w-12 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold text-white">Request Submitted!</h2>
            <p className="text-slate-400 mt-1 text-sm">Your ticket has been created</p>
          </div>
          
          <CardContent className="p-6 space-y-5">
            <div className="p-4 bg-slate-800/50 rounded-xl text-center">
              <p className="text-slate-400 text-xs mb-1">TICKET ID</p>
              <p className="text-emerald-400 text-2xl font-mono font-bold tracking-wider">{ticketResult?.ticket_id}</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
                <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                <p className="text-sm text-slate-300">Confirmation sent to your phone</p>
              </div>
              <div className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
                <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                <p className="text-sm text-slate-300">Our team will contact you shortly</p>
              </div>
              <div className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
                <Brain className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                <p className="text-sm text-slate-300">EFI Intelligence is analyzing your issue</p>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <Button
                onClick={() => navigate(`/track-ticket?id=${ticketResult?.ticket_id}`)}
                className="w-full h-12 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold rounded-xl active:scale-[0.98]"
                data-testid="track-ticket-btn"
              >
                Track Your Ticket
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
              <Button
                variant="outline"
                onClick={() => { setStep(1); setFormData({ ...formData, title: "", description: "" }); }}
                className="w-full h-12 border-slate-700 hover:bg-slate-800 rounded-xl"
              >
                Submit Another Request
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Footer />
    </div>
  );
}
