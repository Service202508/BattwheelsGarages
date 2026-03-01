import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Switch } from "../components/ui/switch";
import { Textarea } from "../components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Tabs, TabsContent, TabsList, TabsTrigger
} from "../components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  Bell, CreditCard, Clock, DollarSign, AlertTriangle, Send, Calendar,
  Settings, RefreshCw, TrendingUp, Users, FileText, CheckCircle, XCircle,
  Mail, Repeat, Plus, Play, Pause, Trash2, Edit, Eye
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function InvoiceSettings() {
  const [loading, setLoading] = useState(true);
  const [agingReport, setAgingReport] = useState(null);
  const [overdueInvoices, setOverdueInvoices] = useState([]);
  const [dueSoonInvoices, setDueSoonInvoices] = useState([]);
  const [recurringInvoices, setRecurringInvoices] = useState([]);
  const [recurringStats, setRecurringStats] = useState(null);
  const [customers, setCustomers] = useState([]);
  
  // Settings
  const [reminderSettings, setReminderSettings] = useState({
    enabled: true,
    reminder_before_days: [7, 3, 1],
    reminder_after_days: [1, 7, 14, 30],
    email_template: "default",
    include_payment_link: true
  });
  
  const [lateFeeSettings, setLateFeeSettings] = useState({
    enabled: false,
    fee_type: "percentage",
    fee_value: 2.0,
    grace_period_days: 0,
    max_fee_percentage: 10.0,
    apply_automatically: false
  });
  
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  
  // Recurring Invoice Dialog
  const [showRecurringDialog, setShowRecurringDialog] = useState(false);
  const [newRecurring, setNewRecurring] = useState({
    customer_id: "",
    profile_name: "",
    frequency: "monthly",
    repeat_every: 1,
    start_date: "",
    end_date: "",
    line_items: [],
    payment_terms_days: 15,
    notes: "",
    send_email_on_generation: true
  });
  const [newLineItem, setNewLineItem] = useState({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });

  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const responses = await Promise.all([
        fetch(`${API}/invoice-automation/aging-report`, { headers }),
        fetch(`${API}/invoice-automation/overdue-invoices`, { headers }),
        fetch(`${API}/invoice-automation/due-soon-invoices?days=7`, { headers }),
        fetch(`${API}/invoice-automation/reminder-settings`, { headers }),
        fetch(`${API}/invoice-automation/late-fee-settings`, { headers }),
        fetch(`${API}/recurring-invoices`, { headers }),
        fetch(`${API}/recurring-invoices/summary`, { headers }),
        fetch(`${API}/contacts-enhanced/?contact_type=customer&per_page=200`, { headers })
      ]);
      
      const [aging, overdue, dueSoon, reminder, lateFee, recurring, recurringSummary, customersData] = 
        await Promise.all(responses.map(r => r.json()));
      
      setAgingReport(aging);
      setOverdueInvoices(overdue.overdue_invoices || []);
      setDueSoonInvoices(dueSoon.due_soon_invoices || []);
      if (reminder.settings) setReminderSettings(reminder.settings);
      if (lateFee.settings) setLateFeeSettings(lateFee.settings);
      setRecurringInvoices(recurring.recurring_invoices || []);
      setRecurringStats(recurringSummary);
      setCustomers(customersData.contacts || []);
    } catch (e) {
      console.error("Failed to fetch data:", e);
    }
    setLoading(false);
  };

  const saveReminderSettings = async () => {
    try {
      const res = await fetch(`${API}/invoice-automation/reminder-settings`, {
        method: "PUT",
        headers,
        body: JSON.stringify(reminderSettings)
      });
      if (res.ok) {
        toast.success("Reminder settings saved");
      }
    } catch (e) {
      toast.error("Failed to save settings");
    }
  };

  const saveLateFeeSettings = async () => {
    try {
      const res = await fetch(`${API}/invoice-automation/late-fee-settings`, {
        method: "PUT",
        headers,
        body: JSON.stringify(lateFeeSettings)
      });
      if (res.ok) {
        toast.success("Late fee settings saved");
      }
    } catch (e) {
      toast.error("Failed to save settings");
    }
  };

  const sendReminder = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoice-automation/send-reminder/${invoiceId}`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
      } else {
        toast.error(data.detail || "Failed to send reminder");
      }
    } catch (e) {
      toast.error("Failed to send reminder");
    }
  };

  const sendBulkReminders = async () => {
    if (selectedInvoices.length === 0) {
      toast.error("Select invoices first");
      return;
    }
    
    try {
      const res = await fetch(`${API}/invoice-automation/send-bulk-reminders`, {
        method: "POST",
        headers,
        body: JSON.stringify(selectedInvoices)
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        setSelectedInvoices([]);
      }
    } catch (e) {
      toast.error("Failed to send reminders");
    }
  };

  const applyLateFee = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoice-automation/apply-late-fee/${invoiceId}`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        fetchData();
      }
    } catch (e) {
      toast.error("Failed to apply late fee");
    }
  };

  const autoApplyCredits = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/invoice-automation/auto-apply-credits/${invoiceId}`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        fetchData();
      }
    } catch (e) {
      toast.error("Failed to apply credits");
    }
  };

  // Recurring Invoice Functions
  const handleAddLineItem = () => {
    if (!newLineItem.name || newLineItem.rate <= 0) {
      toast.error("Enter item name and rate");
      return;
    }
    setNewRecurring({
      ...newRecurring,
      line_items: [...newRecurring.line_items, { ...newLineItem }]
    });
    setNewLineItem({ name: "", rate: 0, quantity: 1, tax_percentage: 18 });
  };

  const removeLineItem = (index) => {
    setNewRecurring({
      ...newRecurring,
      line_items: newRecurring.line_items.filter((_, i) => i !== index)
    });
  };

  const calculateRecurringTotal = () => {
    return newRecurring.line_items.reduce((sum, item) => 
      sum + item.quantity * item.rate * (1 + item.tax_percentage / 100), 0
    );
  };

  const createRecurringInvoice = async () => {
    if (!newRecurring.customer_id) {
      toast.error("Select a customer");
      return;
    }
    if (!newRecurring.profile_name) {
      toast.error("Enter profile name");
      return;
    }
    if (!newRecurring.start_date) {
      toast.error("Select start date");
      return;
    }
    if (newRecurring.line_items.length === 0) {
      toast.error("Add at least one line item");
      return;
    }

    try {
      const res = await fetch(`${API}/recurring-invoices`, {
        method: "POST",
        headers,
        body: JSON.stringify(newRecurring)
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Recurring invoice created");
        setShowRecurringDialog(false);
        setNewRecurring({
          customer_id: "",
          profile_name: "",
          frequency: "monthly",
          repeat_every: 1,
          start_date: "",
          end_date: "",
          line_items: [],
          payment_terms_days: 15,
          notes: "",
          send_email_on_generation: true
        });
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create");
      }
    } catch (e) {
      toast.error("Failed to create recurring invoice");
    }
  };

  const toggleRecurringStatus = async (ri) => {
    const endpoint = ri.status === "active" ? "stop" : "resume";
    try {
      const res = await fetch(`${API}/recurring-invoices/${ri.recurring_id}/${endpoint}`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(ri.status === "active" ? "Recurring invoice stopped" : "Recurring invoice resumed");
        fetchData();
      }
    } catch (e) {
      toast.error("Failed to update status");
    }
  };

  const generateNow = async (recurringId) => {
    try {
      const res = await fetch(`${API}/recurring-invoices/${recurringId}/generate-now`, {
        method: "POST",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(`Invoice ${data.invoice_number} generated`);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to generate");
      }
    } catch (e) {
      toast.error("Failed to generate invoice");
    }
  };

  const deleteRecurring = async (recurringId) => {
    if (!confirm("Delete this recurring invoice profile?")) return;
    try {
      const res = await fetch(`${API}/recurring-invoices/${recurringId}`, {
        method: "DELETE",
        headers
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Recurring invoice deleted");
        fetchData();
      }
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  
  const frequencyLabels = {
    daily: "Daily",
    weekly: "Weekly",
    monthly: "Monthly",
    yearly: "Yearly"
  };

  return (
    <div className="p-6 space-y-6" data-testid="invoice-settings-page">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Invoice Automation</h1>
          <p className="text-bw-white/[0.45]">Payment reminders, late fees, recurring invoices, and aging reports</p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Aging Summary Cards */}
      {agingReport && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <Card className="col-span-2 md:col-span-1 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-4">
              <p className="text-sm text-bw-blue font-medium">Total AR</p>
              <p className="text-xl font-bold text-blue-800">{formatCurrency(agingReport.total_receivable)}</p>
            </CardContent>
          </Card>
          {agingReport.aging_buckets?.map((bucket, idx) => (
            <Card key={idx} className={bucket.amount > 0 && idx > 0 ? "border-red-200 bg-bw-red/[0.08]" : ""}>
              <CardContent className="p-4">
                <p className="text-sm text-bw-white/[0.45]">{bucket.label}</p>
                <p className="text-lg font-bold">{formatCurrency(bucket.amount)}</p>
                <p className="text-xs text-bw-white/25">{bucket.count} invoices</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Tabs defaultValue="overdue" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-flex">
          <TabsTrigger value="overdue" className="gap-2">
            <AlertTriangle className="h-4 w-4" /> Overdue
          </TabsTrigger>
          <TabsTrigger value="due-soon" className="gap-2">
            <Clock className="h-4 w-4" /> Due Soon
          </TabsTrigger>
          <TabsTrigger value="recurring" className="gap-2">
            <Repeat className="h-4 w-4" /> Recurring
          </TabsTrigger>
          <TabsTrigger value="reminders" className="gap-2">
            <Bell className="h-4 w-4" /> Reminders
          </TabsTrigger>
          <TabsTrigger value="late-fees" className="gap-2">
            <DollarSign className="h-4 w-4" /> Late Fees
          </TabsTrigger>
        </TabsList>

        {/* Overdue Invoices */}
        <TabsContent value="overdue">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-red-600 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" /> Overdue Invoices
                  </CardTitle>
                  <CardDescription>Invoices past their due date</CardDescription>
                </div>
                {selectedInvoices.length > 0 && (
                  <Button onClick={sendBulkReminders} className="bg-bw-orange hover:bg-orange-600 text-bw-black">
                    <Send className="h-4 w-4 mr-2" /> Send {selectedInvoices.length} Reminders
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center py-8 text-bw-white/[0.45]">Loading...</p>
              ) : overdueInvoices.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-2" />
                  <p className="text-bw-white/[0.45]">No overdue invoices! Great job.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-bw-red/[0.08]">
                      <tr>
                        <th className="px-4 py-3 text-left">
                          <input 
                            type="checkbox"
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedInvoices(overdueInvoices.map(i => i.invoice_id));
                              } else {
                                setSelectedInvoices([]);
                              }
                            }}
                          />
                        </th>
                        <th className="px-4 py-3 text-left">Invoice #</th>
                        <th className="px-4 py-3 text-left">Customer</th>
                        <th className="px-4 py-3 text-right">Amount Due</th>
                        <th className="px-4 py-3 text-center">Days Overdue</th>
                        <th className="px-4 py-3 text-center">Reminders</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {overdueInvoices.map((inv) => (
                        <tr key={inv.invoice_id} className="hover:bg-bw-panel">
                          <td className="px-4 py-3">
                            <input 
                              type="checkbox"
                              checked={selectedInvoices.includes(inv.invoice_id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedInvoices([...selectedInvoices, inv.invoice_id]);
                                } else {
                                  setSelectedInvoices(selectedInvoices.filter(id => id !== inv.invoice_id));
                                }
                              }}
                            />
                          </td>
                          <td className="px-4 py-3 font-medium">{inv.invoice_number}</td>
                          <td className="px-4 py-3">{inv.customer_name}</td>
                          <td className="px-4 py-3 text-right font-medium text-red-600">
                            {formatCurrency(inv.balance_due)}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <Badge variant="destructive">{inv.days_overdue} days</Badge>
                          </td>
                          <td className="px-4 py-3 text-center">{inv.reminder_count || 0}</td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex gap-2 justify-end">
                              <Button size="sm" variant="outline" onClick={() => sendReminder(inv.invoice_id)}>
                                <Bell className="h-3 w-3 mr-1" /> Remind
                              </Button>
                              {lateFeeSettings.enabled && (
                                <Button size="sm" variant="outline" className="text-bw-orange" onClick={() => applyLateFee(inv.invoice_id)}>
                                  <DollarSign className="h-3 w-3 mr-1" /> Fee
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Due Soon */}
        <TabsContent value="due-soon">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-bw-amber" /> Due Soon
              </CardTitle>
              <CardDescription>Invoices due within 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              {dueSoonInvoices.length === 0 ? (
                <p className="text-center py-8 text-bw-white/[0.45]">No invoices due soon</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-bw-amber/[0.08]">
                      <tr>
                        <th className="px-4 py-3 text-left">Invoice #</th>
                        <th className="px-4 py-3 text-left">Customer</th>
                        <th className="px-4 py-3 text-right">Amount Due</th>
                        <th className="px-4 py-3 text-center">Due Date</th>
                        <th className="px-4 py-3 text-center">Days Left</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {dueSoonInvoices.map((inv) => (
                        <tr key={inv.invoice_id} className="hover:bg-bw-panel">
                          <td className="px-4 py-3 font-medium">{inv.invoice_number}</td>
                          <td className="px-4 py-3">{inv.customer_name}</td>
                          <td className="px-4 py-3 text-right font-medium">{formatCurrency(inv.balance_due)}</td>
                          <td className="px-4 py-3 text-center">{inv.due_date}</td>
                          <td className="px-4 py-3 text-center">
                            <Badge variant="outline" className="bg-bw-amber/[0.08] text-bw-amber">{inv.days_until_due} days</Badge>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Button size="sm" variant="outline" onClick={() => sendReminder(inv.invoice_id)}>
                              <Bell className="h-3 w-3 mr-1" /> Remind
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recurring Invoices */}
        <TabsContent value="recurring">
          <div className="space-y-4">
            {/* Recurring Stats */}
            {recurringStats && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-bw-white/[0.45]">Total Profiles</p>
                    <p className="text-2xl font-bold">{recurringStats.total_profiles}</p>
                  </CardContent>
                </Card>
                <Card className="bg-bw-green/[0.08] border-green-200">
                  <CardContent className="p-4">
                    <p className="text-sm text-green-600">Active</p>
                    <p className="text-2xl font-bold text-green-700">{recurringStats.active}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-bw-white/[0.45]">Stopped</p>
                    <p className="text-2xl font-bold">{recurringStats.stopped}</p>
                  </CardContent>
                </Card>
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="p-4">
                    <p className="text-sm text-bw-blue">MRR</p>
                    <p className="text-2xl font-bold text-bw-blue">{formatCurrency(recurringStats.monthly_recurring_revenue)}</p>
                  </CardContent>
                </Card>
                <Card className="bg-bw-orange/[0.08] border-orange-200">
                  <CardContent className="p-4">
                    <p className="text-sm text-bw-orange">Due Today</p>
                    <p className="text-2xl font-bold text-bw-orange">{recurringStats.due_today}</p>
                  </CardContent>
                </Card>
              </div>
            )}

            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Repeat className="h-5 w-5" /> Recurring Invoices
                    </CardTitle>
                    <CardDescription>Automatically generate invoices on a schedule</CardDescription>
                  </div>
                  <Button onClick={() => setShowRecurringDialog(true)}>
                    <Plus className="h-4 w-4 mr-2" /> New Recurring
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {recurringInvoices.length === 0 ? (
                  <div className="text-center py-8">
                    <Repeat className="h-12 w-12 mx-auto text-bw-white/20 mb-2" />
                    <p className="text-bw-white/[0.45]">No recurring invoices yet</p>
                    <p className="text-sm text-bw-white/25">Create one to automate billing</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-bw-panel">
                        <tr>
                          <th className="px-4 py-3 text-left">Profile Name</th>
                          <th className="px-4 py-3 text-left">Customer</th>
                          <th className="px-4 py-3 text-center">Frequency</th>
                          <th className="px-4 py-3 text-right">Amount</th>
                          <th className="px-4 py-3 text-center">Next Invoice</th>
                          <th className="px-4 py-3 text-center">Status</th>
                          <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {recurringInvoices.map((ri) => (
                          <tr key={ri.recurring_id} className="hover:bg-bw-panel">
                            <td className="px-4 py-3 font-medium">{ri.profile_name}</td>
                            <td className="px-4 py-3">{ri.customer_name}</td>
                            <td className="px-4 py-3 text-center">
                              {ri.repeat_every > 1 && `Every ${ri.repeat_every} `}
                              {frequencyLabels[ri.frequency] || ri.frequency}
                            </td>
                            <td className="px-4 py-3 text-right font-medium">{formatCurrency(ri.grand_total)}</td>
                            <td className="px-4 py-3 text-center">{ri.next_invoice_date}</td>
                            <td className="px-4 py-3 text-center">
                              <Badge className={
                                ri.status === "active" ? "bg-bw-volt/10 text-bw-volt border border-bw-volt/25" :
                                ri.status === "stopped" ? "bg-bw-card text-bw-white/[0.45]" :
                                "bg-bw-red/10 text-bw-red border border-bw-red/25"
                              }>
                                {ri.status}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex gap-1 justify-end">
                                <Button size="sm" variant="ghost" onClick={() => toggleRecurringStatus(ri)} title={ri.status === "active" ? "Stop" : "Resume"}>
                                  {ri.status === "active" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => generateNow(ri.recurring_id)} title="Generate Now">
                                  <FileText className="h-4 w-4" />
                                </Button>
                                <Button size="sm" variant="ghost" className="text-red-500" onClick={() => deleteRecurring(ri.recurring_id)} title="Delete">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Reminder Settings */}
        <TabsContent value="reminders">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" /> Payment Reminder Settings
              </CardTitle>
              <CardDescription>Configure automatic payment reminders</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Payment Reminders</Label>
                  <p className="text-sm text-bw-white/[0.45]">Send automatic email reminders</p>
                </div>
                <Switch
                  checked={reminderSettings.enabled}
                  onCheckedChange={(checked) => setReminderSettings({...reminderSettings, enabled: checked})}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <Label>Include Payment Link</Label>
                  <p className="text-sm text-bw-white/[0.45]">Add online payment link (Stripe) in reminders</p>
                </div>
                <Switch
                  checked={reminderSettings.include_payment_link}
                  onCheckedChange={(checked) => setReminderSettings({...reminderSettings, include_payment_link: checked})}
                />
              </div>

              <Separator />

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
                  <Mail className="h-4 w-4" /> Email Integration Status
                </h4>
                <p className="text-sm text-bw-blue">
                  Email reminders will be sent via <strong>Resend</strong>. 
                  To activate, add <code className="bg-bw-panel px-1 rounded">RESEND_API_KEY</code> to your environment.
                </p>
              </div>

              <Button onClick={saveReminderSettings}>Save Reminder Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Late Fee Settings */}
        <TabsContent value="late-fees">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" /> Late Fee Settings
              </CardTitle>
              <CardDescription>Configure late payment fees</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Late Fees</Label>
                  <p className="text-sm text-bw-white/[0.45]">Apply late fees to overdue invoices</p>
                </div>
                <Switch
                  checked={lateFeeSettings.enabled}
                  onCheckedChange={(checked) => setLateFeeSettings({...lateFeeSettings, enabled: checked})}
                />
              </div>

              {lateFeeSettings.enabled && (
                <>
                  <Separator />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Fee Type</Label>
                      <Select
                        value={lateFeeSettings.fee_type}
                        onValueChange={(v) => setLateFeeSettings({...lateFeeSettings, fee_type: v})}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="percentage">Percentage of Balance</SelectItem>
                          <SelectItem value="fixed">Fixed Amount</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Fee Value ({lateFeeSettings.fee_type === "percentage" ? "%" : "₹"})</Label>
                      <Input
                        type="number"
                        value={lateFeeSettings.fee_value}
                        onChange={(e) => setLateFeeSettings({...lateFeeSettings, fee_value: parseFloat(e.target.value) || 0})}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Grace Period (Days)</Label>
                      <Input
                        type="number"
                        value={lateFeeSettings.grace_period_days}
                        onChange={(e) => setLateFeeSettings({...lateFeeSettings, grace_period_days: parseInt(e.target.value) || 0})}
                      />
                      <p className="text-xs text-bw-white/[0.45] mt-1">Days after due date before fee applies</p>
                    </div>
                    <div>
                      <Label>Maximum Fee (%)</Label>
                      <Input
                        type="number"
                        value={lateFeeSettings.max_fee_percentage}
                        onChange={(e) => setLateFeeSettings({...lateFeeSettings, max_fee_percentage: parseFloat(e.target.value) || 0})}
                      />
                      <p className="text-xs text-bw-white/[0.45] mt-1">Cap on total late fees</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Apply Automatically</Label>
                      <p className="text-sm text-bw-white/[0.45]">Auto-apply fees when invoice becomes overdue</p>
                    </div>
                    <Switch
                      checked={lateFeeSettings.apply_automatically}
                      onCheckedChange={(checked) => setLateFeeSettings({...lateFeeSettings, apply_automatically: checked})}
                    />
                  </div>
                </>
              )}

              <Button onClick={saveLateFeeSettings}>Save Late Fee Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Recurring Invoice Dialog */}
      <Dialog open={showRecurringDialog} onOpenChange={setShowRecurringDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Recurring Invoice</DialogTitle>
            <DialogDescription>Set up automatic invoice generation</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Customer Selection */}
            <div>
              <Label>Customer *</Label>
              <Select
                value={newRecurring.customer_id}
                onValueChange={(v) => {
                  const customer = customers.find(c => c.contact_id === v);
                  setNewRecurring({
                    ...newRecurring,
                    customer_id: v,
                    customer_name: customer?.display_name || customer?.contact_name || ""
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select customer" />
                </SelectTrigger>
                <SelectContent>
                  {customers.map(c => (
                    <SelectItem key={c.contact_id} value={c.contact_id}>
                      {c.display_name || c.contact_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Profile Name */}
            <div>
              <Label>Profile Name *</Label>
              <Input
                placeholder="e.g., Monthly Retainer - ABC Corp"
                value={newRecurring.profile_name}
                onChange={(e) => setNewRecurring({...newRecurring, profile_name: e.target.value})}
              />
            </div>

            {/* Frequency */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Frequency</Label>
                <Select
                  value={newRecurring.frequency}
                  onValueChange={(v) => setNewRecurring({...newRecurring, frequency: v})}
                >
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
              <div>
                <Label>Repeat Every</Label>
                <Input
                  type="number"
                  min="1"
                  value={newRecurring.repeat_every}
                  onChange={(e) => setNewRecurring({...newRecurring, repeat_every: parseInt(e.target.value) || 1})}
                />
              </div>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Start Date *</Label>
                <Input
                  type="date"
                  value={newRecurring.start_date}
                  onChange={(e) => setNewRecurring({...newRecurring, start_date: e.target.value})}
                />
              </div>
              <div>
                <Label>End Date (optional)</Label>
                <Input
                  type="date"
                  value={newRecurring.end_date}
                  onChange={(e) => setNewRecurring({...newRecurring, end_date: e.target.value})}
                />
              </div>
            </div>

            {/* Payment Terms */}
            <div>
              <Label>Payment Terms (Days)</Label>
              <Input
                type="number"
                value={newRecurring.payment_terms_days}
                onChange={(e) => setNewRecurring({...newRecurring, payment_terms_days: parseInt(e.target.value) || 15})}
              />
            </div>

            <Separator />

            {/* Line Items */}
            <div>
              <Label className="mb-2 block">Line Items</Label>
              <div className="grid grid-cols-4 gap-2 mb-2">
                <Input
                  placeholder="Item name"
                  value={newLineItem.name}
                  onChange={(e) => setNewLineItem({...newLineItem, name: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="Rate"
                  value={newLineItem.rate || ""}
                  onChange={(e) => setNewLineItem({...newLineItem, rate: parseFloat(e.target.value) || 0})}
                />
                <Input
                  type="number"
                  placeholder="Qty"
                  value={newLineItem.quantity}
                  onChange={(e) => setNewLineItem({...newLineItem, quantity: parseFloat(e.target.value) || 1})}
                />
                <Button type="button" onClick={handleAddLineItem}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>

              {newRecurring.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-bw-panel">
                      <tr>
                        <th className="px-3 py-2 text-left">Item</th>
                        <th className="px-3 py-2 text-right">Rate</th>
                        <th className="px-3 py-2 text-right">Qty</th>
                        <th className="px-3 py-2 text-right">Total</th>
                        <th className="px-3 py-2"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {newRecurring.line_items.map((item, idx) => (
                        <tr key={idx}>
                          <td className="px-3 py-2">{item.name}</td>
                          <td className="px-3 py-2 text-right">{formatCurrency(item.rate)}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right">{formatCurrency(item.rate * item.quantity * (1 + item.tax_percentage / 100))}</td>
                          <td className="px-3 py-2 text-right">
                            <Button size="sm" variant="ghost" onClick={() => removeLineItem(idx)}>
                              <XCircle className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-bw-panel">
                      <tr>
                        <td colSpan="3" className="px-3 py-2 text-right font-medium">Total (incl. 18% GST):</td>
                        <td className="px-3 py-2 text-right font-bold">{formatCurrency(calculateRecurringTotal())}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>

            {/* Notes */}
            <div>
              <Label>Notes</Label>
              <Textarea
                placeholder="Notes to include on invoices"
                value={newRecurring.notes}
                onChange={(e) => setNewRecurring({...newRecurring, notes: e.target.value})}
              />
            </div>

            {/* Email Option */}
            <div className="flex items-center justify-between">
              <div>
                <Label>Send Email on Generation</Label>
                <p className="text-sm text-bw-white/[0.45]">Automatically email invoice to customer</p>
              </div>
              <Switch
                checked={newRecurring.send_email_on_generation}
                onCheckedChange={(checked) => setNewRecurring({...newRecurring, send_email_on_generation: checked})}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRecurringDialog(false)}>Cancel</Button>
            <Button onClick={createRecurringInvoice}>Create Recurring Invoice</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
