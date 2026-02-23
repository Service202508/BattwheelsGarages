import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { 
  Brain, Search, Plus, Loader2, Zap, CheckCircle2, AlertTriangle,
  Lightbulb, TrendingUp, Database, Network, Target, ThumbsUp, ThumbsDown,
  FileText, Wrench, Battery, Cpu, Cable, Activity, Eye, Edit, Clock
} from "lucide-react";
import { API } from "@/App";

const subsystemIcons = {
  battery: Battery,
  motor: Cpu,
  controller: Cpu,
  wiring: Cable,
  bms: Activity,
  charger: Zap,
  default: Wrench
};

const statusColors = {
  draft: "bg-[rgba(234,179,8,0.20)] text-yellow-400 border-yellow-500/30",
  pending_review: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  approved: "bg-[rgba(34,197,94,0.20)] text-green-400 border-green-500/30",
  deprecated: "bg-[#111820]0/20 text-gray-400 border-gray-500/30"
};

const confidenceColors = {
  low: "bg-[rgba(255,59,47,0.20)] text-red-400",
  medium: "bg-[rgba(234,179,8,0.20)] text-yellow-400",
  high: "bg-blue-500/20 text-blue-400",
  verified: "bg-[rgba(34,197,94,0.20)] text-green-400"
};

const subsystems = [
  { value: "battery", label: "Battery" },
  { value: "motor", label: "Motor" },
  { value: "controller", label: "Controller" },
  { value: "wiring", label: "Wiring" },
  { value: "throttle", label: "Throttle" },
  { value: "charger", label: "Charger" },
  { value: "bms", label: "BMS" },
  { value: "display", label: "Display" },
  { value: "brakes", label: "Brakes" },
  { value: "lights", label: "Lights" },
  { value: "software", label: "Software" },
  { value: "other", label: "Other" }
];

const failureModes = [
  { value: "complete_failure", label: "Complete Failure" },
  { value: "intermittent", label: "Intermittent" },
  { value: "degradation", label: "Degradation" },
  { value: "erratic_behavior", label: "Erratic Behavior" },
  { value: "no_response", label: "No Response" },
  { value: "overheating", label: "Overheating" },
  { value: "noise", label: "Noise" },
  { value: "vibration", label: "Vibration" }
];

