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
          <h3 key={i} className="text-sm font-semibold text-bw-volt mt-4 mb-2">
            {line.substring(4)}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={i} className="text-base font-bold text-bw-white mt-5 mb-2 pb-2 border-b border-white/[0.07]">
            {line.substring(3)}
          </h2>
        );
      }
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} className="mb-1.5 text-bw-white/70 text-sm leading-relaxed">
            {parts.map((part, j) => 
              j % 2 === 1 ? <strong key={j} className="text-bw-volt font-medium">{part}</strong> : part
            )}
          </p>
        );
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return (
          <li key={i} className="ml-4 mb-1.5 list-disc text-bw-white/70 text-sm">
            {line.substring(2)}
          </li>
        );
      }
      if (/^\d+\.\s/.test(line)) {
        return (
          <li key={i} className="ml-4 mb-2 list-decimal text-bw-white/70 text-sm">
            {line.substring(line.indexOf('.') + 2)}
          </li>
        );
      }
      if (line.trim() === '') {
        return <div key={i} className="h-2" />;
      }
      return <p key={i} className="mb-1.5 text-bw-white/70 text-sm leading-relaxed">{line}</p>;
    });
  };

  return (
    <div className="space-y-6">
      {/* Clean Header with Volt Theme */}
      <div className="bg-bw-panel border border-bw-volt/20 border-l-[3px] border-l-bw-volt rounded-xl p-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            {/* Icon container */}
            <div className="p-3 bg-bw-volt/[0.08] border border-bw-volt/20 rounded-xl">
              <Brain className="h-8 w-8 text-bw-volt" />
            </div>
            {/* Live indicator dot */}
            <div className="absolute -top-1 -right-1 w-3 h-3">
              <span className="absolute inline-flex h-full w-full rounded-full bg-bw-volt opacity-75 animate-ping" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-bw-volt" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-bw-white">AI Diagnostic Assistant</h1>
              <span className="px-3 py-1 text-[10px] font-semibold bg-bw-volt/10 text-bw-volt border border-bw-volt/25 rounded-full font-mono uppercase tracking-[0.1em]">
                Powered by EFI
              </span>
            </div>
            <p className="text-bw-white/[0.45] mt-1">Get instant AI-powered diagnosis for your EV issues</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Input Form */}
        <Card className="bg-bw-panel border border-white/[0.07]">
          <CardHeader className="pb-4 border-b border-white/[0.07]">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-bw-volt" />
              <CardTitle className="text-lg text-bw-white">Describe Your Issue</CardTitle>
            </div>
            <p className="text-sm text-bw-white/[0.45]">Select category and provide details about your EV problem</p>
          </CardHeader>
          <CardContent className="p-5 space-y-5">
            {/* Issue Category */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-bw-white">Issue Category</label>
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
                          ? "bg-bw-volt/[0.12] border-bw-volt/35 border-t-2 border-t-bw-volt"
                          : "bg-bw-panel border-white/[0.07] text-bw-white/60 hover:border-bw-volt/20 hover:bg-bw-volt/5"
                      }`}
                      data-testid={`category-${category.id}`}
                    >
                      <Icon className={`h-5 w-5 ${isSelected ? "text-bw-volt" : "text-bw-white/50"}`} />
                      <span className={`text-xs font-medium text-center leading-tight ${isSelected ? "text-bw-volt" : ""}`}>{category.label}</span>
                      {isSelected && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-bw-volt rounded-full flex items-center justify-center shadow">
                          <CheckCircle className="h-3 w-3 text-bw-black" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Vehicle Category */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-bw-white">Vehicle Category</label>
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
                          ? "bg-bw-volt/[0.12] border-bw-volt/35 border-t-2 border-t-bw-volt"
                          : "bg-bw-panel border-white/[0.07] text-bw-white/60 hover:border-bw-volt/20 hover:bg-bw-volt/5"
                      }`}
                      data-testid={`vehicle-${vehicle.id}`}
                    >
                      <Icon className={`h-6 w-6 ${isSelected ? "text-bw-volt" : "text-bw-white/50"}`} />
                      <span className={`text-xs font-medium text-center ${isSelected ? "text-bw-volt" : ""}`}>{vehicle.label}</span>
                      {isSelected && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-bw-volt rounded-full flex items-center justify-center shadow">
                          <CheckCircle className="h-3 w-3 text-bw-black" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Vehicle Model */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-bw-white">Vehicle Model</label>
              <Select
                value={selectedModel}
                onValueChange={setSelectedModel}
                disabled={!selectedVehicleType}
              >
                <SelectTrigger className="w-full bg-bw-panel border-white/[0.07] text-bw-white" data-testid="vehicle-model-select">
                  <SelectValue placeholder={selectedVehicleType ? "Select vehicle model" : "Select vehicle category first"} />
                </SelectTrigger>
                <SelectContent className="bg-bw-panel border-white/10">
                  {selectedVehicleType && VEHICLE_MODELS[selectedVehicleType]?.map((model) => (
                    <SelectItem key={model} value={model} className="text-bw-white focus:bg-bw-volt/10 focus:text-bw-volt">
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* DTC Codes */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-bw-white">
                DTC/Error Codes <span className="text-bw-white/35 font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                value={dtcCodes}
                onChange={(e) => setDtcCodes(e.target.value)}
                placeholder="e.g., P0A80, U0100, B1234"
                className="w-full px-4 py-2.5 rounded border border-white/[0.07] bg-bw-panel text-bw-white placeholder:text-bw-white/25 focus:border-bw-volt focus:ring-2 focus:ring-bw-volt/20 transition-all"
                data-testid="dtc-codes-input"
              />
            </div>

            {/* Issue Description */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-bw-white">
                Describe the Issue <span className="text-bw-red">*</span>
              </label>
              <Textarea
                value={issueDescription}
                onChange={(e) => setIssueDescription(e.target.value)}
                placeholder="Example: My scooter won't charge past 80%. The charging port light blinks red after reaching 80% and charging stops automatically..."
                className="min-h-[120px] resize-none bg-bw-panel border-white/[0.07] text-bw-white placeholder:text-bw-white/25 focus:border-bw-volt"
                data-testid="issue-description"
              />
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleGetDiagnosis}
              disabled={loading || !issueDescription.trim()}
              className="w-full h-12 bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold rounded"
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
        <Card className="bg-bw-panel border border-white/[0.07]">
          <CardHeader className="pb-4 border-b border-white/[0.07]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-bw-volt" />
                <CardTitle className="text-lg text-bw-white">AI Diagnosis</CardTitle>
              </div>
              {diagnosis && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={copyDiagnosis}
                    className="text-bw-white/[0.45] hover:text-bw-white hover:bg-bw-volt/[0.06]"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleReset}
                    className="text-bw-white/[0.45] hover:text-bw-white hover:bg-bw-volt/[0.06]"
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    Reset
                  </Button>
                </div>
              )}
            </div>
            <p className="text-sm text-bw-white/[0.45]">
              {diagnosis ? "AI-powered analysis of your issue" : "Submit your query for diagnosis"}
            </p>
          </CardHeader>
          <CardContent className="p-5">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative mb-6">
                  {/* Glowing ring animation */}
                  <div className="absolute inset-0 bg-bw-volt/20 rounded-2xl blur-xl animate-pulse" />
                  <div className="absolute -inset-2 bg-gradient-to-r from-bw-volt/15 to-bw-teal/15 rounded-2xl blur-lg animate-pulse" style={{ animationDelay: '150ms' }} />
                  <div className="relative p-5 bg-bw-volt/[0.08] rounded-xl border border-bw-volt/20">
                    <Bot className="h-12 w-12 text-bw-volt animate-bounce" style={{ animationDuration: '1.5s' }} />
                  </div>
                  {/* Scanning line effect */}
                  <div className="absolute inset-x-0 top-1/2 h-0.5 bg-gradient-to-r from-transparent via-bw-volt to-transparent animate-pulse" />
                </div>
                <p className="text-bw-white font-semibold text-lg">Analyzing your issue...</p>
                <p className="text-sm text-bw-white/[0.45] mt-1.5">EFI Intelligence is processing</p>
                {/* Loading dots */}
                <div className="flex gap-1.5 mt-4">
                  <span className="w-2 h-2 bg-bw-volt rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '0.8s' }} />
                  <span className="w-2 h-2 bg-bw-volt rounded-full animate-bounce" style={{ animationDelay: '150ms', animationDuration: '0.8s' }} />
                  <span className="w-2 h-2 bg-bw-volt rounded-full animate-bounce" style={{ animationDelay: '300ms', animationDuration: '0.8s' }} />
                </div>
              </div>
            ) : diagnosis ? (
              <ScrollArea className="h-[500px] pr-4">
                {/* Confidence Indicator */}
                {diagnosis.confidence && (
                  <div className="flex items-center gap-2 mb-4 p-3 bg-bw-volt/[0.08] rounded-lg border border-bw-volt/20">
                    <CheckCircle className="h-5 w-5 text-bw-volt" />
                    <span className="text-sm text-bw-volt font-medium">
                      AI Confidence: {Math.round(diagnosis.confidence * 100)}%
                    </span>
                  </div>
                )}
                
                {/* Diagnosis Content */}
                <div className="prose prose-sm prose-invert max-w-none">
                  {formatDiagnosis(diagnosis.content)}
                </div>

                {/* Disclaimer */}
                <div className="mt-6 p-3 bg-bw-amber/[0.08] rounded-lg border border-bw-amber/20">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-bw-amber mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-bw-amber">
                      This AI diagnosis is for reference only. Always verify with proper diagnostic tools and follow manufacturer guidelines.
                    </p>
                  </div>
                </div>

                {/* Timestamp */}
                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-bw-white/35">
                  <Clock className="h-3 w-3" />
                  Generated at {new Date(diagnosis.timestamp).toLocaleTimeString()}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="p-4 bg-white/5 rounded-full mb-4">
                  <Bot className="h-12 w-12 text-bw-white/35" />
                </div>
                <p className="text-bw-white font-medium">Describe your issue to get started</p>
                <p className="text-sm text-bw-white/[0.45] mt-1 max-w-xs">
                  Fill in the details on the left panel and click "Get AI Diagnosis"
                </p>
                <div className="mt-6 flex items-center gap-4 text-xs text-bw-white/35">
                  <div className="flex items-center gap-1">
                    <Zap className="h-3.5 w-3.5 text-bw-volt" />
                    Instant Analysis
                  </div>
                  <div className="flex items-center gap-1">
                    <Shield className="h-3.5 w-3.5 text-bw-volt" />
                    Expert Knowledge
                  </div>
                  <div className="flex items-center gap-1">
                    <Target className="h-3.5 w-3.5 text-bw-volt" />
                    Accurate Results
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tips Section */}
      <Card className="bg-bw-volt/5 border border-bw-volt/15">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Lightbulb className="h-5 w-5 text-bw-volt mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-bw-volt mb-1">Tips for better diagnosis</h4>
              <ul className="text-sm text-bw-white/60 space-y-1">
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
