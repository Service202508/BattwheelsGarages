/**
 * Battwheels OS - Time Tracking Page
 * Track technician hours, manage timers, and convert to invoices
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Clock, Play, Square, Plus, RefreshCw, FileText, DollarSign,
  User, Calendar, Timer, AlertCircle, CheckCircle
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";
import { toast } from "sonner";

// Format duration
const formatDuration = (seconds) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', { 
    style: 'currency', 
    currency: 'INR',
    minimumFractionDigits: 2 
  }).format(amount || 0);
};

// Active Timer Component
const ActiveTimer = ({ timer, onStop }) => {
  const [elapsed, setElapsed] = useState(timer.elapsed_seconds || 0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <Card className="border-bw-green/25 bg-bw-green/[0.08]">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-bw-green flex items-center justify-center animate-pulse">
              <Timer className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="font-semibold">{timer.description || "Active Timer"}</p>
              <p className="text-sm text-muted-foreground">
                {timer.user_name} • {timer.task_type}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-3xl font-mono font-bold text-green-600">
                {formatDuration(elapsed)}
              </p>
              <p className="text-xs text-muted-foreground">
                Started at {new Date(timer.start_time).toLocaleTimeString()}
              </p>
            </div>
            <Button 
              variant="destructive" 
              size="lg"
              onClick={() => onStop(timer.timer_id)}
            >
              <Square className="h-5 w-5 mr-2" />
              Stop
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// New Entry Dialog
const NewEntryDialog = ({ open, onClose, onSave, tickets, users }) => {
  const [formData, setFormData] = useState({
    ticket_id: "",
    user_id: "",
    user_name: "",
    date: new Date().toISOString().split("T")[0],
    hours: "",
    description: "",
    task_type: "service",
    billable: true,
    hourly_rate: "500"
  });
  
  const handleSubmit = () => {
    if (!formData.hours || !formData.user_id) {
      toast.error("Please fill required fields");
      return;
    }
    onSave({
      ...formData,
      hours: parseFloat(formData.hours),
      hourly_rate: parseFloat(formData.hourly_rate)
    });
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Log Time Entry</DialogTitle>
          <DialogDescription>Record time spent on a task</DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Date *</Label>
              <Input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              />
            </div>
            <div>
              <Label>Hours *</Label>
              <Input
                type="number"
                step="0.5"
                min="0.5"
                max="24"
                placeholder="e.g., 2.5"
                value={formData.hours}
                onChange={(e) => setFormData({ ...formData, hours: e.target.value })}
              />
            </div>
          </div>
          
          <div>
            <Label>Technician *</Label>
            <Select
              value={formData.user_id}
              onValueChange={(v) => {
                const user = users.find(u => u.user_id === v);
                setFormData({ 
                  ...formData, 
                  user_id: v,
                  user_name: user?.name || user?.email || v
                });
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select technician" />
              </SelectTrigger>
              <SelectContent>
                {users.map((user) => (
                  <SelectItem key={user.user_id} value={user.user_id}>
                    {user.name || user.email}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Ticket (Optional)</Label>
            <Select
              value={formData.ticket_id || "__none__"}
              onValueChange={(v) => setFormData({ ...formData, ticket_id: v === "__none__" ? "" : v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Link to ticket" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">None</SelectItem>
                {tickets.map((ticket) => (
                  <SelectItem key={ticket.ticket_id} value={ticket.ticket_id}>
                    {ticket.issue?.substring(0, 40) || ticket.ticket_id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Task Type</Label>
            <Select
              value={formData.task_type}
              onValueChange={(v) => setFormData({ ...formData, task_type: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="service">Service</SelectItem>
                <SelectItem value="repair">Repair</SelectItem>
                <SelectItem value="inspection">Inspection</SelectItem>
                <SelectItem value="admin">Administrative</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Description</Label>
            <Textarea
              placeholder="What did you work on?"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Hourly Rate (₹)</Label>
              <Input
                type="number"
                value={formData.hourly_rate}
                onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })}
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <Checkbox
                id="billable"
                checked={formData.billable}
                onCheckedChange={(checked) => setFormData({ ...formData, billable: checked })}
              />
              <Label htmlFor="billable">Billable</Label>
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Save Entry</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Start Timer Dialog
const StartTimerDialog = ({ open, onClose, onStart, tickets, currentUser }) => {
  const [formData, setFormData] = useState({
    ticket_id: "",
    description: "",
    task_type: "service",
    billable: true
  });
  
  const handleStart = () => {
    onStart({
      ...formData,
      user_id: currentUser?.user_id || "admin",
      user_name: currentUser?.name || currentUser?.email || "Admin"
    });
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Start Timer</DialogTitle>
          <DialogDescription>Begin tracking time for a task</DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <Label>Link to Ticket (Optional)</Label>
            <Select
              value={formData.ticket_id || "__none__"}
              onValueChange={(v) => setFormData({ ...formData, ticket_id: v === "__none__" ? "" : v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select ticket" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">None</SelectItem>
                {tickets.map((ticket) => (
                  <SelectItem key={ticket.ticket_id} value={ticket.ticket_id}>
                    {ticket.issue?.substring(0, 40) || ticket.ticket_id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Description</Label>
            <Input
              placeholder="What are you working on?"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>
          
          <div>
            <Label>Task Type</Label>
            <Select
              value={formData.task_type}
              onValueChange={(v) => setFormData({ ...formData, task_type: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="service">Service</SelectItem>
                <SelectItem value="repair">Repair</SelectItem>
                <SelectItem value="inspection">Inspection</SelectItem>
                <SelectItem value="admin">Administrative</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex items-center gap-2">
            <Checkbox
              id="billable-timer"
              checked={formData.billable}
              onCheckedChange={(checked) => setFormData({ ...formData, billable: checked })}
            />
            <Label htmlFor="billable-timer">Billable</Label>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleStart} className="bg-bw-green hover:bg-bw-green-hover">
            <Play className="h-4 w-4 mr-2" />
            Start Timer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Main Time Tracking Page
export default function TimeTracking({ user }) {
  const [loading, setLoading] = useState(true);
  const [entries, setEntries] = useState([]);
  const [activeTimers, setActiveTimers] = useState([]);
  const [unbilled, setUnbilled] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedEntries, setSelectedEntries] = useState([]);
  
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [showStartTimer, setShowStartTimer] = useState(false);
  
  const headers = getAuthHeaders();
  
  const fetchData = useCallback(async () => {
    try {
      const [entriesRes, timersRes, unbilledRes, ticketsRes, usersRes] = await Promise.all([
        fetch(`${API}/time-tracking/entries?per_page=100`, { headers }),
        fetch(`${API}/time-tracking/timer/active`, { headers }),
        fetch(`${API}/time-tracking/unbilled`, { headers }),
        fetch(`${API}/tickets?status=open,in_progress&per_page=50`, { headers }),
        fetch(`${API}/users`, { headers })
      ]);
      
      if (entriesRes.ok) {
        const data = await entriesRes.json();
        setEntries(data.entries || []);
      }
      
      if (timersRes.ok) {
        const data = await timersRes.json();
        setActiveTimers(data.timers || []);
      }
      
      if (unbilledRes.ok) {
        const data = await unbilledRes.json();
        setUnbilled(data.unbilled);
      }
      
      if (ticketsRes.ok) {
        const data = await ticketsRes.json();
        setTickets(data.data || data.tickets || []);
      }
      
      if (usersRes.ok) {
        const data = await usersRes.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  }, [headers]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  const handleCreateEntry = async (data) => {
    try {
      const res = await fetch(`${API}/time-tracking/entries`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        toast.success("Time entry created");
        setShowNewEntry(false);
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to create entry");
      }
    } catch (error) {
      toast.error("Failed to create entry");
    }
  };
  
  const handleStartTimer = async (data) => {
    try {
      const res = await fetch(`${API}/time-tracking/timer/start`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      
      if (res.ok) {
        toast.success("Timer started");
        setShowStartTimer(false);
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to start timer");
      }
    } catch (error) {
      toast.error("Failed to start timer");
    }
  };
  
  const handleStopTimer = async (timerId) => {
    try {
      const res = await fetch(`${API}/time-tracking/timer/stop/${timerId}?hourly_rate=500`, {
        method: "POST",
        headers
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Timer stopped. Logged ${data.hours} hours`);
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to stop timer");
      }
    } catch (error) {
      toast.error("Failed to stop timer");
    }
  };
  
  const handleDeleteEntry = async (entryId) => {
    if (!confirm("Delete this time entry?")) return;
    
    try {
      const res = await fetch(`${API}/time-tracking/entries/${entryId}`, {
        method: "DELETE",
        headers
      });
      
      if (res.ok) {
        toast.success("Entry deleted");
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to delete");
      }
    } catch (error) {
      toast.error("Failed to delete entry");
    }
  };
  
  const handleConvertToInvoice = async () => {
    if (selectedEntries.length === 0) {
      toast.error("Select entries to convert");
      return;
    }
    
    // For now, use first customer from entries
    const customerId = ""; // Would need to select customer
    
    toast.info("Invoice conversion coming soon. Use manual invoice creation for now.");
  };
  
  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6" data-testid="time-tracking-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Time Tracking</h1>
          <p className="text-muted-foreground">Track hours, manage timers, and bill customers</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={() => setShowNewEntry(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Log Time
          </Button>
          <Button onClick={() => setShowStartTimer(true)} className="bg-bw-green hover:bg-bw-green-hover">
            <Play className="h-4 w-4 mr-2" />
            Start Timer
          </Button>
        </div>
      </div>
      
      {/* Active Timers */}
      {activeTimers.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Timer className="h-5 w-5 text-green-500" />
            Active Timers
          </h2>
          {activeTimers.map((timer) => (
            <ActiveTimer 
              key={timer.timer_id} 
              timer={timer} 
              onStop={handleStopTimer}
            />
          ))}
        </div>
      )}
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Clock className="h-5 w-5 text-bw-blue" />
              </div>
              <div>
                <p className="text-2xl font-bold">{unbilled?.total_hours || 0}</p>
                <p className="text-sm text-muted-foreground">Unbilled Hours</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-bw-green/10 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCurrency(unbilled?.total_amount || 0)}</p>
                <p className="text-sm text-muted-foreground">Unbilled Amount</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-orange-100 flex items-center justify-center">
                <FileText className="h-5 w-5 text-bw-orange" />
              </div>
              <div>
                <p className="text-2xl font-bold">{unbilled?.entry_count || 0}</p>
                <p className="text-sm text-muted-foreground">Unbilled Entries</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <User className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeTimers.length}</p>
                <p className="text-sm text-muted-foreground">Active Timers</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Time Entries Table */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Entries</TabsTrigger>
          <TabsTrigger value="unbilled">Unbilled</TabsTrigger>
          <TabsTrigger value="billed">Billed</TabsTrigger>
        </TabsList>
        
        <TabsContent value="all" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Time Entries</CardTitle>
              {selectedEntries.length > 0 && (
                <Button onClick={handleConvertToInvoice}>
                  <FileText className="h-4 w-4 mr-2" />
                  Convert to Invoice ({selectedEntries.length})
                </Button>
              )}
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10">
                      <Checkbox
                        checked={selectedEntries.length === entries.filter(e => !e.billed).length}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedEntries(entries.filter(e => !e.billed).map(e => e.entry_id));
                          } else {
                            setSelectedEntries([]);
                          }
                        }}
                      />
                    </TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Technician</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Task Type</TableHead>
                    <TableHead className="text-right">Hours</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-20"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No time entries found. Start tracking time!
                      </TableCell>
                    </TableRow>
                  ) : (
                    entries.map((entry) => (
                      <TableRow key={entry.entry_id}>
                        <TableCell>
                          <Checkbox
                            disabled={entry.billed}
                            checked={selectedEntries.includes(entry.entry_id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedEntries([...selectedEntries, entry.entry_id]);
                              } else {
                                setSelectedEntries(selectedEntries.filter(id => id !== entry.entry_id));
                              }
                            }}
                          />
                        </TableCell>
                        <TableCell>{entry.date}</TableCell>
                        <TableCell>{entry.user_name}</TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {entry.description || "-"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{entry.task_type}</Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {entry.hours?.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(entry.amount)}
                        </TableCell>
                        <TableCell>
                          {entry.billed ? (
                            <Badge className="bg-bw-green/10 text-bw-green">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Billed
                            </Badge>
                          ) : entry.billable ? (
                            <Badge variant="secondary">
                              <Clock className="h-3 w-3 mr-1" />
                              Unbilled
                            </Badge>
                          ) : (
                            <Badge variant="outline">Non-billable</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {!entry.billed && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteEntry(entry.entry_id)}
                            >
                              Delete
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="unbilled" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Unbilled Time Entries</CardTitle>
              <CardDescription>
                {unbilled?.entry_count || 0} entries worth {formatCurrency(unbilled?.total_amount || 0)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(unbilled?.groups || []).map((group) => (
                <div key={group.ticket_id || "unassigned"} className="mb-6 last:mb-0">
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg mb-2">
                    <div>
                      <p className="font-medium">
                        {group.ticket_id ? `Ticket: ${group.ticket_id}` : "Unassigned"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {group.entries?.length || 0} entries
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">{group.total_hours?.toFixed(2)} hours</p>
                      <p className="text-sm text-green-600">{formatCurrency(group.total_amount)}</p>
                    </div>
                  </div>
                </div>
              ))}
              
              {(!unbilled?.groups || unbilled.groups.length === 0) && (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>All time entries have been billed!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="billed" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Billed Time Entries</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Technician</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Hours</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Invoice</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.filter(e => e.billed).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                        No billed entries yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    entries.filter(e => e.billed).map((entry) => (
                      <TableRow key={entry.entry_id}>
                        <TableCell>{entry.date}</TableCell>
                        <TableCell>{entry.user_name}</TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {entry.description || "-"}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {entry.hours?.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(entry.amount)}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{entry.invoice_id || "-"}</Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      {/* Dialogs */}
      <NewEntryDialog
        open={showNewEntry}
        onClose={() => setShowNewEntry(false)}
        onSave={handleCreateEntry}
        tickets={tickets}
        users={users}
      />
      
      <StartTimerDialog
        open={showStartTimer}
        onClose={() => setShowStartTimer(false)}
        onStart={handleStartTimer}
        tickets={tickets}
        currentUser={user}
      />
    </div>
  );
}
