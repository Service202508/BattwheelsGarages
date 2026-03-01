import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Calendar } from "@/components/ui/calendar";
import { toast } from "sonner";
import {
  Clock, Play, Square, Loader2, Calendar as CalendarIcon,
  CheckCircle, AlertCircle, Coffee, Sun, ChevronLeft, ChevronRight
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  present: "bg-bw-volt/[0.08]0/20 text-bw-volt text-400 border-bw-volt/50/30",
  absent: "bg-bw-red/[0.08]0/20 text-red-400 border-red-500/30",
  late: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  half_day: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  leave: "bg-bw-purple/[0.08]0/20 text-purple-400 border-purple-500/30",
};

const statusIcons = {
  present: CheckCircle,
  absent: AlertCircle,
  late: Clock,
  half_day: Coffee,
  leave: Sun,
};

export default function TechnicianAttendance({ user }) {
  const [attendanceData, setAttendanceData] = useState({ records: [], summary: {} });
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [todayStatus, setTodayStatus] = useState(null);
  const [showCheckDialog, setShowCheckDialog] = useState(false);
  const [checkType, setCheckType] = useState(null);
  const [checkingIn, setCheckingIn] = useState(false);

  useEffect(() => {
    fetchAttendance();
    fetchTodayStatus();
  }, [month, year]);

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/technician/attendance?month=${month}&year=${year}`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setAttendanceData(data);
      }
    } catch (error) {
      console.error("Failed to fetch attendance:", error);
      toast.error("Failed to load attendance");
    } finally {
      setLoading(false);
    }
  };

  const fetchTodayStatus = async () => {
    try {
      const res = await fetch(`${API}/technician/dashboard`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setTodayStatus(data.attendance);
      }
    } catch (error) {
      console.error("Failed to fetch today's status:", error);
    }
  };

  const handleCheckInOut = async (type) => {
    setCheckingIn(true);
    try {
      const endpoint = type === 'in' ? 'check-in' : 'check-out';
      const res = await fetch(`${API}/technician/attendance/${endpoint}`, {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include"
      });
      
      if (res.ok) {
        toast.success(type === 'in' ? "Checked in successfully!" : "Checked out successfully!");
        setShowCheckDialog(false);
        fetchAttendance();
        fetchTodayStatus();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to record attendance");
      }
    } catch (error) {
      toast.error("Failed to record attendance");
    } finally {
      setCheckingIn(false);
    }
  };

  const navigateMonth = (direction) => {
    if (direction === 'prev') {
      if (month === 1) {
        setMonth(12);
        setYear(year - 1);
      } else {
        setMonth(month - 1);
      }
    } else {
      if (month === 12) {
        setMonth(1);
        setYear(year + 1);
      } else {
        setMonth(month + 1);
      }
    }
  };

  const getMonthName = (m) => {
    return new Date(2000, m - 1, 1).toLocaleDateString('en-US', { month: 'long' });
  };

  const canCheckIn = !todayStatus?.check_in;
  const canCheckOut = todayStatus?.check_in && !todayStatus?.check_out;

  const { summary } = attendanceData;

  return (
    <div className="space-y-6" data-testid="technician-attendance">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Attendance</h1>
          <p className="text-slate-400">Track your daily attendance</p>
        </div>
        <div className="flex items-center gap-3">
          {canCheckIn && (
            <Button 
              onClick={() => { setCheckType('in'); setShowCheckDialog(true); }}
              className="bg-bw-green hover:bg-bw-green-hover"
              data-testid="check-in-btn"
            >
              <Play className="h-4 w-4 mr-2" />
              Check In
            </Button>
          )}
          {canCheckOut && (
            <Button 
              onClick={() => { setCheckType('out'); setShowCheckDialog(true); }}
              variant="outline"
              className="border-red-500/30 text-red-400 hover:bg-bw-red/[0.08]0/10"
              data-testid="check-out-btn"
            >
              <Square className="h-4 w-4 mr-2" />
              Check Out
            </Button>
          )}
        </div>
      </div>

      {/* Today's Status */}
      {todayStatus && (
        <Card className="bg-gradient-to-br from-green-500/20 via-emerald-500/10 to-slate-900 border border-green-500/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Today's Status</p>
                <div className="flex items-center gap-3 mt-2">
                  {todayStatus.check_in ? (
                    <>
                      <Badge className={statusColors[todayStatus.today || 'present']}>
                        {todayStatus.today || 'Present'}
                      </Badge>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-white/[0.07] border-700">
                          <Clock className="h-4 w-4 text-green-400" />
                          <span className="text-slate-300">In: {todayStatus.check_in}</span>
                        </div>
                        {todayStatus.check_out && (
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-white/[0.07] border-700">
                            <Clock className="h-4 w-4 text-red-400" />
                            <span className="text-slate-300">Out: {todayStatus.check_out}</span>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <span className="text-slate-400">Not checked in yet</span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-white">{new Date().getDate()}</p>
                <p className="text-slate-400">{new Date().toLocaleDateString('en-US', { weekday: 'long' })}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Present</p>
                <p className="text-2xl font-bold text-bw-volt text-400 mt-1">{summary.present || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-bw-volt/[0.08]0/10">
                <CheckCircle className="h-5 w-5 text-bw-volt text-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Absent</p>
                <p className="text-2xl font-bold text-red-400 mt-1">{summary.absent || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-bw-red/[0.08]0/10">
                <AlertCircle className="h-5 w-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Late</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">{summary.late || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-amber-500/10">
                <Clock className="h-5 w-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Half Day</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">{summary.half_day || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-blue-500/10">
                <Coffee className="h-5 w-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Month Navigation */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigateMonth('prev')} className="text-slate-400">
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>
        <h3 className="text-lg font-semibold text-white">
          {getMonthName(month)} {year}
        </h3>
        <Button variant="ghost" onClick={() => navigateMonth('next')} className="text-slate-400">
          Next
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>

      {/* Attendance Records */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-green-500" />
        </div>
      ) : (
        <Card className="bg-slate-900/50 border-white/[0.07] border-800">
          <CardContent className="p-0">
            <div className="divide-y divide-slate-800">
              {attendanceData.records.length === 0 ? (
                <div className="py-12 text-center">
                  <CalendarIcon className="h-12 w-12 mx-auto text-slate-600 mb-3" />
                  <p className="text-slate-400">No attendance records for this month</p>
                </div>
              ) : (
                attendanceData.records.map((record) => {
                  const StatusIcon = statusIcons[record.status] || Clock;
                  return (
                    <div 
                      key={record.date} 
                      className="flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
                      data-testid={`attendance-row-${record.date}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="text-center w-16">
                          <p className="text-2xl font-bold text-white">
                            {new Date(record.date).getDate()}
                          </p>
                          <p className="text-xs text-slate-500">
                            {new Date(record.date).toLocaleDateString('en-US', { weekday: 'short' })}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${record.status === 'present' ? 'bg-bw-volt/[0.08]0/10' : 
                            record.status === 'absent' ? 'bg-bw-red/[0.08]0/10' : 
                            record.status === 'late' ? 'bg-amber-500/10' : 'bg-blue-500/10'}`}>
                            <StatusIcon className={`h-5 w-5 ${record.status === 'present' ? 'text-bw-volt text-400' : 
                              record.status === 'absent' ? 'text-red-400' : 
                              record.status === 'late' ? 'text-amber-400' : 'text-blue-400'}`} />
                          </div>
                          <Badge className={statusColors[record.status]}>
                            {record.status?.replace('_', ' ')}
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6 text-sm">
                        {record.check_in && (
                          <div className="text-slate-400">
                            <span className="text-slate-500">In:</span>{' '}
                            <span className="text-white font-medium">{record.check_in}</span>
                          </div>
                        )}
                        {record.check_out && (
                          <div className="text-slate-400">
                            <span className="text-slate-500">Out:</span>{' '}
                            <span className="text-white font-medium">{record.check_out}</span>
                          </div>
                        )}
                        {record.working_hours && (
                          <div className="text-bw-volt text-400 font-medium">
                            {record.working_hours}h
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Check In/Out Dialog */}
      <Dialog open={showCheckDialog} onOpenChange={setShowCheckDialog}>
        <DialogContent className="bg-slate-900 border-white/[0.07] border-800">
          <DialogHeader>
            <DialogTitle className="text-white">
              {checkType === 'in' ? 'Check In' : 'Check Out'} Confirmation
            </DialogTitle>
          </DialogHeader>
          <div className="py-4 text-center">
            <div className={`inline-flex p-4 rounded-full ${checkType === 'in' ? 'bg-bw-green/[0.08]0/20' : 'bg-bw-red/[0.08]0/20'} mb-4`}>
              {checkType === 'in' ? (
                <Play className="h-8 w-8 text-green-400" />
              ) : (
                <Square className="h-8 w-8 text-red-400" />
              )}
            </div>
            <p className="text-slate-300">
              {checkType === 'in' 
                ? 'Start your work day by checking in.' 
                : 'End your work day by checking out.'}
            </p>
            <p className="text-sm text-slate-500 mt-2">
              Current time: {new Date().toLocaleTimeString()}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCheckDialog(false)} className="border-white/[0.07] border-700">
              Cancel
            </Button>
            <Button 
              onClick={() => handleCheckInOut(checkType)}
              disabled={checkingIn}
              className={checkType === 'in' ? 'bg-bw-green hover:bg-bw-green-hover' : 'bg-red-600 hover:bg-red-700'}
            >
              {checkingIn ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              {checkType === 'in' ? 'Check In' : 'Check Out'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
