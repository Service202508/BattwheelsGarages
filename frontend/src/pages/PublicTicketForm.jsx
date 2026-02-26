import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { 
  Car, User, MapPin, Upload, X, FileText, 
  Phone, Mail, Zap, Building2, IndianRupee, CreditCard,
  CheckCircle, Loader2, Bike, Truck, Bus, ArrowRight, Shield, Clock, Headphones,
  Brain, Sparkles, ChevronRight, Wrench, Camera, CheckCircle2
} from "lucide-react";
import LocationPicker from "@/components/LocationPicker";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Resolve the workshop slug from the current URL:
// workshopname.battwheels.com → "workshopname"
// Falls back to ?org query param for development / preview URLs
function getOrgSlug() {
  const hostname = window.location.hostname;
  const parts = hostname.split(".");
  if (parts.length >= 3 && !["www", "app", "api", "platform"].includes(parts[0])) {
    return parts[0];
  }
  const params = new URLSearchParams(window.location.search);
  return params.get("org") || null;
}

function getPublicHeaders() {
  const slug = getOrgSlug();
  const headers = { "Content-Type": "application/json" };
  if (slug) headers["X-Organization-Slug"] = slug;
  return headers;
}

// Customer types
const customerTypes = [
  { value: "individual", label: "Individual", icon: User, desc: "Personal EV Owner" },
  { value: "business", label: "Business / Fleet", icon: Building2, desc: "Company or Fleet" },
];

// Priority levels
const priorities = [
  { value: "low", label: "Low", desc: "Can wait", bgColor: "bg-[rgba(200,255,0,0.08)]", textColor: "text-[#C8FF00] text-700", borderColor: "border-[rgba(200,255,0,0.20)]", activeBg: "bg-[rgba(200,255,0,0.08)]0" },
  { value: "medium", label: "Medium", desc: "24-48h", bgColor: "bg-amber-50", textColor: "text-amber-700", borderColor: "border-amber-200", activeBg: "bg-amber-500" },
  { value: "high", label: "High", desc: "Urgent", bgColor: "bg-[rgba(255,140,0,0.08)]", textColor: "text-[#FF8C00]", borderColor: "border-orange-200", activeBg: "bg-[rgba(255,140,0,0.08)]0" },
  { value: "critical", label: "Critical", desc: "Immobile", bgColor: "bg-[rgba(255,59,47,0.08)]", textColor: "text-red-700", borderColor: "border-red-200", activeBg: "bg-[rgba(255,59,47,0.08)]0" },
];

// Category icons
const categoryIcons = { "2W_EV": Bike, "3W_EV": Truck, "4W_EV": Car, "COMM_EV": Bus, "LEV": Bike };

