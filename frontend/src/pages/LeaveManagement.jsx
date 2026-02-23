import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { 
  Calendar, Plus, CheckCircle2, XCircle, Clock, 
  AlertCircle, Umbrella, Stethoscope, Palmtree, Ban
} from "lucide-react";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const LEAVE_ICONS = {
  CL: Umbrella,
  SL: Stethoscope,
  EL: Palmtree,
  LWP: Ban,
  CO: Clock,
};

const LEAVE_COLORS = {
  CL: "text-blue-500",
  SL: "text-red-500",
  EL: "text-green-500",
  LWP: "text-[rgba(244,246,240,0.45)]",
  CO: "text-purple-500",
};

export default function LeaveManagement({ user }) {
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [leaveBalance, setLeaveBalance] = useState(null);
  const [myRequests, setMyRequests] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isApplyOpen, setIsApplyOpen] = useState(false);
  
  const initialFormData = {
    leave_type: "CL",
    start_date: "",
    end_date: "",
    reason: ""
  };
  const [formData, setFormData] = useState(initialFormData);

  // Auto-save for Apply Leave form
  const leavePersistence = useFormPersistence(
    'leave_apply_new',
    formData,
    initialFormData,
    {
      enabled: isApplyOpen,
      isDialogOpen: isApplyOpen,
      setFormData: setFormData,
      debounceMs: 2000,
      entityName: 'Leave Request'
    }
  );

  const fetchLeaveTypes = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/types`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setLeaveTypes(data);
      }
    } catch (error) {
      console.error("Failed to fetch leave types:", error);
    }
  }, []);

  const fetchLeaveBalance = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/balance`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setLeaveBalance(data);
      }
    } catch (error) {
      console.error("Failed to fetch balance:", error);
    }
  }, []);

  const fetchMyRequests = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/my-requests`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setMyRequests(data);
      }
    } catch (error) {
      console.error("Failed to fetch requests:", error);
    }
  }, []);

  const fetchPendingApprovals = useCallback(async () => {
    if (user?.role !== "admin" && user?.role !== "technician") return;
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/pending-approvals`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setPendingApprovals(data);
      }
    } catch (error) {
      console.error("Failed to fetch approvals:", error);
    }
  }, [user?.role]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchLeaveTypes(),
        fetchLeaveBalance(),
        fetchMyRequests(),
        fetchPendingApprovals()
      ]);
      setLoading(false);
    };
    loadData();
  }, [fetchLeaveTypes, fetchLeaveBalance, fetchMyRequests, fetchPendingApprovals]);

  const handleApplyLeave = async () => {
    if (!formData.leave_type || !formData.start_date || !formData.end_date || !formData.reason) {
      toast.error("Please fill all fields");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Leave request submitted!");
        leavePersistence.onSuccessfulSave();
        setIsApplyOpen(false);
        setFormData(initialFormData);
        fetchMyRequests();
        fetchLeaveBalance();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to submit request");
      }
    } catch (error) {
      toast.error("Error submitting request");
    }
  };

  const handleApproval = async (leaveId, status, rejectionReason = null) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/${leaveId}/approve`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ status, rejection_reason: rejectionReason }),
      });

      if (response.ok) {
        toast.success(`Leave ${status}`);
        fetchPendingApprovals();
        fetchMyRequests();
      } else {
        toast.error("Failed to process request");
      }
    } catch (error) {
      toast.error("Error processing request");
    }
  };

  const handleCancelRequest = async (leaveId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/leave/${leaveId}`, {
        method: "DELETE",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        toast.success("Leave request cancelled");
        fetchMyRequests();
        fetchLeaveBalance();
      } else {
        toast.error("Failed to cancel request");
      }
    } catch (error) {
      toast.error("Error cancelling request");
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-[rgba(234,179,8,0.10)]",
      approved: "badge-success",
      rejected: "bg-[rgba(255,59,47,0.10)]",
      cancelled: "badge-muted",
    };
    return <Badge className={styles[status]}>{status}</Badge>;
  };

  const calculateDays = () => {
    if (!formData.start_date || !formData.end_date) return 0;
    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);
    return Math.max(0, Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1);
  };

  return (
    <div className="space-y-6" data-testid="leave-management-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Leave Management</h1>
          <p className="text-muted-foreground">Apply for leaves and track your balance.</p>
        </div>
        <Dialog 
          open={isApplyOpen} 
          onOpenChange={(open) => {
            if (!open && leavePersistence.isDirty) {
              leavePersistence.setShowCloseConfirm(true);
            } else {
              if (!open) leavePersistence.clearSavedData();
              setIsApplyOpen(open);
            }
          }}
        >
          <DialogTrigger asChild>
            <Button data-testid="apply-leave-btn">
              <Plus className="mr-2 h-4 w-4" />
              Apply Leave
            </Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle>Apply for Leave</DialogTitle>
                <AutoSaveIndicator 
                  lastSaved={leavePersistence.lastSaved} 
                  isSaving={leavePersistence.isSaving} 
                  isDirty={leavePersistence.isDirty} 
                />
              </div>
            </DialogHeader>
            
            <DraftRecoveryBanner
              show={leavePersistence.showRecoveryBanner}
              savedAt={leavePersistence.savedDraftInfo?.timestamp}
              onRestore={leavePersistence.handleRestoreDraft}
              onDiscard={leavePersistence.handleDiscardDraft}
            />
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Leave Type</Label>
                <Select 
                  value={formData.leave_type} 
                  onValueChange={(v) => setFormData({...formData, leave_type: v})}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {leaveTypes.map((lt) => (
                      <SelectItem key={lt.code} value={lt.code}>
                        {lt.name} ({lt.code}) - {leaveBalance?.balances?.[lt.code]?.available || 0} days available
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                  />
                </div>
              </div>
              {calculateDays() > 0 && (
                <div className="p-3 bg-muted rounded-lg text-center">
                  <span className="text-lg font-bold">{calculateDays()}</span>
                  <span className="text-muted-foreground"> day(s) requested</span>
                </div>
              )}
              <div className="space-y-2">
                <Label>Reason</Label>
                <Textarea
                  value={formData.reason}
                  onChange={(e) => setFormData({...formData, reason: e.target.value})}
                  placeholder="Please provide a reason for your leave..."
                />
              </div>
            </div>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  if (leavePersistence.isDirty) {
                    leavePersistence.setShowCloseConfirm(true);
                  } else {
                    setIsApplyOpen(false);
                  }
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleApplyLeave}>Submit Request</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Leave Balance Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        {leaveTypes.map((lt) => {
          const balance = leaveBalance?.balances?.[lt.code] || {};
          const Icon = LEAVE_ICONS[lt.code] || Calendar;
          const color = LEAVE_COLORS[lt.code] || "text-[rgba(244,246,240,0.45)]";
          const usedPct = balance.total ? (balance.used / balance.total) * 100 : 0;
          
          return (
            <Card key={lt.code}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${color}`} />
                  {lt.code}
                </CardTitle>
                <CardDescription>{lt.name}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Available</span>
                    <span className="font-bold text-lg">{balance.available || 0}</span>
                  </div>
                  <Progress value={usedPct} className="h-2" />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Used: {balance.used || 0}</span>
                    <span>Total: {balance.total || 0}</span>
                  </div>
                  {balance.pending > 0 && (
                    <Badge variant="outline" className="text-yellow-500">
                      {balance.pending} pending
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="my-requests">
        <TabsList>
          <TabsTrigger value="my-requests">My Requests</TabsTrigger>
          {(user?.role === "admin" || user?.role === "technician") && (
            <TabsTrigger value="approvals">
              Pending Approvals
              {pendingApprovals.length > 0 && (
                <Badge className="ml-2 bg-[rgba(255,59,47,0.10)]">{pendingApprovals.length}</Badge>
              )}
            </TabsTrigger>
          )}
        </TabsList>

        {/* My Requests */}
        <TabsContent value="my-requests">
          <Card>
            <CardContent className="p-0">
              {myRequests.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
                  <Calendar className="h-12 w-12 mb-4 opacity-50" />
                  <p>No leave requests yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>From</TableHead>
                      <TableHead>To</TableHead>
                      <TableHead>Days</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Manager</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {myRequests.map((req) => {
                      const Icon = LEAVE_ICONS[req.leave_type] || Calendar;
                      const color = LEAVE_COLORS[req.leave_type] || "text-[rgba(244,246,240,0.45)]";
                      
                      return (
                        <TableRow key={req.leave_id}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Icon className={`h-4 w-4 ${color}`} />
                              <span>{req.leave_type}</span>
                            </div>
                          </TableCell>
                          <TableCell>{req.start_date}</TableCell>
                          <TableCell>{req.end_date}</TableCell>
                          <TableCell>{req.days}</TableCell>
                          <TableCell className="max-w-[200px] truncate">{req.reason}</TableCell>
                          <TableCell>{getStatusBadge(req.status)}</TableCell>
                          <TableCell>{req.manager_name || "-"}</TableCell>
                          <TableCell>
                            {req.status === "pending" && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                className="text-red-500"
                                onClick={() => handleCancelRequest(req.leave_id)}
                              >
                                Cancel
                              </Button>
                            )}
                            {req.status === "rejected" && req.rejection_reason && (
                              <span className="text-xs text-red-500">{req.rejection_reason}</span>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pending Approvals (Admin/Manager) */}
        {(user?.role === "admin" || user?.role === "technician") && (
          <TabsContent value="approvals">
            <Card>
              <CardContent className="p-0">
                {pendingApprovals.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
                    <CheckCircle2 className="h-12 w-12 mb-4 opacity-50" />
                    <p>No pending approvals</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Employee</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>From</TableHead>
                        <TableHead>To</TableHead>
                        <TableHead>Days</TableHead>
                        <TableHead>Reason</TableHead>
                        <TableHead>Applied On</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pendingApprovals.map((req) => (
                        <TableRow key={req.leave_id}>
                          <TableCell className="font-medium">{req.user_name}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{req.leave_type}</Badge>
                          </TableCell>
                          <TableCell>{req.start_date}</TableCell>
                          <TableCell>{req.end_date}</TableCell>
                          <TableCell>{req.days}</TableCell>
                          <TableCell className="max-w-[200px] truncate">{req.reason}</TableCell>
                          <TableCell>{new Date(req.created_at).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                className="bg-[#22C55E] hover:bg-green-600 text-[#080C0F]"
                                onClick={() => handleApproval(req.leave_id, "approved")}
                              >
                                <CheckCircle2 className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleApproval(req.leave_id, "rejected", "Not approved")}
                              >
                                <XCircle className="h-4 w-4" />
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
          </TabsContent>
        )}
      </Tabs>
      
      {/* Unsaved Changes Confirmation Dialog */}
      <FormCloseConfirmDialog
        open={leavePersistence.showCloseConfirm}
        onClose={() => leavePersistence.setShowCloseConfirm(false)}
        onSave={handleApplyLeave}
        onDiscard={() => {
          leavePersistence.clearSavedData();
          setFormData(initialFormData);
          setIsApplyOpen(false);
        }}
        entityName="Leave Request"
      />
    </div>
  );
}
