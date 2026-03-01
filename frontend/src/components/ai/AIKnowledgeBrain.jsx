import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import {
  Sparkles, Send, Loader2, Bot, User, Lightbulb, AlertTriangle,
  Wrench, Battery, Cpu, CircuitBoard, MessageSquare, Zap,
  Copy, CheckCircle, RotateCcw, ThumbsUp, ThumbsDown, 
  ExternalLink, FileText, BookOpen, AlertCircle, ChevronRight,
  Shield, HelpCircle, List
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// Categories for different diagnostic areas
const CATEGORIES = [
  { value: "general", label: "General Query", icon: MessageSquare, color: "slate" },
  { value: "battery", label: "Battery/BMS", icon: Battery, color: "amber" },
  { value: "motor", label: "Motor/Controller", icon: Cpu, color: "blue" },
  { value: "electrical", label: "Electrical", icon: CircuitBoard, color: "purple" },
  { value: "charger", label: "Charging", icon: Zap, color: "green" },
  { value: "diagnosis", label: "Diagnosis", icon: Wrench, color: "rose" },
];

// Quick questions for each category
const QUICK_QUESTIONS = {
  general: [
    "How to interpret OBD error codes?",
    "Standard EV service checklist",
    "Pre-delivery inspection steps",
  ],
  battery: [
    "BMS communication error diagnosis",
    "Battery cell imbalance solutions",
    "Thermal runaway prevention",
    "SOC calibration procedure",
  ],
  motor: [
    "Motor controller overheating steps",
    "BLDC motor testing procedure",
    "Regenerative braking issues",
    "Hall sensor fault diagnosis",
  ],
  electrical: [
    "High voltage system safety",
    "12V auxiliary battery issues",
    "Ground fault detection",
    "Wiring harness inspection",
  ],
  charger: [
    "Charger not detecting vehicle",
    "Slow charging troubleshooting",
    "CCS connector issues",
    "Onboard charger faults",
  ],
  diagnosis: [
    "Systematic fault isolation",
    "CAN bus diagnostics",
    "Error code interpretation",
    "Component testing procedures",
  ],
};

export default function AIKnowledgeBrain({ user, portalType = "technician", ticketId = null, vehicleInfo = null }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("general");
  const [showSources, setShowSources] = useState(false);
  const [currentSources, setCurrentSources] = useState([]);
  const [queryId, setQueryId] = useState(null);
  const [lastUserQuery, setLastUserQuery] = useState("");
  const [escalating, setEscalating] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message on mount
  useEffect(() => {
    const userName = user?.name?.split(' ')[0] || 'Technician';
    setMessages([{
      id: 'welcome',
      role: "assistant",
      content: null,
      isWelcome: true,
      userName
    }]);
  }, [user]);

  // Handle escalation to Expert Queue
  const handleEscalate = async (message) => {
    if (escalating) return;
    setEscalating(true);
    
    try {
      const escalationData = {
        query_id: message.queryId || queryId,
        ticket_id: ticketId,
        organization_id: user?.organization_id,
        original_query: lastUserQuery,
        ai_response: message.content,
        sources_checked: (message.sources || []).map(s => s.source_id),
        vehicle_info: vehicleInfo,
        symptoms: [],
        dtc_codes: [],
        images: [],
        documents: [],
        urgency: message.escalationRecommended ? "high" : "normal",
        reason: message.escalationReason || "User requested expert review",
        user_id: user?.user_id,
        user_name: user?.name || "Technician"
      };
      
      const res = await fetch(`${API}/ai/assist/escalate`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
          "X-Organization-ID": user?.organization_id || "",
          "X-User-ID": user?.user_id || "",
          "X-User-Name": user?.name || ""
        },
        credentials: "include",
        body: JSON.stringify(escalationData)
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(`Escalation created: ${result.escalation_id}. An expert will review your query.`);
        
        // Add escalation confirmation to chat
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: "assistant",
          content: `✅ **Escalation Created**\n\nYour query has been escalated to the Expert Queue (ID: ${result.escalation_id}).\n\nAn expert technician will review your issue and respond. You'll be notified when they respond.\n\n**Priority:** ${result.priority || "normal"}`,
          timestamp: new Date().toISOString(),
          isEscalationConfirmation: true
        }]);
      } else {
        throw new Error("Failed to create escalation");
      }
    } catch (error) {
      console.error("Escalation error:", error);
      toast.error("Failed to escalate. Please try again.");
    } finally {
      setEscalating(false);
    }
  };

  const sendMessage = async (messageText = input) => {
    if (!messageText.trim()) return;
    
    setLastUserQuery(messageText);

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setCurrentSources([]);

    try {
      const res = await fetch(`${API}/ai/assist/query`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({
          query: messageText,
          category: selectedCategory,
          portal_type: portalType,
          user_id: user?.user_id,
          organization_id: user?.organization_id
        })
      });

      if (res.ok) {
        const data = await res.json();
        
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response,
          timestamp: new Date().toISOString(),
          sources: data.sources || [],
          confidence: data.confidence_level,
          safetyWarnings: data.safety_warnings || [],
          diagnosticSteps: data.diagnostic_steps || [],
          probableCauses: data.probable_causes || [],
          escalationRecommended: data.escalation_recommended,
          escalationReason: data.escalation_reason,
          queryId: data.query_id
        }]);
        
        setCurrentSources(data.sources || []);
        setQueryId(data.query_id);
      } else {
        throw new Error("Failed to get AI response");
      }
    } catch (error) {
      console.error("AI assist error:", error);
      toast.error("Failed to get AI response");
      
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error. Please try again or escalate to an expert.",
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const submitFeedback = async (type) => {
    if (!queryId) return;
    
    try {
      await fetch(`${API}/ai/assist/feedback`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({
          query_id: queryId,
          feedback_type: type,
          user_id: user?.user_id,
          organization_id: user?.organization_id,
          created_at: new Date().toISOString()
        })
      });
      
      toast.success(type === "helpful" ? "Thank you for your feedback!" : "Feedback recorded. We'll improve.");
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  const resetChat = () => {
    const userName = user?.name?.split(' ')[0] || 'Technician';
    setMessages([{
      id: 'welcome',
      role: "assistant",
      content: null,
      isWelcome: true,
      userName
    }]);
    setInput("");
    setCurrentSources([]);
    setQueryId(null);
    toast.success("Chat cleared");
  };

  const formatMarkdown = (content) => {
    if (!content) return null;
    
    return content.split('\n').map((line, i) => {
      // Headers
      if (line.startsWith('## ')) {
        return <h2 key={i} className="text-lg font-bold text-bw-volt text-400 mt-4 mb-2">{line.substring(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={i} className="text-base font-semibold text-white mt-3 mb-1">{line.substring(4)}</h3>;
      }
      // Bold text
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} className="mb-1.5">
            {parts.map((part, j) => 
              j % 2 === 1 ? <strong key={j} className="text-amber-400 font-semibold">{part}</strong> : part
            )}
          </p>
        );
      }
      // Bullet points
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return <li key={i} className="ml-5 mb-1 list-disc text-slate-300">{line.substring(2)}</li>;
      }
      // Numbered lists
      if (/^\d+\.\s/.test(line)) {
        return <li key={i} className="ml-5 mb-1 list-decimal text-slate-300">{line.substring(line.indexOf('.') + 2)}</li>;
      }
      // Empty lines
      if (line.trim() === '') {
        return <br key={i} />;
      }
      return <p key={i} className="mb-1.5 text-slate-300">{line}</p>;
    });
  };

  // Welcome message component
  const WelcomeMessage = ({ userName }) => (
    <div className="space-y-4">
      <p className="text-lg">
        Hello <span className="text-bw-volt text-400 font-semibold">{userName}</span>! 
        I'm your AI Diagnostic Assistant powered by Gemini.
      </p>
      
      <div className="space-y-2">
        <p className="text-slate-300">I can help you with:</p>
        <ul className="space-y-2 ml-2">
          <li className="flex items-start gap-2">
            <Wrench className="h-4 w-4 text-bw-volt text-400 mt-1 flex-shrink-0" />
            <span><strong className="text-bw-volt text-400">Fault Diagnosis:</strong> Describe symptoms, I'll suggest causes</span>
          </li>
          <li className="flex items-start gap-2">
            <BookOpen className="h-4 w-4 text-bw-volt text-400 mt-1 flex-shrink-0" />
            <span><strong className="text-bw-volt text-400">Repair Procedures:</strong> Step-by-step repair guides</span>
          </li>
          <li className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-bw-volt text-400 mt-1 flex-shrink-0" />
            <span><strong className="text-bw-volt text-400">Error Code Interpretation:</strong> Decode OBD/CAN error codes</span>
          </li>
          <li className="flex items-start gap-2">
            <FileText className="h-4 w-4 text-bw-volt text-400 mt-1 flex-shrink-0" />
            <span><strong className="text-bw-volt text-400">Technical Documentation:</strong> Quick access to repair knowledge</span>
          </li>
        </ul>
      </div>
      
      <Separator className="bg-slate-700/50" />
      
      <p className="text-slate-400">
        Select a category or ask me anything about EV service and repair!
      </p>
    </div>
  );

  // Source citation component
  const SourceCitation = ({ source, index }) => (
    <div className="flex items-start gap-2 p-2 bg-slate-800/50 rounded-lg border border-white/[0.07] border-700/50 hover:border-bw-volt/50/30 transition-colors">
      <div className="flex-shrink-0 w-6 h-6 rounded bg-bw-volt/[0.08]0/20 flex items-center justify-center">
        <span className="text-xs text-bw-volt text-400 font-medium">{index + 1}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{source.title}</p>
        <p className="text-xs text-slate-400 mt-0.5">{source.source_type} • {Math.round(source.relevance_score * 100)}% match</p>
        <p className="text-xs text-slate-500 mt-1 line-clamp-2">{source.snippet}</p>
      </div>
      <Button variant="ghost" size="sm" className="flex-shrink-0 h-7 w-7 p-0">
        <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
      </Button>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-slate-900 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/[0.07] border-800/50 bg-gradient-to-r from-slate-900 to-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-bw-volt/[0.08]0/20 rounded-xl blur-xl" />
              <div className="relative p-3 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl border border-bw-volt/50/20">
                <Sparkles className="h-6 w-6 text-bw-volt text-400" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AI Diagnostic Assistant</h1>
              <p className="text-sm text-slate-400">Powered by Gemini - Your EV repair companion</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={resetChat}
              className="text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <RotateCcw className="h-4 w-4 mr-1.5" />
              Clear
            </Button>
            <Badge className="bg-bw-volt/[0.08]0/20 text-bw-volt text-400 border border-bw-volt/50/30 px-3 py-1">
              <Zap className="h-3 w-3 mr-1.5" />
              AI Enabled
            </Badge>
          </div>
        </div>
      </div>

      {/* Quick Questions Section */}
      <div className="px-6 py-3 border-b border-white/[0.07] border-800/50 bg-slate-900/50">
        <div className="flex items-center gap-2 mb-2">
          <Lightbulb className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium text-slate-300">Quick Questions:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {QUICK_QUESTIONS[selectedCategory]?.map((question, idx) => (
            <button
              key={idx}
              onClick={() => sendMessage(question)}
              disabled={loading}
              className="px-3 py-1.5 text-xs bg-slate-800/80 border border-white/[0.07] border-700/50 rounded-full text-slate-300 hover:bg-slate-700 hover:text-white hover:border-bw-volt/50/30 transition-all disabled:opacity-50 flex items-center gap-1"
            >
              {question}
              <ChevronRight className="h-3 w-3 opacity-50" />
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Messages */}
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="space-y-6 max-w-4xl">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : ""}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 ${message.role === "user" ? "order-1" : ""}`}>
                  {message.role === "assistant" ? (
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/30 to-emerald-600/20 border border-bw-volt/50/30 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-bw-volt text-400" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 border border-white/[0.07] border-600 flex items-center justify-center">
                      <User className="h-5 w-5 text-slate-300" />
                    </div>
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex-1 max-w-[85%] ${message.role === "user" ? "text-right" : ""}`}>
                  <div
                    className={`inline-block rounded-2xl px-5 py-4 ${
                      message.role === "user"
                        ? "bg-bw-volt/15 text-bw-white border border-bw-volt/25 rounded-br-md"
                        : message.error
                        ? "bg-bw-red/[0.08] border border-bw-red/30 text-bw-white rounded-bl-md"
                        : "bg-slate-800/80 border border-white/[0.07] text-bw-white rounded-bl-md"
                    }`}
                  >
                    {message.isWelcome ? (
                      <WelcomeMessage userName={message.userName} />
                    ) : (
                      <div className="text-sm leading-relaxed">
                        {formatMarkdown(message.content)}
                      </div>
                    )}
                    
                    {/* Safety Warnings */}
                    {message.safetyWarnings?.length > 0 && (
                      <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                        <div className="flex items-center gap-2 text-amber-400 mb-2">
                          <AlertTriangle className="h-4 w-4" />
                          <span className="font-semibold text-sm">Safety Warnings</span>
                        </div>
                        <ul className="text-xs text-amber-200 space-y-1">
                          {message.safetyWarnings.map((warning, i) => (
                            <li key={i}>• {warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* Escalation Warning */}
                    {message.escalationRecommended && (
                      <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                        <div className="flex items-center gap-2 text-rose-400 mb-2">
                          <Shield className="h-4 w-4" />
                          <span className="font-semibold text-sm">Expert Review Recommended</span>
                        </div>
                        <p className="text-xs text-rose-200 mb-3">{message.escalationReason}</p>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-rose-500/50 text-rose-400 hover:bg-rose-500/20"
                          onClick={() => handleEscalate(message)}
                          data-testid="escalate-to-expert-btn"
                        >
                          <HelpCircle className="h-3.5 w-3.5 mr-1.5" />
                          Escalate to Expert Queue
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Message Actions */}
                  {message.role === "assistant" && !message.isWelcome && (
                    <div className="flex items-center gap-3 mt-2 text-slate-500">
                      <span className="text-xs">
                        {message.confidence && (
                          <Badge variant="outline" className={`text-xs mr-2 ${
                            message.confidence === 'high' ? 'border-bw-volt/50/50 text-bw-volt text-400' :
                            message.confidence === 'medium' ? 'border-amber-500/50 text-amber-400' :
                            'border-white/[0.07] border-500/50 text-slate-400'
                          }`}>
                            {message.confidence} confidence
                          </Badge>
                        )}
                        {message.sources?.length > 0 && (
                          <span className="text-bw-volt text-400">{message.sources.length} sources</span>
                        )}
                      </span>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => copyToClipboard(message.content)}
                        className="text-xs hover:text-slate-300 flex items-center gap-1 transition-colors"
                      >
                        <Copy className="h-3 w-3" />
                        Copy
                      </button>
                      <button 
                        onClick={() => submitFeedback("helpful")}
                        className="text-xs hover:text-bw-volt text-400 flex items-center gap-1 transition-colors"
                      >
                        <ThumbsUp className="h-3 w-3" />
                        Helpful
                      </button>
                      <button 
                        onClick={() => submitFeedback("not_helpful")}
                        className="text-xs hover:text-rose-400 flex items-center gap-1 transition-colors"
                      >
                        <ThumbsDown className="h-3 w-3" />
                        Not helpful
                      </button>
                      {!message.escalationRecommended && (
                        <button 
                          onClick={() => handleEscalate(message)}
                          className="text-xs hover:text-amber-400 flex items-center gap-1 transition-colors"
                        >
                          <HelpCircle className="h-3 w-3" />
                          Escalate
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading State */}
            {loading && (
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/30 to-emerald-600/20 border border-bw-volt/50/30 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-bw-volt text-400" />
                </div>
                <div className="bg-slate-800/80 border border-white/[0.07] rounded-2xl rounded-bl-md px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-bw-volt rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-bw-volt rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-bw-volt rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm text-bw-white/[0.45]">Searching knowledge base...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Sources Panel */}
        {currentSources.length > 0 && (
          <div className="w-80 border-l border-white/[0.07] border-800/50 bg-slate-900/50 flex flex-col">
            <div className="px-4 py-3 border-b border-white/[0.07] border-800/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-bw-volt text-400" />
                  <span className="text-sm font-medium text-white">Sources Used</span>
                </div>
                <Badge variant="outline" className="text-xs border-bw-volt/50/30 text-bw-volt text-400">
                  {currentSources.length}
                </Badge>
              </div>
            </div>
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-3">
                {currentSources.map((source, idx) => (
                  <SourceCitation key={idx} source={source} index={idx} />
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-white/[0.07] border-800/50 bg-slate-900">
        <div className="flex gap-3 items-end max-w-4xl">
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-48 bg-slate-800/50 border-white/[0.07] border-700/50 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-white/[0.07] border-700">
              {CATEGORIES.map(cat => {
                const Icon = cat.icon;
                return (
                  <SelectItem key={cat.value} value={cat.value} className="text-white hover:bg-slate-700">
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      {cat.label}
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
          
          <div className="flex-1">
            <Input
              ref={inputRef}
              placeholder="Ask me anything about EV diagnostics, repairs, or error codes..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              className="bg-slate-800/50 border-white/[0.07] border-700/50 text-white placeholder:text-slate-500 focus:border-bw-volt/50/50 focus:ring-emerald-500/20 h-12"
              disabled={loading}
              data-testid="ai-query-input"
            />
          </div>
          
          <Button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="h-12 w-12 rounded-xl bg-bw-volt hover:bg-bw-volt-hover text-bw-black border-0"
            data-testid="ai-send-btn"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
