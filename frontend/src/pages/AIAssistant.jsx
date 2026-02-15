import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Bot, Send, Loader2, Zap, Battery, Plug, Wrench, AlertCircle } from "lucide-react";
import { API } from "@/App";

const categories = [
  { value: "battery", label: "Battery Issues", icon: Battery },
  { value: "motor", label: "Motor Problems", icon: Wrench },
  { value: "charging", label: "Charging System", icon: Plug },
  { value: "electrical", label: "Electrical", icon: Zap },
  { value: "other", label: "Other", icon: AlertCircle },
];

const vehicleModels = [
  "Tata Nexon EV",
  "Tata Tigor EV",
  "Mahindra XUV400",
  "MG ZS EV",
  "Hyundai Kona Electric",
  "Kia EV6",
  "BYD Atto 3",
  "Mercedes EQS",
  "BMW iX",
  "Audi e-tron",
  "Other"
];

export default function AIAssistant({ user }) {
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState({
    issue_description: "",
    vehicle_model: "",
    category: "",
  });
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.issue_description) {
      toast.error("Please describe your issue");
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/ai/diagnose`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(query),
      });

      if (res.ok) {
        const data = await res.json();
        setResponse(data);
      } else {
        toast.error("Failed to get diagnosis");
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="ai-assistant-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-14 w-14 rounded-xl bg-primary/20 flex items-center justify-center animate-pulse-glow">
          <Bot className="h-8 w-8 text-primary" />
        </div>
        <div>
          <h1 className="text-4xl font-bold tracking-tight">AI Diagnostic Assistant</h1>
          <p className="text-muted-foreground mt-1">
            Get instant AI-powered diagnosis for your EV issues.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Form */}
        <Card className="border-white/10 bg-card/50">
          <CardHeader>
            <CardTitle>Describe Your Issue</CardTitle>
            <CardDescription>
              Provide details about the problem you're experiencing with your EV.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Category Selection */}
              <div className="space-y-3">
                <Label>Issue Category</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {categories.map((cat) => {
                    const Icon = cat.icon;
                    return (
                      <button
                        key={cat.value}
                        type="button"
                        onClick={() => setQuery({ ...query, category: cat.value })}
                        className={`p-4 rounded-lg border transition-all text-left ${
                          query.category === cat.value
                            ? "border-primary bg-primary/10"
                            : "border-white/10 hover:border-white/20 bg-background/50"
                        }`}
                        data-testid={`category-btn-${cat.value}`}
                      >
                        <Icon className={`h-5 w-5 mb-2 ${
                          query.category === cat.value ? "text-primary" : "text-muted-foreground"
                        }`} />
                        <p className="text-sm font-medium">{cat.label}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Vehicle Model */}
              <div className="space-y-2">
                <Label>Vehicle Model</Label>
                <Select
                  value={query.vehicle_model}
                  onValueChange={(value) => setQuery({ ...query, vehicle_model: value })}
                >
                  <SelectTrigger className="bg-background/50" data-testid="vehicle-model-select">
                    <SelectValue placeholder="Select your vehicle model" />
                  </SelectTrigger>
                  <SelectContent>
                    {vehicleModels.map((model) => (
                      <SelectItem key={model} value={model}>{model}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Issue Description */}
              <div className="space-y-2">
                <Label>Describe the Issue *</Label>
                <Textarea
                  placeholder="Example: My car won't charge past 80%. The charging port light blinks red after reaching 80% and the charging stops automatically..."
                  className="bg-background/50 min-h-[150px]"
                  value={query.issue_description}
                  onChange={(e) => setQuery({ ...query, issue_description: e.target.value })}
                  data-testid="issue-description-input"
                />
              </div>

              <Button
                type="submit"
                className="w-full glow-primary"
                disabled={loading}
                data-testid="diagnose-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Get AI Diagnosis
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Response */}
        <Card className={`border-white/10 bg-card/50 ${response ? "border-primary/30" : ""}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              AI Diagnosis
            </CardTitle>
            <CardDescription>
              {response ? "Here's our analysis of your issue" : "Submit your query to get an AI-powered diagnosis"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="relative">
                  <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                  <Bot className="h-8 w-8 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </div>
                <p className="text-muted-foreground mt-4">Analyzing your issue...</p>
              </div>
            ) : response ? (
              <div className="space-y-6" data-testid="ai-response">
                {/* Confidence */}
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 bg-background/50 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${response.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground mono">
                    {Math.round(response.confidence * 100)}% confidence
                  </span>
                </div>

                {/* Solution */}
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                  <h4 className="font-semibold mb-3 text-primary">Diagnosis & Solution</h4>
                  <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {response.solution}
                  </div>
                </div>

                {/* Related Tickets */}
                {response.related_tickets?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 text-sm">Related Tickets</h4>
                    <div className="flex flex-wrap gap-2">
                      {response.related_tickets.map((ticket, i) => (
                        <span key={i} className="px-2 py-1 bg-background/50 rounded text-xs mono">
                          {ticket}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Parts */}
                {response.recommended_parts?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 text-sm">Recommended Parts</h4>
                    <div className="flex flex-wrap gap-2">
                      {response.recommended_parts.map((part, i) => (
                        <span key={i} className="px-2 py-1 bg-chart-2/10 text-chart-2 rounded text-xs">
                          {part}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <Bot className="h-16 w-16 mb-4 opacity-20" />
                <p>Describe your issue to get started</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Tips */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-6">
          <h3 className="font-semibold mb-4">Tips for Better Diagnosis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-background/50">
              <p className="font-medium mb-1">Be Specific</p>
              <p className="text-sm text-muted-foreground">Include exact symptoms, sounds, or error messages you've noticed.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/50">
              <p className="font-medium mb-1">Add Context</p>
              <p className="text-sm text-muted-foreground">Mention when the issue started and any recent changes or incidents.</p>
            </div>
            <div className="p-4 rounded-lg bg-background/50">
              <p className="font-medium mb-1">Include Conditions</p>
              <p className="text-sm text-muted-foreground">Note weather, driving conditions, or charging setup when issue occurs.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
