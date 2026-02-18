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
  Settings, RefreshCw, TrendingUp, Users, FileText, CheckCircle, XCircle
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function InvoiceSettings() {
  const [loading, setLoading] = useState(true);
  const [agingReport, setAgingReport] = useState(null);
  const [overdueInvoices, setOverdueInvoices] = useState([]);
  const [dueSoonInvoices, setDueSoonInvoices] = useState([]);
  
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
      const [agingRes, overdueRes, dueSoonRes, reminderRes, lateFeeRes] = await Promise.all([
        fetch(`${API}/invoice-automation/aging-report`, { headers }),
        fetch(`${API}/invoice-automation/overdue-invoices`, { headers }),
        fetch(`${API}/invoice-automation/due-soon-invoices?days=7`, { headers }),
        fetch(`${API}/invoice-automation/reminder-settings`, { headers }),
        fetch(`${API}/invoice-automation/late-fee-settings`, { headers })
      ]);
      
      const [aging, overdue, dueSoon, reminder, lateFee] = await Promise.all([
        agingRes.json(), overdueRes.json(), dueSoonRes.json(), reminderRes.json(), lateFeeRes.json()
      ]);
      
      setAgingReport(aging);
      setOverdueInvoices(overdue.overdue_invoices || []);
      setDueSoonInvoices(dueSoon.due_soon_invoices || []);
      if (reminder.settings) setReminderSettings(reminder.settings);
      if (lateFee.settings) setLateFeeSettings(lateFee.settings);
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

  const formatCurrency = (amount) => `₹${(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  return (
    <div className="p-6 space-y-6" data-testid="invoice-settings-page">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Invoice Automation</h1>
          <p className="text-gray-500">Payment reminders, late fees, and aging reports</p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Aging Summary Cards */}
      {agingReport && (
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <Card className="col-span-1">
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">Total AR</p>
              <p className="text-xl font-bold">{formatCurrency(agingReport.total_receivable)}</p>
            </CardContent>
          </Card>
          {agingReport.aging_buckets?.map((bucket, idx) => (
            <Card key={idx} className={bucket.amount > 0 && idx > 0 ? "border-red-200" : ""}>
              <CardContent className="p-4">
                <p className="text-sm text-gray-500">{bucket.label}</p>
                <p className="text-lg font-bold">{formatCurrency(bucket.amount)}</p>
                <p className="text-xs text-gray-400">{bucket.count} invoices</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Tabs defaultValue="overdue" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overdue">
            <AlertTriangle className="h-4 w-4 mr-2" /> Overdue ({overdueInvoices.length})
          </TabsTrigger>
          <TabsTrigger value="due-soon">
            <Clock className="h-4 w-4 mr-2" /> Due Soon ({dueSoonInvoices.length})
          </TabsTrigger>
          <TabsTrigger value="reminders">
            <Bell className="h-4 w-4 mr-2" /> Reminder Settings
          </TabsTrigger>
          <TabsTrigger value="late-fees">
            <DollarSign className="h-4 w-4 mr-2" /> Late Fees
          </TabsTrigger>
        </TabsList>

        {/* Overdue Invoices */}
        <TabsContent value="overdue">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-red-600">Overdue Invoices</CardTitle>
                  <CardDescription>Invoices past their due date</CardDescription>
                </div>
                {selectedInvoices.length > 0 && (
                  <Button onClick={sendBulkReminders}>
                    <Send className="h-4 w-4 mr-2" /> Send {selectedInvoices.length} Reminders
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center py-8 text-gray-500">Loading...</p>
              ) : overdueInvoices.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-2" />
                  <p className="text-gray-500">No overdue invoices!</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-red-50">
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
                        <th className="px-4 py-3 text-center">Reminders Sent</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {overdueInvoices.map((inv) => (
                        <tr key={inv.invoice_id} className="hover:bg-gray-50">
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
                                <Button size="sm" variant="outline" onClick={() => applyLateFee(inv.invoice_id)}>
                                  <DollarSign className="h-3 w-3 mr-1" /> Late Fee
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
              <CardTitle>Due Soon</CardTitle>
              <CardDescription>Invoices due within 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              {dueSoonInvoices.length === 0 ? (
                <p className="text-center py-8 text-gray-500">No invoices due soon</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-yellow-50">
                      <tr>
                        <th className="px-4 py-3 text-left">Invoice #</th>
                        <th className="px-4 py-3 text-left">Customer</th>
                        <th className="px-4 py-3 text-right">Amount Due</th>
                        <th className="px-4 py-3 text-center">Due Date</th>
                        <th className="px-4 py-3 text-center">Days Until Due</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {dueSoonInvoices.map((inv) => (
                        <tr key={inv.invoice_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium">{inv.invoice_number}</td>
                          <td className="px-4 py-3">{inv.customer_name}</td>
                          <td className="px-4 py-3 text-right font-medium">{formatCurrency(inv.balance_due)}</td>
                          <td className="px-4 py-3 text-center">{inv.due_date}</td>
                          <td className="px-4 py-3 text-center">
                            <Badge variant="outline" className="bg-yellow-50">{inv.days_until_due} days</Badge>
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

        {/* Reminder Settings */}
        <TabsContent value="reminders">
          <Card>
            <CardHeader>
              <CardTitle>Payment Reminder Settings</CardTitle>
              <CardDescription>Configure automatic payment reminders</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Payment Reminders</Label>
                  <p className="text-sm text-gray-500">Send automatic email reminders</p>
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
                  <p className="text-sm text-gray-500">Add online payment link in reminders</p>
                </div>
                <Switch
                  checked={reminderSettings.include_payment_link}
                  onCheckedChange={(checked) => setReminderSettings({...reminderSettings, include_payment_link: checked})}
                />
              </div>

              <Button onClick={saveReminderSettings}>Save Reminder Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Late Fee Settings */}
        <TabsContent value="late-fees">
          <Card>
            <CardHeader>
              <CardTitle>Late Fee Settings</CardTitle>
              <CardDescription>Configure late payment fees</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Late Fees</Label>
                  <p className="text-sm text-gray-500">Apply late fees to overdue invoices</p>
                </div>
                <Switch
                  checked={lateFeeSettings.enabled}
                  onCheckedChange={(checked) => setLateFeeSettings({...lateFeeSettings, enabled: checked})}
                />
              </div>

              {lateFeeSettings.enabled && (
                <>
                  <Separator />
                  
                  <div className="grid grid-cols-2 gap-4">
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

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Grace Period (Days)</Label>
                      <Input
                        type="number"
                        value={lateFeeSettings.grace_period_days}
                        onChange={(e) => setLateFeeSettings({...lateFeeSettings, grace_period_days: parseInt(e.target.value) || 0})}
                      />
                      <p className="text-xs text-gray-500 mt-1">Days after due date before fee applies</p>
                    </div>
                    <div>
                      <Label>Maximum Fee (%)</Label>
                      <Input
                        type="number"
                        value={lateFeeSettings.max_fee_percentage}
                        onChange={(e) => setLateFeeSettings({...lateFeeSettings, max_fee_percentage: parseFloat(e.target.value) || 0})}
                      />
                      <p className="text-xs text-gray-500 mt-1">Cap on total late fees</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Apply Automatically</Label>
                      <p className="text-sm text-gray-500">Auto-apply fees when invoice becomes overdue</p>
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
    </div>
  );
}
