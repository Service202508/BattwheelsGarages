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
import { toast } from "sonner";
import { 
  Plus, RefreshCw, Play, Pause, Trash2, Loader2, 
  Calendar, IndianRupee, Clock, Building2
} from "lucide-react";
import { API } from "@/App";

export default function RecurringExpenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [vendors, setVendors] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [generating, setGenerating] = useState(false);
  
  const [formData, setFormData] = useState({
    vendor_id: "",
    vendor_name: "",
    account_id: "",
    account_name: "",
    recurrence_name: "",
    recurrence_frequency: "monthly",
    repeat_every: 1,
    start_date: new Date().toISOString().split('T')[0],
    end_date: "",
    never_expires: true,
    amount: 0,
    tax_percentage: 0,
    description: "",
    is_billable: false,
    customer_id: "",
    project_id: ""
  });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchExpenses();
    fetchVendors();
    fetchAccounts();
  }, [statusFilter]);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      const url = `${API}/zoho/recurring-expenses${statusFilter ? `?status=${statusFilter}` : ''}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setExpenses(data.recurring_expenses || []);
    } catch (error) {
      console.error("Error fetching recurring expenses:", error);
      toast.error("Failed to load recurring expenses");
    } finally {
      setLoading(false);
    }
  };

  const fetchVendors = async () => {
    try {
      const res = await fetch(`${API}/zoho/contacts?contact_type=vendor`, { headers });
      const data = await res.json();
      setVendors(data.contacts || []);
    } catch (error) {
      console.error("Error fetching vendors:", error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await fetch(`${API}/zoho/chartofaccounts?account_type=expense`, { headers });
      const data = await res.json();
      setAccounts(data.accounts || []);
    } catch (error) {
      console.error("Error fetching accounts:", error);
    }
  };

  const handleCreate = async () => {
    if (!formData.recurrence_name || !formData.account_id || !formData.amount) {
      toast.error("Please fill required fields: Name, Account, and Amount");
      return;
    }

    try {
      const vendor = vendors.find(v => v.contact_id === formData.vendor_id);
      const account = accounts.find(a => a.account_id === formData.account_id);
      
      const payload = {
        ...formData,
        vendor_name: vendor?.contact_name || "",
        account_name: account?.account_name || ""
      };

      const res = await fetch(`${API}/zoho/recurring-expenses`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Recurring expense created");
        setDialogOpen(false);
        fetchExpenses();
        resetForm();
      } else {
        toast.error(data.message || "Failed to create");
      }
    } catch (error) {
      toast.error("Failed to create recurring expense");
    }
  };

  const handleStop = async (reId) => {
    try {
      const res = await fetch(`${API}/zoho/recurring-expenses/${reId}/stop`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Recurring expense stopped");
        fetchExpenses();
      }
    } catch (error) {
      toast.error("Failed to stop");
    }
  };

  const handleResume = async (reId) => {
    try {
      const res = await fetch(`${API}/zoho/recurring-expenses/${reId}/resume`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Recurring expense resumed");
        fetchExpenses();
      }
    } catch (error) {
      toast.error("Failed to resume");
    }
  };

  const handleDelete = async (reId) => {
    if (!confirm("Are you sure you want to delete this recurring expense?")) return;
    
    try {
      const res = await fetch(`${API}/zoho/recurring-expenses/${reId}`, {
        method: "DELETE",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Recurring expense deleted");
        fetchExpenses();
      }
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/zoho/recurring-expenses/generate`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      toast.success(`Generated ${data.generated_count || 0} expenses`);
      fetchExpenses();
    } catch (error) {
      toast.error("Failed to generate expenses");
    } finally {
      setGenerating(false);
    }
  };

  const resetForm = () => {
    setFormData({
      vendor_id: "",
      vendor_name: "",
      account_id: "",
      account_name: "",
      recurrence_name: "",
      recurrence_frequency: "monthly",
      repeat_every: 1,
      start_date: new Date().toISOString().split('T')[0],
      end_date: "",
      never_expires: true,
      amount: 0,
      tax_percentage: 0,
      description: "",
      is_billable: false,
      customer_id: "",
      project_id: ""
    });
  };

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const getStatusBadge = (status) => {
    const styles = {
      active: "bg-[rgba(34,197,94,0.10)] text-[#22C55E]",
      stopped: "bg-[rgba(255,59,47,0.10)] text-red-800",
      expired: "bg-[rgba(255,255,255,0.05)] text-[#F4F6F0]"
    };
    return <Badge className={styles[status] || "bg-[rgba(255,255,255,0.05)]"}>{status}</Badge>;
  };

  const frequencyLabels = {
    daily: "Daily",
    weekly: "Weekly",
    monthly: "Monthly",
    yearly: "Yearly"
  };

  return (
    <div className="space-y-6" data-testid="recurring-expenses-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Recurring Expenses</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">Manage automated expense schedules</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={statusFilter || "all"} onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-32" data-testid="status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="stopped">Stopped</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={fetchExpenses}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="outline" onClick={handleGenerate} disabled={generating} data-testid="generate-btn">
            {generating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Clock className="h-4 w-4 mr-2" />}
            Generate Due
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold" data-testid="new-recurring-expense-btn">
                <Plus className="h-4 w-4 mr-2" /> New Recurring
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Create Recurring Expense</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="space-y-2">
                  <Label>Recurrence Name *</Label>
                  <Input
                    value={formData.recurrence_name}
                    onChange={(e) => setFormData({...formData, recurrence_name: e.target.value})}
                    placeholder="e.g., Monthly Rent"
                    data-testid="recurrence-name-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Expense Account *</Label>
                    <Select value={formData.account_id} onValueChange={(v) => setFormData({...formData, account_id: v})}>
                      <SelectTrigger data-testid="account-select">
                        <SelectValue placeholder="Select Account" />
                      </SelectTrigger>
                      <SelectContent>
                        {accounts.map(acc => (
                          <SelectItem key={acc.account_id} value={acc.account_id}>
                            {acc.account_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Vendor</Label>
                    <Select value={formData.vendor_id || "none"} onValueChange={(v) => setFormData({...formData, vendor_id: v === "none" ? "" : v})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Vendor" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Vendor</SelectItem>
                        {vendors.map(v => (
                          <SelectItem key={v.contact_id} value={v.contact_id}>
                            {v.contact_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Amount *</Label>
                    <Input
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData({...formData, amount: parseFloat(e.target.value) || 0})}
                      data-testid="amount-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Tax %</Label>
                    <Input
                      type="number"
                      value={formData.tax_percentage}
                      onChange={(e) => setFormData({...formData, tax_percentage: parseFloat(e.target.value) || 0})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Frequency</Label>
                    <Select value={formData.recurrence_frequency} onValueChange={(v) => setFormData({...formData, recurrence_frequency: v})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="yearly">Yearly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Repeat Every</Label>
                    <Input
                      type="number"
                      min={1}
                      value={formData.repeat_every}
                      onChange={(e) => setFormData({...formData, repeat_every: parseInt(e.target.value) || 1})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Date</Label>
                    <Input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>End Date</Label>
                    <Input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                      disabled={formData.never_expires}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.never_expires}
                    onCheckedChange={(v) => setFormData({...formData, never_expires: v})}
                  />
                  <Label>Never Expires</Label>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Optional notes..."
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} className="bg-[#C8FF00] hover:bg-[#1dd699] text-[#080C0F] font-bold" data-testid="save-recurring-btn">
                  Create Recurring
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[#C8FF00]" />
            </div>
          ) : expenses.length === 0 ? (
            <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No recurring expenses found</p>
              <p className="text-sm">Create your first recurring expense to automate regular payments</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#111820]">
                  <TableHead>Name</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Next Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Generated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {expenses.map((exp) => (
                  <TableRow key={exp.recurring_expense_id}>
                    <TableCell className="font-medium">{exp.recurrence_name}</TableCell>
                    <TableCell>{exp.account_name}</TableCell>
                    <TableCell>{exp.vendor_name || "-"}</TableCell>
                    <TableCell>
                      Every {exp.repeat_every} {frequencyLabels[exp.recurrence_frequency] || exp.recurrence_frequency}
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(exp.total)}</TableCell>
                    <TableCell>{exp.next_expense_date || "-"}</TableCell>
                    <TableCell>{getStatusBadge(exp.status)}</TableCell>
                    <TableCell>{exp.expenses_generated || 0}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {exp.status === "active" ? (
                          <Button variant="ghost" size="sm" onClick={() => handleStop(exp.recurring_expense_id)} title="Stop">
                            <Pause className="h-4 w-4 text-[#FF8C00]" />
                          </Button>
                        ) : (
                          <Button variant="ghost" size="sm" onClick={() => handleResume(exp.recurring_expense_id)} title="Resume">
                            <Play className="h-4 w-4 text-[#22C55E]" />
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(exp.recurring_expense_id)} title="Delete">
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
