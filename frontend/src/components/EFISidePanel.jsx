import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { toast } from "sonner";
import { 
  ChevronRight, ChevronDown, ChevronLeft, Brain, Zap, CheckCircle2, XCircle, 
  AlertTriangle, Wrench, Clock, Target, ArrowRight, Lightbulb, Image,
  FileText, Play, RefreshCw, BookOpen, TrendingUp
} from "lucide-react";
import { API } from "@/App";

// Confidence badge styling
const confidenceBadge = (level, score) => {
  const styles = {
    high: "bg-[rgba(34,197,94,0.08)]0/15 text-green-600 border-green-500/30",
    medium: "bg-[rgba(234,179,8,0.08)]0/15 text-[#EAB308] border-yellow-500/30",
    low: "bg-[rgba(255,140,0,0.08)]0/15 text-[#FF8C00] border-orange-500/30"
  };
  return (
    <Badge variant="outline" className={styles[level] || styles.low}>
      {Math.round((score || 0) * 100)}% Match
    </Badge>
  );
};

// Subsystem icon mapping
const subsystemIcons = {
  battery: "🔋",
  motor: "⚡",
  controller: "🧠",
  wiring: "🔌",
  electrical: "🔌",
  mechanical: "⚙️"
};

export default function EFISidePanel({ ticket, user, isOpen, onToggle, onEstimateSuggested }) {
  const [suggestions, setSuggestions] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stepNotes, setStepNotes] = useState("");
  const [completedSteps, setCompletedSteps] = useState([]);
  const [selectedPath, setSelectedPath] = useState(null);
  const [estimate, setEstimate] = useState(null);
  
  const token = localStorage.getItem("token");
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  // Fetch EFI suggestions when ticket changes
  const fetchSuggestions = useCallback(async () => {
    if (!ticket?.ticket_id) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API}/efi-guided/suggestions/${ticket.ticket_id}`, {
        credentials: "include",
        headers
      });
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data);
        
        // Check if there's an active session
        if (data.active_session) {
          setActiveSession(data.active_session);
          await fetchSession(data.active_session.session_id);
        }
      }
    } catch (error) {
      console.error("Failed to fetch EFI suggestions:", error);
    } finally {
      setLoading(false);
    }
  }, [ticket?.ticket_id]);

  // Fetch session details
  const fetchSession = async (sessionId) => {
    try {
      const response = await fetch(`${API}/efi-guided/session/${sessionId}`, {
        credentials: "include",
        headers
      });
      
      if (response.ok) {
        const data = await response.json();
        setActiveSession(data);
        setCurrentStep(data.current_step);
        setCompletedSteps(data.completed_steps || []);
        
        // If session completed, fetch estimate
        if (data.status === "completed") {
          fetchEstimate(sessionId);
        }
      }
    } catch (error) {
      console.error("Failed to fetch session:", error);
    }
  };

  // Start diagnostic session
  const startSession = async (failureCardId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/efi-guided/session/start`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          ticket_id: ticket.ticket_id,
          failure_card_id: failureCardId
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setActiveSession(data);
        setCurrentStep(data.current_step);
        setCompletedSteps([]);
        setSelectedPath(suggestions.suggested_paths.find(p => p.failure_id === failureCardId));
        toast.success("Diagnostic session started");
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to start session");
      }
    } catch (error) {
      toast.error("Failed to start diagnostic session");
    } finally {
      setLoading(false);
    }
  };

  // Record step outcome
  const recordOutcome = async (outcome) => {
    if (!activeSession || !currentStep) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/efi-guided/session/${activeSession.session_id}/step/${currentStep.step_id}`,
        {
          method: "POST",
          headers: { ...headers, "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            outcome,
            notes: stepNotes,
            time_taken_seconds: 60 // Placeholder
          })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setStepNotes("");
        
        // Update completed steps
        setCompletedSteps(prev => [...prev, {
          step_id: currentStep.step_id,
          outcome,
          instruction: currentStep.instruction
        }]);
        
        if (data.session_completed) {
          // Session complete - show resolution
          toast.success("Diagnosis complete!");
          setCurrentStep(null);
          
          if (data.resolution) {
            setEstimate(data.resolution);
            // Notify parent of estimate suggestion
            if (onEstimateSuggested) {
              onEstimateSuggested(data.resolution);
            }
          }
          
          // Refresh session
          fetchSession(activeSession.session_id);
        } else if (data.next_step) {
          setCurrentStep(data.next_step);
          toast.info(`Step ${outcome === "pass" ? "passed" : "failed"} - Moving to next step`);
        }
      }
    } catch (error) {
      toast.error("Failed to record outcome");
    } finally {
      setLoading(false);
    }
  };

  // Fetch estimate suggestion
  const fetchEstimate = async (sessionId) => {
    try {
      const response = await fetch(`${API}/efi-guided/session/${sessionId}/estimate`, {
        credentials: "include",
        headers
      });
      
      if (response.ok) {
        const data = await response.json();
        setEstimate(data);
      }
    } catch (error) {
      console.error("Failed to fetch estimate:", error);
    }
  };

  // Apply estimate to job card
  const applyEstimate = () => {
    if (estimate && onEstimateSuggested) {
      onEstimateSuggested(estimate);
      toast.success("Estimate applied to job card");
    }
  };

  useEffect(() => {
    if (isOpen && ticket?.ticket_id) {
      fetchSuggestions();
    }
  }, [isOpen, ticket?.ticket_id, fetchSuggestions]);

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-50 bg-primary text-primary-foreground p-3 rounded-l-lg shadow-lg hover:bg-primary/90 transition-all"
        data-testid="efi-toggle-btn"
      >
        <Brain className="h-5 w-5" />
        <span className="sr-only">Open EFI Assistant</span>
      </button>
    );
  }

  return (
    <div className="w-[400px] border-l bg-background shadow-xl flex flex-col h-full" data-testid="efi-side-panel">
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            <h2 className="font-semibold">EV Failure Intelligence</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onToggle} className="text-white hover:bg-[#111820]/20">
            <ChevronRight className="h-5 w-5" />
          </Button>
        </div>
        {suggestions?.classified_subsystem && (
          <div className="mt-2 flex items-center gap-2 text-sm text-white/80">
            <span>{subsystemIcons[suggestions.classified_subsystem] || "🔧"}</span>
            <span>Detected: {suggestions.classified_subsystem.toUpperCase()} System</span>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          
          {/* Loading State */}
          {loading && !activeSession && (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* No Suggestions Yet */}
          {!loading && !suggestions?.suggested_paths?.length && !activeSession && (
            <Card className="border-dashed">
              <CardContent className="py-8 text-center">
                <Lightbulb className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">
                  No matching failure patterns found for this complaint.
                </p>
                <Button variant="outline" size="sm" className="mt-4" onClick={fetchSuggestions}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh Analysis
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Active Diagnostic Session */}
          {activeSession && currentStep && (
            <Card className="border-blue-500/50 bg-blue-50/50 dark:bg-blue-950/20">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Play className="h-4 w-4 text-[#3B9EFF]" />
                    Active Diagnosis
                  </CardTitle>
                  <Badge variant="outline" className="bg-blue-100 text-[#3B9EFF]">
                    Step {completedSteps.length + 1}
                  </Badge>
                </div>
                {selectedPath && (
                  <CardDescription className="text-xs">
                    {selectedPath.title}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Progress */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Progress</span>
                    <span>{completedSteps.length} steps completed</span>
                  </div>
                  <Progress value={(completedSteps.length / (activeSession.tree?.steps?.length || 1)) * 100} />
                </div>

                {/* Current Step */}
                <div className="p-3 bg-[#111820] dark:bg-[#080C0F] rounded-lg border">
                  <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                    <Target className="h-4 w-4 text-[#3B9EFF]" />
                    {currentStep.instruction}
                  </h4>
                  
                  {currentStep.expected_measurement && (
                    <p className="text-xs text-muted-foreground mb-2">
                      <span className="font-medium">Expected:</span> {currentStep.expected_measurement}
                    </p>
                  )}

                  {currentStep.tools_required?.length > 0 && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
                      <Wrench className="h-3 w-3" />
                      <span>{currentStep.tools_required.join(", ")}</span>
                    </div>
                  )}

                  {currentStep.safety_notes && (
                    <div className="flex items-start gap-2 p-2 bg-[rgba(234,179,8,0.08)] dark:bg-yellow-900/20 rounded text-xs text-[#EAB308] dark:text-yellow-400 mb-2">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span>{currentStep.safety_notes}</span>
                    </div>
                  )}

                  {currentStep.reference_image && (
                    <div className="mb-3">
                      <div className="flex items-center gap-2 text-xs text-[#3B9EFF] mb-2">
                        <Image className="h-3 w-3" />
                        <span className="font-medium">Reference Image</span>
                      </div>
                      <div className="relative rounded-lg overflow-hidden border bg-[#111820]">
                        <img 
                          src={currentStep.reference_image.startsWith('/api') 
                            ? `${window.location.origin}${currentStep.reference_image}` 
                            : currentStep.reference_image
                          }
                          alt="Step reference"
                          className="w-full h-auto max-h-48 object-contain cursor-pointer hover:opacity-90 transition-opacity"
                          onClick={() => window.open(currentStep.reference_image, '_blank')}
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                        <div 
                          className="hidden items-center justify-center p-4 text-xs text-gray-500"
                          onClick={() => window.open(currentStep.reference_image, '_blank')}
                        >
                          <Image className="h-8 w-8 text-[rgba(244,246,240,0.20)] mr-2" />
                          Click to view reference image
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Notes */}
                <Textarea
                  placeholder="Add notes or measurements (optional)..."
                  value={stepNotes}
                  onChange={(e) => setStepNotes(e.target.value)}
                  className="h-16 text-sm"
                />

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    onClick={() => recordOutcome("pass")}
                    disabled={loading}
                    data-testid="efi-pass-btn"
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    PASS
                  </Button>
                  <Button
                    className="flex-1 bg-red-600 hover:bg-red-700"
                    onClick={() => recordOutcome("fail")}
                    disabled={loading}
                    data-testid="efi-fail-btn"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    FAIL
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Completed Steps */}
          {completedSteps.length > 0 && (
            <Collapsible>
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 bg-muted/50 rounded-lg text-sm">
                <span className="font-medium">Completed Steps ({completedSteps.length})</span>
                <ChevronDown className="h-4 w-4" />
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 space-y-2">
                {completedSteps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 bg-muted/30 rounded text-xs">
                    {step.outcome === "pass" ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-600 shrink-0" />
                    )}
                    <span className="truncate">{step.instruction}</span>
                  </div>
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}

          {/* Session Completed - Show Estimate */}
          {activeSession?.status === "completed" && estimate && (
            <Card className="border-green-500/50 bg-[rgba(34,197,94,0.08)]/50 dark:bg-green-950/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-400">
                  <CheckCircle2 className="h-5 w-5" />
                  Diagnosis Complete
                </CardTitle>
                <CardDescription>
                  {estimate.resolution?.title || "Resolution identified"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  {estimate.resolution?.description}
                </p>

                {/* Suggested Parts */}
                {estimate.parts?.length > 0 && (
                  <div>
                    <h5 className="text-xs font-medium mb-1">Suggested Parts:</h5>
                    <div className="space-y-1">
                      {estimate.parts.map((part, idx) => (
                        <div key={idx} className="flex justify-between text-xs p-1.5 bg-[#111820] dark:bg-[#080C0F] rounded">
                          <span>{part.name} × {part.quantity}</span>
                          <span className="font-mono">₹{(part.price || 0).toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Estimate Summary */}
                <div className="p-3 bg-[#111820] dark:bg-[#080C0F] rounded-lg border space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Parts Total</span>
                    <span className="font-mono">₹{(estimate.parts_total || 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Labor ({estimate.labor_hours}h × ₹{estimate.labor_rate})</span>
                    <span className="font-mono">₹{(estimate.labor_total || 0).toLocaleString()}</span>
                  </div>
                  <Separator className="my-1" />
                  <div className="flex justify-between font-medium">
                    <span>Estimated Total</span>
                    <span className="font-mono">₹{(estimate.estimated_total || 0).toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>Expected time: ~{estimate.expected_time_minutes} minutes</span>
                </div>

                <Button className="w-full" onClick={applyEstimate} data-testid="efi-apply-estimate-btn">
                  <FileText className="h-4 w-4 mr-2" />
                  Apply to Job Card Estimate
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Suggested Paths (when no active session) */}
          {!activeSession && suggestions?.suggested_paths?.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Suggested Diagnostic Paths
              </h3>
              
              {suggestions.suggested_paths.map((path, index) => (
                <Card 
                  key={path.failure_id} 
                  className={`cursor-pointer transition-all hover:border-blue-500 ${index === 0 ? 'border-blue-500/50' : ''}`}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{subsystemIcons[path.subsystem_category] || "🔧"}</span>
                        <div>
                          <CardTitle className="text-sm">{path.title}</CardTitle>
                          {index === 0 && (
                            <Badge className="mt-1 bg-blue-600 text-xs">Best Match</Badge>
                          )}
                        </div>
                      </div>
                      {confidenceBadge(path.confidence_level, path.similarity_score)}
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0 space-y-2">
                    {path.symptom_text && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {path.symptom_text}
                      </p>
                    )}
                    
                    {path.root_cause && (
                      <div className="text-xs">
                        <span className="font-medium">Root Cause:</span>{" "}
                        <span className="text-muted-foreground">{path.root_cause}</span>
                      </div>
                    )}

                    {path.has_decision_tree && (
                      <div className="flex items-center gap-2 text-xs text-green-600">
                        <BookOpen className="h-3 w-3" />
                        <span>{path.decision_tree_steps} step guided diagnosis available</span>
                      </div>
                    )}

                    <Button 
                      size="sm" 
                      className="w-full mt-2"
                      onClick={() => startSession(path.failure_id)}
                      disabled={loading || !path.has_decision_tree}
                      data-testid={`efi-start-path-${index}`}
                    >
                      {path.has_decision_tree ? (
                        <>
                          <Play className="h-3 w-3 mr-2" />
                          Start Guided Diagnosis
                        </>
                      ) : (
                        <>
                          <Zap className="h-3 w-3 mr-2" />
                          View Details
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-3 border-t bg-muted/30 text-xs text-muted-foreground flex items-center justify-between">
        <span>Powered by AI Intelligence</span>
        <Button variant="ghost" size="sm" onClick={fetchSuggestions} className="h-7">
          <RefreshCw className="h-3 w-3 mr-1" />
          Refresh
        </Button>
      </div>
    </div>
  );
}