export default function FailureIntelligence({ user }) {
  const [activeTab, setActiveTab] = useState("cards");
  const [failureCards, setFailureCards] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [subsystemFilter, setSubsystemFilter] = useState("all");
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [matchDialogOpen, setMatchDialogOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);
  
  // Match states
  const [matchQuery, setMatchQuery] = useState("");
  const [matchResults, setMatchResults] = useState([]);
  const [matching, setMatching] = useState(false);
  
  // Form states
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    subsystem_category: "battery",
    failure_mode: "complete_failure",
    symptom_text: "",
    error_codes: "",
    root_cause: "",
    root_cause_details: "",
    keywords: "",
    verification_steps: [],
    resolution_steps: [],
    required_parts: []
  });
  const [saving, setSaving] = useState(false);

  const fetchFailureCards = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      let url = `${API}/efi/failure-cards?limit=100`;
      if (statusFilter && statusFilter !== "all") url += `&status=${statusFilter}`;
      if (subsystemFilter && subsystemFilter !== "all") url += `&subsystem=${subsystemFilter}`;
      if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;
      
      const response = await fetch(url, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        const data = await response.json();
        setFailureCards(data.items || []);
      }
    } catch (error) {
      console.error("Failed to fetch failure cards:", error);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, subsystemFilter, searchTerm]);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/efi/analytics/overview`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        setAnalytics(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    }
  };

  useEffect(() => {
    fetchFailureCards();
    fetchAnalytics();
  }, [fetchFailureCards]);

  const handleMatch = async () => {
    if (!matchQuery.trim()) {
      toast.error("Please enter symptoms to match");
      return;
    }
    
    setMatching(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/efi/match`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          symptom_text: matchQuery,
          error_codes: [],
          limit: 5
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMatchResults(data.matches || []);
        toast.success(`Found ${data.matches?.length || 0} matching failures in ${data.processing_time_ms?.toFixed(0)}ms`);
      }
    } catch (error) {
      toast.error("Matching failed");
    } finally {
      setMatching(false);
    }
  };

  const handleCreateCard = async () => {
    if (!formData.title || !formData.root_cause) {
      toast.error("Title and root cause are required");
      return;
    }
    
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/efi/failure-cards`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          ...formData,
          error_codes: formData.error_codes.split(",").map(s => s.trim()).filter(Boolean),
          keywords: formData.keywords.split(",").map(s => s.trim().toLowerCase()).filter(Boolean)
        })
      });
      
      if (response.ok) {
        toast.success("Failure card created successfully");
        setCreateDialogOpen(false);
        setFormData({
          title: "", description: "", subsystem_category: "battery",
          failure_mode: "complete_failure", symptom_text: "", error_codes: "",
          root_cause: "", root_cause_details: "", keywords: "",
          verification_steps: [], resolution_steps: [], required_parts: []
        });
        fetchFailureCards();
        fetchAnalytics();
      } else {
        const err = await response.json();
        toast.error(err.detail || "Failed to create card");
      }
    } catch (error) {
      toast.error("Network error");
    } finally {
      setSaving(false);
    }
  };

  const handleApproveCard = async (failureId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/efi/failure-cards/${failureId}/approve`, {
        method: "POST",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        toast.success("Failure card approved");
        fetchFailureCards();
        fetchAnalytics();
      }
    } catch (error) {
      toast.error("Failed to approve card");
    }
  };

  const SubsystemIcon = ({ subsystem }) => {
    const Icon = subsystemIcons[subsystem] || subsystemIcons.default;
    return <Icon className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6" data-testid="failure-intelligence-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            EV Failure Intelligence
          </h1>
          <p className="text-muted-foreground">
            AI-powered failure knowledge base • Every repair makes the system smarter
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setMatchDialogOpen(true)} data-testid="match-btn">
            <Target className="mr-2 h-4 w-4" />
            Match Symptoms
          </Button>
          <Button onClick={() => setCreateDialogOpen(true)} data-testid="create-card-btn">
            <Plus className="mr-2 h-4 w-4" />
            New Failure Card
          </Button>
        </div>
      </div>

      {/* Analytics Overview */}
      {analytics && (
        <div className="grid gap-4 md:grid-cols-5">
          <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4" />
                Total Cards
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{analytics.total_failure_cards}</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Approved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{analytics.approved_cards}</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Drafts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{analytics.draft_cards}</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="h-4 w-4" />
                Matches Performed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{analytics.total_matches_performed}</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 border-cyan-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Network className="h-4 w-4" />
                Subsystems
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{analytics.by_subsystem?.length || 0}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="cards">Failure Cards</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
        </TabsList>

        {/* Failure Cards Tab */}
        <TabsContent value="cards" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search failures, symptoms, error codes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="deprecated">Deprecated</SelectItem>
              </SelectContent>
            </Select>
            <Select value={subsystemFilter} onValueChange={setSubsystemFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Subsystem" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Subsystems</SelectItem>
                {subsystems.map(s => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Cards Table */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : failureCards.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                  <Brain className="h-12 w-12 mb-4 opacity-50" />
                  <p>No failure cards found</p>
                  <Button variant="outline" className="mt-4" onClick={() => setCreateDialogOpen(true)}>
                    Create First Card
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Failure</TableHead>
                      <TableHead>Subsystem</TableHead>
                      <TableHead>Root Cause</TableHead>
                      <TableHead>Confidence</TableHead>
                      <TableHead>Usage</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {failureCards.map((card) => (
                      <TableRow 
                        key={card.failure_id} 
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => { setSelectedCard(card); setViewDialogOpen(true); }}
                      >
                        <TableCell>
                          <div className="space-y-1">
                            <p className="font-medium">{card.title}</p>
                            <p className="text-xs text-muted-foreground">{card.failure_id}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <SubsystemIcon subsystem={card.subsystem_category} />
                            <span className="capitalize">{card.subsystem_category}</span>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {card.root_cause}
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <Badge className={confidenceColors[card.confidence_level] || confidenceColors.medium}>
                              {Math.round(card.confidence_score * 100)}%
                            </Badge>
                            <Progress value={card.confidence_score * 100} className="h-1 w-16" />
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-green-500">{card.success_count || 0}</span>
                            <span>/</span>
                            <span>{card.usage_count || 0}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[card.status] || statusColors.draft}>
                            {card.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                            <Button variant="ghost" size="icon">
                              <Eye className="h-4 w-4" />
                            </Button>
                            {card.status === "draft" && (
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => handleApproveCard(card.failure_id)}
                              >
                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Top Performing Cards */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Top Performing Cards
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.top_performing_cards?.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.top_performing_cards.map((card, i) => (
                      <div key={card.failure_id} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-bold text-muted-foreground">#{i + 1}</span>
                          <div>
                            <p className="font-medium text-sm">{card.title}</p>
                            <p className="text-xs text-muted-foreground">Used {card.usage_count} times</p>
                          </div>
                        </div>
                        <Badge className={confidenceColors.high}>
                          {Math.round((card.effectiveness_score || 0) * 100)}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">No data yet</p>
                )}
              </CardContent>
            </Card>

            {/* By Subsystem */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Network className="h-5 w-5" />
                  Cards by Subsystem
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.by_subsystem?.length > 0 ? (
                  <div className="space-y-2">
                    {analytics.by_subsystem.map((item) => (
                      <div key={item._id} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <SubsystemIcon subsystem={item._id} />
                          <span className="capitalize">{item._id}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Progress value={(item.count / analytics.total_failure_cards) * 100} className="w-24 h-2" />
                          <span className="text-sm font-medium w-8">{item.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">No data yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Events</CardTitle>
              <CardDescription>System events from the EFI engine</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics?.recent_events?.length > 0 ? (
                <div className="space-y-2">
                  {analytics.recent_events.map((event) => (
                    <div key={event.event_id} className="flex items-center justify-between p-3 bg-muted/30 rounded">
                      <div className="flex items-center gap-3">
                        <Activity className="h-4 w-4 text-primary" />
                        <div>
                          <p className="font-medium text-sm">{event.event_type}</p>
                          <p className="text-xs text-muted-foreground">{event.source}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={event.processed ? "default" : "secondary"}>
                          {event.processed ? "Processed" : "Pending"}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">No recent events</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Match Dialog */}
      <Dialog open={matchDialogOpen} onOpenChange={setMatchDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              AI Failure Matching
            </DialogTitle>
            <DialogDescription>
              Describe symptoms to find matching failure solutions
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <Textarea
              placeholder="Describe the symptoms, error codes, or issues observed...
Example: Battery not charging beyond 80%, intermittent error E401"
              value={matchQuery}
              onChange={(e) => setMatchQuery(e.target.value)}
              rows={4}
            />
            
            <Button onClick={handleMatch} disabled={matching} className="w-full">
              {matching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Matching...
                </>
              ) : (
                <>
                  <Brain className="mr-2 h-4 w-4" />
                  Find Matches
                </>
              )}
            </Button>
            
            {matchResults.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-semibold">Matches Found:</h4>
                {matchResults.map((match, i) => (
                  <Card key={match.failure_id} className={i === 0 ? "border-green-500/50 bg-[rgba(34,197,94,0.05)]" : ""}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-2">
                            {i === 0 && <Lightbulb className="h-4 w-4 text-green-500" />}
                            <h5 className="font-medium">{match.title}</h5>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Match type: {match.match_type}
                          </p>
                        </div>
                        <div className="text-right">
                          <Badge className={confidenceColors[match.confidence_level]}>
                            {Math.round(match.match_score * 100)}% match
                          </Badge>
                        </div>
                      </div>
                      {match.matched_symptoms?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {match.matched_symptoms.map((sym, j) => (
                            <Badge key={j} variant="outline" className="text-xs">{sym}</Badge>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Card Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Failure Intelligence Card</DialogTitle>
            <DialogDescription>
              Document a new EV failure pattern for the knowledge base
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  placeholder="e.g., BMS Cell Balancing Failure"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subsystem">Subsystem *</Label>
                <Select 
                  value={formData.subsystem_category} 
                  onValueChange={(v) => setFormData({...formData, subsystem_category: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {subsystems.map(s => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="symptom_text">Symptoms Description</Label>
              <Textarea
                id="symptom_text"
                value={formData.symptom_text}
                onChange={(e) => setFormData({...formData, symptom_text: e.target.value})}
                placeholder="Describe the symptoms observed..."
                rows={3}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="error_codes">Error Codes (comma-separated)</Label>
                <Input
                  id="error_codes"
                  value={formData.error_codes}
                  onChange={(e) => setFormData({...formData, error_codes: e.target.value})}
                  placeholder="E401, E402, E501"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="failure_mode">Failure Mode</Label>
                <Select 
                  value={formData.failure_mode} 
                  onValueChange={(v) => setFormData({...formData, failure_mode: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {failureModes.map(m => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-2">
              <Label htmlFor="root_cause">Root Cause *</Label>
              <Input
                id="root_cause"
                value={formData.root_cause}
                onChange={(e) => setFormData({...formData, root_cause: e.target.value})}
                placeholder="e.g., BMS cell balancing circuit failure"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="root_cause_details">Root Cause Details</Label>
              <Textarea
                id="root_cause_details"
                value={formData.root_cause_details}
                onChange={(e) => setFormData({...formData, root_cause_details: e.target.value})}
                placeholder="Detailed explanation of the root cause..."
                rows={3}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="keywords">Keywords (comma-separated)</Label>
              <Input
                id="keywords"
                value={formData.keywords}
                onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                placeholder="battery, charging, BMS, 80%, intermittent"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateCard} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Create Card
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Card Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {selectedCard && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <DialogTitle>{selectedCard.title}</DialogTitle>
                  <Badge className={statusColors[selectedCard.status]}>{selectedCard.status}</Badge>
                </div>
                <DialogDescription>{selectedCard.failure_id}</DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-muted/30 rounded">
                    <p className="text-xs text-muted-foreground">Subsystem</p>
                    <p className="font-medium capitalize">{selectedCard.subsystem_category}</p>
                  </div>
                  <div className="p-3 bg-muted/30 rounded">
                    <p className="text-xs text-muted-foreground">Confidence</p>
                    <p className="font-medium">{Math.round(selectedCard.confidence_score * 100)}%</p>
                  </div>
                  <div className="p-3 bg-muted/30 rounded">
                    <p className="text-xs text-muted-foreground">Usage</p>
                    <p className="font-medium">{selectedCard.success_count || 0} / {selectedCard.usage_count || 0}</p>
                  </div>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="font-semibold mb-2">Symptoms</h4>
                  <p className="text-sm text-muted-foreground">{selectedCard.symptom_text || "No symptoms documented"}</p>
                  {selectedCard.error_codes?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {selectedCard.error_codes.map((code, i) => (
                        <Badge key={i} variant="outline">{code}</Badge>
                      ))}
                    </div>
                  )}
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Root Cause</h4>
                  <p className="text-sm font-medium">{selectedCard.root_cause}</p>
                  {selectedCard.root_cause_details && (
                    <p className="text-sm text-muted-foreground mt-1">{selectedCard.root_cause_details}</p>
                  )}
                </div>
                
                {selectedCard.keywords?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Keywords</h4>
                    <div className="flex flex-wrap gap-1">
                      {selectedCard.keywords.slice(0, 15).map((kw, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">{kw}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <DialogFooter>
                {selectedCard.status === "draft" && (
                  <Button onClick={() => { handleApproveCard(selectedCard.failure_id); setViewDialogOpen(false); }}>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Approve Card
                  </Button>
                )}
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
