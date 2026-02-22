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
  Copy, RotateCcw, Brain, Target, Shield, Clock, Cpu
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// Issue categories - clean single-color design
const ISSUE_CATEGORIES = [
  { id: "battery", label: "Battery Issues", icon: Battery },
  { id: "motor", label: "Motor Problems", icon: Cpu },
  { id: "charging", label: "Charging System", icon: Plug },
  { id: "electrical", label: "Electrical", icon: Zap },
  { id: "mechanical", label: "Mechanical", icon: Settings },
  { id: "software", label: "Software Issues", icon: Code },
  { id: "suspension", label: "Suspension", icon: ArrowUpDown },
  { id: "braking", label: "Braking System", icon: CircleDot },
  { id: "cooling", label: "Cooling System", icon: Thermometer },
  { id: "hvac", label: "AC/Heating", icon: Wind },
  { id: "other", label: "Other", icon: HelpCircle },
];

// Vehicle categories
const VEHICLE_CATEGORIES = [
  { id: "2_wheeler", label: "2 Wheeler", icon: Bike },
  { id: "3_wheeler", label: "3 Wheeler", icon: Truck },
  { id: "4_wheeler_commercial", label: "4W Commercial", icon: Truck },
  { id: "car", label: "Car", icon: Car },
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

      const headers = getAuthHeaders();
      headers["Content-Type"] = "application/json";

      const res = await fetch(`${API}/ai-assist/diagnose`, {
        method: "POST",
        headers,
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

      if (!res.ok) {
        const errorText = await res.text();
        console.error("AI API error:", res.status, errorText);
        throw new Error(`API Error: ${res.status}`);
      }

      const data = await res.json();
      
      if (!data.response) {
        throw new Error("Empty response from AI");
      }
      
      setDiagnosis({
        content: data.response,
        timestamp: new Date().toISOString(),
        ai_enabled: data.ai_enabled,
        confidence: data.confidence
      });
      toast.success("Diagnosis generated successfully");
    } catch (error) {
      console.error("AI diagnosis error:", error);
      toast.error(error.message || "Failed to get AI diagnosis. Please try again.");
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
          <h3 key={i} className="text-sm font-semibold text-emerald-500 mt-4 mb-2">
            {line.substring(4)}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={i} className="text-base font-bold text-gray-800 dark:text-white mt-5 mb-2 pb-2 border-b border-gray-200 dark:border-gray-700">
            {line.substring(3)}
          </h2>
        );
      }
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} className="mb-1.5 text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
            {parts.map((part, j) => 
              j % 2 === 1 ? <strong key={j} className="text-emerald-600 dark:text-emerald-400 font-medium">{part}</strong> : part
            )}
          </p>
        );
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return (
          <li key={i} className="ml-4 mb-1.5 list-disc text-gray-600 dark:text-gray-300 text-sm">
            {line.substring(2)}
          </li>
        );
      }
      if (/^\d+\.\s/.test(line)) {
        return (
          <li key={i} className="ml-4 mb-2 list-decimal text-gray-600 dark:text-gray-300 text-sm">
            {line.substring(line.indexOf('.') + 2)}
          </li>
        );
      }
      if (line.trim() === '') {
        return <div key={i} className="h-2" />;
      }
      return <p key={i} className="mb-1.5 text-gray-600 dark:text-gray-300 text-sm leading-relaxed">{line}</p>;
    });
  };

  return (
    <div className="space-y-6">
      {/* Clean Header with Volt Theme */}
      <div className="bg-[#111820] border border-[rgba(200,255,0,0.20)] border-l-[3px] border-l-[#C8FF00] rounded-xl p-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            {/* Icon container */}
            <div className="p-3 bg-[rgba(200,255,0,0.08)] border border-[rgba(200,255,0,0.2)] rounded-xl">
              <Brain className="h-8 w-8 text-[#C8FF00]" />
            </div>
            {/* Live indicator dot */}
            <div className="absolute -top-1 -right-1 w-3 h-3">
              <span className="absolute inline-flex h-full w-full rounded-full bg-[#C8FF00] opacity-75 animate-ping" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-[#C8FF00] shadow-lg shadow-[rgba(200,255,0,0.5)]" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-[#F4F6F0]">AI Diagnostic Assistant</h1>
              <span className="px-3 py-1 text-[10px] font-semibold bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)] rounded-full font-mono uppercase tracking-[0.1em]">
                Powered by EFI
              </span>
            </div>
            <p className="text-[rgba(244,246,240,0.45)] mt-1">Get instant AI-powered diagnosis for your EV issues</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Input Form */}
        <Card className="border border-gray-200 dark:border-gray-700 shadow-sm">
          <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-800">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-500" />
              <CardTitle className="text-lg text-gray-800 dark:text-white">Describe Your Issue</CardTitle>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Select category and provide details about your EV problem</p>
          </CardHeader>
          <CardContent className="p-5 space-y-5">
            {/* Issue Category */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Issue Category</label>
              <div className="grid grid-cols-4 gap-2">
                {ISSUE_CATEGORIES.map((category) => {
                  const Icon = category.icon;
                  const isSelected = selectedCategory === category.id;
                  return (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`relative flex flex-col items-center gap-2 p-3 rounded-lg border transition-all duration-150 ${
                        isSelected
                          ? "bg-[rgba(200,255,0,0.12)] border-[rgba(200,255,0,0.35)] border-t-2 border-t-[#C8FF00]"
                          : "bg-[#111820] border-[rgba(255,255,255,0.07)] text-[rgba(244,246,240,0.6)] hover:border-[rgba(200,255,0,0.2)] hover:bg-[rgba(200,255,0,0.05)]"
                      }`}
                      data-testid={`category-${category.id}`}
                    >
                      <Icon className={`h-5 w-5 ${isSelected ? "text-[#C8FF00]" : "text-[rgba(244,246,240,0.5)]"}`} />
                      <span className={`text-xs font-medium text-center leading-tight ${isSelected ? "text-[#C8FF00]" : ""}`}>{category.label}</span>
                      {isSelected && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-[#C8FF00] rounded-full flex items-center justify-center shadow">
                          <CheckCircle className="h-3 w-3 text-[#080C0F]" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Vehicle Category */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Vehicle Category</label>
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
                      className={`relative flex flex-col items-center gap-2 p-4 rounded-lg border transition-all duration-150 ${
                        isSelected
                          ? "bg-emerald-500 border-emerald-500 text-white shadow-md"
                          : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                      }`}
                      data-testid={`vehicle-${vehicle.id}`}
                    >
                      <Icon className={`h-6 w-6 ${isSelected ? "text-white" : ""}`} />
                      <span className="text-xs font-medium text-center">{vehicle.label}</span>
                      {isSelected && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center shadow">
                          <CheckCircle className="h-3 w-3 text-emerald-500" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Vehicle Model */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Vehicle Model</label>
              <Select
                value={selectedModel}
                onValueChange={setSelectedModel}
                disabled={!selectedVehicleType}
              >
                <SelectTrigger className="w-full" data-testid="vehicle-model-select">
                  <SelectValue placeholder={selectedVehicleType ? "Select vehicle model" : "Select vehicle category first"} />
                </SelectTrigger>
                <SelectContent>
                  {selectedVehicleType && VEHICLE_MODELS[selectedVehicleType]?.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* DTC Codes */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                DTC/Error Codes <span className="text-gray-400 font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                value={dtcCodes}
                onChange={(e) => setDtcCodes(e.target.value)}
                placeholder="e.g., P0A80, U0100, B1234"
                className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                data-testid="dtc-codes-input"
              />
            </div>

            {/* Issue Description */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Describe the Issue <span className="text-red-500">*</span>
              </label>
              <Textarea
                value={issueDescription}
                onChange={(e) => setIssueDescription(e.target.value)}
                placeholder="Example: My scooter won't charge past 80%. The charging port light blinks red after reaching 80% and charging stops automatically..."
                className="min-h-[120px] resize-none"
                data-testid="issue-description"
              />
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleGetDiagnosis}
              disabled={loading || !issueDescription.trim()}
              className="w-full h-12 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg shadow-md shadow-emerald-500/20"
              data-testid="get-diagnosis-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Analyzing...
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

        {/* Right Panel - Diagnosis Results */}
        <Card className="border border-gray-200 dark:border-gray-700 shadow-sm">
          <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-500" />
                <CardTitle className="text-lg text-gray-800 dark:text-white">AI Diagnosis</CardTitle>
              </div>
              {diagnosis && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={copyDiagnosis}
                    className="text-gray-500 hover:text-gray-700 dark:hover:text-white"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleReset}
                    className="text-gray-500 hover:text-gray-700 dark:hover:text-white"
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    Reset
                  </Button>
                </div>
              )}
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {diagnosis ? "AI-powered analysis of your issue" : "Submit your query for diagnosis"}
            </p>
          </CardHeader>
          <CardContent className="p-5">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative mb-6">
                  {/* Glowing ring animation */}
                  <div className="absolute inset-0 bg-emerald-500/30 rounded-2xl blur-xl animate-pulse" />
                  <div className="absolute -inset-2 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-2xl blur-lg animate-pulse" style={{ animationDelay: '150ms' }} />
                  <div className="relative p-5 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/30 dark:to-teal-900/30 rounded-2xl border border-emerald-200 dark:border-emerald-700 shadow-lg">
                    <Bot className="h-12 w-12 text-emerald-500 animate-bounce" style={{ animationDuration: '1.5s' }} />
                  </div>
                  {/* Scanning line effect */}
                  <div className="absolute inset-x-0 top-1/2 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-pulse" />
                </div>
                <p className="text-gray-800 dark:text-white font-semibold text-lg">Analyzing your issue...</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1.5">EFI Intelligence is processing</p>
                {/* Loading dots */}
                <div className="flex gap-1.5 mt-4">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '0.8s' }} />
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms', animationDuration: '0.8s' }} />
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms', animationDuration: '0.8s' }} />
                </div>
              </div>
            ) : diagnosis ? (
              <ScrollArea className="h-[500px] pr-4">
                {/* Confidence Indicator */}
                {diagnosis.confidence && (
                  <div className="flex items-center gap-2 mb-4 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                    <span className="text-sm text-emerald-700 dark:text-emerald-400 font-medium">
                      AI Confidence: {Math.round(diagnosis.confidence * 100)}%
                    </span>
                  </div>
                )}
                
                {/* Diagnosis Content */}
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {formatDiagnosis(diagnosis.content)}
                </div>

                {/* Disclaimer */}
                <div className="mt-6 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-amber-700 dark:text-amber-400">
                      This AI diagnosis is for reference only. Always verify with proper diagnostic tools and follow manufacturer guidelines.
                    </p>
                  </div>
                </div>

                {/* Timestamp */}
                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-gray-400">
                  <Clock className="h-3 w-3" />
                  Generated at {new Date(diagnosis.timestamp).toLocaleTimeString()}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
                  <Bot className="h-12 w-12 text-gray-400" />
                </div>
                <p className="text-gray-700 dark:text-gray-300 font-medium">Describe your issue to get started</p>
                <p className="text-sm text-gray-500 mt-1 max-w-xs">
                  Fill in the details on the left panel and click "Get AI Diagnosis"
                </p>
                <div className="mt-6 flex items-center gap-4 text-xs text-gray-400">
                  <div className="flex items-center gap-1">
                    <Zap className="h-3.5 w-3.5 text-emerald-500" />
                    Instant Analysis
                  </div>
                  <div className="flex items-center gap-1">
                    <Shield className="h-3.5 w-3.5 text-emerald-500" />
                    Expert Knowledge
                  </div>
                  <div className="flex items-center gap-1">
                    <Target className="h-3.5 w-3.5 text-emerald-500" />
                    Accurate Results
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tips Section */}
      <Card className="border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/10">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Lightbulb className="h-5 w-5 text-emerald-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-emerald-700 dark:text-emerald-400 mb-1">Tips for better diagnosis</h4>
              <ul className="text-sm text-emerald-600 dark:text-emerald-300/80 space-y-1">
                <li>• Be specific about symptoms (sounds, warning lights, behavior)</li>
                <li>• Include any DTC/error codes if available</li>
                <li>• Mention when the issue started and under what conditions</li>
                <li>• Note any recent repairs or changes made to the vehicle</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
