import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { 
  Plus, RefreshCw, Edit, Trash2, Loader2, 
  FolderKanban, Clock, IndianRupee, CheckCircle2
} from "lucide-react";
import { API } from "@/App";

export default function ProjectTasks() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  
  const [formData, setFormData] = useState({
    project_id: "",
    task_name: "",
    description: "",
    rate: 0,
    budget_hours: 0,
    is_billable: true
  });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchTasks(selectedProject.project_id);
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/zoho/projects`, { headers });
      const data = await res.json();
      setProjects(data.projects || []);
      if (data.projects?.length > 0) {
        setSelectedProject(data.projects[0]);
      }
    } catch (error) {
      console.error("Error fetching projects:", error);
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const fetchTasks = async (projectId) => {
    setTasksLoading(true);
    try {
      const res = await fetch(`${API}/zoho/projects/${projectId}/tasks`, { headers });
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      toast.error("Failed to load tasks");
    } finally {
      setTasksLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.task_name) {
      toast.error("Task name is required");
      return;
    }

    try {
      const payload = {
        ...formData,
        project_id: selectedProject.project_id
      };

      const res = await fetch(`${API}/zoho/projects/${selectedProject.project_id}/tasks`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Task created");
        setDialogOpen(false);
        fetchTasks(selectedProject.project_id);
        resetForm();
      } else {
        toast.error(data.message || "Failed to create");
      }
    } catch (error) {
      toast.error("Failed to create task");
    }
  };

  const handleUpdate = async () => {
    if (!formData.task_name) {
      toast.error("Task name is required");
      return;
    }

    try {
      const res = await fetch(`${API}/zoho/projects/${selectedProject.project_id}/tasks/${editingTask.task_id}`, {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Task updated");
        setDialogOpen(false);
        setEditingTask(null);
        fetchTasks(selectedProject.project_id);
        resetForm();
      } else {
        toast.error(data.message || "Failed to update");
      }
    } catch (error) {
      toast.error("Failed to update task");
    }
  };

  const handleDelete = async (taskId) => {
    if (!confirm("Are you sure you want to delete this task?")) return;
    
    try {
      const res = await fetch(`${API}/zoho/projects/${selectedProject.project_id}/tasks/${taskId}`, {
        method: "DELETE",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Task deleted");
        fetchTasks(selectedProject.project_id);
      }
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  const openEditDialog = (task) => {
    setEditingTask(task);
    setFormData({
      project_id: task.project_id,
      task_name: task.task_name,
      description: task.description || "",
      rate: task.rate || 0,
      budget_hours: task.budget_hours || 0,
      is_billable: task.is_billable !== false
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      project_id: "",
      task_name: "",
      description: "",
      rate: 0,
      budget_hours: 0,
      is_billable: true
    });
    setEditingTask(null);
  };

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const getProgressPercent = (logged, budget) => {
    if (!budget || budget === 0) return 0;
    return Math.min(100, (logged / budget) * 100);
  };

  return (
    <div className="space-y-6" data-testid="project-tasks-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Project Tasks</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Manage tasks within projects for time tracking</p>
        </div>
        <div className="flex items-center gap-3">
          <Select 
            value={selectedProject?.project_id || ""} 
            onValueChange={(v) => setSelectedProject(projects.find(p => p.project_id === v))}
          >
            <SelectTrigger className="w-64" data-testid="project-select">
              <SelectValue placeholder="Select Project" />
            </SelectTrigger>
            <SelectContent>
              {projects.map(p => (
                <SelectItem key={p.project_id} value={p.project_id}>
                  {p.project_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => selectedProject && fetchTasks(selectedProject.project_id)}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button 
                className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold" 
                disabled={!selectedProject}
                data-testid="new-task-btn"
              >
                <Plus className="h-4 w-4 mr-2" /> New Task
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingTask ? "Edit Task" : "Create Task"}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Task Name *</Label>
                  <Input
                    value={formData.task_name}
                    onChange={(e) => setFormData({...formData, task_name: e.target.value})}
                    placeholder="e.g., Design Phase"
                    data-testid="task-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Task details..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Hourly Rate (₹)</Label>
                    <Input
                      type="number"
                      value={formData.rate}
                      onChange={(e) => setFormData({...formData, rate: parseFloat(e.target.value) || 0})}
                      data-testid="rate-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Budget Hours</Label>
                    <Input
                      type="number"
                      value={formData.budget_hours}
                      onChange={(e) => setFormData({...formData, budget_hours: parseFloat(e.target.value) || 0})}
                      data-testid="budget-hours-input"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.is_billable}
                    onCheckedChange={(v) => setFormData({...formData, is_billable: v})}
                  />
                  <Label>Billable Task</Label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button 
                  onClick={editingTask ? handleUpdate : handleCreate} 
                  className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold"
                  data-testid="save-task-btn"
                >
                  {editingTask ? "Update Task" : "Create Task"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Project Info Card */}
      {selectedProject && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="py-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-blue-900">{selectedProject.project_name}</h2>
                <p className="text-sm text-[#3B9EFF]">{selectedProject.customer_name || "No customer"}</p>
              </div>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-[rgba(244,246,240,0.45)]">Status:</span>
                  <Badge className="ml-2 bg-blue-100 text-blue-800">{selectedProject.status || "active"}</Badge>
                </div>
                <div>
                  <span className="text-[rgba(244,246,240,0.45)]">Budget:</span>
                  <span className="ml-2 font-medium">{formatCurrency(selectedProject.budget_amount)}</span>
                </div>
                <div>
                  <span className="text-[rgba(244,246,240,0.45)]">Tasks:</span>
                  <span className="ml-2 font-medium">{tasks.length}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading || tasksLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
            </div>
          ) : !selectedProject ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
              <FolderKanban className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No project selected</p>
              <p className="text-sm">Select a project to view and manage its tasks</p>
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No tasks in this project</p>
              <p className="text-sm">Create tasks to track time and billing</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#111820]">
                  <TableHead>Task Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead className="text-center">Budget Hours</TableHead>
                  <TableHead className="text-center">Logged Hours</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Billable</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.task_id}>
                    <TableCell className="font-medium">{task.task_name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{task.description || "-"}</TableCell>
                    <TableCell className="text-right">{formatCurrency(task.rate)}/hr</TableCell>
                    <TableCell className="text-center">{task.budget_hours || 0}h</TableCell>
                    <TableCell className="text-center">{task.logged_hours || 0}h</TableCell>
                    <TableCell>
                      <div className="w-24">
                        <Progress 
                          value={getProgressPercent(task.logged_hours, task.budget_hours)} 
                          className="h-2"
                        />
                        <span className="text-xs text-[rgba(244,246,240,0.45)]">
                          {Math.round(getProgressPercent(task.logged_hours, task.budget_hours))}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {task.is_billable ? (
                        <Badge className="bg-[rgba(34,197,94,0.10)] text-[#22C55E]">Yes</Badge>
                      ) : (
                        <Badge className="bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.35)]">No</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="sm" onClick={() => openEditDialog(task)} title="Edit">
                          <Edit className="h-4 w-4 text-[#3B9EFF]" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(task.task_id)} title="Delete">
                          <Trash2 className="h-4 w-4 text-[#FF3B2F]" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
