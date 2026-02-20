import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import {
  Sparkles, Send, Loader2, Bot, 
  Battery, Wrench, Plug, Zap, Settings, Code, ArrowUpDown, 
  CircleDot, Thermometer, Wind, HelpCircle,
  Bike, Truck, Car, CheckCircle, AlertTriangle, Lightbulb,
  Copy, RotateCcw, Brain, Target, Shield, Clock, FileText,
  ChevronRight, Cpu, CircuitBoard
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// Enhanced issue categories with gradient colors
const ISSUE_CATEGORIES = [
  { id: "battery", label: "Battery Issues", icon: Battery, gradient: "from-amber-500 to-orange-600", bgLight: "bg-amber-50 dark:bg-amber-900/20" },
  { id: "motor", label: "Motor Problems", icon: Cpu, gradient: "from-blue-500 to-indigo-600", bgLight: "bg-blue-50 dark:bg-blue-900/20" },
  { id: "charging", label: "Charging System", icon: Plug, gradient: "from-emerald-500 to-teal-600", bgLight: "bg-emerald-50 dark:bg-emerald-900/20" },
  { id: "electrical", label: "Electrical", icon: Zap, gradient: "from-yellow-500 to-amber-600", bgLight: "bg-yellow-50 dark:bg-yellow-900/20" },
  { id: "mechanical", label: "Mechanical", icon: Settings, gradient: "from-slate-500 to-gray-600", bgLight: "bg-slate-50 dark:bg-slate-900/20" },
  { id: "software", label: "Software Issues", icon: Code, gradient: "from-purple-500 to-violet-600", bgLight: "bg-purple-50 dark:bg-purple-900/20" },
  { id: "suspension", label: "Suspension", icon: ArrowUpDown, gradient: "from-cyan-500 to-blue-600", bgLight: "bg-cyan-50 dark:bg-cyan-900/20" },
  { id: "braking", label: "Braking System", icon: CircleDot, gradient: "from-red-500 to-rose-600", bgLight: "bg-red-50 dark:bg-red-900/20" },
  { id: "cooling", label: "Cooling System", icon: Thermometer, gradient: "from-sky-500 to-cyan-600", bgLight: "bg-sky-50 dark:bg-sky-900/20" },
  { id: "hvac", label: "AC/Heating", icon: Wind, gradient: "from-teal-500 to-emerald-600", bgLight: "bg-teal-50 dark:bg-teal-900/20" },
  { id: "other", label: "Other", icon: HelpCircle, gradient: "from-gray-500 to-slate-600", bgLight: "bg-gray-50 dark:bg-gray-900/20" },
];

// Vehicle categories with icons
const VEHICLE_CATEGORIES = [
  { id: "2_wheeler", label: "2 Wheeler", icon: Bike, gradient: "from-emerald-500 to-teal-600" },
  { id: "3_wheeler", label: "3 Wheeler", icon: Truck, gradient: "from-blue-500 to-indigo-600" },
  { id: "4_wheeler_commercial", label: "4W Commercial", icon: Truck, gradient: "from-orange-500 to-amber-600" },
  { id: "car", label: "Car", icon: Car, gradient: "from-violet-500 to-purple-600" },
];

// Vehicle models by category
const VEHICLE_MODELS = {
  "2_wheeler": [
    "Ola S1 Pro", "Ola S1 Air", "Ola S1 X", "Ather 450X", "Ather 450S", "Ather Rizta",
    "TVS iQube", "TVS iQube ST", "Hero Vida V1", "Hero Electric Optima",
    "Bajaj Chetak", "Simple One", "Okinawa Praise Pro", "Ampere Magnus",
    "Revolt RV400", "Ultraviolette F77", "Other 2 Wheeler"
  ],
  "3_wheeler": [
    "Mahindra Treo", "Mahindra Treo Zor", "Piaggio Ape E-City", "Piaggio Ape E-Xtra",
    "Euler HiLoad", "OSM Rage+", "Kinetic Safar", "YC Electric Yatri",
    "Altigreen neEV", "Other 3 Wheeler"
  ],
  "4_wheeler_commercial": [
    "Tata Ace EV", "Mahindra Zeo", "Euler Storm EV", "OSM Stream",
    "Omega Seiki Stream", "Other Commercial EV"
  ],
  "car": [
    "Tata Nexon EV", "Tata Nexon EV Max", "Tata Tigor EV", "Tata Punch EV",
    "Tata Tiago EV", "Tata Curvv EV", "MG ZS EV", "MG Comet EV",
    "Hyundai Kona Electric", "Hyundai Ioniq 5", "Kia EV6", "BYD Atto 3",
    "BYD e6", "Mahindra XUV400", "Citroen eC3", "Other Car"
  ]
};

export default function AIDiagnosticAssistant({ user, ticketContext = null }) {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedVehicleType, setSelectedVehicleType] = useState(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [issueDescription, setIssueDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [dtcCodes, setDtcCodes] = useState("");

  // Pre-fill from ticket context if available
  useEffect(() => {
    if (ticketContext) {
      setIssueDescription(ticketContext.description || "");
      if (ticketContext.category) {
        const category = ISSUE_CATEGORIES.find(c => 
          c.id === ticketContext.category || c.label.toLowerCase().includes(ticketContext.category.toLowerCase())
        );
        if (category) setSelectedCategory(category.id);
      }
      if (ticketContext.vehicle_type) {
        const vehicleType = VEHICLE_CATEGORIES.find(v => 
          v.id === ticketContext.vehicle_type || v.label.toLowerCase().includes(ticketContext.vehicle_type.toLowerCase())
        );
        if (vehicleType) setSelectedVehicleType(vehicleType.id);
      }
      if (ticketContext.vehicle_model) {
        setSelectedModel(ticketContext.vehicle_model);
      }
    }
  }, [ticketContext]);

  const handleGetDiagnosis = async () => {
    if (!issueDescription.trim()) {
      toast.error("Please describe the issue");
      return;
    }

    setLoading(true);
    setDiagnosis(null);

    try {
      const categoryLabel = ISSUE_CATEGORIES.find(c => c.id === selectedCategory)?.label || "General";
      const vehicleTypeLabel = VEHICLE_CATEGORIES.find(v => v.id === selectedVehicleType)?.label || "Unknown";
      
      const contextInfo = `
Vehicle Type: ${vehicleTypeLabel}
Vehicle Model: ${selectedModel || "Not specified"}
Issue Category: ${categoryLabel}
${dtcCodes ? `DTC Codes: ${dtcCodes}` : ""}
${ticketContext?.ticket_id ? `Ticket ID: ${ticketContext.ticket_id}` : ""}
      `.trim();

      const fullQuery = `${contextInfo}

Issue Description:
${issueDescription}

Please provide:
1. Likely root causes (in order of probability)
2. Diagnostic steps to confirm the issue
3. Recommended repair procedure
4. Required parts/tools
5. Safety precautions
6. Estimated repair time and difficulty level`;

      const res = await fetch(`${API}/ai-assist/diagnose`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({
          query: fullQuery,
          category: selectedCategory || "diagnosis",
          portal_type: user?.role === "technician" ? "technician" : "admin",
          context: {
            user_name: user?.name,
            role: user?.role,
            vehicle_type: selectedVehicleType,
            vehicle_model: selectedModel,
            issue_category: selectedCategory,
            dtc_codes: dtcCodes,
            ticket_id: ticketContext?.ticket_id
          }
        })
      });

      if (res.ok) {
        const data = await res.json();
        setDiagnosis({
          content: data.response,
          timestamp: new Date().toISOString(),
          ai_enabled: data.ai_enabled,
          confidence: data.confidence
        });
        toast.success("Diagnosis generated successfully");
      } else {
        throw new Error("Failed to get AI diagnosis");
      }
    } catch (error) {
      console.error("AI diagnosis error:", error);
      toast.error("Failed to get AI diagnosis. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedCategory(null);
    setSelectedVehicleType(null);
    setSelectedModel("");
    setIssueDescription("");
    setDiagnosis(null);
    setDtcCodes("");
    toast.success("Form cleared");
  };

  const copyDiagnosis = () => {
    if (diagnosis?.content) {
      navigator.clipboard.writeText(diagnosis.content);
      toast.success("Diagnosis copied to clipboard");
    }
  };

  const formatDiagnosis = (content) => {
    if (!content) return null;
    
    return content.split('\n').map((line, i) => {
      if (line.startsWith('### ')) {
        return (
          <h3 key={i} className="text-base font-semibold text-emerald-400 mt-5 mb-2 flex items-center gap-2">
            <ChevronRight className="h-4 w-4" />
            {line.substring(4)}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={i} className="text-lg font-bold text-white mt-6 mb-3 pb-2 border-b border-slate-700/50 flex items-center gap-2">
            <Target className="h-5 w-5 text-emerald-400" />
            {line.substring(3)}
          </h2>
        );
      }
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} className="mb-2 text-slate-300 leading-relaxed">
            {parts.map((part, j) => 
              j % 2 === 1 ? <strong key={j} className="text-emerald-400 font-semibold">{part}</strong> : part
            )}
          </p>
        );
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return (
          <li key={i} className="ml-5 mb-2 list-none flex items-start gap-2 text-slate-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 flex-shrink-0" />
            <span>{line.substring(2)}</span>
          </li>
        );
      }
      if (/^\d+\.\s/.test(line)) {
        const num = line.match(/^(\d+)\./)[1];
        return (
          <li key={i} className="ml-4 mb-3 list-none flex items-start gap-3 text-slate-300">
            <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-semibold flex items-center justify-center flex-shrink-0">
              {num}
            </span>
            <span className="pt-0.5">{line.substring(line.indexOf('.') + 2)}</span>
          </li>
        );
      }
      if (line.trim() === '') {
        return <div key={i} className="h-2" />;
      }
      return <p key={i} className="mb-2 text-slate-300 leading-relaxed">{line}</p>;
    });
  };

  const selectedCategoryData = ISSUE_CATEGORIES.find(c => c.id === selectedCategory);
  const selectedVehicleData = VEHICLE_CATEGORIES.find(v => v.id === selectedVehicleType);

  return (
    <div className="space-y-6">
      {/* Enhanced Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 border border-slate-700/50">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMjIiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyem0wLTR2Mkg yNHYtMmgxMnptMC00djJIMjR2LTJoMTJ6bTAtNHYySDI0di0yaDEyem0wLTR2MkgyNFYxOGgxMnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-20" />
        <div className="relative flex items-center gap-5">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/30 rounded-2xl blur-xl animate-pulse" />
            <div className="relative p-4 bg-gradient-to-br from-emerald-500/20 to-teal-500/10 rounded-2xl border border-emerald-500/30">
              <Brain className="h-10 w-10 text-emerald-400" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              AI Diagnostic Assistant
              <span className="px-3 py-1 text-xs font-medium bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                Powered by Gemini
              </span>
            </h1>
            <p className="text-slate-400 mt-1">Get instant AI-powered diagnosis for your EV issues</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Input Form */}
        <div className="space-y-6">
          {/* Issue Category Card */}
          <Card className="border-slate-700/50 bg-slate-900/50 backdrop-blur-sm overflow-hidden">
            <CardHeader className="pb-4 border-b border-slate-700/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg">
                  <Sparkles className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-white">Describe Your Issue</CardTitle>
                  <p className="text-sm text-slate-400 mt-0.5">Select category and provide details</p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-6">
              {/* Issue Category Grid */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <CircuitBoard className="h-4 w-4 text-emerald-400" />
                  Issue Category
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {ISSUE_CATEGORIES.map((category) => {
                    const Icon = category.icon;
                    const isSelected = selectedCategory === category.id;
                    return (
                      <button
                        key={category.id}
                        onClick={() => setSelectedCategory(category.id)}
                        className={`group relative flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all duration-200 ${
                          isSelected
                            ? `bg-gradient-to-br ${category.gradient} border-transparent text-white shadow-lg shadow-${category.gradient.split('-')[1]}-500/20`
                            : "bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-slate-600 hover:bg-slate-800"
                        }`}
                        data-testid={`category-${category.id}`}
                      >
                        <div className={`p-2 rounded-lg transition-colors ${
                          isSelected ? "bg-white/20" : "bg-slate-700/50 group-hover:bg-slate-700"
                        }`}>
                          <Icon className={`h-5 w-5 ${isSelected ? "text-white" : "text-slate-400 group-hover:text-white"}`} />
                        </div>
                        <span className={`text-xs font-medium text-center leading-tight ${isSelected ? "text-white" : ""}`}>
                          {category.label}
                        </span>
                        {isSelected && (
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center">
                            <CheckCircle className="h-3 w-3 text-emerald-600" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Vehicle Category */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Car className="h-4 w-4 text-emerald-400" />
                  Vehicle Category
                </label>
                <div className="grid grid-cols-4 gap-3">
                  {VEHICLE_CATEGORIES.map((vehicle) => {
                    const Icon = vehicle.icon;
                    const isSelected = selectedVehicleType === vehicle.id;
                    return (
                      <button
                        key={vehicle.id}
                        onClick={() => {
                          setSelectedVehicleType(vehicle.id);
                          setSelectedModel("");
                        }}
                        className={`group relative flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 ${
                          isSelected
                            ? `bg-gradient-to-br ${vehicle.gradient} border-transparent text-white shadow-lg`
                            : "bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-slate-600 hover:bg-slate-800"
                        }`}
                        data-testid={`vehicle-${vehicle.id}`}
                      >
                        <Icon className={`h-6 w-6 ${isSelected ? "text-white" : "text-slate-400 group-hover:text-white"}`} />
                        <span className={`text-xs font-medium text-center ${isSelected ? "text-white" : ""}`}>
                          {vehicle.label}
                        </span>
                        {isSelected && (
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center">
                            <CheckCircle className="h-3 w-3 text-emerald-600" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Vehicle Model */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-emerald-400" />
                  Vehicle Model
                </label>
                <Select
                  value={selectedModel}
                  onValueChange={setSelectedModel}
                  disabled={!selectedVehicleType}
                >
                  <SelectTrigger 
                    className="w-full bg-slate-800/50 border-slate-700/50 text-white"
                    data-testid="vehicle-model-select"
                  >
                    <SelectValue placeholder={selectedVehicleType ? "Select vehicle model" : "Select vehicle category first"} />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {selectedVehicleType && VEHICLE_MODELS[selectedVehicleType]?.map((model) => (
                      <SelectItem key={model} value={model} className="text-white hover:bg-slate-700">
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* DTC Codes */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Code className="h-4 w-4 text-emerald-400" />
                  DTC/Error Codes 
                  <span className="text-slate-500 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={dtcCodes}
                  onChange={(e) => setDtcCodes(e.target.value)}
                  placeholder="e.g., P0A80, U0100, B1234"
                  className="w-full px-4 py-3 rounded-xl border border-slate-700/50 bg-slate-800/50 text-white placeholder:text-slate-500 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                  data-testid="dtc-codes-input"
                />
              </div>

              {/* Issue Description */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-emerald-400" />
                  Describe the Issue 
                  <span className="text-red-400">*</span>
                </label>
                <Textarea
                  value={issueDescription}
                  onChange={(e) => setIssueDescription(e.target.value)}
                  placeholder="Example: My scooter won't charge past 80%. The charging port light blinks red after reaching 80% and charging stops automatically. This started happening 2 days ago after a software update..."
                  className="min-h-[140px] resize-none bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 rounded-xl"
                  data-testid="issue-description"
                />
              </div>

              {/* Submit Button */}
              <Button
                onClick={handleGetDiagnosis}
                disabled={loading || !issueDescription.trim()}
                className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-white font-semibold text-base rounded-xl shadow-lg shadow-emerald-500/25 border-0 transition-all duration-200"
                data-testid="get-diagnosis-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Analyzing with AI...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Get AI Diagnosis
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Tips Card */}
          <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg flex-shrink-0">
                  <Lightbulb className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <h4 className="font-semibold text-emerald-400 mb-2">Tips for better diagnosis</h4>
                  <ul className="text-sm text-slate-400 space-y-1.5">
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5" />
                      Be specific about symptoms (sounds, warning lights, behavior)
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5" />
                      Include any DTC/error codes displayed
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5" />
                      Mention when the issue started and conditions
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5" />
                      Note any recent repairs or changes
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Panel - Diagnosis Results */}
        <Card className="border-slate-700/50 bg-slate-900/50 backdrop-blur-sm overflow-hidden">
          <CardHeader className="pb-4 border-b border-slate-700/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 rounded-lg">
                  <Brain className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <CardTitle className="text-lg text-white">AI Diagnosis</CardTitle>
                  <p className="text-sm text-slate-400 mt-0.5">
                    {diagnosis ? "AI-powered analysis of your issue" : "Submit query for diagnosis"}
                  </p>
                </div>
              </div>
              {diagnosis && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={copyDiagnosis}
                    className="text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <Copy className="h-4 w-4 mr-1.5" />
                    Copy
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleReset}
                    className="text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <RotateCcw className="h-4 w-4 mr-1.5" />
                    Reset
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="relative mb-6">
                  <div className="absolute inset-0 bg-emerald-500/30 rounded-full blur-xl animate-pulse" />
                  <div className="relative p-5 bg-gradient-to-br from-emerald-500/20 to-teal-500/10 rounded-full border border-emerald-500/30">
                    <Loader2 className="h-10 w-10 text-emerald-400 animate-spin" />
                  </div>
                </div>
                <p className="text-white font-medium text-lg">Analyzing your issue...</p>
                <p className="text-sm text-slate-400 mt-2">Our AI is processing your diagnosis</p>
                <div className="flex gap-2 mt-6">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            ) : diagnosis ? (
              <ScrollArea className="h-[600px]">
                <div className="p-5">
                  {/* Confidence & Context Summary */}
                  <div className="grid grid-cols-3 gap-3 mb-6">
                    {diagnosis.confidence && (
                      <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                        <div className="flex items-center gap-2 mb-1">
                          <Shield className="h-4 w-4 text-emerald-400" />
                          <span className="text-xs text-slate-400">Confidence</span>
                        </div>
                        <p className="text-lg font-bold text-emerald-400">{Math.round(diagnosis.confidence * 100)}%</p>
                      </div>
                    )}
                    {selectedCategoryData && (
                      <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                        <div className="flex items-center gap-2 mb-1">
                          <selectedCategoryData.icon className="h-4 w-4 text-slate-400" />
                          <span className="text-xs text-slate-400">Category</span>
                        </div>
                        <p className="text-sm font-medium text-white truncate">{selectedCategoryData.label}</p>
                      </div>
                    )}
                    {selectedModel && (
                      <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                        <div className="flex items-center gap-2 mb-1">
                          <Car className="h-4 w-4 text-slate-400" />
                          <span className="text-xs text-slate-400">Vehicle</span>
                        </div>
                        <p className="text-sm font-medium text-white truncate">{selectedModel}</p>
                      </div>
                    )}
                  </div>

                  {/* Diagnosis Content */}
                  <div className="prose prose-invert max-w-none">
                    {formatDiagnosis(diagnosis.content)}
                  </div>

                  {/* Disclaimer */}
                  <div className="mt-8 p-4 bg-amber-500/10 rounded-xl border border-amber-500/20">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-amber-400 mb-1">Important Notice</p>
                        <p className="text-xs text-amber-300/80">
                          This AI diagnosis is for reference only. Always verify with proper diagnostic tools and follow manufacturer guidelines. For high-voltage systems, ensure proper safety protocols and use appropriate PPE.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Timestamp */}
                  <div className="mt-4 flex items-center justify-center gap-2 text-xs text-slate-500">
                    <Clock className="h-3 w-3" />
                    Generated at {new Date(diagnosis.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center px-8">
                <div className="relative mb-6">
                  <div className="absolute inset-0 bg-slate-700/30 rounded-full blur-xl" />
                  <div className="relative p-6 bg-slate-800/50 rounded-full border border-slate-700/50">
                    <Bot className="h-14 w-14 text-slate-500" />
                  </div>
                </div>
                <p className="text-white font-medium text-lg mb-2">Describe your issue to get started</p>
                <p className="text-sm text-slate-400 max-w-sm">
                  Fill in the details on the left panel and click "Get AI Diagnosis" to receive instant diagnostic assistance
                </p>
                <div className="mt-6 flex items-center gap-6 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-emerald-500" />
                    Instant Analysis
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Shield className="h-3.5 w-3.5 text-emerald-500" />
                    Expert Knowledge
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Target className="h-3.5 w-3.5 text-emerald-500" />
                    Accurate Results
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
