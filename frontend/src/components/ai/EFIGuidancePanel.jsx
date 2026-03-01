import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Shield, Zap, CheckCircle2, AlertTriangle, 
  ClipboardList, BarChart3, RefreshCw, ChevronRight,
  ThumbsUp, ThumbsDown, Plus, HelpCircle, Loader2,
  BookOpen, Wrench, Eye, EyeOff
} from "lucide-react";
import { toast } from "sonner";
import mermaid from "mermaid";

const API = process.env.REACT_APP_BACKEND_URL;

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#22C55E',
    primaryTextColor: '#F4F6F0',
    primaryBorderColor: '#22C55E',
    lineColor: '#64748b',
    secondaryColor: '#111820',
    tertiaryColor: '#080C0F',
    background: '#080C0F',
    mainBkg: '#111820',
    nodeBorder: '#22C55E'
  }
});

// Micro Chart Components
const GaugeChart = ({ value, max = 100, title, unit = "%", color, zones }) => {
  const percentage = (value / max) * 100;
  const rotation = (percentage / 100) * 180;
  
  return (
    <div className="flex flex-col items-center p-3 bg-slate-800/50 rounded-lg">
      <span className="text-xs text-slate-400 mb-2">{title}</span>
      <div className="relative w-20 h-10 overflow-hidden">
        <div className="absolute w-20 h-20 rounded-full border-4 border-white/[0.07] border-700" 
             style={{ borderTopColor: 'transparent', borderLeftColor: 'transparent', transform: 'rotate(225deg)' }}>
        </div>
        <div 
          className="absolute w-20 h-20 rounded-full border-4 border-transparent transition-transform duration-500"
          style={{ 
            borderTopColor: color || 'rgb(var(--bw-green))', 
            borderLeftColor: color || 'rgb(var(--bw-green))',
            transform: `rotate(${225 + rotation}deg)` 
          }}
        />
        <div className="absolute inset-0 flex items-end justify-center pb-1">
          <span className="text-lg font-bold" style={{ color: color || 'rgb(var(--bw-green))' }}>
            {Math.round(value)}{unit}
          </span>
        </div>
      </div>
    </div>
  );
};