export default function PublicTicketForm() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  
  // Master data
  const [categories, setCategories] = useState([]);
  const [models, setModels] = useState([]);
  const [modelsByOem, setModelsByOem] = useState({});
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
    ticket_type: "onsite",
    incident_location: "",
    location_lat: null,
    location_lng: null,
    include_visit_fee: true,
    include_diagnostic_fee: false,
  });
  
  const [paymentDetails, setPaymentDetails] = useState(null);
  const [ticketResult, setTicketResult] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [showAiSuggestions, setShowAiSuggestions] = useState(false);
  const aiDebounceRef = useRef(null);

  useEffect(() => { fetchMasterData(); }, []);

  useEffect(() => {
    if (formData.vehicle_category) fetchModels(formData.vehicle_category);
  }, [formData.vehicle_category]);

  const fetchMasterData = async () => {
    try {
      const [catRes, chargesRes] = await Promise.all([
        fetch(`${API}/public/vehicle-categories`),
        fetch(`${API}/public/service-charges`)
      ]);
      if (catRes.ok) setCategories((await catRes.json()).categories || []);
      if (chargesRes.ok) {
        const d = await chargesRes.json();
        setServiceCharges({ visit_fee: d.visit_fee?.amount || 299, diagnostic_fee: d.diagnostic_fee?.amount || 199 });
      }
    } catch (e) { console.error(e); }
  };

  const fetchModels = async (categoryCode) => {
    try {
      const res = await fetch(`${API}/public/vehicle-models?category_code=${categoryCode}`);
      if (res.ok) {
        const d = await res.json();
        setModels(d.models || []);
        setModelsByOem(d.by_oem || {});
      }
    } catch (e) { console.error(e); }
  };

  const handleModelSelect = (modelId) => {
    const model = models.find(m => m.model_id === modelId);
    if (model) setFormData(prev => ({ ...prev, vehicle_model_id: modelId, vehicle_model_name: model.name, vehicle_oem: model.oem }));
  };

  const fetchAiSuggestions = async (userInput) => {
    if (!userInput || userInput.length < 3 || !formData.vehicle_category) return;
    setAiLoading(true);
    try {
      const res = await fetch(`${API}/public/ai/issue-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vehicle_category: formData.vehicle_category, vehicle_model: formData.vehicle_model_name, vehicle_oem: formData.vehicle_oem, user_input: userInput })
      });
      if (res.ok) {
        const d = await res.json();
        setAiSuggestions(d.suggestions || []);
        if (d.suggestions?.length > 0) setShowAiSuggestions(true);
      }
    } catch (e) { console.error(e); }
    finally { setAiLoading(false); }
  };

  const handleTitleChange = (value) => {
    setFormData(prev => ({ ...prev, title: value }));
    if (aiDebounceRef.current) clearTimeout(aiDebounceRef.current);
    if (value.length >= 3) aiDebounceRef.current = setTimeout(() => fetchAiSuggestions(value), 500);
    else setShowAiSuggestions(false);
  };

  const handleSuggestionSelect = (s) => {
    setFormData(prev => ({ ...prev, title: s.title, issue_type: s.issue_type || "general" }));
    setShowAiSuggestions(false);
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    const newAtts = files.map(f => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2,9)}`,
      file: f, name: f.name, size: f.size, type: f.type,
      preview: f.type.startsWith('image/') ? URL.createObjectURL(f) : null
    }));
    setAttachments(prev => [...prev, ...newAtts]);
  };

  const removeAttachment = (id) => {
    setAttachments(prev => {
      const att = prev.find(a => a.id === id);
      if (att?.preview) URL.revokeObjectURL(att.preview);
      return prev.filter(a => a.id !== id);
    });
  };

  const validateForm = () => {
    if (!formData.vehicle_category) { toast.error("Please select vehicle category"); return false; }
    if (!formData.vehicle_number) { toast.error("Please enter vehicle number"); return false; }
    if (!formData.customer_name) { toast.error("Please enter your name"); return false; }
    if (!formData.contact_number) { toast.error("Please enter contact number"); return false; }
    if (!formData.title) { toast.error("Please describe the issue"); return false; }
    if (!formData.description) { toast.error("Please provide issue details"); return false; }
    if (formData.incident_location && formData.incident_location.trim()) { /* location provided */ }
    return true;
  };

  const requiresPayment = () => formData.customer_type === "individual" && formData.include_visit_fee;
  const calculateTotal = () => !requiresPayment() ? 0 : serviceCharges.visit_fee + (formData.include_diagnostic_fee ? serviceCharges.diagnostic_fee : 0);

  const handleSubmit = async () => {
    if (!validateForm()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/public/tickets/submit`, {
        method: "POST",
        headers: getPublicHeaders(),
        body: JSON.stringify({ ...formData, include_visit_fee: requiresPayment() })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to submit");
      if (data.requires_payment) { setPaymentDetails(data.payment_details); setTicketResult(data); setStep(2); }
      else { setTicketResult(data); setStep(3); toast.success("Ticket submitted!"); }
    } catch (e) { toast.error(e.message); }
    finally { setSubmitting(false); }
  };

  const handlePayment = async () => {
    if (!paymentDetails) return;
    if (paymentDetails.is_mock) {
      const res = await fetch(`${API}/public/tickets/verify-payment`, {
        method: "POST", headers: getPublicHeaders(),
        body: JSON.stringify({ ticket_id: ticketResult.ticket_id, razorpay_order_id: paymentDetails.order_id, razorpay_payment_id: `pay_mock_${Date.now()}`, razorpay_signature: "mock" })
      });
      if (res.ok) { setStep(3); toast.success("Payment successful!"); }
      return;
    }
    const rzp = new window.Razorpay({
      key: paymentDetails.key_id, amount: paymentDetails.amount_paise, currency: "INR",
      name: "Battwheels Garages", description: "Service Charges", order_id: paymentDetails.order_id,
      handler: async (r) => {
        const res = await fetch(`${API}/public/tickets/verify-payment`, {
          method: "POST", headers: getPublicHeaders(),
          body: JSON.stringify({ ticket_id: ticketResult.ticket_id, ...r })
        });
        if (res.ok) { setStep(3); toast.success("Payment successful!"); }
      },
      prefill: { name: formData.customer_name, email: formData.email, contact: formData.contact_number },
      theme: { color: "#10b981" }
    });
    rzp.open();
  };

  // =============== COMPONENTS ===============

  const SectionCard = ({ children, className = "", gradient = false }) => (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`bg-[#111820] rounded border border-[rgba(255,255,255,0.07)] p-5 md:p-6 ${gradient ? 'bg-gradient-to-br from-white to-emerald-50/30' : ''} ${className}`}
    >
      {children}
    </motion.div>
  );

  const SectionHeader = ({ icon: Icon, title, subtitle, badge }) => (
    <div className="flex items-start gap-3 mb-5">
      <div className="w-10 h-10 rounded bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-white" strokeWidth={2} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-[#F4F6F0]">{title}</h3>
          {badge && (
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-full shadow-sm">
              {badge}
            </span>
          )}
        </div>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );

  const StyledInput = ({ className = "", ...props }) => (
    <Input
      className={`h-12 bg-[#14141B] border-2 border-[rgba(244,246,240,0.12)] focus:border-[rgba(200,255,0,0.50)] focus:bg-[#111820] focus:ring-4 focus:ring-emerald-500/10 rounded text-[#F4F6F0] text-base placeholder:text-[rgba(244,246,240,0.3)] transition-all duration-200 ${className}`}
      {...props}
    />
  );

  const Footer = () => (
    <footer className="text-center py-8 mt-6">
      <div className="flex items-center justify-center gap-2 mb-3">
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full">
          <Brain className="w-3.5 h-3.5 text-white" strokeWidth={2} />
          <span className="text-xs font-semibold text-white">Powered by EFI Intelligence</span>
          <Sparkles className="w-3 h-3 text-white" />
        </div>
      </div>
      <p className="text-xs text-gray-400 leading-relaxed">
        © 2026 BATTWHEELS SERVICES PRIVATE LIMITED.<br />All rights reserved.
      </p>
    </footer>
  );

  // =============== STEP 1: FORM ===============
  if (step === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-emerald-50/30">
        {/* Header */}
        <header className="sticky top-0 z-50 bg-[#111820]/80 backdrop-blur-xl border-b border-gray-100 shadow-sm">
          <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
            <img src="/battwheels_garages_logo.png" alt="Battwheels Garages" className="h-10 invert" />
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.20)] rounded-full">
              <div className="w-2 h-2 bg-[rgba(200,255,0,0.08)]0 rounded-full animate-pulse" />
              <span className="text-xs font-semibold text-[#C8FF00] text-700">EFI Active</span>
            </div>
          </div>
        </header>

        {/* Hero */}
        <div className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-transparent to-transparent" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gradient-to-b from-emerald-400/10 to-transparent rounded-full blur-3xl" />
          
          <div className="max-w-2xl mx-auto px-4 pt-8 pb-6 relative">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
              <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-gray-900 via-emerald-800 to-teal-800 bg-clip-text text-transparent">
                EV Service Request
              </h1>
              <p className="text-gray-500 mt-2">AI-powered diagnostics for your electric vehicle</p>
            </motion.div>

            {/* Trust Badges */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="flex justify-center gap-2 mt-6 flex-wrap">
              {[
                { icon: Shield, label: "Certified", color: "emerald" },
                { icon: Clock, label: "Quick Response", color: "blue" },
                { icon: Headphones, label: "24/7 Support", color: "purple" }
              ].map((b, i) => (
                <div key={i} className={`flex items-center gap-2 px-4 py-2 bg-[#111820] rounded-full shadow-sm border border-gray-100`}>
                  <b.icon className={`w-4 h-4 text-${b.color}-500`} strokeWidth={2} />
                  <span className="text-xs font-medium text-[rgba(244,246,240,0.7)]">{b.label}</span>
                </div>
              ))}
            </motion.div>
          </div>
        </div>

        {/* Form */}
        <div className="max-w-2xl mx-auto px-4 pb-8 space-y-4" data-testid="public-ticket-form">
          
          {/* Customer Type */}
          <SectionCard>
            <SectionHeader icon={User} title="Customer Type" />
            <div className="grid grid-cols-2 gap-3">
              {customerTypes.map((type) => {
                const Icon = type.icon;
                const isSelected = formData.customer_type === type.value;
                return (
                  <motion.button
                    key={type.value}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setFormData(prev => ({ ...prev, customer_type: type.value }))}
                    className={`relative p-5 rounded border-2 transition-all duration-200 text-left ${
                      isSelected 
                        ? "border-[rgba(200,255,0,0.50)] bg-gradient-to-br from-emerald-50 to-teal-50" 
                        : "border-gray-200 bg-[#111820] hover:border-gray-300"
                    }`}
                    data-testid={`customer-type-${type.value}`}
                  >
                    <div className={`w-12 h-12 rounded flex items-center justify-center mb-3 ${
                      isSelected ? "bg-gradient-to-br from-emerald-500 to-teal-500" : "bg-[rgba(255,255,255,0.05)]"
                    }`}>
                      <Icon className={`w-6 h-6 ${isSelected ? "text-white" : "text-gray-500"}`} strokeWidth={2} />
                    </div>
                    <p className={`font-semibold ${isSelected ? "text-[#C8FF00] text-700" : "text-[#F4F6F0]"}`}>{type.label}</p>
                    <p className="text-xs text-gray-500 mt-1">{type.desc}</p>
                    {isSelected && (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute top-3 right-3">
                        <CheckCircle2 className="w-6 h-6 text-[#C8FF00] text-500" fill="#10b981" stroke="white" />
                      </motion.div>
                    )}
                  </motion.button>
                );
              })}
            </div>
          </SectionCard>

          {/* Vehicle Details */}
          <SectionCard>
            <SectionHeader icon={Car} title="Vehicle Details" subtitle="Enter your EV information" />
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Category <span className="text-[#C8FF00] text-500">*</span></Label>
                  <Select value={formData.vehicle_category} onValueChange={(v) => setFormData(prev => ({ ...prev, vehicle_category: v, vehicle_model_id: "", vehicle_model_name: "", vehicle_oem: "" }))}>
                    <SelectTrigger className="h-12 bg-[#14141B] border-2 border-[rgba(244,246,240,0.12)] focus:border-[rgba(200,255,0,0.50)] rounded text-[#F4F6F0]" data-testid="vehicle-category-select">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#111820] border-gray-200 rounded border border-[rgba(255,255,255,0.13)]">
                      {categories.map((cat) => {
                        const Icon = categoryIcons[cat.code] || Car;
                        return (
                          <SelectItem key={cat.code} value={cat.code} className="hover:bg-[rgba(200,255,0,0.08)] focus:bg-[rgba(200,255,0,0.08)] rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-[rgba(200,255,0,0.10)] flex items-center justify-center">
                                <Icon className="w-4 h-4 text-[#C8FF00] text-600" />
                              </div>
                              <span className="font-medium">{cat.name}</span>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Model (OEM)</Label>
                  <Select value={formData.vehicle_model_id} onValueChange={handleModelSelect} disabled={!formData.vehicle_category}>
                    <SelectTrigger className="h-12 bg-[#14141B] border-2 border-[rgba(244,246,240,0.12)] focus:border-[rgba(200,255,0,0.50)] rounded text-[#F4F6F0] disabled:opacity-50" data-testid="vehicle-model-select">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#111820] border-gray-200 rounded border border-[rgba(255,255,255,0.13)] max-h-60">
                      {Object.entries(modelsByOem).map(([oem, oemModels]) => (
                        <div key={oem}>
                          <div className="px-3 py-2 text-xs font-bold text-[#C8FF00] text-600 bg-[rgba(200,255,0,0.08)] sticky top-0">{oem}</div>
                          {oemModels.map((m) => (
                            <SelectItem key={m.model_id} value={m.model_id} className="hover:bg-[rgba(200,255,0,0.08)] rounded-lg">{m.name}</SelectItem>
                          ))}
                        </div>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Vehicle Number <span className="text-[#C8FF00] text-500">*</span></Label>
                <StyledInput placeholder="MH12AB1234" value={formData.vehicle_number} onChange={(e) => setFormData(prev => ({ ...prev, vehicle_number: e.target.value.toUpperCase() }))} className="uppercase tracking-widest font-mono text-lg" data-testid="vehicle-number-input" />
              </div>
            </div>
          </SectionCard>

          {/* Contact Details */}
          <SectionCard>
            <SectionHeader icon={Phone} title="Contact Details" subtitle="How can we reach you?" />
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Full Name <span className="text-[#C8FF00] text-500">*</span></Label>
                  <StyledInput placeholder="Enter your name" value={formData.customer_name} onChange={(e) => setFormData(prev => ({ ...prev, customer_name: e.target.value }))} data-testid="customer-name-input" />
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Phone Number <span className="text-[#C8FF00] text-500">*</span></Label>
                  <div className="flex">
                    <div className="flex items-center px-4 bg-[rgba(200,255,0,0.08)] border-2 border-r-0 border-[rgba(200,255,0,0.20)] rounded-l-xl text-sm font-semibold text-[#C8FF00] text-700">+91</div>
                    <StyledInput type="tel" placeholder="9876543210" value={formData.contact_number} onChange={(e) => setFormData(prev => ({ ...prev, contact_number: e.target.value }))} className="rounded-l-none" data-testid="contact-number-input" />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Email <span className="text-gray-400">(Optional)</span></Label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <StyledInput type="email" placeholder="you@example.com" value={formData.email} onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))} className="pl-12" data-testid="email-input" />
                </div>
              </div>
              {formData.customer_type === "business" && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Business Name</Label>
                    <StyledInput placeholder="Company name" value={formData.business_name} onChange={(e) => setFormData(prev => ({ ...prev, business_name: e.target.value }))} data-testid="business-name-input" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">GSTIN</Label>
                    <StyledInput placeholder="22AAAAA0000A1Z5" value={formData.gst_number} onChange={(e) => setFormData(prev => ({ ...prev, gst_number: e.target.value.toUpperCase() }))} className="uppercase font-mono" data-testid="gst-number-input" />
                  </div>
                </motion.div>
              )}
            </div>
          </SectionCard>

          {/* Issue Details */}
          <SectionCard gradient>
            <SectionHeader icon={Brain} title="Describe Your Issue" subtitle="AI will analyze and suggest solutions" badge="AI" />
            <div className="space-y-4">
              <div className="space-y-2 relative">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Issue <span className="text-[#C8FF00] text-500">*</span></Label>
                  {aiLoading && <span className="flex items-center gap-1.5 text-xs text-[#C8FF00] text-600"><Loader2 className="w-3 h-3 animate-spin" />Analyzing...</span>}
                </div>
                <StyledInput placeholder="e.g., Battery not charging, motor noise..." value={formData.title} onChange={(e) => handleTitleChange(e.target.value)} onFocus={() => { if (aiSuggestions.length > 0) setShowAiSuggestions(true); }} data-testid="issue-title-input" />
                
                <AnimatePresence>
                  {showAiSuggestions && aiSuggestions.length > 0 && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="absolute z-50 w-full mt-2 bg-[#111820] border-2 border-[rgba(200,255,0,0.20)] rounded border border-[rgba(255,255,255,0.13)] overflow-hidden">
                      <div className="px-4 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center gap-2">
                        <Brain className="w-4 h-4 text-white" />
                        <span className="text-sm font-semibold text-white">AI Suggestions</span>
                        <Sparkles className="w-3 h-3 text-white" />
                      </div>
                      <div className="max-h-48 overflow-y-auto">
                        {aiSuggestions.slice(0, 4).map((s, i) => (
                          <button key={i} onClick={() => handleSuggestionSelect(s)} className="w-full px-4 py-3 text-left hover:bg-[rgba(200,255,0,0.08)] transition-colors border-b border-gray-100 last:border-b-0 flex items-center justify-between group">
                            <span className="text-sm text-[rgba(244,246,240,0.7)] font-medium">{s.title}</span>
                            <ChevronRight className="w-4 h-4 text-[rgba(244,246,240,0.20)] group-hover:text-[#C8FF00] text-500 transition-colors" />
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Detailed Description <span className="text-[#C8FF00] text-500">*</span></Label>
                <Textarea placeholder="Describe symptoms, when it started, error codes..." value={formData.description} onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))} className="min-h-[120px] bg-[#14141B] border-2 border-[rgba(244,246,240,0.12)] focus:border-[rgba(200,255,0,0.50)] focus:bg-[#111820] focus:ring-4 focus:ring-emerald-500/10 rounded text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.3)] resize-none" data-testid="description-input" />
              </div>

              {/* Priority */}
              <div className="space-y-3">
                <Label className="text-sm font-medium text-[rgba(244,246,240,0.7)]">Priority Level</Label>
                <div className="flex flex-wrap gap-2">
                  {priorities.map((p) => {
                    const isSelected = formData.priority === p.value;
                    return (
                      <motion.button key={p.value} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => setFormData(prev => ({ ...prev, priority: p.value }))}
                        className={`px-4 py-2.5 rounded border-2 transition-all duration-200 ${isSelected ? `${p.activeBg} text-white border-transparent` : `${p.bgColor} ${p.textColor} ${p.borderColor}`}`}
                        data-testid={`priority-${p.value}`}>
                        <span className="text-sm font-semibold">{p.label}</span>
                      </motion.button>
                    );
                  })}
                </div>
              </div>
            </div>
          </SectionCard>

          {/* Service Location */}
          <SectionCard>
            <SectionHeader icon={MapPin} title="Service Location" subtitle="Where is the vehicle?" />
            <LocationPicker value={formData.incident_location ? { address: formData.incident_location, lat: formData.location_lat, lng: formData.location_lng } : null} onChange={(loc) => setFormData(prev => ({ ...prev, incident_location: loc.address, location_lat: loc.lat, location_lng: loc.lng }))} placeholder="Tap to select location" buttonText="Open Map" />
          </SectionCard>

          {/* Payment */}
          {requiresPayment() && (
            <SectionCard className="border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50">
              <SectionHeader icon={IndianRupee} title="Service Charges" subtitle="Doorstep service requires advance payment" />
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 bg-[#111820] rounded border border-[rgba(255,255,255,0.07)]">
                  <div className="flex items-center gap-3">
                    <Checkbox checked disabled className="bg-[rgba(200,255,0,0.08)]0 border-[rgba(200,255,0,0.50)]" />
                    <div><p className="text-sm font-medium text-[#F4F6F0]">Visit Charges</p><p className="text-xs text-gray-500">Mandatory</p></div>
                  </div>
                  <span className="text-lg font-bold text-[#C8FF00] text-600">₹{serviceCharges.visit_fee}</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-[#111820] rounded border border-[rgba(255,255,255,0.07)]">
                  <div className="flex items-center gap-3">
                    <Checkbox checked={formData.include_diagnostic_fee} onCheckedChange={(c) => setFormData(prev => ({ ...prev, include_diagnostic_fee: !!c }))} className="border-gray-300" data-testid="diagnostic-fee-checkbox" />
                    <div><p className="text-sm font-medium text-[#F4F6F0]">Diagnostic Report</p><p className="text-xs text-gray-500">Optional</p></div>
                  </div>
                  <span className="text-lg font-semibold text-gray-600">₹{serviceCharges.diagnostic_fee}</span>
                </div>
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <span className="font-semibold text-[#F4F6F0]">Total Amount</span>
                  <span className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">₹{calculateTotal()}</span>
                </div>
              </div>
            </SectionCard>
          )}

          {/* Photos */}
          <SectionCard>
            <SectionHeader icon={Camera} title="Attach Photos" subtitle="Optional - helps diagnose faster" />
            <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} onClick={() => fileInputRef.current?.click()}
              className="w-full p-8 border-2 border-dashed border-gray-200 rounded hover:border-emerald-400 hover:bg-[rgba(200,255,0,0.08)]/50 transition-all duration-200 group">
              <div className="w-14 h-14 mx-auto mb-3 rounded bg-[rgba(255,255,255,0.05)] group-hover:bg-[rgba(200,255,0,0.10)] flex items-center justify-center transition-colors">
                <Upload className="w-7 h-7 text-gray-400 group-hover:text-[#C8FF00] text-500" />
              </div>
              <p className="text-sm font-medium text-gray-600 group-hover:text-[#C8FF00] text-700">Tap to upload photos</p>
              <p className="text-xs text-gray-400 mt-1">PNG, JPG up to 10MB</p>
              <input ref={fileInputRef} type="file" multiple accept="image/*" className="hidden" onChange={handleFileChange} />
            </motion.button>
            {attachments.length > 0 && (
              <div className="grid grid-cols-3 gap-3 mt-4">
                {attachments.map((att) => (
                  <div key={att.id} className="relative aspect-square rounded overflow-hidden bg-[rgba(255,255,255,0.05)] border border-gray-200">
                    {att.preview ? <img src={att.preview} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><FileText className="w-6 h-6 text-gray-400" /></div>}
                    <button onClick={() => removeAttachment(att.id)} className="absolute top-2 right-2 p-1.5 bg-[#111820]/90 hover:bg-[rgba(255,59,47,0.08)]0 hover:text-white rounded-full transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          {/* Submit */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="sticky bottom-4 pt-4">
            <Button onClick={handleSubmit} disabled={submitting}
              className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-lg font-bold rounded hover:shadow-[0_0_20px_rgba(16,185,129,0.30)] transition-all duration-200"
              data-testid="submit-ticket-btn">
              {submitting ? <Loader2 className="w-6 h-6 animate-spin" /> : requiresPayment() ? (
                <><CreditCard className="w-5 h-5 mr-2" />Proceed to Pay ₹{calculateTotal()}<ArrowRight className="w-5 h-5 ml-2" /></>
              ) : (
                <><CheckCircle className="w-5 h-5 mr-2" />Submit Request<ArrowRight className="w-5 h-5 ml-2" /></>
              )}
            </Button>
          </motion.div>

          {/* Links */}
          <div className="flex items-center justify-center gap-6 text-sm text-gray-500 pt-2">
            <a href="/track-ticket" className="hover:text-[#C8FF00] text-600 transition-colors flex items-center gap-1 font-medium">Track Ticket <ChevronRight className="w-4 h-4" /></a>
            <span className="text-[rgba(244,246,240,0.20)]">|</span>
            <a href="/login" className="hover:text-[#C8FF00] text-600 transition-colors flex items-center gap-1 font-medium">Customer Portal <ChevronRight className="w-4 h-4" /></a>
          </div>

          <Footer />
        </div>
      </div>
    );
  }

  // =============== STEP 2: PAYMENT ===============
  if (step === 2) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-emerald-50/30 flex flex-col">
        <header className="bg-[#111820]/80 backdrop-blur-xl border-b border-gray-100">
          <div className="max-w-md mx-auto px-4 py-4 flex justify-center">
            <img src="/battwheels_garages_logo.png" alt="Battwheels Garages" className="h-10 invert" />
          </div>
        </header>

        <div className="flex-1 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-md bg-[#111820] rounded border border-[rgba(255,255,255,0.13)] overflow-hidden">
            <div className="p-8 text-center bg-gradient-to-br from-emerald-50 to-teal-50">
              <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-emerald-500 to-teal-500 rounded flex items-center justify-center">
                <CreditCard className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-[#F4F6F0]">Complete Payment</h2>
              <p className="text-gray-500 mt-1">Confirm your service booking</p>
            </div>
            <div className="p-6 space-y-4">
              <div className="p-4 bg-[#14141B] rounded space-y-3">
                <div className="flex justify-between text-sm"><span className="text-gray-500">Ticket ID</span><span className="text-[#C8FF00] text-600 font-mono font-bold">{ticketResult?.ticket_id}</span></div>
                <div className="flex justify-between text-sm"><span className="text-gray-500">Visit Charges</span><span className="text-[#F4F6F0] font-medium">₹{paymentDetails?.visit_fee}</span></div>
                {paymentDetails?.diagnostic_fee > 0 && <div className="flex justify-between text-sm"><span className="text-gray-500">Diagnostic</span><span className="text-[#F4F6F0] font-medium">₹{paymentDetails?.diagnostic_fee}</span></div>}
                <div className="flex justify-between pt-3 border-t border-gray-200"><span className="font-semibold text-[#F4F6F0]">Total</span><span className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">₹{paymentDetails?.amount}</span></div>
              </div>
              {paymentDetails?.is_mock && <div className="p-3 bg-amber-50 border border-amber-200 rounded"><p className="text-sm text-amber-700 text-center font-medium">Test Mode - Payment will be simulated</p></div>}
              <Button onClick={handlePayment} className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold text-lg rounded hover:shadow-[0_0_20px_rgba(16,185,129,0.30)]" data-testid="pay-now-btn">
                <IndianRupee className="w-5 h-5 mr-2" />Pay ₹{paymentDetails?.amount}
              </Button>
            </div>
          </motion.div>
        </div>
        <Footer />
      </div>
    );
  }

  // =============== STEP 3: SUCCESS ===============
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-emerald-50/30 flex flex-col">
      <header className="bg-[#111820]/80 backdrop-blur-xl border-b border-gray-100">
        <div className="max-w-md mx-auto px-4 py-4 flex justify-center">
          <img src="/battwheels_garages_logo.png" alt="Battwheels Garages" className="h-10 invert" />
        </div>
      </header>

      <div className="flex-1 flex items-center justify-center p-4">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-md bg-[#111820] rounded border border-[rgba(255,255,255,0.13)] overflow-hidden">
          <div className="relative p-8 text-center bg-gradient-to-br from-emerald-500 to-teal-500">
            <div className="absolute inset-0 opacity-10" style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "20px 20px" }} />
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", delay: 0.2 }} className="relative w-20 h-20 mx-auto mb-4 bg-[#111820] rounded-full flex items-center justify-center shadow-2xl">
              <CheckCircle className="w-10 h-10 text-[#C8FF00] text-500" fill="#d1fae5" />
            </motion.div>
            <h2 className="text-2xl font-bold text-white mb-1">Request Submitted!</h2>
            <p className="text-[#C8FF00] text-100">Your service ticket has been created</p>
          </div>

          <div className="p-6 space-y-5">
            <div className="p-5 bg-gradient-to-br from-emerald-50 to-teal-50 rounded text-center border border-emerald-100">
              <p className="text-xs text-[#C8FF00] text-600 uppercase tracking-wider font-semibold mb-1">Ticket ID</p>
              <p className="text-3xl font-mono font-bold text-[#F4F6F0] tracking-wider">{ticketResult?.ticket_id}</p>
            </div>

            <div className="space-y-3">
              {[
                { icon: CheckCircle, text: "Confirmation sent to your phone", color: "emerald" },
                { icon: Clock, text: "Our team will contact you shortly", color: "blue" },
                { icon: Brain, text: "EFI Intelligence is analyzing your issue", color: "purple" }
              ].map((item, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.1 }}
                  className="flex items-center gap-3 p-3 bg-[#14141B] rounded">
                  <div className={`w-8 h-8 rounded-lg bg-${item.color}-100 flex items-center justify-center`}>
                    <item.icon className={`w-4 h-4 text-${item.color}-600`} />
                  </div>
                  <p className="text-sm text-[rgba(244,246,240,0.7)] font-medium">{item.text}</p>
                </motion.div>
              ))}
            </div>

            <div className="space-y-3 pt-2">
              <Button onClick={() => navigate(`/track-ticket?id=${ticketResult?.ticket_id}`)} className="w-full h-12 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold rounded hover:shadow-[0_0_20px_rgba(16,185,129,0.30)]" data-testid="track-ticket-btn">
                Track Your Ticket<ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <Button variant="outline" onClick={() => { setStep(1); setFormData({ ...formData, title: "", description: "" }); }} className="w-full h-12 border-[rgba(244,246,240,0.15)] hover:bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.7)] font-medium rounded">
                Submit Another Request
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}
