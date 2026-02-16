import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { Plus, FolderKanban, Clock, User, Calendar, Play, Pause, CheckCircle } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  active: "bg-green-100 text-green-700",
  on_hold: "bg-yellow-100 text-yellow-700",
  completed: "bg-blue-100 text-blue-700",
  cancelled: "bg-red-100 text-red-700"
};

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [timeEntries, setTimeEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTimeDialog, setShowTimeDialog] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);

  const [newProject, setNewProject] = useState({
    project_name: "", customer_id: "", customer_name: "", description: "",
    billing_type: "fixed_cost", rate: 0, budget_type: "no_budget", budget_hours: 0
  });

  const [newTimeEntry, setNewTimeEntry] = useState({
    project_id: "", project_name: "", task_name: "", hours: 0, is_billable: true, description: "", rate: 0
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [projRes, custRes, timeRes] = await Promise.all([
        fetch(`${API}/zoho/projects`, { headers }),
        fetch(`${API}/zoho/contacts?contact_type=customer&per_page=200`, { headers }),
        fetch(`${API}/zoho/time-entries`, { headers })
      ]);
      const [projData, custData, timeData] = await Promise.all([projRes.json(), custRes.json(), timeRes.json()]);
      setProjects(projData.projects || []);
      setCustomers(custData.contacts || []);
      setTimeEntries(timeData.time_entries || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleCreateProject = async () => {
    if (!newProject.project_name) return toast.error("Enter project name");
    if (!newProject.customer_id) return toast.error("Select a customer");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newProject)
      });
      if (res.ok) {
        toast.success("Project created");
        setShowCreateDialog(false);
        setNewProject({ project_name: "", customer_id: "", customer_name: "", description: "", billing_type: "fixed_cost", rate: 0, budget_type: "no_budget", budget_hours: 0 });
        fetchData();
      }
    } catch { toast.error("Error creating project"); }
  };

  const handleLogTime = async () => {
    if (!newTimeEntry.project_id) return toast.error("Select a project");
    if (newTimeEntry.hours <= 0) return toast.error("Enter hours");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/time-entries`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newTimeEntry)
      });
      if (res.ok) {
        toast.success("Time logged");
        setShowTimeDialog(false);
        setNewTimeEntry({ project_id: "", project_name: "", task_name: "", hours: 0, is_billable: true, description: "", rate: 0 });
        fetchData();
      }
    } catch { toast.error("Error logging time"); }
  };

  const handleUpdateStatus = async (projectId, status) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/projects/${projectId}/status/${status}`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Project marked as ${status}`);
      fetchData();
    } catch { toast.error("Error updating status"); }
  };

  return (
    <div className="space-y-6" data-testid="projects-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-500 text-sm mt-1">Track projects & time</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showTimeDialog} onOpenChange={setShowTimeDialog}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Clock className="h-4 w-4 mr-2" /> Log Time
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Log Time Entry</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>Project *</Label>
                  <Select onValueChange={(v) => {
                    const proj = projects.find(p => p.project_id === v);
                    if (proj) setNewTimeEntry({ ...newTimeEntry, project_id: proj.project_id, project_name: proj.project_name, rate: proj.rate || 0 });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select project" /></SelectTrigger>
                    <SelectContent>{projects.filter(p => p.status === "active").map(p => <SelectItem key={p.project_id} value={p.project_id}>{p.project_name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Task</Label>
                  <Input value={newTimeEntry.task_name} onChange={(e) => setNewTimeEntry({ ...newTimeEntry, task_name: e.target.value })} placeholder="e.g., Development" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Hours *</Label>
                    <Input type="number" value={newTimeEntry.hours} onChange={(e) => setNewTimeEntry({ ...newTimeEntry, hours: parseFloat(e.target.value) })} step={0.25} min={0.25} />
                  </div>
                  <div>
                    <Label>Rate (per hour)</Label>
                    <Input type="number" value={newTimeEntry.rate} onChange={(e) => setNewTimeEntry({ ...newTimeEntry, rate: parseFloat(e.target.value) })} />
                  </div>
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea value={newTimeEntry.description} onChange={(e) => setNewTimeEntry({ ...newTimeEntry, description: e.target.value })} placeholder="Work done..." />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowTimeDialog(false)}>Cancel</Button>
                <Button onClick={handleLogTime} className="bg-[#22EDA9] text-black">Log Time</Button>
              </div>
            </DialogContent>
          </Dialog>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black" data-testid="create-project-btn">
                <Plus className="h-4 w-4 mr-2" /> New Project
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create Project</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>Project Name *</Label>
                  <Input value={newProject.project_name} onChange={(e) => setNewProject({ ...newProject, project_name: e.target.value })} placeholder="e.g., Website Redesign" />
                </div>
                <div>
                  <Label>Customer *</Label>
                  <Select onValueChange={(v) => {
                    const cust = customers.find(c => c.contact_id === v);
                    if (cust) setNewProject({ ...newProject, customer_id: cust.contact_id, customer_name: cust.contact_name });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                    <SelectContent>{customers.map(c => <SelectItem key={c.contact_id} value={c.contact_id}>{c.contact_name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea value={newProject.description} onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Billing Type</Label>
                    <Select value={newProject.billing_type} onValueChange={(v) => setNewProject({ ...newProject, billing_type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fixed_cost">Fixed Cost</SelectItem>
                        <SelectItem value="based_on_project_hours">Based on Hours</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Hourly Rate</Label>
                    <Input type="number" value={newProject.rate} onChange={(e) => setNewProject({ ...newProject, rate: parseFloat(e.target.value) })} />
                  </div>
                </div>
                <div>
                  <Label>Budget Hours</Label>
                  <Input type="number" value={newProject.budget_hours} onChange={(e) => setNewProject({ ...newProject, budget_hours: parseFloat(e.target.value) })} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                <Button onClick={handleCreateProject} className="bg-[#22EDA9] text-black">Create Project</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        projects.length === 0 ? <Card><CardContent className="py-12 text-center text-gray-500">No projects found</CardContent></Card> :
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map(project => {
            const progress = project.budget_hours > 0 ? (project.total_hours / project.budget_hours) * 100 : 0;
            return (
              <Card key={project.project_id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <FolderKanban className="h-5 w-5 text-[#22EDA9]" />
                        <h3 className="font-semibold">{project.project_name}</h3>
                      </div>
                      <Badge className={statusColors[project.status]}>{project.status}</Badge>
                    </div>
                    <div className="flex gap-1">
                      {project.status === "active" && (
                        <>
                          <Button size="icon" variant="ghost" onClick={() => handleUpdateStatus(project.project_id, "on_hold")}><Pause className="h-4 w-4" /></Button>
                          <Button size="icon" variant="ghost" onClick={() => handleUpdateStatus(project.project_id, "completed")}><CheckCircle className="h-4 w-4" /></Button>
                        </>
                      )}
                      {project.status === "on_hold" && (
                        <Button size="icon" variant="ghost" onClick={() => handleUpdateStatus(project.project_id, "active")}><Play className="h-4 w-4" /></Button>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500 mb-3">
                    <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" />{project.customer_name}</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Hours Logged</span>
                      <span className="font-medium">{project.total_hours?.toFixed(1)} / {project.budget_hours || '∞'} hrs</span>
                    </div>
                    {project.budget_hours > 0 && <Progress value={Math.min(progress, 100)} className="h-2" />}
                    <div className="flex justify-between text-sm">
                      <span>Unbilled Hours</span>
                      <span className="font-medium text-orange-600">{project.unbilled_hours?.toFixed(1)} hrs</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Total Cost</span>
                      <span className="font-bold">₹{project.total_cost?.toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      }
    </div>
  );
}