const HorizontalBarChart = ({ data, title, max = 100 }) => (
  <div className="p-3 bg-slate-800/50 rounded-lg">
    <span className="text-xs text-slate-400">{title}</span>
    <div className="mt-2 space-y-2">
      {data?.slice(0, 4).map((item, i) => (
        <div key={i} className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 truncate max-w-[120px]">{item.label}</span>
            <span className="text-slate-400">{item.value}%</span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${item.percentage || (item.value / max * 100)}%`, backgroundColor: item.color }}
            />
          </div>
        </div>
      ))}
    </div>
  </div>
);

const InfoCard = ({ title, value, unit, icon: Icon, subtitle }) => (
  <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
    <div className="w-10 h-10 rounded-full bg-bw-volt/[0.08]0/20 flex items-center justify-center">
      {Icon && <Icon className="h-5 w-5 text-bw-volt text-400" />}
    </div>
    <div>
      <span className="text-xs text-slate-400">{title}</span>
      <div className="text-xl font-bold text-white">{value}{unit}</div>
      {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
    </div>
  </div>
);

// Mermaid Diagram Component
const MermaidDiagram = ({ code, title }) => {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const renderDiagram = async () => {
      if (!code) return;
      try {
        const { svg } = await mermaid.render(`mermaid-${Date.now()}`, code);
        setSvg(svg);
        setError(null);
      } catch (err) {
        console.error("Mermaid render error:", err);
        setError("Could not render diagram");
      }
    };
    renderDiagram();
  }, [code]);
  
  if (error) {
    return (
      <div className="p-4 bg-slate-800/50 rounded-lg text-center">
        <span className="text-sm text-slate-400">{error}</span>
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto">
      {title && <h4 className="text-sm font-medium text-slate-300 mb-2">{title}</h4>}
      <div 
        className="mermaid-diagram" 
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
};

// Ask-Back Form Component
const AskBackForm = ({ questions, onSubmit, loading }) => {
  const [answers, setAnswers] = useState({});
  
  const handleChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };
  
  const handleMultiSelect = (questionId, option) => {
    setAnswers(prev => {
      const current = prev[questionId] || [];
      const updated = current.includes(option)
        ? current.filter(o => o !== option)
        : [...current, option];
      return { ...prev, [questionId]: updated };
    });
  };
  
  return (
    <div className="space-y-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
      <div className="flex items-center gap-2 text-amber-400">
        <HelpCircle className="h-5 w-5" />
        <span className="font-semibold">Kuch details chahiye - Please answer:</span>
      </div>
      
      {questions.map((q, i) => (
        <div key={q.id} className="space-y-2">
          <label className="text-sm text-slate-300">
            {i + 1}. {q.question}
            <span className="text-slate-500 text-xs ml-2">({q.question_en})</span>
          </label>
          
          {q.type === "select" && (
            <div className="flex flex-wrap gap-2">
              {q.options.map(opt => (
                <Button
                  key={opt}
                  size="sm"
                  variant={answers[q.id] === opt ? "default" : "outline"}
                  className={answers[q.id] === opt 
                    ? "bg-bw-volt text-bw-black font-bold" 
                    : "border-white/[0.07] text-bw-white/70 hover:bg-bw-volt/[0.08]"}
                  onClick={() => handleChange(q.id, opt)}
                >
                  {opt}
                </Button>
              ))}
            </div>
          )}
          
          {q.type === "multi_select" && (
            <div className="flex flex-wrap gap-2">
              {q.options.map(opt => (
                <Button
                  key={opt}
                  size="sm"
                  variant={(answers[q.id] || []).includes(opt) ? "default" : "outline"}
                  className={(answers[q.id] || []).includes(opt)
                    ? "bg-bw-volt text-bw-black font-bold"
                    : "border-white/[0.07] text-bw-white/70 hover:bg-bw-volt/[0.08]"}
                  onClick={() => handleMultiSelect(q.id, opt)}
                >
                  {opt}
                </Button>
              ))}
            </div>
          )}
          
          {q.type === "text" && (
            <input
              type="text"
              placeholder={q.placeholder}
              className="w-full px-3 py-2 bg-slate-800 border border-white/[0.07] border-700 rounded text-white text-sm"
              value={answers[q.id] || ""}
              onChange={(e) => handleChange(q.id, e.target.value)}
            />
          )}
          
          {q.type === "number" && (
            <input
              type="number"
              min={q.min}
              max={q.max}
              placeholder="Enter value"
              className="w-24 px-3 py-2 bg-slate-800 border border-white/[0.07] border-700 rounded text-white text-sm"
              value={answers[q.id] || ""}
              onChange={(e) => handleChange(q.id, parseFloat(e.target.value))}
            />
          )}
        </div>
      ))}
      
      <Button 
        onClick={() => onSubmit(answers)} 
        disabled={loading}
        className="w-full bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
        Submit Answers & Get Guidance
      </Button>
    </div>
  );
};

// Diagnostic Step Component
const DiagnosticStep = ({ step, index, onMarkDone, isDone }) => (
  <div className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
    isDone ? 'bg-bw-volt/[0.08] border border-bw-volt/30' : 'bg-slate-800/50'
  }`}>
    <button
      onClick={() => onMarkDone(index)}
      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
        isDone 
          ? 'bg-bw-volt/[0.08]0 border-bw-volt/50 text-white' 
          : 'border-white/[0.07] border-600 hover:border-emerald-400'
      }`}
    >
      {isDone && <CheckCircle2 className="h-4 w-4" />}
      {!isDone && <span className="text-xs text-slate-400">{index + 1}</span>}
    </button>
    <div className="flex-1">
      <p className={`text-sm ${isDone ? 'text-bw-volt text-300 line-through' : 'text-white'}`}>
        {step.hinglish || step.action}
      </p>
      {step.expected && (
        <p className="text-xs text-slate-400 mt-1">
          Expected: <span className="text-bw-volt text-400">{step.expected}</span>
        </p>
      )}
    </div>
  </div>
);

// Main EFI Guidance Panel Component
export default function EFIGuidancePanel({ 
  ticketId, 
  user, 
  vehicleInfo,
  symptoms = [],
  dtcCodes = [],
  category = "general",
  description = "",
  onEstimateUpdated
}) {
  const [guidance, setGuidance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("quick"); // quick or deep
  const [completedSteps, setCompletedSteps] = useState([]);
  const [showDiagram, setShowDiagram] = useState(true);
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const [showRegenerateBtn, setShowRegenerateBtn] = useState(false);
  
  const orgId = user?.organization_id;
  
  // Role-based visibility
  const isSupervisorOrAdmin = user?.role === "admin" || user?.role === "supervisor";
  
  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };
  
  // Check if regeneration is needed (context changed)
  const checkContextChanged = useCallback(async () => {
    if (!ticketId || !orgId) return;
    
    try {
      const res = await fetch(`${API}/api/ai/guidance/check-context`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Organization-ID": orgId
        },
        credentials: "include",
        body: JSON.stringify({
          ticket_id: ticketId,
          mode,
          vehicle_make: vehicleInfo?.make,
          vehicle_model: vehicleInfo?.model,
          symptoms,
          dtc_codes: dtcCodes,
          description
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setShowRegenerateBtn(data.needs_regeneration && data.reason === "context_changed");
      }
    } catch (error) {
      console.error("Context check error:", error);
    }
  }, [ticketId, orgId, mode, vehicleInfo, symptoms, dtcCodes, description]);
  
  // Fetch guidance
  const fetchGuidance = useCallback(async (forceRegenerate = false) => {
    if (!ticketId || !orgId) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/ai/guidance/generate`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Organization-ID": orgId,
          "X-User-ID": user?.user_id || ""
        },
        credentials: "include",
        body: JSON.stringify({
          ticket_id: ticketId,
          mode,
          force_regenerate: forceRegenerate,
          vehicle_make: vehicleInfo?.make,
          vehicle_model: vehicleInfo?.model,
          symptoms,
          dtc_codes: dtcCodes,
          description
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setGuidance(data);
        setCompletedSteps([]);
        setShowRegenerateBtn(false);  // Reset after fetch
        
        // Check for context changes if loaded from cache
        if (data.from_cache) {
          await checkContextChanged();
        }
      } else if (res.status === 403) {
        setGuidance({ enabled: false, message: "EFI Guidance not enabled" });
      } else {
        throw new Error("Failed to fetch guidance");
      }
    } catch (error) {
      console.error("Guidance fetch error:", error);
      toast.error("Could not load guidance");
    } finally {
      setLoading(false);
    }
  }, [ticketId, orgId, mode, vehicleInfo, symptoms, dtcCodes, description, user, checkContextChanged]);
  
  useEffect(() => {
    fetchGuidance();
  }, [ticketId, mode]);
  
  // Submit ask-back answers
  const submitAskBack = async (answers) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/ai/guidance/ask-back`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Organization-ID": orgId
        },
        credentials: "include",
        body: JSON.stringify({
          ticket_id: ticketId,
          answers
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setGuidance(data);
        toast.success("Guidance updated!");
      }
    } catch (error) {
      toast.error("Failed to update guidance");
    } finally {
      setLoading(false);
    }
  };
  
  // Add to estimate
  const addToEstimate = async (items) => {
    try {
      const res = await fetch(`${API}/api/ai/guidance/add-to-estimate`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Organization-ID": orgId
        },
        credentials: "include",
        body: JSON.stringify({
          ticket_id: ticketId,
          items
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`${data.items_added} items added to estimate!`);
        onEstimateUpdated?.();
      }
    } catch (error) {
      toast.error("Failed to add to estimate");
    }
  };
  
  // Submit feedback
  const submitFeedback = async (helped) => {
    if (!guidance?.guidance_id) return;
    
    try {
      await fetch(`${API}/api/ai/guidance/feedback`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Organization-ID": orgId,
          "X-User-ID": user?.user_id || ""
        },
        credentials: "include",
        body: JSON.stringify({
          guidance_id: guidance.guidance_id,
          ticket_id: ticketId,
          helped
        })
      });
      
      setFeedbackGiven(true);
      toast.success("Feedback recorded. Dhanyavaad!");
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };
  
  // Mark step as done
  const markStepDone = (index) => {
    setCompletedSteps(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };
  
  if (guidance?.enabled === false) {
    return (
      <Card className="bg-slate-900/50 border-white/[0.07] border-700">
        <CardContent className="p-6 text-center text-slate-400">
          <Shield className="h-10 w-10 mx-auto mb-3 text-slate-500" />
          <p>EFI Guidance Layer is not enabled for your organization.</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="bg-slate-900 border-white/[0.07] border-700 overflow-hidden" data-testid="efi-guidance-panel">
      {/* Header */}
      <CardHeader className="bg-gradient-to-r from-emerald-900/50 to-slate-900 border-b border-white/[0.07] border-700 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-bw-volt/[0.08]0/20 flex items-center justify-center">
              <Zap className="h-6 w-6 text-bw-volt text-400" />
            </div>
            <div>
              <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                EFI Guidance
                <Badge variant="outline" className="text-xs border-bw-volt/50/50 text-bw-volt text-400">
                  Hinglish
                </Badge>
              </CardTitle>
              <p className="text-xs text-slate-400">
                {guidance?.from_cache && !loading ? "Cached" : "AI-powered"}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Regenerate button - only show when context changed */}
            {showRegenerateBtn && !loading && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => fetchGuidance(true)}
                className="border-amber-500/50 text-amber-400 hover:bg-amber-500/20 text-xs"
                data-testid="regenerate-guidance-btn"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Update
              </Button>
            )}
            
            {/* Refresh/Loading indicator */}
            {loading && (
              <RefreshCw className="h-4 w-4 animate-spin text-bw-volt text-400" />
            )}
            
            {/* Mode Toggle */}
            <div className="flex bg-slate-800 rounded-lg p-0.5">
              <Button
                size="sm"
                variant={mode === "quick" ? "default" : "ghost"}
                className={`text-xs px-2 py-1 h-7 ${mode === "quick" ? "bg-bw-volt text-bw-black font-bold" : "text-bw-white/[0.45]"}`}
                onClick={() => setMode("quick")}
              >
                Quick
              </Button>
              <Button
                size="sm"
                variant={mode === "deep" ? "default" : "ghost"}
                className={`text-xs px-2 py-1 h-7 ${mode === "deep" ? "bg-bw-volt text-bw-black font-bold" : "text-bw-white/[0.45]"}`}
                onClick={() => setMode("deep")}
              >
                Deep
              </Button>
            </div>
          </div>
        </div>
        
        {/* Confidence Badge - Only show to Supervisor/Admin */}
        {isSupervisorOrAdmin && guidance?.confidence && (
          <div className="mt-3 flex items-center gap-2">
            <Badge className={`text-xs ${
              guidance.confidence === 'high' ? 'bg-bw-volt/[0.08]0/20 text-bw-volt text-400' :
              guidance.confidence === 'medium' ? 'bg-amber-500/20 text-amber-400' :
              'bg-rose-500/20 text-rose-400'
            }`}>
              {guidance.confidence} confidence
            </Badge>
            {guidance.sources_count > 0 && (
              <Badge variant="outline" className="text-xs border-white/[0.07] border-600 text-slate-400">
                {guidance.sources_count} sources
              </Badge>
            )}
            {guidance.generation_time_ms && (
              <Badge variant="outline" className="text-xs border-white/[0.07] border-600 text-slate-400">
                {guidance.generation_time_ms}ms
              </Badge>
            )}
          </div>
        )}
      </CardHeader>
      
      <CardContent className="p-0">
        {loading && !guidance ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-bw-volt text-400" />
            <span className="ml-3 text-slate-400">Generating guidance...</span>
          </div>
        ) : guidance?.needs_ask_back && guidance.ask_back_questions?.length > 0 ? (
          <div className="p-4">
            <AskBackForm 
              questions={guidance.ask_back_questions}
              onSubmit={submitAskBack}
              loading={loading}
            />
            
            {/* Safe checklist while waiting */}
            {guidance.diagnostic_steps?.length > 0 && (
              <div className="mt-4 p-4 bg-slate-800/50 rounded-lg">
                <h4 className="text-sm font-medium text-amber-400 mb-3 flex items-center gap-2">
                  <ClipboardList className="h-4 w-4" />
                  Safe Checklist (jab tak detailed guidance nahi milti)
                </h4>
                <div className="space-y-2">
                  {guidance.diagnostic_steps.map((step, i) => (
                    <DiagnosticStep
                      key={i}
                      step={step}
                      index={i}
                      onMarkDone={markStepDone}
                      isDone={completedSteps.includes(i)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <Tabs defaultValue="steps" className="w-full">
            <TabsList className="w-full bg-slate-800/50 border-b border-white/[0.07] border-700 rounded-none p-0">
              <TabsTrigger value="steps" className="flex-1 py-3 data-[state=active]:bg-slate-700">
                <ClipboardList className="h-4 w-4 mr-2" />
                Steps
              </TabsTrigger>
              <TabsTrigger value="visuals" className="flex-1 py-3 data-[state=active]:bg-slate-700">
                <BarChart3 className="h-4 w-4 mr-2" />
                Visuals
              </TabsTrigger>
              <TabsTrigger value="estimate" className="flex-1 py-3 data-[state=active]:bg-slate-700">
                <Wrench className="h-4 w-4 mr-2" />
                Estimate
              </TabsTrigger>
            </TabsList>
            
            {/* STEPS TAB */}
            <TabsContent value="steps" className="p-4 space-y-4 m-0">
              {/* Safety Block */}
              {guidance?.safety_block && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-rose-400 mb-2">
                    <AlertTriangle className="h-5 w-5" />
                    <span className="font-semibold">Safety First - Pehle ye karo!</span>
                  </div>
                  <div className="text-sm text-rose-200 whitespace-pre-line">
                    {guidance.safety_block.replace("## 🛡️ Safety First", "").trim()}
                  </div>
                </div>
              )}
              
              {/* Symptom Summary */}
              {guidance?.symptom_summary && (
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <h4 className="text-xs font-medium text-slate-400 mb-1">Symptom Summary</h4>
                  <p className="text-sm text-white">{guidance.symptom_summary}</p>
                </div>
              )}
              
              {/* Diagnostic Steps */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                    <ClipboardList className="h-4 w-4 text-bw-volt text-400" />
                    Diagnostic Steps ({mode === "quick" ? "Quick Mode" : "Deep Mode"})
                  </h4>
                  <span className="text-xs text-slate-500">
                    {completedSteps.length}/{guidance?.diagnostic_steps?.length || 0} done
                  </span>
                </div>
                
                <div className="space-y-2">
                  {guidance?.diagnostic_steps?.map((step, i) => (
                    <DiagnosticStep
                      key={i}
                      step={step}
                      index={i}
                      onMarkDone={markStepDone}
                      isDone={completedSteps.includes(i)}
                    />
                  ))}
                </div>
              </div>
              
              {/* Probable Causes - Top 3 only (simplified for technicians) */}
              {guidance?.probable_causes?.length > 0 && (
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-400" />
                    Top Probable Causes
                  </h4>
                  <div className="space-y-2">
                    {guidance.probable_causes.slice(0, 3).map((cause, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 text-xs flex items-center justify-center">
                          {i + 1}
                        </span>
                        <span className="text-sm text-white flex-1">{cause.cause}</span>
                        <span className="text-xs text-slate-400">{cause.confidence}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Recommended Fix */}
              {guidance?.recommended_fix && (
                <div className="p-3 bg-bw-volt/[0.08]0/10 border border-bw-volt/50/30 rounded-lg">
                  <h4 className="text-sm font-medium text-bw-volt text-400 mb-2 flex items-center gap-2">
                    <Wrench className="h-4 w-4" />
                    Recommended Fix
                  </h4>
                  <p className="text-sm text-bw-volt text-200">{guidance.recommended_fix}</p>
                </div>
              )}
              
              {/* Sources - Only show to Supervisor/Admin */}
              {isSupervisorOrAdmin && guidance?.sources?.length > 0 && (
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <h4 className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-2">
                    <BookOpen className="h-3 w-3" />
                    Sources Used
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {guidance.sources.map((source, i) => (
                      <Badge key={i} variant="outline" className="text-xs border-white/[0.07] border-600 text-slate-300">
                        {source.source_id || source.title || `Source ${i+1}`}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </TabsContent>
            
            {/* VISUALS TAB */}
            <TabsContent value="visuals" className="p-4 space-y-4 m-0">
              {/* Diagram Toggle */}
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-slate-300">Diagnostic Flow</h4>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowDiagram(!showDiagram)}
                  className="text-slate-400"
                >
                  {showDiagram ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              
              {/* Mermaid Diagram */}
              {showDiagram && guidance?.diagram_spec?.code && (
                <div className="p-4 bg-slate-800/50 rounded-lg overflow-x-auto">
                  <MermaidDiagram 
                    code={guidance.diagram_spec.code}
                    title={guidance.diagram_spec.title}
                  />
                </div>
              )}
              
              {/* Micro Charts */}
              <div className="grid grid-cols-2 gap-3">
                {guidance?.charts_spec?.soc_gauge && (
                  <GaugeChart 
                    value={guidance.charts_spec.soc_gauge.value}
                    max={guidance.charts_spec.soc_gauge.max}
                    title={guidance.charts_spec.soc_gauge.title}
                    unit={guidance.charts_spec.soc_gauge.unit}
                    color={guidance.charts_spec.soc_gauge.color}
                  />
                )}
                
                {guidance?.charts_spec?.confidence_indicator && (
                  <GaugeChart
                    value={guidance.charts_spec.confidence_indicator.value}
                    max={100}
                    title="Source Confidence"
                    unit="%"
                    color={guidance.charts_spec.confidence_indicator.value > 70 ? themeColors.green : themeColors.amber}
                  />
                )}
                
                {guidance?.charts_spec?.time_estimate && (
                  <InfoCard
                    title="Est. Time"
                    value={guidance.charts_spec.time_estimate.value}
                    unit=" min"
                    subtitle={`${guidance.charts_spec.time_estimate.steps_count} steps`}
                  />
                )}
              </div>
              
              {/* Causes Bar Chart */}
              {guidance?.charts_spec?.causes_chart && (
                <HorizontalBarChart
                  data={guidance.charts_spec.causes_chart.data}
                  title={guidance.charts_spec.causes_chart.title}
                  max={guidance.charts_spec.causes_chart.max}
                />
              )}
            </TabsContent>
            
            {/* ESTIMATE TAB */}
            <TabsContent value="estimate" className="p-4 space-y-4 m-0">
              <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                <Wrench className="h-4 w-4 text-bw-volt text-400" />
                Suggested Parts & Labour
              </h4>
              
              {guidance?.estimate_suggestions?.length > 0 ? (
                <>
                  <div className="space-y-2">
                    {guidance.estimate_suggestions.map((item, i) => (
                      <div 
                        key={i}
                        className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Badge className={`text-xs ${
                            item.type === "part" ? "bg-blue-500/20 text-blue-400" : "bg-bw-purple/[0.08]0/20 text-purple-400"
                          }`}>
                            {item.type}
                          </Badge>
                          <div>
                            <p className="text-sm text-white">{item.name}</p>
                            {item.quantity > 1 && (
                              <p className="text-xs text-slate-400">Qty: {item.quantity}</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-bw-volt text-400">
                            ₹{item.estimated_cost?.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-bw-volt/[0.08]0/10 rounded-lg">
                    <span className="text-sm text-bw-white/70">
                      Total: ₹{guidance.estimate_suggestions.reduce((sum, i) => sum + (i.estimated_cost || 0), 0).toLocaleString()}
                    </span>
                    <Button
                      onClick={() => addToEstimate(guidance.estimate_suggestions)}
                      className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold"
                      data-testid="add-all-to-estimate-btn"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add All to Estimate
                    </Button>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <Wrench className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No suggestions available for this diagnosis</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
        
        {/* Footer Actions */}
        {guidance && !guidance.needs_ask_back && (
          <div className="p-4 border-t border-white/[0.07] border-700 flex items-center justify-between">
            {/* Feedback */}
            {!feedbackGiven ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Was this helpful?</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => submitFeedback(true)}
                  className="text-bw-volt text-400 hover:bg-bw-volt/[0.08]0/20"
                >
                  <ThumbsUp className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => submitFeedback(false)}
                  className="text-rose-400 hover:bg-rose-500/20"
                >
                  <ThumbsDown className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <span className="text-xs text-bw-volt text-400">Dhanyavaad for feedback!</span>
            )}
            
            {/* Escalate */}
            <Button
              size="sm"
              variant="outline"
              className="border-amber-500/50 text-amber-400 hover:bg-amber-500/20"
              data-testid="escalate-from-guidance-btn"
            >
              <HelpCircle className="h-4 w-4 mr-2" />
              Escalate to Expert
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
