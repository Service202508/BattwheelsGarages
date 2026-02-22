import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { 
  DollarSign, Users, Calculator, TrendingUp, 
  Download, Clock, AlertTriangle, CheckCircle2, Save
} from "lucide-react";
import { API } from "@/App";

export default function Payroll({ user }) {
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [myPayroll, setMyPayroll] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchData();
  }, [selectedMonth, selectedYear]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      
      // Fetch my payroll
      const myResponse = await fetch(`${API}/payroll/my-records`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (myResponse.ok) {
        const data = await myResponse.json();
        setMyPayroll(data);
      }

      // Fetch all payroll (admin only)
      if (user?.role === "admin") {
        const allResponse = await fetch(
          `${API}/payroll/records?month=${selectedMonth}&year=${selectedYear}`,
          {
            credentials: "include",
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          }
        );
        if (allResponse.ok) {
          const data = await allResponse.json();
          setPayrollRecords(data);
        }
      }
    } catch (error) {
      console.error("Failed to fetch payroll:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePayroll = async () => {
    setGenerating(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API}/payroll/generate?month=${selectedMonth}&year=${selectedYear}`,
        {
          method: "POST",
          credentials: "include",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        fetchData();
      } else {
        toast.error("Failed to generate payroll");
      }
    } catch (error) {
      toast.error("Error generating payroll");
    } finally {
      setGenerating(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getProductivityBadge = (pct) => {
    if (pct >= 100) return <Badge className="badge-success">{pct}%</Badge>;
    if (pct >= 80) return <Badge className="bg-yellow-500">{pct}%</Badge>;
    return <Badge className="bg-red-500">{pct}%</Badge>;
  };

  const totalNetSalary = payrollRecords.reduce((sum, r) => sum + r.net_salary, 0);
  const totalOvertime = payrollRecords.reduce((sum, r) => sum + r.overtime_pay, 0);
  const avgProductivity = payrollRecords.length > 0
    ? (payrollRecords.reduce((sum, r) => sum + r.productivity_score, 0) / payrollRecords.length).toFixed(1)
    : 0;

  return (
    <div className="space-y-6" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Payroll</h1>
          <p className="text-muted-foreground">Process payroll based on attendance and productivity.</p>
        </div>
        {user?.role === "admin" && (
          <Button 
            onClick={handleGeneratePayroll} 
            disabled={generating}
            data-testid="generate-payroll-btn"
          >
            <Calculator className="mr-2 h-4 w-4" />
            {generating ? "Generating..." : "Generate Payroll"}
          </Button>
        )}
      </div>

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

      <Tabs defaultValue={user?.role === "admin" ? "all" : "my-payroll"}>
        <TabsList>
          {user?.role === "admin" && <TabsTrigger value="all">All Employees</TabsTrigger>}
          <TabsTrigger value="my-payroll">My Payslips</TabsTrigger>
        </TabsList>

        {/* All Employees (Admin) */}
        {user?.role === "admin" && (
          <TabsContent value="all" className="space-y-4">
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Total Net Salary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrency(totalNetSalary)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Total Overtime Pay</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrency(totalOvertime)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Employees</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{payrollRecords.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Avg Productivity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{avgProductivity}%</div>
                </CardContent>
              </Card>
            </div>

            {/* Payroll Table */}
            <Card>
              <CardHeader>
                <CardTitle>Payroll Summary - {["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][selectedMonth]} {selectedYear}</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {payrollRecords.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
                    <Calculator className="h-12 w-12 mb-4 opacity-50" />
                    <p>No payroll data. Click "Generate Payroll" to calculate.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Employee</TableHead>
                        <TableHead>Working Days</TableHead>
                        <TableHead>Present</TableHead>
                        <TableHead>Hours</TableHead>
                        <TableHead>Attendance %</TableHead>
                        <TableHead>Productivity</TableHead>
                        <TableHead>Base Salary</TableHead>
                        <TableHead>Overtime</TableHead>
                        <TableHead>Deductions</TableHead>
                        <TableHead>Net Salary</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {payrollRecords.map((record) => (
                        <TableRow key={record.payroll_id}>
                          <TableCell className="font-medium">{record.user_name}</TableCell>
                          <TableCell>{record.working_days}</TableCell>
                          <TableCell>
                            {record.days_present}
                            {record.days_half > 0 && <span className="text-muted-foreground"> (+{record.days_half}½)</span>}
                          </TableCell>
                          <TableCell>
                            {record.total_hours}
                            {record.overtime_hours > 0 && (
                              <span className="text-green-500"> (+{record.overtime_hours})</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={record.attendance_percentage} className="w-12 h-2" />
                              <span className="text-sm">{record.attendance_percentage}%</span>
                            </div>
                          </TableCell>
                          <TableCell>{getProductivityBadge(record.productivity_score)}</TableCell>
                          <TableCell>{formatCurrency(record.base_salary)}</TableCell>
                          <TableCell className="text-green-500">+{formatCurrency(record.overtime_pay)}</TableCell>
                          <TableCell className="text-red-500">-{formatCurrency(record.deductions)}</TableCell>
                          <TableCell className="font-bold">{formatCurrency(record.net_salary)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* My Payslips */}
        <TabsContent value="my-payroll" className="space-y-4">
          {myPayroll.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center h-48 text-muted-foreground">
                <DollarSign className="h-12 w-12 mb-4 opacity-50" />
                <p>No payslips available yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {myPayroll.map((record) => (
                <Card key={record.payroll_id}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][record.month]} {record.year}</span>
                      <Badge className={record.status === "paid" ? "badge-success" : "bg-yellow-500"}>
                        {record.status}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Attendance Summary */}
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div className="p-2 bg-muted rounded">
                        <p className="text-lg font-bold text-green-500">{record.days_present}</p>
                        <p className="text-xs text-muted-foreground">Present</p>
                      </div>
                      <div className="p-2 bg-muted rounded">
                        <p className="text-lg font-bold text-yellow-500">{record.days_half}</p>
                        <p className="text-xs text-muted-foreground">Half Days</p>
                      </div>
                      <div className="p-2 bg-muted rounded">
                        <p className="text-lg font-bold text-blue-500">{record.days_leave}</p>
                        <p className="text-xs text-muted-foreground">Leave</p>
                      </div>
                      <div className="p-2 bg-muted rounded">
                        <p className="text-lg font-bold text-red-500">{record.days_absent}</p>
                        <p className="text-xs text-muted-foreground">Absent</p>
                      </div>
                    </div>

                    {/* Metrics */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Attendance</p>
                        <div className="flex items-center gap-2">
                          <Progress value={record.attendance_percentage} className="flex-1 h-2" />
                          <span className="font-bold">{record.attendance_percentage}%</span>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Productivity</p>
                        <div className="flex items-center gap-2">
                          <Progress value={record.productivity_score} className="flex-1 h-2" />
                          <span className="font-bold">{record.productivity_score}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Salary Breakdown */}
                    <div className="border-t pt-4 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Base Salary</span>
                        <span>{formatCurrency(record.base_salary)}</span>
                      </div>
                      <div className="flex justify-between text-green-500">
                        <span>Overtime ({record.overtime_hours} hrs)</span>
                        <span>+{formatCurrency(record.overtime_pay)}</span>
                      </div>
                      <div className="flex justify-between text-red-500">
                        <span>Deductions</span>
                        <span>-{formatCurrency(record.deductions)}</span>
                      </div>
                      <div className="flex justify-between font-bold text-lg border-t pt-2">
                        <span>Net Salary</span>
                        <span>{formatCurrency(record.net_salary)}</span>
                      </div>
                    </div>

                    {record.late_arrivals > 0 && (
                      <div className="flex items-center gap-2 p-2 bg-yellow-500/10 text-yellow-500 rounded text-sm">
                        <AlertTriangle className="h-4 w-4" />
                        <span>{record.late_arrivals} late arrival(s) - ₹{record.deduction_breakdown?.late_penalty || 0} penalty</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
