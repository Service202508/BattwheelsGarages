import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import {
  Zap, Send, Loader2, Bot, User, Lightbulb, AlertTriangle,
  Wrench, Battery, Cpu, CircuitBoard, RefreshCw, Copy, 
  MessageSquare, ChevronDown, Sparkles
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

export default function TechnicianAIAssistant({ user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("general");
  const messagesEndRef = useRef(null);

  const categories = [
    { value: "general", label: "General Query", icon: MessageSquare },
    { value: "battery", label: "Battery Issues", icon: Battery },
    { value: "motor", label: "Motor/Controller", icon: Cpu },
    { value: "electrical", label: "Electrical System", icon: CircuitBoard },
    { value: "diagnosis", label: "Fault Diagnosis", icon: Wrench },
  ];

  // Quick prompts for common issues
  const quickPrompts = [
    { text: "How to diagnose BMS communication error?", category: "battery" },
    { text: "Motor controller overheating troubleshooting", category: "motor" },
    { text: "Charger not detecting vehicle - steps to fix", category: "electrical" },
    { text: "Battery cell imbalance symptoms and solutions", category: "battery" },
    { text: "Controller fault codes interpretation guide", category: "motor" },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize with a welcome message
  useEffect(() => {
    setMessages([{
      role: "assistant",
      content: `Hello ${user?.name?.split(' ')[0] || 'Technician'}! I'm your AI Diagnostic Assistant powered by Gemini. 

I can help you with:
- **Fault Diagnosis**: Describe symptoms and I'll suggest possible causes
- **Repair Procedures**: Step-by-step guides for common repairs
- **Error Code Interpretation**: Decode OBD/CAN error codes
- **Technical Documentation**: Quick access to repair knowledge

Select a category or ask me anything about EV service and repair!`,
      timestamp: new Date().toISOString()
    }]);
  }, [user]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/technician/ai-assist`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({
          query: input,
          category: selectedCategory,
          context: {
            technician_name: user?.name,
            role: "technician"
          }
        })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
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
      
      // Fallback response
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I apologize, but I'm having trouble processing your request right now. Please try again in a moment, or contact support if the issue persists.",
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickPrompt = (prompt) => {
    setInput(prompt.text);
    setSelectedCategory(prompt.category);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        // Headers
        if (line.startsWith('### ')) {
          return <h3 key={i} className="text-lg font-semibold text-white mt-3 mb-1">{line.substring(4)}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={i} className="text-xl font-bold text-white mt-4 mb-2">{line.substring(3)}</h2>;
        }
        // Bold text
        if (line.includes('**')) {
          const parts = line.split(/\*\*(.*?)\*\*/g);
          return (
            <p key={i} className="mb-1">
              {parts.map((part, j) => 
                j % 2 === 1 ? <strong key={j} className="text-green-400">{part}</strong> : part
              )}
            </p>
          );
        }
        // Bullet points
        if (line.startsWith('- ')) {
          return <li key={i} className="ml-4 mb-0.5">{line.substring(2)}</li>;
        }
        if (line.startsWith('• ')) {
          return <li key={i} className="ml-4 mb-0.5">{line.substring(2)}</li>;
        }
        // Numbered lists
        if (/^\d+\.\s/.test(line)) {
          return <li key={i} className="ml-4 mb-0.5 list-decimal">{line.substring(line.indexOf('.') + 2)}</li>;
        }
        // Empty line
        if (line.trim() === '') {
          return <br key={i} />;
        }
        return <p key={i} className="mb-1">{line}</p>;
      });
  };

  return (
    <div className="space-y-4 h-[calc(100vh-200px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <Sparkles className="h-6 w-6 text-green-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AI Diagnostic Assistant</h1>
            <p className="text-sm text-slate-400">Powered by Gemini - Your EV repair companion</p>
          </div>
        </div>
        <Badge variant="outline" className="border-green-500/50 text-green-400">
          <Zap className="h-3 w-3 mr-1" />
          AI Enabled
        </Badge>
      </div>

      {/* Quick Prompts */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-3">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            <span className="text-sm text-slate-400">Quick Questions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="text-xs border-slate-600 hover:bg-slate-700"
                onClick={() => handleQuickPrompt(prompt)}
              >
                {prompt.text.length > 40 ? prompt.text.substring(0, 40) + "..." : prompt.text}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Chat Container */}
      <Card className="flex-1 bg-slate-800/50 border-slate-700 overflow-hidden flex flex-col">
        <CardContent className="p-4 flex-1 overflow-y-auto space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-green-400" />
                </div>
              )}
              
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === "user"
                    ? "bg-green-600 text-white"
                    : message.error
                    ? "bg-red-500/10 border border-red-500/30 text-slate-200"
                    : "bg-slate-700/50 text-slate-200"
                }`}
              >
                <div className="text-sm leading-relaxed">
                  {message.role === "assistant" ? formatMessage(message.content) : message.content}
                </div>
                
                {message.role === "assistant" && !message.error && (
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-600/50">
                    <span className="text-xs text-slate-500">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 text-xs text-slate-400 hover:text-white"
                      onClick={() => copyToClipboard(message.content)}
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </Button>
                  </div>
                )}
              </div>
              
              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                <Bot className="h-4 w-4 text-green-400" />
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-green-400" />
                <span className="text-sm text-slate-400">AI is analyzing...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-700 bg-slate-800/80">
          <div className="flex gap-2 mb-2">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[180px] bg-slate-700 border-slate-600">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => {
                  const Icon = cat.icon;
                  return (
                    <SelectItem key={cat.value} value={cat.value}>
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4" />
                        {cat.label}
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex gap-2">
            <Input
              placeholder="Ask me anything about EV diagnostics, repairs, or error codes..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              className="flex-1 bg-slate-700 border-slate-600"
              disabled={loading}
              data-testid="ai-chat-input"
            />
            <Button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-green-600 hover:bg-green-700"
              data-testid="ai-send-btn"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
