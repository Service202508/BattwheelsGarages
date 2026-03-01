import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Plus, FolderKanban, Clock, User, Calendar, DollarSign, 
  TrendingUp, FileText, CheckCircle2, AlertCircle, ArrowRight,
  Timer, Receipt, BarChart3, GripVertical, MoreHorizontal,
  ChevronRight, Download
} from "lucide-react";
import { API } from "@/App";
import { useNavigate, useParams } from "react-router-dom";

const statusConfig = {
  PLANNING: { label: "Planning", bg: "bg-bw-blue/10", text: "text-bw-blue", border: "border-bw-blue/25" },
  ACTIVE: { label: "Active", bg: "bg-bw-volt/10", text: "text-bw-volt", border: "border-bw-volt/25" },
  ON_HOLD: { label: "On Hold", bg: "bg-bw-amber/10", text: "text-bw-amber", border: "border-bw-amber/25" },
  COMPLETED: { label: "Completed", bg: "bg-bw-teal/10", text: "text-bw-teal", border: "border-bw-teal/25" },
  CANCELLED: { label: "Cancelled", bg: "bg-bw-red/10", text: "text-bw-red", border: "border-bw-red/25" }
};

const taskStatusConfig = {
  TODO: { label: "To Do", bg: "bg-bw-white/10", text: "text-bw-white/[0.65]" },
  IN_PROGRESS: { label: "In Progress", bg: "bg-bw-blue/10", text: "text-bw-blue" },
  REVIEW: { label: "Review", bg: "bg-bw-amber/10", text: "text-bw-amber" },
  DONE: { label: "Done", bg: "bg-bw-volt/10", text: "text-bw-volt" }
};

const priorityConfig = {
  LOW: { label: "Low", text: "text-bw-white/[0.45]" },
  MEDIUM: { label: "Medium", text: "text-bw-blue" },
  HIGH: { label: "High", text: "text-bw-orange" },
  URGENT: { label: "Urgent", text: "text-bw-red" }
};

const expenseStatusConfig = {
  PENDING: { label: "Pending", bg: "bg-bw-amber/10", text: "text-bw-amber" },
  APPROVED: { label: "Approved", bg: "bg-bw-volt/10", text: "text-bw-volt" },
  REJECTED: { label: "Rejected", bg: "bg-bw-red/10", text: "text-bw-red" },
  PAID: { label: "Paid", bg: "bg-bw-white/10", text: "text-bw-white/[0.45]" }
};

