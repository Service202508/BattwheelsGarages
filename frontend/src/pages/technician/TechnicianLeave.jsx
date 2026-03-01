import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { toast } from "sonner";
import { format } from "date-fns";
import {
  Calendar as CalendarIcon, Plus, Loader2, Clock, CheckCircle,
  XCircle, AlertCircle, Sun, Umbrella, Heart, Plane
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  approved: "bg-bw-volt/[0.08]0/20 text-bw-volt text-400 border-bw-volt/50/30",
  rejected: "bg-bw-red/[0.08]0/20 text-red-400 border-red-500/30",
};

const leaveTypeIcons = {
  casual: Sun,
  sick: Heart,
  earned: Umbrella,
  unpaid: Clock,
};

export default function TechnicianLeave({ user }) {
  const [leaveData, setLeaveData] = useState({ requests: [], balance: {} });
  const [loading, setLoading] = useState(true);
  const [showRequestDialog, setShowRequestDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  
  const [formData, setFormData] = useState({
    leave_type: "casual",
    reason: ""
  });

  useEffect(() => {
    fetchLeaveData();
  }, []);

  const fetchLeaveData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/technician/leave`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setLeaveData(data);
      }
    } catch (error) {
      console.error("Failed to fetch leave data:", error);
      toast.error("Failed to load leave data");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitLeave = async () => {
    if (!startDate || !endDate || !formData.reason) {
      toast.error("Please fill in all fields");
      return;
    }
    
    if (endDate < startDate) {
      toast.error("End date must be after start date");
      return;
    }
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/technician/leave`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          leave_type: formData.leave_type,
          start_date: format(startDate, "yyyy-MM-dd"),
          end_date: format(endDate, "yyyy-MM-dd"),
          reason: formData.reason
        })
      });
      
      if (res.ok) {
        toast.success("Leave request submitted successfully!");
        setShowRequestDialog(false);
        setFormData({ leave_type: "casual", reason: "" });
        setStartDate(null);
        setEndDate(null);
        fetchLeaveData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to submit leave request");
      }
    } catch (error) {
      toast.error("Failed to submit leave request");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  const balance = leaveData.balance || {};
  const used = balance.used || {};

  return (
    <div className="space-y-6" data-testid="technician-leave">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Leave Management</h1>
          <p className="text-slate-400">Request and track your leaves</p>
        </div>
        <Button 
          onClick={() => setShowRequestDialog(true)}
          className="bg-bw-green hover:bg-bw-green-hover"
          data-testid="request-leave-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Request Leave
        </Button>
      </div>

      {/* Leave Balance */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-amber-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <Sun className="h-5 w-5 text-amber-400" />
              </div>
              <Badge variant="outline" className="text-xs text-slate-400">Casual</Badge>
            </div>
            <p className="text-3xl font-bold text-white">{(balance.casual || 12) - (used.casual || 0)}</p>
            <p className="text-xs text-slate-500 mt-1">of {balance.casual || 12} days</p>
            <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-amber-500 rounded-full"
                style={{ width: `${((balance.casual || 12) - (used.casual || 0)) / (balance.casual || 12) * 100}%` }}
              />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-rose-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-rose-500/10">
                <Heart className="h-5 w-5 text-rose-400" />
              </div>
              <Badge variant="outline" className="text-xs text-slate-400">Sick</Badge>
            </div>
            <p className="text-3xl font-bold text-white">{(balance.sick || 12) - (used.sick || 0)}</p>
            <p className="text-xs text-slate-500 mt-1">of {balance.sick || 12} days</p>
            <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-rose-500 rounded-full"
                style={{ width: `${((balance.sick || 12) - (used.sick || 0)) / (balance.sick || 12) * 100}%` }}
              />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-blue-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Umbrella className="h-5 w-5 text-blue-400" />
              </div>
              <Badge variant="outline" className="text-xs text-slate-400">Earned</Badge>
            </div>
            <p className="text-3xl font-bold text-white">{(balance.earned || 15) - (used.earned || 0)}</p>
            <p className="text-xs text-slate-500 mt-1">of {balance.earned || 15} days</p>
            <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${((balance.earned || 15) - (used.earned || 0)) / (balance.earned || 15) * 100}%` }}
              />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800 hover:border-purple-500/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-bw-purple/[0.08]0/10">
                <Plane className="h-5 w-5 text-purple-400" />
              </div>
              <Badge variant="outline" className="text-xs text-slate-400">Total Used</Badge>
            </div>
            <p className="text-3xl font-bold text-white">
              {(used.casual || 0) + (used.sick || 0) + (used.earned || 0)}
            </p>
            <p className="text-xs text-slate-500 mt-1">days this year</p>
          </CardContent>
        </Card>
      </div>

      {/* Leave Requests */}
      <Card className="bg-slate-900/50 border-white/[0.07] border-800">
        <CardHeader>
          <CardTitle className="text-white">Leave Requests</CardTitle>
          <CardDescription>Your leave request history</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-green-500" />
            </div>
          ) : leaveData.requests.length === 0 ? (
            <div className="py-12 text-center">
              <CalendarIcon className="h-12 w-12 mx-auto text-slate-600 mb-3" />
              <p className="text-slate-400">No leave requests found</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {leaveData.requests.map((request) => {
                const LeaveIcon = leaveTypeIcons[request.leave_type] || CalendarIcon;
                return (
                  <div 
                    key={request.leave_id} 
                    className="flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
                    data-testid={`leave-row-${request.leave_id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2.5 rounded-xl ${
                        request.leave_type === 'casual' ? 'bg-amber-500/10' :
                        request.leave_type === 'sick' ? 'bg-rose-500/10' :
                        'bg-blue-500/10'
                      }`}>
                        <LeaveIcon className={`h-5 w-5 ${
                          request.leave_type === 'casual' ? 'text-amber-400' :
                          request.leave_type === 'sick' ? 'text-rose-400' :
                          'text-blue-400'
                        }`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={statusColors[request.status]}>
                            {request.status}
                          </Badge>
                          <span className="text-sm text-slate-400 capitalize">{request.leave_type} Leave</span>
                        </div>
                        <p className="text-sm text-white">{request.reason}</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-white font-medium">
                        {formatDate(request.start_date)} - {formatDate(request.end_date)}
                      </p>
                      <p className="text-sm text-slate-400">{request.days} day(s)</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Request Leave Dialog */}
      <Dialog open={showRequestDialog} onOpenChange={setShowRequestDialog}>
        <DialogContent className="bg-slate-900 border-white/[0.07] border-800">
          <DialogHeader>
            <DialogTitle className="text-white">Request Leave</DialogTitle>
            <DialogDescription>Submit a new leave request</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Leave Type</Label>
              <Select 
                value={formData.leave_type}
                onValueChange={(value) => setFormData(prev => ({ ...prev, leave_type: value }))}
              >
                <SelectTrigger className="bg-slate-800/50 border-white/[0.07] border-700">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="casual">Casual Leave</SelectItem>
                  <SelectItem value="sick">Sick Leave</SelectItem>
                  <SelectItem value="earned">Earned Leave</SelectItem>
                  <SelectItem value="unpaid">Unpaid Leave</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-slate-300">Start Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start border-white/[0.07] border-700 bg-slate-800/50">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      {startDate ? format(startDate, "MMM dd, yyyy") : "Select date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="single"
                      selected={startDate}
                      onSelect={setStartDate}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
              
              <div className="space-y-2">
                <Label className="text-slate-300">End Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start border-white/[0.07] border-700 bg-slate-800/50">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      {endDate ? format(endDate, "MMM dd, yyyy") : "Select date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="single"
                      selected={endDate}
                      onSelect={setEndDate}
                      disabled={(date) => startDate && date < startDate}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-slate-300">Reason</Label>
              <Textarea
                placeholder="Reason for leave..."
                className="bg-slate-800/50 border-white/[0.07] border-700 min-h-[100px]"
                value={formData.reason}
                onChange={(e) => setFormData(prev => ({ ...prev, reason: e.target.value }))}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRequestDialog(false)} className="border-white/[0.07] border-700">
              Cancel
            </Button>
            <Button 
              onClick={handleSubmitLeave}
              disabled={submitting}
              className="bg-bw-green hover:bg-bw-green-hover"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              Submit Request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
