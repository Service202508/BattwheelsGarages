import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { 
  Clock, LogIn, LogOut, Calendar, Users, TrendingUp, 
  AlertTriangle, CheckCircle2, XCircle, Timer, Coffee
} from "lucide-react";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

export default function Attendance({ user }) {
  const [todayAttendance, setTodayAttendance] = useState(null);
  const [myRecords, setMyRecords] = useState(null);
  const [teamData, setTeamData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clockingIn, setClockingIn] = useState(false);
  const [clockingOut, setClockingOut] = useState(false);
  const [showClockOutDialog, setShowClockOutDialog] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [currentTime, setCurrentTime] = useState(new Date());

  // Clock-out form state
  const initialClockOutData = { breakMinutes: 60, remarks: "" };
  const [clockOutForm, setClockOutForm] = useState(initialClockOutData);

  // Auto-save for Clock Out form
  const clockOutPersistence = useFormPersistence(
    'attendance_clock_out',
    clockOutForm,
    initialClockOutData,
    {
      enabled: showClockOutDialog,
      isDialogOpen: showClockOutDialog,
      setFormData: setClockOutForm,
      debounceMs: 2000,
      entityName: 'Clock Out'
    }
  );

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchTodayAttendance = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/attendance/today`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setTodayAttendance(data);
      }
    } catch (error) {
      console.error("Failed to fetch today's attendance:", error);
    }
  }, []);

  const fetchMyRecords = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API}/attendance/my-records?month=${selectedMonth}&year=${selectedYear}`,
        {
          credentials: "include",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      if (response.ok) {
        const data = await response.json();
        setMyRecords(data);
      }
    } catch (error) {
      console.error("Failed to fetch records:", error);
    }
  }, [selectedMonth, selectedYear]);

  const fetchTeamData = useCallback(async () => {
    if (user?.role !== "admin") return;
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API}/attendance/team-summary?month=${selectedMonth}&year=${selectedYear}`,
        {
          credentials: "include",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      if (response.ok) {
        const data = await response.json();
        setTeamData(data);
      }
    } catch (error) {
      console.error("Failed to fetch team data:", error);
    }
  }, [user?.role, selectedMonth, selectedYear]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTodayAttendance(), fetchMyRecords(), fetchTeamData()]);
      setLoading(false);
    };
    loadData();
  }, [fetchTodayAttendance, fetchMyRecords, fetchTeamData]);

  const handleClockIn = async () => {
    setClockingIn(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/attendance/clock-in`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ remarks: clockOutForm.remarks, location: "Office" }),
      });

      const data = await response.json();
      if (response.ok) {
        toast.success("Clocked in successfully!");
        if (data.late_arrival) {
          toast.warning(`You are ${data.late_by_minutes} minutes late`);
        }
        fetchTodayAttendance();
        fetchMyRecords();
      } else {
        toast.error(data.detail || "Failed to clock in");
      }
    } catch (error) {
      toast.error("Error clocking in");
    } finally {
      setClockingIn(false);
    }
  };

  const handleClockOut = async () => {
    setClockingOut(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/attendance/clock-out`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ break_minutes: clockOutForm.breakMinutes, remarks: clockOutForm.remarks }),
      });

      const data = await response.json();
      if (response.ok) {
        toast.success(`Clocked out! Total hours: ${data.total_hours}`);
        if (data.warnings) {
          data.warnings.forEach(w => toast.warning(w));
        }
        clockOutPersistence.onSuccessfulSave();
        setShowClockOutDialog(false);
        setClockOutForm(initialClockOutData);
        fetchTodayAttendance();
        fetchMyRecords();
      } else {
        toast.error(data.detail || "Failed to clock out");
      }
    } catch (error) {
      toast.error("Error clocking out");
    } finally {
      setClockingOut(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return "-";
    return new Date(isoString).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status) => {
    const styles = {
      present: "badge-success",
      half_day: "bg-bw-amber/10",
      absent: "bg-bw-red/10",
      on_leave: "bg-blue-500",
      short_day: "bg-bw-orange/10",
    };
    return <Badge className={styles[status] || "badge-muted"}>{status?.replace("_", " ")}</Badge>;
  };

  const isClockedIn = todayAttendance?.attendance?.clock_in && !todayAttendance?.attendance?.clock_out;
  const isClockedOut = todayAttendance?.attendance?.clock_out;

  return (
    <div className="space-y-6" data-testid="attendance-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Attendance</h1>
          <p className="text-muted-foreground">Track your daily attendance and productivity.</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-mono font-bold">{currentTime.toLocaleTimeString("en-IN")}</p>
          <p className="text-muted-foreground">{currentTime.toLocaleDateString("en-IN", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
      </div>

      {/* Clock In/Out Card */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Today's Attendance
          </CardTitle>
          <CardDescription>
            Standard hours: {todayAttendance?.standard_start} - {todayAttendance?.standard_end} ({todayAttendance?.standard_hours} hrs)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-center gap-6">
            {/* Status */}
            <div className="flex-1 space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <LogIn className="h-6 w-6 mx-auto mb-2 text-green-500" />
                  <p className="text-sm text-muted-foreground">Clock In</p>
                  <p className="text-lg font-bold">{formatTime(todayAttendance?.attendance?.clock_in)}</p>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <LogOut className="h-6 w-6 mx-auto mb-2 text-red-500" />
                  <p className="text-sm text-muted-foreground">Clock Out</p>
                  <p className="text-lg font-bold">{formatTime(todayAttendance?.attendance?.clock_out)}</p>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <Timer className="h-6 w-6 mx-auto mb-2 text-blue-500" />
                  <p className="text-sm text-muted-foreground">Hours Worked</p>
                  <p className="text-lg font-bold">{todayAttendance?.attendance?.total_hours || 0}</p>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <TrendingUp className="h-6 w-6 mx-auto mb-2 text-purple-500" />
                  <p className="text-sm text-muted-foreground">Overtime</p>
                  <p className="text-lg font-bold">{todayAttendance?.attendance?.overtime_hours || 0}</p>
                </div>
              </div>

              {/* Warnings */}
              {todayAttendance?.attendance?.late_arrival && (
                <div className="flex items-center gap-2 p-3 bg-bw-amber/10 text-yellow-500 rounded-lg">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">Late arrival recorded</span>
                </div>
              )}
              {todayAttendance?.attendance?.early_departure && (
                <div className="flex items-center gap-2 p-3 bg-bw-orange/10 text-orange-500 rounded-lg">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">Early departure recorded</span>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3">
              {!isClockedIn && !isClockedOut && (
                <Button 
                  size="lg" 
                  className="min-w-[150px]"
                  onClick={handleClockIn}
                  disabled={clockingIn}
                  data-testid="clock-in-btn"
                >
                  <LogIn className="mr-2 h-5 w-5" />
                  {clockingIn ? "Clocking In..." : "Clock In"}
                </Button>
              )}
              {isClockedIn && (
                <Button 
                  size="lg" 
                  variant="destructive"
                  className="min-w-[150px]"
                  onClick={() => setShowClockOutDialog(true)}
                  data-testid="clock-out-btn"
                >
                  <LogOut className="mr-2 h-5 w-5" />
                  Clock Out
                </Button>
              )}
              {isClockedOut && (
                <div className="text-center p-4 bg-bw-green/10 rounded-lg">
                  <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  <p className="text-green-500 font-medium">Day Complete</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for Records */}
      <Tabs defaultValue="my-records">
        <TabsList>
          <TabsTrigger value="my-records">My Records</TabsTrigger>
          {user?.role === "admin" && (
            <TabsTrigger value="team">Team Overview</TabsTrigger>
          )}
        </TabsList>

        {/* My Records Tab */}
        <TabsContent value="my-records" className="space-y-4">
          {/* Month Selector */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4 items-center">
                <div className="flex gap-2 items-center">
                  <Label>Month:</Label>
                  <Select value={String(selectedMonth)} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
                    <SelectTrigger className="w-[130px]"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((m, i) => (
                        <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex gap-2 items-center">
                  <Label>Year:</Label>
                  <Select value={String(selectedYear)} onValueChange={(v) => setSelectedYear(parseInt(v))}>
                    <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {[2024, 2025, 2026].map((y) => (
                        <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Summary Cards */}
          {myRecords?.summary && (
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Attendance %</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{myRecords.summary.attendance_percentage}%</div>
                  <Progress value={myRecords.summary.attendance_percentage} className="mt-2" />
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Productivity %</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{myRecords.summary.productivity_percentage}%</div>
                  <Progress value={myRecords.summary.productivity_percentage} className="mt-2" />
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Total Hours</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{myRecords.summary.total_hours}</div>
                  <p className="text-xs text-muted-foreground">Expected: {myRecords.summary.expected_hours}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Overtime</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{myRecords.summary.overtime_hours}</div>
                  <p className="text-xs text-muted-foreground">hours extra</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Attendance Stats */}
          {myRecords?.summary && (
            <div className="grid gap-4 md:grid-cols-6">
              <Card className="text-center p-4">
                <p className="text-2xl font-bold text-green-500">{myRecords.summary.present_days}</p>
                <p className="text-xs text-muted-foreground">Present</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-2xl font-bold text-yellow-500">{myRecords.summary.half_days}</p>
                <p className="text-xs text-muted-foreground">Half Days</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-2xl font-bold text-red-500">{myRecords.summary.absent_days}</p>
                <p className="text-xs text-muted-foreground">Absent</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-2xl font-bold text-blue-500">{myRecords.summary.leave_days}</p>
                <p className="text-xs text-muted-foreground">On Leave</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-2xl font-bold text-orange-500">{myRecords.summary.late_arrivals}</p>
                <p className="text-xs text-muted-foreground">Late Arrivals</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-2xl font-bold text-purple-500">{myRecords.summary.early_departures}</p>
                <p className="text-xs text-muted-foreground">Early Departures</p>
              </Card>
            </div>
          )}

          {/* Records Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Clock In</TableHead>
                    <TableHead>Clock Out</TableHead>
                    <TableHead>Hours</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Flags</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {myRecords?.records?.map((record) => (
                    <TableRow key={record.attendance_id}>
                      <TableCell className="font-medium">{record.date}</TableCell>
                      <TableCell>{formatTime(record.clock_in)}</TableCell>
                      <TableCell>{formatTime(record.clock_out)}</TableCell>
                      <TableCell>{record.total_hours || 0}</TableCell>
                      <TableCell>{getStatusBadge(record.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {record.late_arrival && (
                            <Badge variant="outline" className="text-yellow-500 border-yellow-500">Late</Badge>
                          )}
                          {record.early_departure && (
                            <Badge variant="outline" className="text-orange-500 border-orange-500">Early</Badge>
                          )}
                          {record.overtime_hours > 0 && (
                            <Badge variant="outline" className="text-green-500 border-green-500">OT</Badge>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Team Tab (Admin Only) */}
        {user?.role === "admin" && (
          <TabsContent value="team" className="space-y-4">
            {teamData && (
              <>
                {/* Team Averages */}
                <div className="grid gap-4 md:grid-cols-3">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Team Avg Attendance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{teamData.averages.avg_attendance}%</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Team Avg Productivity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{teamData.averages.avg_productivity}%</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Total Team Overtime</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{teamData.averages.total_overtime} hrs</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Team Table */}
                <Card>
                  <CardHeader>
                    <CardTitle>Team Performance</CardTitle>
                    <CardDescription>Ranked by productivity</CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>#</TableHead>
                          <TableHead>Employee</TableHead>
                          <TableHead>Days Present</TableHead>
                          <TableHead>Total Hours</TableHead>
                          <TableHead>Overtime</TableHead>
                          <TableHead>Late</TableHead>
                          <TableHead>Attendance %</TableHead>
                          <TableHead>Productivity %</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {teamData.team_stats.map((stat, idx) => (
                          <TableRow key={stat.user_id}>
                            <TableCell>{idx + 1}</TableCell>
                            <TableCell>
                              <div>
                                <p className="font-medium">{stat.name}</p>
                                <p className="text-xs text-muted-foreground">{stat.designation || stat.role}</p>
                              </div>
                            </TableCell>
                            <TableCell>{stat.days_present}</TableCell>
                            <TableCell>{stat.total_hours}</TableCell>
                            <TableCell>{stat.overtime_hours}</TableCell>
                            <TableCell>{stat.late_arrivals}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Progress value={stat.attendance_percentage} className="w-16 h-2" />
                                <span className="text-sm">{stat.attendance_percentage}%</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Progress 
                                  value={stat.productivity_percentage} 
                                  className={`w-16 h-2 ${stat.productivity_percentage >= 100 ? 'bg-bw-green' : ''}`} 
                                />
                                <span className="text-sm font-medium">{stat.productivity_percentage}%</span>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>
        )}
      </Tabs>

      {/* Clock Out Dialog */}
      <Dialog 
        open={showClockOutDialog} 
        onOpenChange={(open) => {
          if (!open && clockOutPersistence.isDirty) {
            clockOutPersistence.setShowCloseConfirm(true);
          } else {
            if (!open) clockOutPersistence.clearSavedData();
            setShowClockOutDialog(open);
          }
        }}
      >
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>Clock Out</DialogTitle>
              <AutoSaveIndicator 
                lastSaved={clockOutPersistence.lastSaved} 
                isSaving={clockOutPersistence.isSaving} 
                isDirty={clockOutPersistence.isDirty} 
              />
            </div>
          </DialogHeader>
          
          <DraftRecoveryBanner
            show={clockOutPersistence.showRecoveryBanner}
            savedAt={clockOutPersistence.savedDraftInfo?.timestamp}
            onRestore={clockOutPersistence.handleRestoreDraft}
            onDiscard={clockOutPersistence.handleDiscardDraft}
          />
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Break Duration (minutes)</Label>
              <div className="flex gap-2">
                {[30, 45, 60, 90].map((mins) => (
                  <Button
                    key={mins}
                    variant={clockOutForm.breakMinutes === mins ? "default" : "outline"}
                    size="sm"
                    onClick={() => setClockOutForm({...clockOutForm, breakMinutes: mins})}
                  >
                    <Coffee className="mr-1 h-3 w-3" />
                    {mins}m
                  </Button>
                ))}
              </div>
              <Input
                type="number"
                value={clockOutForm.breakMinutes}
                onChange={(e) => setClockOutForm({...clockOutForm, breakMinutes: parseInt(e.target.value) || 0})}
                placeholder="Custom minutes"
              />
            </div>
            <div className="space-y-2">
              <Label>Remarks (optional)</Label>
              <Textarea
                value={clockOutForm.remarks}
                onChange={(e) => setClockOutForm({...clockOutForm, remarks: e.target.value})}
                placeholder="Any notes for today..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                if (clockOutPersistence.isDirty) {
                  clockOutPersistence.setShowCloseConfirm(true);
                } else {
                  setShowClockOutDialog(false);
                }
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleClockOut} disabled={clockingOut}>
              {clockingOut ? "Processing..." : "Confirm Clock Out"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Unsaved Changes Confirmation Dialog */}
      <FormCloseConfirmDialog
        open={clockOutPersistence.showCloseConfirm}
        onClose={() => clockOutPersistence.setShowCloseConfirm(false)}
        onSave={handleClockOut}
        onDiscard={() => {
          clockOutPersistence.clearSavedData();
          setClockOutForm(initialClockOutData);
          setShowClockOutDialog(false);
        }}
        isSaving={clockingOut}
        entityName="Clock Out"
      />
    </div>
  );
}