// Shared state and headers
const getHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`
});

// ====================== PROJECT LIST PAGE ======================
export default function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  
  const [newProject, setNewProject] = useState({
    name: "", description: "", client_id: "", status: "PLANNING",
    start_date: new Date().toISOString().split("T")[0], end_date: "",
    budget_amount: 0, billing_type: "HOURLY", hourly_rate: 2000
  });

  useEffect(() => { fetchProjects(); fetchCustomers(); }, []);

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API}/projects`, { headers: getHeaders() });
      const data = await res.json();
      setProjects(data.projects || []);
      
      // Fetch stats
      const statsRes = await fetch(`${API}/projects/stats/dashboard`, { headers: getHeaders() });
      const statsData = await statsRes.json();
      setStats(statsData.stats || {});
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${API}/contacts?type=customer`, { headers: getHeaders() });
      const data = await res.json();
      setCustomers(data.contacts || []);
    } catch (err) {
      console.error("Failed to fetch customers:", err);
    }
  };

  const handleCreateProject = async () => {
    if (!newProject.name) return toast.error("Enter project name");
    try {
      const res = await fetch(`${API}/projects`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(newProject)
      });
      if (res.ok) {
        toast.success("Project created");
        setShowCreateDialog(false);
        setNewProject({ name: "", description: "", client_id: "", status: "PLANNING", start_date: new Date().toISOString().split("T")[0], end_date: "", budget_amount: 0, billing_type: "HOURLY", hourly_rate: 2000 });
        fetchProjects();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to create project");
      }
    } catch (err) {
      toast.error("Error creating project");
    }
  };

  // Calculate aggregate stats
  const aggregateStats = useMemo(() => {
    const active = projects.filter(p => p.status === "ACTIVE").length;
    const totalBudget = projects.reduce((sum, p) => sum + (p.budget_amount || 0), 0);
    return { active, totalBudget, ...stats };
  }, [projects, stats]);

  return (
    <div className="space-y-6" data-testid="projects-page">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-bw-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
            Projects
          </h1>
          <p className="text-bw-white/[0.45] text-sm mt-1">
            Track project delivery, time, expenses and billing
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" data-testid="new-project-btn">
              <Plus className="h-4 w-4 mr-2" /> New Project
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Project Name *</Label>
                <Input 
                  value={newProject.name} 
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} 
                  placeholder="e.g., EV Charging Station Setup"
                  data-testid="project-name-input"
                />
              </div>
              <div>
                <Label>Client</Label>
                <Select onValueChange={(v) => setNewProject({ ...newProject, client_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Select client (optional)" /></SelectTrigger>
                  <SelectContent>
                    {customers.map(c => (
                      <SelectItem key={c.contact_id} value={c.contact_id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Description</Label>
                <Textarea 
                  value={newProject.description} 
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} 
                  placeholder="Project scope and deliverables..."
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Start Date</Label>
                  <Input 
                    type="date" 
                    value={newProject.start_date} 
                    onChange={(e) => setNewProject({ ...newProject, start_date: e.target.value })} 
                  />
                </div>
                <div>
                  <Label>End Date</Label>
                  <Input 
                    type="date" 
                    value={newProject.end_date} 
                    onChange={(e) => setNewProject({ ...newProject, end_date: e.target.value })} 
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Billing Type</Label>
                  <Select value={newProject.billing_type} onValueChange={(v) => setNewProject({ ...newProject, billing_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="HOURLY">Hourly</SelectItem>
                      <SelectItem value="FIXED">Fixed Cost</SelectItem>
                      <SelectItem value="RETAINER">Retainer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Hourly Rate (₹)</Label>
                  <Input 
                    type="number" 
                    value={newProject.hourly_rate} 
                    onChange={(e) => setNewProject({ ...newProject, hourly_rate: parseFloat(e.target.value) || 0 })} 
                  />
                </div>
              </div>
              <div>
                <Label>Budget Amount (₹)</Label>
                <Input 
                  type="number" 
                  value={newProject.budget_amount} 
                  onChange={(e) => setNewProject({ ...newProject, budget_amount: parseFloat(e.target.value) || 0 })} 
                  placeholder="0 for no budget"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreateProject} className="bg-bw-volt text-bw-black font-bold" data-testid="create-project-submit">
                Create Project
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Active Projects</div>
            <div className="text-2xl font-bold text-bw-volt" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {aggregateStats.active_projects || 0}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Total Budget</div>
            <div className="text-2xl font-bold text-bw-volt" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              ₹{(aggregateStats.total_budget || 0).toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Hours This Month</div>
            <div className="text-2xl font-bold text-bw-volt" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {stats.hours_this_month || 0}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Revenue Billed</div>
            <div className="text-2xl font-bold text-bw-teal" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              ₹{(stats.revenue_billed || 0).toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="p-4">
            <div className="text-xs text-bw-white/[0.45] mb-1">Pending Invoicing</div>
            <div className="text-2xl font-bold text-bw-orange" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              ₹{(stats.pending_invoicing || 0).toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Project Cards Grid */}
      {loading ? (
        <div className="text-center py-12 text-bw-white/[0.45]">Loading projects...</div>
      ) : projects.length === 0 ? (
        <Card className="bg-bw-panel border-white/[0.07]">
          <CardContent className="py-12 text-center">
            <FolderKanban className="h-12 w-12 mx-auto mb-4 text-bw-white/25" />
            <p className="text-bw-white/[0.45]">No projects yet. Create your first project!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map(project => (
            <ProjectCard key={project.project_id} project={project} onClick={() => navigate(`/projects/${project.project_id}`)} />
          ))}
        </div>
      )}
    </div>
  );
}

// ====================== PROJECT CARD COMPONENT ======================
function ProjectCard({ project, onClick }) {
  const status = statusConfig[project.status] || statusConfig.PLANNING;
  const completion = project.completion_pct || 0;
  const hasUnbilledHours = (project.unbilled_hours || 0) > 0;
  
  return (
    <Card 
      className="bg-bw-panel border border-white/[0.07] hover:border-t-bw-volt hover:border-t-2 transition-all cursor-pointer group"
      onClick={onClick}
      data-testid={`project-card-${project.project_id}`}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-bw-white truncate" style={{ fontFamily: "'DM Serif Display', serif", fontSize: "18px" }}>
              {project.name}
            </h3>
            <Badge className={`${status.bg} ${status.text} ${status.border} border mt-1`}>
              {status.label}
            </Badge>
          </div>
          <ChevronRight className="h-5 w-5 text-bw-white/25 group-hover:text-bw-volt transition-colors" />
        </div>
        
        {/* Client */}
        {project.client_name && (
          <p className="text-xs text-bw-white/[0.45] mb-3">{project.client_name}</p>
        )}
        
        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-bw-white/[0.45]">Completion</span>
            <span className="text-bw-white">{Math.round(completion)}%</span>
          </div>
          <div className="h-1.5 bg-white/[0.07] rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full" 
              style={{ 
                width: `${Math.min(completion, 100)}%`,
                background: 'linear-gradient(90deg, #C8FF00, #1AFFE4)'
              }}
            />
          </div>
        </div>
        
        {/* Stats Row */}
        <div className="flex items-center gap-4 text-xs text-bw-white/[0.65] mb-3">
          <span>Budget: ₹{(project.budget_amount || 0).toLocaleString('en-IN')}</span>
          <span>Hours: {project.total_hours || 0}</span>
          <span>Tasks: {project.completed_tasks || 0}/{project.total_tasks || 0}</span>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-white/[0.07]">
          <span className="text-xs text-bw-white/[0.45]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {project.end_date || project.deadline || 'No deadline'}
          </span>
          {hasUnbilledHours && (
            <Button 
              size="sm" 
              variant="ghost" 
              className="text-xs h-7 text-bw-white/[0.65] hover:text-bw-volt"
              onClick={(e) => { e.stopPropagation(); }}
            >
              Generate Invoice
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ====================== PROJECT DETAIL PAGE ======================
export function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [timeLogs, setTimeLogs] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [profitability, setProfitability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  
  // Dialogs
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [showTimeLogDialog, setShowTimeLogDialog] = useState(false);
  const [showExpenseDialog, setShowExpenseDialog] = useState(false);
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false);
  
  // Forms
  const [newTask, setNewTask] = useState({ title: "", description: "", estimated_hours: 0, priority: "MEDIUM", due_date: "" });
  const [newTimeLog, setNewTimeLog] = useState({ hours_logged: 0, description: "", task_id: "", log_date: new Date().toISOString().split("T")[0] });
  const [newExpense, setNewExpense] = useState({ amount: 0, description: "", category: "general", expense_date: new Date().toISOString().split("T")[0] });
  const [invoiceConfig, setInvoiceConfig] = useState({
    billing_period_from: new Date(new Date().setDate(1)).toISOString().split("T")[0],
    billing_period_to: new Date().toISOString().split("T")[0],
    include_expenses: true,
    line_item_grouping: "BY_TASK",
    notes: ""
  });

  useEffect(() => {
    if (projectId) fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      const [projRes, tasksRes, logsRes, expRes, profRes] = await Promise.all([
        fetch(`${API}/projects/${projectId}`, { headers: getHeaders() }),
        fetch(`${API}/projects/${projectId}/tasks`, { headers: getHeaders() }),
        fetch(`${API}/projects/${projectId}/time-logs`, { headers: getHeaders() }),
        fetch(`${API}/projects/${projectId}/expenses`, { headers: getHeaders() }),
        fetch(`${API}/projects/${projectId}/profitability`, { headers: getHeaders() })
      ]);
      
      const projData = await projRes.json();
      const tasksData = await tasksRes.json();
      const logsData = await logsRes.json();
      const expData = await expRes.json();
      const profData = await profRes.json();
      
      setProject(projData.project);
      setTasks(tasksData.tasks || []);
      setTimeLogs(logsData.time_logs || []);
      setExpenses(expData.expenses || []);
      setProfitability(profData.profitability);
    } catch (err) {
      console.error("Failed to fetch project data:", err);
      toast.error("Failed to load project");
    } finally {
      setLoading(false);
    }
  };

  // Task handlers
  const handleCreateTask = async () => {
    if (!newTask.title) return toast.error("Enter task title");
    try {
      const res = await fetch(`${API}/projects/${projectId}/tasks`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(newTask)
      });
      if (res.ok) {
        toast.success("Task created");
        setShowTaskDialog(false);
        setNewTask({ title: "", description: "", estimated_hours: 0, priority: "MEDIUM", due_date: "" });
        fetchProjectData();
      }
    } catch { toast.error("Error creating task"); }
  };

  const handleUpdateTaskStatus = async (taskId, status) => {
    try {
      await fetch(`${API}/projects/${projectId}/tasks/${taskId}`, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify({ status })
      });
      fetchProjectData();
    } catch { toast.error("Error updating task"); }
  };

  // Time log handlers
  const handleLogTime = async () => {
    if (newTimeLog.hours_logged <= 0) return toast.error("Enter hours");
    try {
      const res = await fetch(`${API}/projects/${projectId}/time-log`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(newTimeLog)
      });
      if (res.ok) {
        toast.success("Time logged");
        setShowTimeLogDialog(false);
        setNewTimeLog({ hours_logged: 0, description: "", task_id: "", log_date: new Date().toISOString().split("T")[0] });
        fetchProjectData();
      }
    } catch { toast.error("Error logging time"); }
  };

  // Expense handlers
  const handleAddExpense = async () => {
    if (newExpense.amount <= 0) return toast.error("Enter amount");
    try {
      const res = await fetch(`${API}/projects/${projectId}/expenses`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(newExpense)
      });
      if (res.ok) {
        toast.success("Expense added");
        setShowExpenseDialog(false);
        setNewExpense({ amount: 0, description: "", category: "general", expense_date: new Date().toISOString().split("T")[0] });
        fetchProjectData();
      }
    } catch { toast.error("Error adding expense"); }
  };

  const handleApproveExpense = async (expenseId, approved) => {
    try {
      const res = await fetch(`${API}/projects/${projectId}/expenses/${expenseId}/approve`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ approved })
      });
      if (res.ok) {
        toast.success(approved ? "Expense approved" : "Expense rejected");
        fetchProjectData();
      }
    } catch { toast.error("Error updating expense"); }
  };

  // Invoice generation
  const handleGenerateInvoice = async () => {
    try {
      const res = await fetch(`${API}/projects/${projectId}/invoice`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(invoiceConfig)
      });
      const data = await res.json();
      if (res.ok && data.invoice_id) {
        toast.success("Invoice created successfully");
        setShowInvoiceDialog(false);
        navigate(data.redirect_url || `/finance/invoices/${data.invoice_id}`);
      } else {
        toast.error(data.error || data.detail || "Failed to generate invoice");
      }
    } catch { toast.error("Error generating invoice"); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-bw-white/[0.45]">Loading project...</div>;
  }

  if (!project) {
    return <div className="text-center py-12 text-bw-white/[0.45]">Project not found</div>;
  }

  const status = statusConfig[project.status] || statusConfig.PLANNING;
  const uninvoicedLogs = timeLogs.filter(l => !l.invoiced);
  const approvedExpenses = expenses.filter(e => e.status === "APPROVED" && !e.invoiced);

  return (
    <div className="space-y-6" data-testid="project-detail-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-bw-white/[0.45] mb-2">
            <span className="cursor-pointer hover:text-bw-volt" onClick={() => navigate('/projects')}>Projects</span>
            <ChevronRight className="h-4 w-4" />
            <span>{project.name}</span>
          </div>
          <h1 className="text-2xl font-bold text-bw-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
            {project.name}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <Badge className={`${status.bg} ${status.text} ${status.border} border`}>{status.label}</Badge>
            {project.client_name && <span className="text-sm text-bw-white/[0.45]">{project.client_name}</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <Dialog open={showInvoiceDialog} onOpenChange={setShowInvoiceDialog}>
            <DialogTrigger asChild>
              <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" disabled={uninvoicedLogs.length === 0 && approvedExpenses.length === 0}>
                <Receipt className="h-4 w-4 mr-2" /> Generate Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Generate Invoice from Project</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Period From</Label>
                    <Input type="date" value={invoiceConfig.billing_period_from} onChange={(e) => setInvoiceConfig({...invoiceConfig, billing_period_from: e.target.value})} />
                  </div>
                  <div>
                    <Label>Period To</Label>
                    <Input type="date" value={invoiceConfig.billing_period_to} onChange={(e) => setInvoiceConfig({...invoiceConfig, billing_period_to: e.target.value})} />
                  </div>
                </div>
                <div>
                  <Label>Line Item Grouping</Label>
                  <Select value={invoiceConfig.line_item_grouping} onValueChange={(v) => setInvoiceConfig({...invoiceConfig, line_item_grouping: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BY_TASK">By Task</SelectItem>
                      <SelectItem value="BY_EMPLOYEE">By Employee</SelectItem>
                      <SelectItem value="BY_DATE">By Date</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    id="include-expenses" 
                    checked={invoiceConfig.include_expenses}
                    onChange={(e) => setInvoiceConfig({...invoiceConfig, include_expenses: e.target.checked})}
                    className="rounded"
                  />
                  <Label htmlFor="include-expenses">Include approved expenses ({approvedExpenses.length} items)</Label>
                </div>
                <div>
                  <Label>Notes</Label>
                  <Textarea 
                    value={invoiceConfig.notes} 
                    onChange={(e) => setInvoiceConfig({...invoiceConfig, notes: e.target.value})}
                    placeholder="Additional notes for invoice..."
                    rows={2}
                  />
                </div>
                <div className="bg-bw-card p-3 rounded text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="text-bw-white/[0.45]">Uninvoiced time logs:</span>
                    <span>{uninvoicedLogs.length} entries ({uninvoicedLogs.reduce((s,l) => s + l.hours_logged, 0).toFixed(1)} hrs)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Hourly rate:</span>
                    <span>₹{project.hourly_rate?.toLocaleString('en-IN')}</span>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowInvoiceDialog(false)}>Cancel</Button>
                <Button onClick={handleGenerateInvoice} className="bg-bw-volt text-bw-black font-bold">
                  Generate Invoice
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-bw-panel border border-white/[0.07]">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="tasks" data-testid="tab-tasks">Tasks</TabsTrigger>
          <TabsTrigger value="time-logs" data-testid="tab-time-logs">Time Logs</TabsTrigger>
          <TabsTrigger value="expenses" data-testid="tab-expenses">Expenses</TabsTrigger>
          <TabsTrigger value="financials" data-testid="tab-financials">Financials</TabsTrigger>
        </TabsList>

        {/* OVERVIEW TAB */}
        <TabsContent value="overview" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Project Details */}
            <Card className="bg-bw-panel border-white/[0.07]">
              <CardHeader>
                <CardTitle className="text-lg">Project Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-bw-white/[0.45]">Status</span>
                    <div className="mt-1"><Badge className={`${status.bg} ${status.text}`}>{status.label}</Badge></div>
                  </div>
                  <div>
                    <span className="text-bw-white/[0.45]">Billing Type</span>
                    <div className="mt-1 font-medium">{project.billing_type}</div>
                  </div>
                  <div>
                    <span className="text-bw-white/[0.45]">Start Date</span>
                    <div className="mt-1 font-medium">{project.start_date || '-'}</div>
                  </div>
                  <div>
                    <span className="text-bw-white/[0.45]">End Date</span>
                    <div className="mt-1 font-medium">{project.end_date || '-'}</div>
                  </div>
                  <div>
                    <span className="text-bw-white/[0.45]">Budget</span>
                    <div className="mt-1 font-medium">₹{(project.budget_amount || 0).toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span className="text-bw-white/[0.45]">Hourly Rate</span>
                    <div className="mt-1 font-medium">₹{(project.hourly_rate || 0).toLocaleString('en-IN')}/hr</div>
                  </div>
                </div>
                {project.description && (
                  <div>
                    <span className="text-sm text-bw-white/[0.45]">Description</span>
                    <p className="mt-1 text-sm">{project.description}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Profitability Summary */}
            <Card className="bg-bw-panel border-white/[0.07]">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-bw-volt" /> Profitability Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                {profitability ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-bw-card p-3 rounded">
                        <div className="text-xs text-bw-white/[0.45]">Budget</div>
                        <div className="text-xl font-bold">₹{(profitability.budget || 0).toLocaleString('en-IN')}</div>
                      </div>
                      <div className="bg-bw-card p-3 rounded">
                        <div className="text-xs text-bw-white/[0.45]">Revenue</div>
                        <div className="text-xl font-bold text-bw-teal">₹{(profitability.revenue || 0).toLocaleString('en-IN')}</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-bw-card p-3 rounded">
                        <div className="text-xs text-bw-white/[0.45]">Total Cost</div>
                        <div className="text-xl font-bold text-bw-orange">₹{(profitability.costs?.total || 0).toLocaleString('en-IN')}</div>
                      </div>
                      <div className="bg-bw-card p-3 rounded">
                        <div className="text-xs text-bw-white/[0.45]">Gross Profit</div>
                        <div className={`text-xl font-bold ${profitability.is_profitable ? 'text-bw-volt' : 'text-bw-red'}`}>
                          ₹{(profitability.gross_profit || 0).toLocaleString('en-IN')}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-bw-card p-3 rounded">
                      <span className="text-sm">Margin</span>
                      <span className={`text-2xl font-bold ${profitability.is_profitable ? 'text-bw-volt' : 'text-bw-red'}`}>
                        {profitability.margin_pct?.toFixed(1) || 0}%
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-bw-white/[0.45]">Hours Estimated</span>
                        <div className="font-medium">{profitability.hours?.estimated || 0} hrs</div>
                      </div>
                      <div>
                        <span className="text-bw-white/[0.45]">Hours Logged</span>
                        <div className="font-medium">{profitability.hours?.logged || 0} hrs</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-bw-white/[0.45]">No profitability data</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TASKS TAB - Kanban Board */}
        <TabsContent value="tasks" className="mt-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Tasks ({tasks.length})</h3>
            <Dialog open={showTaskDialog} onOpenChange={setShowTaskDialog}>
              <DialogTrigger asChild>
                <Button size="sm" className="bg-bw-volt text-bw-black">
                  <Plus className="h-4 w-4 mr-1" /> Add Task
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Task</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label>Title *</Label>
                    <Input value={newTask.title} onChange={(e) => setNewTask({...newTask, title: e.target.value})} placeholder="Task title" />
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Textarea value={newTask.description} onChange={(e) => setNewTask({...newTask, description: e.target.value})} rows={2} />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Estimated Hours</Label>
                      <Input type="number" value={newTask.estimated_hours} onChange={(e) => setNewTask({...newTask, estimated_hours: parseFloat(e.target.value) || 0})} />
                    </div>
                    <div>
                      <Label>Priority</Label>
                      <Select value={newTask.priority} onValueChange={(v) => setNewTask({...newTask, priority: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="LOW">Low</SelectItem>
                          <SelectItem value="MEDIUM">Medium</SelectItem>
                          <SelectItem value="HIGH">High</SelectItem>
                          <SelectItem value="URGENT">Urgent</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label>Due Date</Label>
                    <Input type="date" value={newTask.due_date} onChange={(e) => setNewTask({...newTask, due_date: e.target.value})} />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowTaskDialog(false)}>Cancel</Button>
                  <Button onClick={handleCreateTask} className="bg-bw-volt text-bw-black">Create Task</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Kanban Columns */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {['TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'].map(status => {
              const config = taskStatusConfig[status];
              const statusTasks = tasks.filter(t => t.status === status);
              return (
                <div key={status} className="bg-bw-panel rounded-lg p-3 border border-white/[0.07]">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`text-sm font-medium ${config.text}`}>{config.label}</span>
                    <span className="text-xs text-bw-white/[0.45]">{statusTasks.length}</span>
                  </div>
                  <div className="space-y-2 min-h-[200px]">
                    {statusTasks.map(task => (
                      <TaskCard 
                        key={task.task_id} 
                        task={task} 
                        onStatusChange={(newStatus) => handleUpdateTaskStatus(task.task_id, newStatus)}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </TabsContent>

        {/* TIME LOGS TAB */}
        <TabsContent value="time-logs" className="mt-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold">Time Logs</h3>
              <p className="text-sm text-bw-white/[0.45]">Total: {timeLogs.reduce((s,l) => s + l.hours_logged, 0).toFixed(1)} hours</p>
            </div>
            <Dialog open={showTimeLogDialog} onOpenChange={setShowTimeLogDialog}>
              <DialogTrigger asChild>
                <Button size="sm" className="bg-bw-volt text-bw-black">
                  <Clock className="h-4 w-4 mr-1" /> Log Time
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Log Time</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label>Task (optional)</Label>
                    <Select onValueChange={(v) => setNewTimeLog({...newTimeLog, task_id: v})}>
                      <SelectTrigger><SelectValue placeholder="Select task" /></SelectTrigger>
                      <SelectContent>
                        {tasks.map(t => <SelectItem key={t.task_id} value={t.task_id}>{t.title}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Hours *</Label>
                      <Input type="number" step="0.25" min="0.25" value={newTimeLog.hours_logged} onChange={(e) => setNewTimeLog({...newTimeLog, hours_logged: parseFloat(e.target.value) || 0})} />
                    </div>
                    <div>
                      <Label>Date</Label>
                      <Input type="date" value={newTimeLog.log_date} onChange={(e) => setNewTimeLog({...newTimeLog, log_date: e.target.value})} />
                    </div>
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Textarea value={newTimeLog.description} onChange={(e) => setNewTimeLog({...newTimeLog, description: e.target.value})} rows={2} placeholder="Work done..." />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowTimeLogDialog(false)}>Cancel</Button>
                  <Button onClick={handleLogTime} className="bg-bw-volt text-bw-black">Log Time</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <Card className="bg-bw-panel border-white/[0.07]">
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/[0.07]">
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Date</th>
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Employee</th>
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Task</th>
                    <th className="text-right p-3 text-xs text-bw-white/[0.45]">Hours</th>
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Description</th>
                    <th className="text-center p-3 text-xs text-bw-white/[0.45]">Invoiced</th>
                  </tr>
                </thead>
                <tbody>
                  {timeLogs.length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-8 text-bw-white/[0.45]">No time logs yet</td></tr>
                  ) : timeLogs.map(log => {
                    const task = tasks.find(t => t.task_id === log.task_id);
                    return (
                      <tr key={log.log_id} className={`border-b border-white/[0.07] ${log.invoiced ? 'text-bw-white/35' : ''}`}>
                        <td className="p-3 text-sm font-mono">{log.log_date}</td>
                        <td className="p-3 text-sm">{log.employee_name || log.employee_id}</td>
                        <td className="p-3 text-sm">{task?.title || '-'}</td>
                        <td className="p-3 text-sm text-right font-mono">{log.hours_logged}</td>
                        <td className="p-3 text-sm truncate max-w-[200px]">{log.description || '-'}</td>
                        <td className="p-3 text-center">
                          {log.invoiced ? (
                            <Badge className="bg-bw-volt/10 text-bw-volt">Invoiced</Badge>
                          ) : (
                            <span className="text-xs text-bw-white/[0.45]">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* EXPENSES TAB */}
        <TabsContent value="expenses" className="mt-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold">Expenses</h3>
              <p className="text-sm text-bw-white/[0.45]">
                Approved: ₹{expenses.filter(e => e.status === 'APPROVED').reduce((s,e) => s + e.amount, 0).toLocaleString('en-IN')}
              </p>
            </div>
            <Dialog open={showExpenseDialog} onOpenChange={setShowExpenseDialog}>
              <DialogTrigger asChild>
                <Button size="sm" className="bg-bw-volt text-bw-black">
                  <Receipt className="h-4 w-4 mr-1" /> Add Expense
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Add Expense</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label>Amount (₹) *</Label>
                    <Input type="number" value={newExpense.amount} onChange={(e) => setNewExpense({...newExpense, amount: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Description *</Label>
                    <Input value={newExpense.description} onChange={(e) => setNewExpense({...newExpense, description: e.target.value})} placeholder="Expense description" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Category</Label>
                      <Select value={newExpense.category} onValueChange={(v) => setNewExpense({...newExpense, category: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="general">General</SelectItem>
                          <SelectItem value="travel">Travel</SelectItem>
                          <SelectItem value="materials">Materials</SelectItem>
                          <SelectItem value="software">Software</SelectItem>
                          <SelectItem value="equipment">Equipment</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Date</Label>
                      <Input type="date" value={newExpense.expense_date} onChange={(e) => setNewExpense({...newExpense, expense_date: e.target.value})} />
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowExpenseDialog(false)}>Cancel</Button>
                  <Button onClick={handleAddExpense} className="bg-bw-volt text-bw-black">Add Expense</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <Card className="bg-bw-panel border-white/[0.07]">
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/[0.07]">
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Date</th>
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Description</th>
                    <th className="text-right p-3 text-xs text-bw-white/[0.45]">Amount</th>
                    <th className="text-left p-3 text-xs text-bw-white/[0.45]">Category</th>
                    <th className="text-center p-3 text-xs text-bw-white/[0.45]">Status</th>
                    <th className="text-right p-3 text-xs text-bw-white/[0.45]">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-8 text-bw-white/[0.45]">No expenses yet</td></tr>
                  ) : expenses.map(exp => {
                    const expStatus = expenseStatusConfig[exp.status] || expenseStatusConfig.PENDING;
                    return (
                      <tr key={exp.project_expense_id} className="border-b border-white/[0.07]">
                        <td className="p-3 text-sm font-mono">{exp.expense_date}</td>
                        <td className="p-3 text-sm">{exp.description}</td>
                        <td className="p-3 text-sm text-right font-mono">₹{exp.amount.toLocaleString('en-IN')}</td>
                        <td className="p-3 text-sm capitalize">{exp.category}</td>
                        <td className="p-3 text-center">
                          <Badge className={`${expStatus.bg} ${expStatus.text}`}>{expStatus.label}</Badge>
                        </td>
                        <td className="p-3 text-right">
                          {exp.status === 'PENDING' && (
                            <div className="flex justify-end gap-1">
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-volt" onClick={() => handleApproveExpense(exp.project_expense_id, true)}>
                                Approve
                              </Button>
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-bw-red" onClick={() => handleApproveExpense(exp.project_expense_id, false)}>
                                Reject
                              </Button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* FINANCIALS TAB */}
        <TabsContent value="financials" className="mt-4">
          {profitability ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Section */}
              <Card className="bg-bw-panel border-white/[0.07]">
                <CardHeader>
                  <CardTitle className="text-lg text-bw-teal">Revenue</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Contract Value / Budget</span>
                    <span className="font-medium">₹{(profitability.budget || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Hourly Projection</span>
                    <span className="font-medium">₹{(profitability.revenue || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between border-t border-white/[0.07] pt-3">
                    <span className="text-bw-white/[0.45]">Amount Outstanding</span>
                    <span className="font-bold text-bw-orange">₹{(profitability.revenue || 0).toLocaleString('en-IN')}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Cost Section */}
              <Card className="bg-bw-panel border-white/[0.07]">
                <CardHeader>
                  <CardTitle className="text-lg text-bw-orange">Costs</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Employee Cost ({profitability.hours?.logged || 0} hrs)</span>
                    <span className="font-medium">₹{(profitability.costs?.employee_cost || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bw-white/[0.45]">Approved Expenses</span>
                    <span className="font-medium">₹{(profitability.costs?.expenses || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex justify-between border-t border-white/[0.07] pt-3">
                    <span className="font-medium">Total Cost</span>
                    <span className="font-bold">₹{(profitability.costs?.total || 0).toLocaleString('en-IN')}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Profit Section */}
              <Card className="bg-bw-panel border-white/[0.07] lg:col-span-2">
                <CardHeader>
                  <CardTitle className={`text-lg ${profitability.is_profitable ? 'text-bw-volt' : 'text-bw-red'}`}>
                    Profit Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-sm text-bw-white/[0.45] mb-1">Revenue</div>
                      <div className="text-2xl font-bold text-bw-teal">₹{(profitability.revenue || 0).toLocaleString('en-IN')}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-bw-white/[0.45] mb-1">Cost</div>
                      <div className="text-2xl font-bold text-bw-orange">₹{(profitability.costs?.total || 0).toLocaleString('en-IN')}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-bw-white/[0.45] mb-1">Gross Profit</div>
                      <div className={`text-2xl font-bold ${profitability.is_profitable ? 'text-bw-volt' : 'text-bw-red'}`}>
                        ₹{(profitability.gross_profit || 0).toLocaleString('en-IN')}
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 flex items-center justify-center">
                    <div className={`text-4xl font-bold ${profitability.is_profitable ? 'text-bw-volt' : 'text-bw-red'}`}>
                      {profitability.margin_pct?.toFixed(1) || 0}%
                    </div>
                    <span className="ml-2 text-bw-white/[0.45]">Margin</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="bg-bw-panel border-white/[0.07]">
              <CardContent className="py-12 text-center text-bw-white/[0.45]">
                No financial data available
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ====================== TASK CARD COMPONENT ======================
function TaskCard({ task, onStatusChange }) {
  const priority = priorityConfig[task.priority] || priorityConfig.MEDIUM;
  
  return (
    <div className="bg-bw-card p-3 rounded border border-white/[0.07] hover:border-bw-volt/20 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h4 className="text-sm font-medium text-bw-white line-clamp-2">{task.title}</h4>
        <Select value={task.status} onValueChange={onStatusChange}>
          <SelectTrigger className="h-6 w-6 p-0 border-0 bg-transparent">
            <MoreHorizontal className="h-4 w-4 text-bw-white/[0.45]" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="TODO">To Do</SelectItem>
            <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
            <SelectItem value="REVIEW">Review</SelectItem>
            <SelectItem value="DONE">Done</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <span className={priority.text}>{priority.label}</span>
        {task.estimated_hours > 0 && (
          <span className="text-bw-white/[0.45]">{task.estimated_hours}h est</span>
        )}
        {task.due_date && (
          <span className="text-bw-white/[0.45] font-mono">{task.due_date}</span>
        )}
      </div>
    </div>
  );
}
