import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Users, Clock, CalendarOff, Wallet, ArrowRight, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { API } from "../App";

export default function HRDashboard({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [payrollRecords, setPayrollRecords] = useState([]);
  const orgId = user?.current_organization?.organization_id;

  const headers = {
    Authorization: `Bearer ${localStorage.getItem("token")}`,
    "Content-Type": "application/json",
    ...(orgId ? { "X-Organization-ID": orgId } : {}),
  };

  const now = new Date();
  const currentMonth = now.toLocaleString("en-IN", { month: "long", year: "numeric" });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [empRes, attRes, leaveRes, payRes] = await Promise.allSettled([
        fetch(`${API}/hr/employees?per_page=200`, { headers }),
        fetch(`${API}/hr/attendance/all?date=${now.toISOString().split("T")[0]}`, { headers }),
        fetch(`${API}/hr/leave/requests?status=pending`, { headers }),
        fetch(`${API}/hr/payroll?month=${now.getMonth() + 1}&year=${now.getFullYear()}`, { headers }),
      ]);

      if (empRes.status === "fulfilled" && empRes.value.ok) {
        const d = await empRes.value.json();
        setEmployees(d.employees || d.data || []);
      }
      if (attRes.status === "fulfilled" && attRes.value.ok) {
        const d = await attRes.value.json();
        setAttendance(d.attendance || d.data || d.records || []);
      }
      if (leaveRes.status === "fulfilled" && leaveRes.value.ok) {
        const d = await leaveRes.value.json();
        setLeaveRequests(d.leave_requests || d.data || d.requests || []);
      }
      if (payRes.status === "fulfilled" && payRes.value.ok) {
        const d = await payRes.value.json();
        setPayrollRecords(d.payroll || d.data || d.records || []);
      }
    } catch (err) {
      toast.error("Failed to load HR data");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleLeaveAction = async (requestId, action) => {
    try {
      const res = await fetch(`${API}/hr/leave/requests/${requestId}/${action}`, {
        method: "POST",
        headers,
      });
      if (!res.ok) throw new Error();
      toast.success(`Leave ${action}d`);
      fetchData();
    } catch {
      toast.error(`Failed to ${action} leave`);
    }
  };

  const totalEmployees = employees.length;
  const presentToday = attendance.filter((a) => a.status === "present" || a.clock_in).length;
  const onLeaveToday = attendance.filter((a) => a.status === "on_leave" || a.leave_type).length;
  const pendingPayroll = payrollRecords.filter((p) => p.status === "pending" || !p.processed_at).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="hr-dashboard-loading">
        <Loader2 className="w-8 h-8 animate-spin text-[#C8FF00]" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="hr-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Human Resources</h1>
          <p className="text-sm text-zinc-500">{currentMonth}</p>
        </div>
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="hr-kpi-strip">
        <KPICard icon={Users} label="Total Employees" value={totalEmployees} color="text-blue-400" testId="kpi-total-employees" />
        <KPICard icon={CheckCircle} label="Present Today" value={presentToday} color="text-emerald-400" testId="kpi-present-today" />
        <KPICard icon={CalendarOff} label="On Leave Today" value={onLeaveToday} color="text-amber-400" testId="kpi-on-leave" />
        <KPICard icon={Wallet} label="Pending Payroll" value={pendingPayroll} color="text-red-400" testId="kpi-pending-payroll" />
      </div>

      {/* Two-column row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Summary */}
        <Card className="bg-zinc-900/60 border-zinc-800" data-testid="hr-attendance-summary">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
              <Clock className="w-4 h-4" /> Attendance Summary (Today)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {attendance.length === 0 ? (
              <p className="text-zinc-500 text-sm text-center py-6">No attendance data for today</p>
            ) : (
              <div className="space-y-2">
                <div className="flex gap-2 mb-4">
                  <StatBar label="Present" value={presentToday} total={totalEmployees} color="bg-emerald-500" />
                  <StatBar label="Absent" value={Math.max(0, totalEmployees - presentToday - onLeaveToday)} total={totalEmployees} color="bg-red-500" />
                  <StatBar label="Leave" value={onLeaveToday} total={totalEmployees} color="bg-amber-500" />
                </div>
                <div className="max-h-[200px] overflow-y-auto space-y-1">
                  {attendance.slice(0, 10).map((a, i) => (
                    <div key={i} className="flex justify-between items-center text-sm py-1 border-b border-zinc-800/50">
                      <span className="text-zinc-300">{a.employee_name || a.user_name || `Employee ${i + 1}`}</span>
                      <Badge variant="outline" className={`text-xs ${a.status === "present" || a.clock_in ? "text-emerald-400 border-emerald-400/30" : "text-red-400 border-red-400/30"}`}>
                        {a.status || (a.clock_in ? "Present" : "Absent")}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Leave Requests */}
        <Card className="bg-zinc-900/60 border-zinc-800" data-testid="hr-leave-requests">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
              <CalendarOff className="w-4 h-4" /> Pending Leave Requests
            </CardTitle>
          </CardHeader>
          <CardContent>
            {leaveRequests.length === 0 ? (
              <p className="text-zinc-500 text-sm text-center py-6">No pending leave requests</p>
            ) : (
              <div className="space-y-3 max-h-[250px] overflow-y-auto">
                {leaveRequests.map((lr, i) => (
                  <div key={lr.request_id || i} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg" data-testid={`leave-request-${i}`}>
                    <div>
                      <p className="text-sm text-zinc-200 font-medium">{lr.employee_name || "Employee"}</p>
                      <p className="text-xs text-zinc-500">{lr.leave_type} · {lr.start_date} to {lr.end_date}</p>
                    </div>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" className="text-emerald-400 hover:bg-emerald-500/10 h-7 px-2" onClick={() => handleLeaveAction(lr.request_id, "approve")} data-testid={`approve-leave-${i}`}>
                        <CheckCircle className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-400 hover:bg-red-500/10 h-7 px-2" onClick={() => handleLeaveAction(lr.request_id, "reject")} data-testid={`reject-leave-${i}`}>
                        <XCircle className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Payroll Status */}
      <Card className="bg-zinc-900/60 border-zinc-800" data-testid="hr-payroll-status">
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-medium text-zinc-300 flex items-center gap-2">
            <Wallet className="w-4 h-4" /> Payroll Status — {currentMonth}
          </CardTitle>
          <Button size="sm" variant="outline" className="text-xs" onClick={() => navigate("/payroll")} data-testid="run-payroll-btn">
            Run Payroll <ArrowRight className="w-3 h-3 ml-1" />
          </Button>
        </CardHeader>
        <CardContent>
          {employees.length === 0 ? (
            <p className="text-zinc-500 text-sm text-center py-4">No employees found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="payroll-table">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-500 text-xs">
                    <th className="text-left py-2 font-medium">Employee</th>
                    <th className="text-left py-2 font-medium">Department</th>
                    <th className="text-right py-2 font-medium">Salary</th>
                    <th className="text-center py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.slice(0, 15).map((emp, i) => {
                    const payRecord = payrollRecords.find((p) => p.employee_id === emp.employee_id);
                    const processed = payRecord?.processed_at || payRecord?.status === "processed";
                    return (
                      <tr key={emp.employee_id || i} className="border-b border-zinc-800/30">
                        <td className="py-2 text-zinc-200">{emp.full_name || emp.name || "—"}</td>
                        <td className="py-2 text-zinc-400">{emp.department || "—"}</td>
                        <td className="py-2 text-zinc-200 text-right font-mono">{emp.salary ? `₹${Number(emp.salary).toLocaleString("en-IN")}` : "—"}</td>
                        <td className="py-2 text-center">
                          <Badge variant="outline" className={`text-xs ${processed ? "text-emerald-400 border-emerald-400/30" : "text-amber-400 border-amber-400/30"}`}>
                            {processed ? "Processed" : "Pending"}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="hr-quick-links">
        <QuickLink label="Add Employee" onClick={() => navigate("/employees")} icon={Users} testId="ql-add-employee" />
        <QuickLink label="Mark Attendance" onClick={() => navigate("/attendance")} icon={Clock} testId="ql-attendance" />
        <QuickLink label="View Payslips" onClick={() => navigate("/payroll")} icon={Wallet} testId="ql-payslips" />
        <QuickLink label="All Employees" onClick={() => navigate("/employees")} icon={Users} testId="ql-employees" />
      </div>
    </div>
  );
}

function KPICard({ icon: Icon, label, value, color, testId }) {
  return (
    <Card className="bg-zinc-900/60 border-zinc-800" data-testid={testId}>
      <CardContent className="p-4 flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-zinc-800 ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-zinc-100 font-mono">{value}</p>
          <p className="text-xs text-zinc-500">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function StatBar({ label, value, total, color }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex-1 text-center">
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden mb-1">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-zinc-400">{label}: {value}</p>
    </div>
  );
}

function QuickLink({ label, onClick, icon: Icon, testId }) {
  return (
    <Button variant="outline" className="justify-start gap-2 h-auto py-3 text-zinc-300 hover:text-[#C8FF00] border-zinc-800 hover:border-[#C8FF00]/30" onClick={onClick} data-testid={testId}>
      <Icon className="w-4 h-4" /> {label}
    </Button>
  );
}
