import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  Sparkles, Send, Loader2, Bot, User, Lightbulb, 
  Wrench, Battery, Cpu, CircuitBoard, MessageSquare,
  Copy, CheckCircle, RotateCcw, Zap, Car, ThumbsUp,
  ThumbsDown, ChevronRight, Mic, Paperclip
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

// Unified AI Chat Component for all portals
export default function UnifiedAIChat({ 
  user, 
  portalType = "technician", // "technician", "admin", "business", "customer"
  apiEndpoint = "/technician/ai-assist"
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("general");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Categories based on portal type
  const categoryConfig = {
    technician: [
      { value: "general", label: "General", icon: MessageSquare, color: "emerald" },
      { value: "battery", label: "Battery", icon: Battery, color: "amber" },
      { value: "motor", label: "Motor", icon: Cpu, color: "blue" },
      { value: "electrical", label: "Electrical", icon: CircuitBoard, color: "purple" },
      { value: "diagnosis", label: "Diagnosis", icon: Wrench, color: "rose" },
    ],
    admin: [
      { value: "general", label: "General", icon: MessageSquare, color: "emerald" },
      { value: "inventory", label: "Inventory", icon: Battery, color: "amber" },
      { value: "reports", label: "Reports", icon: Cpu, color: "blue" },
      { value: "customers", label: "Customers", icon: User, color: "purple" },
    ],
    business: [
      { value: "general", label: "General", icon: MessageSquare, color: "emerald" },
      { value: "invoices", label: "Invoices", icon: Battery, color: "amber" },
      { value: "service", label: "Service", icon: Wrench, color: "blue" },
    ],
    customer: [
      { value: "general", label: "General", icon: MessageSquare, color: "emerald" },
      { value: "vehicle", label: "My Vehicle", icon: Car, color: "amber" },
      { value: "service", label: "Service", icon: Wrench, color: "blue" },
    ],
  };

  const categories = categoryConfig[portalType] || categoryConfig.technician;

  // Quick prompts based on portal type
  const quickPromptConfig = {
    technician: [
      "How to diagnose BMS communication error?",
      "Motor controller overheating steps",
      "Battery cell imbalance solutions",
      "Charger not detecting vehicle",
      "Common OBD error codes for EVs",
    ],
    admin: [
      "Show inventory low stock alerts",
      "Generate monthly revenue report",
      "Pending customer payments",
      "Top service issues this week",
    ],
    business: [
      "Check my pending invoices",
      "Service history for my vehicles",
      "Schedule a maintenance visit",
    ],
    customer: [
      "What's the status of my service?",
      "Explain my invoice charges",
      "Book a new service appointment",
    ],
  };

  const quickPrompts = quickPromptConfig[portalType] || quickPromptConfig.technician;

  const welcomeMessages = {
    technician: `Hello ${user?.name?.split(' ')[0] || 'Technician'}! I'm your AI Diagnostic Assistant.

I can help you with:
• **Fault Diagnosis** - Describe symptoms, I'll suggest causes
• **Repair Procedures** - Step-by-step repair guides
• **Error Codes** - Decode OBD/CAN error codes
• **Technical Docs** - Quick access to repair knowledge

What would you like help with today?`,
    admin: `Hello ${user?.name?.split(' ')[0] || 'Admin'}! I'm your AI Business Assistant.

I can help you with:
• **Reports & Analytics** - Generate insights
• **Inventory Management** - Stock levels & alerts
• **Customer Insights** - Payment & service history
• **Operations** - Workflow optimization

How can I assist you today?`,
    business: `Hello! I'm your AI Service Assistant.

I can help you with:
• **Invoice Queries** - Understand your bills
• **Service Status** - Track your vehicles
• **Scheduling** - Book appointments
• **Support** - Answer your questions

What do you need help with?`,
    customer: `Hello! I'm here to help with your EV service needs.

I can assist with:
• **Service Updates** - Track your repair status
• **Invoice Questions** - Explain charges
• **Booking** - Schedule appointments
• **Support** - Answer questions

How can I help you today?`,
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setMessages([{
      id: 'welcome',
      role: "assistant",
      content: welcomeMessages[portalType] || welcomeMessages.technician,
      timestamp: new Date().toISOString()
    }]);
  }, [user, portalType]);

  const sendMessage = async (messageText = input) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}${apiEndpoint}`, {
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
          context: {
            user_name: user?.name,
            role: user?.role || portalType
          }
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
          confidence: data.confidence
        }]);
      } else {
        throw new Error("Failed to get AI response");
      }
    } catch (error) {
      console.error("AI assist error:", error);
      toast.error("Failed to get AI response");
      
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I'm having trouble right now. Please try again in a moment.",
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  const resetChat = () => {
    setMessages([{
      id: 'welcome',
      role: "assistant",
      content: welcomeMessages[portalType] || welcomeMessages.technician,
      timestamp: new Date().toISOString()
    }]);
    setInput("");
    toast.success("Chat cleared");
  };

  const formatMessage = (content) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('### ')) {
        return <h3 key={i} className="text-base font-semibold text-white mt-3 mb-1">{line.substring(4)}</h3>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={i} className="text-lg font-bold text-white mt-4 mb-2">{line.substring(3)}</h2>;
      }
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} className="mb-1">
            {parts.map((part, j) => 
              j % 2 === 1 ? <strong key={j} className="text-[#C8FF00] text-400 font-medium">{part}</strong> : part
            )}
          </p>
        );
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return <li key={i} className="ml-4 mb-0.5 list-disc">{line.substring(2)}</li>;
      }
      if (/^\d+\.\s/.test(line)) {
        return <li key={i} className="ml-4 mb-0.5 list-decimal">{line.substring(line.indexOf('.') + 2)}</li>;
      }
      if (line.trim() === '') {
        return <br key={i} />;
      }
      return <p key={i} className="mb-1">{line}</p>;
    });
  };

  return (
    <div className="h-[calc(100vh-180px)] flex flex-col bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 rounded-xl overflow-hidden border border-[rgba(255,255,255,0.07)] border-800/50">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.07)] border-800/50 bg-slate-900/80 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-[rgba(200,255,0,0.08)]0/20 rounded-xl blur-xl animate-pulse" />
              <div className="relative p-3 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl border border-[rgba(200,255,0,0.50)]/20">
                <Sparkles className="h-6 w-6 text-[#C8FF00] text-400" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                AI Assistant
                <Badge variant="outline" className="ml-2 border-[rgba(200,255,0,0.50)]/30 text-[#C8FF00] text-400 text-xs font-normal">
                  Gemini Powered
                </Badge>
              </h1>
              <p className="text-sm text-slate-400">Your intelligent EV service companion</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={resetChat}
              className="text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Clear
            </Button>
            <div className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-[rgba(200,255,0,0.08)]0/10 border border-[rgba(200,255,0,0.50)]/20">
              <div className="h-2 w-2 rounded-full bg-[rgba(200,255,0,0.08)]0 animate-pulse" />
              <span className="text-xs text-[#C8FF00] text-400 font-medium">Online</span>
            </div>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex gap-2 mt-4 overflow-x-auto pb-1">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.value;
            return (
              <button
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                  isSelected 
                    ? "bg-[rgba(200,255,0,0.08)]0/20 text-[#C8FF00] text-400 border border-[rgba(200,255,0,0.50)]/30" 
                    : "bg-slate-800/50 text-slate-400 border border-[rgba(255,255,255,0.07)] border-700/50 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4" />
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chat Messages */}
      <ScrollArea className="flex-1 px-6 py-4">
        <div className="space-y-6 max-w-4xl mx-auto">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : ""}`}
            >
              {/* Avatar */}
              <div className={`flex-shrink-0 ${message.role === "user" ? "order-1" : ""}`}>
                {message.role === "assistant" ? (
                  <div className="relative">
                    <div className="absolute inset-0 bg-[rgba(200,255,0,0.08)]0/20 rounded-full blur-md" />
                    <div className="relative w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500/30 to-emerald-600/20 border border-[rgba(200,255,0,0.50)]/30 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-[#C8FF00] text-400" />
                    </div>
                  </div>
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 border border-[rgba(255,255,255,0.07)] border-600 flex items-center justify-center">
                    <User className="h-5 w-5 text-slate-300" />
                  </div>
                )}
              </div>

              {/* Message Content */}
              <div className={`flex-1 max-w-[85%] ${message.role === "user" ? "text-right" : ""}`}>
                <div
                  className={`inline-block rounded-2xl px-5 py-4 ${
                    message.role === "user"
                      ? "bg-gradient-to-br from-emerald-600 to-emerald-700 text-white rounded-br-md"
                      : message.error
                      ? "bg-[rgba(255,59,47,0.08)]0/10 border border-red-500/30 text-slate-200 rounded-bl-md"
                      : "bg-slate-800/80 border border-[rgba(255,255,255,0.07)] border-700/50 text-slate-200 rounded-bl-md"
                  }`}
                >
                  <div className="text-sm leading-relaxed">
                    {message.role === "assistant" ? formatMessage(message.content) : message.content}
                  </div>
                </div>

                {/* Message Actions */}
                {message.role === "assistant" && !message.error && message.id !== 'welcome' && (
                  <div className="flex items-center gap-2 mt-2 text-slate-500">
                    <span className="text-xs">
                      {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className="text-slate-700">•</span>
                    <button
                      onClick={() => copyToClipboard(message.content)}
                      className="text-xs hover:text-slate-300 flex items-center gap-1 transition-colors"
                    >
                      <Copy className="h-3 w-3" />
                      Copy
                    </button>
                    <button className="text-xs hover:text-[#C8FF00] text-400 flex items-center gap-1 transition-colors">
                      <ThumbsUp className="h-3 w-3" />
                    </button>
                    <button className="text-xs hover:text-rose-400 flex items-center gap-1 transition-colors">
                      <ThumbsDown className="h-3 w-3" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading State */}
          {loading && (
            <div className="flex gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-[rgba(200,255,0,0.08)]0/20 rounded-full blur-md animate-pulse" />
                <div className="relative w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500/30 to-emerald-600/20 border border-[rgba(200,255,0,0.50)]/30 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-[#C8FF00] text-400" />
                </div>
              </div>
              <div className="bg-slate-800/80 border border-[rgba(255,255,255,0.07)] border-700/50 rounded-2xl rounded-bl-md px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-[#C8FF00] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-[#C8FF00] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-[#C8FF00] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-sm text-[rgba(244,246,240,0.45)]">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Quick Prompts */}
      {messages.length <= 1 && (
        <div className="px-6 py-3 border-t border-[rgba(255,255,255,0.07)] border-800/50 bg-slate-900/50">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <span className="text-xs text-slate-400 font-medium">Quick questions</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => sendMessage(prompt)}
                className="px-3 py-1.5 text-xs bg-slate-800/50 border border-[rgba(255,255,255,0.07)] border-700/50 rounded-full text-slate-300 hover:bg-slate-700 hover:text-white hover:border-[rgba(255,255,255,0.07)] border-600 transition-all flex items-center gap-1"
              >
                {prompt}
                <ChevronRight className="h-3 w-3 opacity-50" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.07)] border-800/50 bg-slate-900/80 backdrop-blur-sm">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              className="pr-20 py-6 bg-slate-800/50 border-[rgba(255,255,255,0.07)] border-700/50 rounded-xl text-white placeholder:text-slate-500 focus:border-[rgba(200,255,0,0.50)]/50 focus:ring-emerald-500/20"
              disabled={loading}
              data-testid="ai-chat-input"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <button className="p-2 text-slate-500 hover:text-slate-300 transition-colors">
                <Paperclip className="h-4 w-4" />
              </button>
              <button className="p-2 text-slate-500 hover:text-slate-300 transition-colors">
                <Mic className="h-4 w-4" />
              </button>
            </div>
          </div>
          <Button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 border-0"
            data-testid="ai-send-btn"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
        <p className="text-center text-xs text-slate-500 mt-3">
          AI responses are generated by Gemini. Always verify critical information.
        </p>
      </div>
    </div>
  );
}
