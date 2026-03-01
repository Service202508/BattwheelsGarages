import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { 
  DollarSign, Users, Calculator, TrendingUp, 
  Download, Clock, AlertTriangle, CheckCircle2, Save,
  FileText, AlertCircle, XCircle, Landmark, Receipt
} from "lucide-react";
import { API } from "@/App";

export default function Payroll({ user }) {
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [myPayroll, setMyPayroll] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  
  // TDS State
  const [tdsSummary, setTdsSummary] = useState(null);
  const [tdsLoading, setTdsLoading] = useState(false);
  const [tdsChallans, setTdsChallans] = useState([]);
  const [showChallanModal, setShowChallanModal] = useState(false);
  const [challanForm, setChallanForm] = useState({
    challan_number: "",
    bsr_code: "",
    deposit_date: new Date().toISOString().split("T")[0],
    amount: 0,
    payment_mode: "net_banking"
  });
  
  // Form 16 State
  const [selectedFY, setSelectedFY] = useState("2025-26");
  const [selectedEmployeeForForm16, setSelectedEmployeeForForm16] = useState("all");

  const token = localStorage.getItem("token");
  const headers = token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : {};

  useEffect(() => {
    fetchData();
  }, [selectedMonth, selectedYear]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch my payroll
      const myResponse = await fetch(`${API}/hr/payroll/my-records`, {
        credentials: "include",
        headers,
      });
      if (myResponse.ok) {
        const data = await myResponse.json();
        setMyPayroll(data);
      }

      // Fetch all payroll (admin only)
      if (user?.role === "admin") {
        const allResponse = await fetch(
          `${API}/hr/payroll/records?month=${selectedMonth}&year=${selectedYear}`,
          { credentials: "include", headers }
        );
        if (allResponse.ok) {
          const data = await allResponse.json();
          setPayrollRecords(Array.isArray(data) ? data : (data.data || []));
        }
        
        // Fetch TDS Summary
        await fetchTdsSummary();
        
        // Fetch TDS Challans
        await fetchTdsChallans();
      }
    } catch (error) {
      console.error("Failed to fetch payroll:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTdsSummary = async () => {
    setTdsLoading(true);
    try {
      const response = await fetch(
        `${API}/hr/payroll/tds-summary?month=${selectedMonth}&year=${selectedYear}`,
        { credentials: "include", headers }
      );
      if (response.ok) {
        const data = await response.json();
        setTdsSummary(data);
        setChallanForm(prev => ({ ...prev, amount: data.total_tds_this_month || 0 }));
      }
    } catch (error) {
      console.error("Failed to fetch TDS summary:", error);
    } finally {
      setTdsLoading(false);
    }
  };

  const fetchTdsChallans = async () => {
    try {
      const fy = selectedMonth >= 4 
        ? `${selectedYear}-${String(selectedYear + 1).slice(-2)}`
        : `${selectedYear - 1}-${String(selectedYear).slice(-2)}`;
      
      const response = await fetch(
        `${API}/hr/tds/challans?financial_year=${fy}`,
        { credentials: "include", headers }
      );
      if (response.ok) {
        const data = await response.json();
        setTdsChallans(data.challans || []);
      }
    } catch (error) {
      console.error("Failed to fetch TDS challans:", error);
    }
  };

  const handleGeneratePayroll = async () => {
    setGenerating(true);
    try {
      const monthNames = ["", "January", "February", "March", "April", "May", "June", 
                         "July", "August", "September", "October", "November", "December"];
      const response = await fetch(
        `${API}/hr/payroll/generate?month=${monthNames[selectedMonth]}&year=${selectedYear}`,
        { method: "POST", credentials: "include", headers }
      );

      if (response.ok) {
        const data = await response.json();
        toast.success(`Payroll generated for ${data.employees_processed} employees`);
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

  const handleRecordChallan = async () => {
    if (!challanForm.challan_number || !challanForm.bsr_code) {
      toast.error("Please fill in all required fields");
      return;
    }
    
    try {
      // Use the new mark-deposited endpoint which posts journal entries
      const response = await fetch(`${API}/hr/payroll/tds/mark-deposited`, {
        method: "POST",
        credentials: "include",
        headers,
        body: JSON.stringify({
          month: selectedMonth,
          year: selectedYear,
          challan_number: challanForm.challan_number,
          bsr_code: challanForm.bsr_code,
          deposit_date: challanForm.deposit_date,
          amount: challanForm.amount,
          payment_mode: challanForm.payment_mode
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast.success(`TDS deposited — Challan ${challanForm.challan_number} recorded`);
        setShowChallanModal(false);
        setChallanForm({ challan_number: "", bsr_code: "", deposit_date: new Date().toISOString().split("T")[0], amount: 0, payment_mode: "net_banking" });
        fetchTdsChallans();
        fetchTdsSummary();
      } else {
        // Show inline error - do not close modal
        toast.error(data.detail || "Failed to record challan");
      }
    } catch (error) {
      toast.error("Error recording challan");
    }
  };

  const handleExportTdsData = async () => {
    // Use server-side CSV export with complete data
    try {
      const response = await fetch(
        `${API}/hr/payroll/tds/export?month=${selectedMonth}&year=${selectedYear}`,
        { credentials: "include", headers }
      );
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const monthNames = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        a.download = `TDS_Summary_${monthNames[selectedMonth]}_${selectedYear}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("TDS data exported");
      } else {
        toast.error("Failed to export TDS data");
      }
    } catch (error) {
      toast.error("Error exporting TDS data");
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  const getProductivityBadge = (pct) => {
    if (pct >= 100) return <Badge className="badge-success">{pct}%</Badge>;
    if (pct >= 80) return <Badge className="bg-bw-amber/10">{pct}%</Badge>;
    return <Badge className="bg-bw-red/10">{pct}%</Badge>;
  };

  // Calculate totals for payroll
  const totalNetSalary = payrollRecords.reduce((sum, r) => sum + (r.net_salary || 0), 0);
  const totalOvertime = payrollRecords.reduce((sum, r) => sum + (r.overtime_pay || 0), 0);
  const avgProductivity = payrollRecords.length > 0
    ? (payrollRecords.reduce((sum, r) => sum + (r.productivity_score || 0), 0) / payrollRecords.length).toFixed(1)
    : 0;

  // TDS calculations
  const tdsThisMonth = tdsSummary?.total_tds_this_month || 0;
  const tdsYtd = tdsSummary?.total_tds_ytd || 0;
  const tdsDepositedYtd = tdsChallans.reduce((sum, c) => sum + (c.amount || 0), 0);
  const tdsPendingDeposit = tdsYtd + tdsThisMonth - tdsDepositedYtd;
  const tdsAlert = tdsSummary?.tds_due_alert || {};

  return (
    <div className="space-y-6" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Payroll</h1>
          <p className="text-bw-white/[0.65]">Process payroll based on attendance and productivity.</p>
        </div>
        {user?.role === "admin" && (
          <Button 
            onClick={handleGeneratePayroll} 
            disabled={generating}
            className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover"
            data-testid="generate-payroll-btn"
          >
            <Calculator className="mr-2 h-4 w-4" />
            {generating ? "Generating..." : "Generate Payroll"}
          </Button>
        )}
      </div>

      {/* Month Selector */}
      <Card className="bg-bw-off-black border-bw-white/10">
        <CardContent className="pt-6">
          <div className="flex gap-4 items-center">
            <div className="flex gap-2 items-center">
              <Label>Month:</Label>
              <Select value={String(selectedMonth)} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
                <SelectTrigger className="w-[130px] bg-bw-black border-bw-white/10"><SelectValue /></SelectTrigger>
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
                <SelectTrigger className="w-[100px] bg-bw-black border-bw-white/10"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {[2024, 2025, 2026, 2027].map((y) => (
                    <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue={user?.role === "admin" ? "all" : "my-payroll"}>
        <TabsList className="bg-bw-off-black">
          {user?.role === "admin" && <TabsTrigger value="all">All Employees</TabsTrigger>}
          <TabsTrigger value="my-payroll">My Payslips</TabsTrigger>
          {user?.role === "admin" && <TabsTrigger value="tds-summary">TDS Summary</TabsTrigger>}
        </TabsList>

        {/* All Employees (Admin) */}
        {user?.role === "admin" && (
          <TabsContent value="all" className="space-y-4">
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">Total Net Salary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-bw-volt">{formatCurrency(totalNetSalary)}</div>
                </CardContent>
              </Card>
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">Total Overtime Pay</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrency(totalOvertime)}</div>
                </CardContent>
              </Card>
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">Employees</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{payrollRecords.length}</div>
                </CardContent>
              </Card>
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">Avg Productivity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{avgProductivity}%</div>
                </CardContent>
              </Card>
            </div>

            {/* Payroll Table */}
            <Card className="bg-bw-off-black border-bw-white/10">
              <CardHeader>
                <CardTitle>Payroll Summary - {["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][selectedMonth]} {selectedYear}</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {payrollRecords.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-48 text-bw-white/[0.45]">
                    <Calculator className="h-12 w-12 mb-4 opacity-50" />
                    <p>No payroll data. Click "Generate Payroll" to calculate.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-bw-white/10">
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
                        <TableRow key={record.payroll_id} className="border-bw-white/10">
                          <TableCell className="font-medium">{record.employee_name || record.user_name}</TableCell>
                          <TableCell>{record.working_days || 26}</TableCell>
                          <TableCell>
                            {record.days_present || 0}
                            {record.days_half > 0 && <span className="text-bw-white/[0.45]"> (+{record.days_half}½)</span>}
                          </TableCell>
                          <TableCell>
                            {record.total_hours || 0}
                            {record.overtime_hours > 0 && (
                              <span className="text-green-500"> (+{record.overtime_hours})</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={record.attendance_percentage || 100} className="w-12 h-2" />
                              <span className="text-sm">{record.attendance_percentage || 100}%</span>
                            </div>
                          </TableCell>
                          <TableCell>{getProductivityBadge(record.productivity_score || 100)}</TableCell>
                          <TableCell>{formatCurrency(record.earnings?.gross || record.base_salary)}</TableCell>
                          <TableCell className="text-green-500">+{formatCurrency(record.overtime_pay || 0)}</TableCell>
                          <TableCell className="text-bw-red">-{formatCurrency(record.deductions?.total || record.deductions || 0)}</TableCell>
                          <TableCell className="font-bold text-bw-volt">{formatCurrency(record.net_salary)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* TDS Summary Tab (Admin Only) */}
        {user?.role === "admin" && (
          <TabsContent value="tds-summary" className="space-y-4">
            {/* TDS Stat Cards */}
            <div className="grid gap-4 md:grid-cols-4">
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">TDS This Month</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-bw-volt">{formatCurrency(tdsThisMonth)}</div>
                  <p className="text-xs text-bw-white/[0.45] mt-1">Total TDS to deduct</p>
                </CardContent>
              </Card>
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">TDS YTD</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-bw-volt">{formatCurrency(tdsYtd)}</div>
                  <p className="text-xs text-bw-white/[0.45] mt-1">Year to date deducted</p>
                </CardContent>
              </Card>
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">TDS Deposited YTD</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-bw-green">{formatCurrency(tdsDepositedYtd)}</div>
                  <p className="text-xs text-bw-white/[0.45] mt-1">Deposited to government</p>
                </CardContent>
              </Card>
              <Card className="bg-bw-off-black border-bw-white/10">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-bw-white/[0.65]">TDS Pending Deposit</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${tdsPendingDeposit > 0 ? 'text-bw-red' : 'text-bw-white/35'}`}>
                    {formatCurrency(Math.max(0, tdsPendingDeposit))}
                  </div>
                  <p className="text-xs text-bw-white/[0.45] mt-1">Awaiting deposit</p>
                </CardContent>
              </Card>
            </div>

            {/* TDS Due Date Alert Banner */}
            {tdsAlert.is_overdue && (
              <div className="p-4 rounded-lg bg-bw-red/[0.08] border border-bw-red/25 border-l-[3px] border-l-bw-red">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <XCircle className="h-5 w-5 text-bw-red" />
                    <div>
                      <p className="font-semibold text-bw-red">TDS OVERDUE</p>
                      <p className="text-sm text-bw-white/[0.65]">
                        {formatCurrency(tdsThisMonth)} was due on 7th. Interest at 1.5% per month applies under Section 201(1A) of Income Tax Act.
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" className="border-bw-red text-bw-red hover:bg-bw-red/10" onClick={() => setShowChallanModal(true)}>
                    <Landmark className="h-4 w-4 mr-2" /> Mark TDS Deposited
                  </Button>
                </div>
              </div>
            )}
            
            {tdsAlert.is_due_soon && !tdsAlert.is_overdue && (
              <div className="p-4 rounded-lg bg-bw-orange/[0.08] border border-bw-orange/25 border-l-[3px] border-l-bw-orange">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-bw-orange" />
                    <div>
                      <p className="font-semibold text-bw-orange">TDS Due Soon</p>
                      <p className="text-sm text-bw-white/[0.65]">
                        TDS for last month due by 7th. Amount due: {formatCurrency(tdsThisMonth)}. Mark as deposited after payment.
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" className="border-bw-orange text-bw-orange hover:bg-bw-orange/10" onClick={() => setShowChallanModal(true)}>
                    <Landmark className="h-4 w-4 mr-2" /> Mark TDS Deposited
                  </Button>
                </div>
              </div>
            )}
            
            {!tdsAlert.is_overdue && !tdsAlert.is_due_soon && tdsDepositedYtd > 0 && (
              <div className="p-4 rounded-lg bg-bw-green/[0.08] border border-bw-green/25 border-l-[3px] border-l-bw-green">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-bw-green" />
                  <div>
                    <p className="font-semibold text-bw-green">TDS deposits are up to date</p>
                    <p className="text-sm text-bw-white/[0.65]">Next TDS due: 7th of next month</p>
                  </div>
                </div>
              </div>
            )}

            {/* TDS Summary Table */}
            <Card className="bg-bw-off-black border-bw-white/10">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Employee TDS Summary</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={handleExportTdsData}>
                    <Download className="h-4 w-4 mr-2" /> Export CSV
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setShowChallanModal(true)}>
                    <Receipt className="h-4 w-4 mr-2" /> Record Challan
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {tdsLoading ? (
                  <div className="flex items-center justify-center h-48 text-bw-white/[0.45]">
                    <Calculator className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-bw-white/10">
                        <TableHead>Employee Name</TableHead>
                        <TableHead>PAN</TableHead>
                        <TableHead>Regime</TableHead>
                        <TableHead className="text-right">Gross Salary</TableHead>
                        <TableHead className="text-right">Annual Tax</TableHead>
                        <TableHead className="text-right">Monthly TDS</TableHead>
                        <TableHead className="text-right">YTD Deducted</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(tdsSummary?.employees || []).map((emp, idx) => (
                        <TableRow key={emp.employee_id || idx} className="border-bw-white/10">
                          <TableCell className="font-medium">{emp.employee_name}</TableCell>
                          <TableCell>
                            {emp.pan_number ? (
                              <code className="font-mono text-xs bg-bw-white/5 px-2 py-1 rounded">
                                {emp.pan_number}
                              </code>
                            ) : (
                              <Badge className="bg-bw-red/15 text-bw-red hover:bg-bw-red/20" title="Higher TDS rate applied under Section 206AA. Add employee PAN to reduce TDS rate.">
                                PAN MISSING
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge className={emp.tax_regime === "old" 
                              ? "bg-bw-amber/15 text-bw-amber" 
                              : "bg-bw-blue/15 text-bw-blue"}>
                              {(emp.tax_regime || "new").toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(emp.gross_monthly * 12)}</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(emp.annual_tax_liability)}</TableCell>
                          <TableCell className="text-right font-mono font-bold text-bw-volt">{formatCurrency(emp.monthly_tds)}</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(emp.ytd_tds)}</TableCell>
                          <TableCell>
                            <Badge className="bg-bw-volt/15 text-bw-volt">COMPUTED</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                      {/* Footer Total Row */}
                      <TableRow className="bg-bw-volt/[0.06] border-t-2 border-bw-volt/20">
                        <TableCell colSpan={5} className="font-mono font-bold">TOTAL</TableCell>
                        <TableCell className="text-right font-mono font-bold text-bw-volt">
                          {formatCurrency(tdsSummary?.total_tds_this_month || 0)}
                        </TableCell>
                        <TableCell className="text-right font-mono font-bold text-bw-volt">
                          {formatCurrency(tdsSummary?.total_tds_ytd || 0)}
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            {/* Form 16 Section */}
            <Card className="bg-bw-off-black border-bw-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" /> Form 16 Data
                </CardTitle>
                <CardDescription>Generate Form 16 data for employees</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="space-y-2">
                    <Label>Financial Year</Label>
                    <Select value={selectedFY} onValueChange={setSelectedFY}>
                      <SelectTrigger className="w-[140px] bg-bw-black border-bw-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="2024-25">FY 2024-25</SelectItem>
                        <SelectItem value="2025-26">FY 2025-26</SelectItem>
                        <SelectItem value="2026-27">FY 2026-27</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Employee</Label>
                    <Select value={selectedEmployeeForForm16} onValueChange={setSelectedEmployeeForForm16}>
                      <SelectTrigger className="w-[200px] bg-bw-black border-bw-white/10">
                        <SelectValue placeholder="Select employee" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Employees</SelectItem>
                        {(tdsSummary?.employees || []).map(emp => (
                          <SelectItem key={emp.employee_id} value={emp.employee_id}>
                            {emp.employee_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button variant="outline" onClick={async () => {
                    if (selectedEmployeeForForm16 === "all") {
                      toast.info("Select a specific employee for PDF download");
                      return;
                    }
                    try {
                      const token = localStorage.getItem("token");
                      const res = await fetch(`${API}/hr/payroll/form16/${selectedEmployeeForForm16}/${selectedFY}/pdf`, {
                        headers: { Authorization: `Bearer ${token}` }
                      });
                      if (res.ok) {
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        const empName = (tdsSummary?.employees || []).find(e => e.employee_id === selectedEmployeeForForm16)?.employee_name?.replace(/ /g, "_") || "Employee";
                        a.download = `Form16_${empName}_${selectedFY}.pdf`;
                        a.click();
                        URL.revokeObjectURL(url);
                        toast.success("Form 16 PDF downloaded");
                      } else {
                        const data = await res.json();
                        toast.error(data.detail || "Failed to generate Form 16 PDF");
                      }
                    } catch { toast.error("Error downloading Form 16"); }
                  }} data-testid="download-form16-btn">
                    <FileText className="h-4 w-4 mr-2" /> Download Form 16 PDF
                  </Button>
                  <Button variant="outline" onClick={async () => {
                    toast.info(`Generating all Form 16 PDFs for FY ${selectedFY}...`);
                    try {
                      const token = localStorage.getItem("token");
                      const res = await fetch(`${API}/hr/payroll/form16/bulk/${selectedFY}`, {
                        headers: { Authorization: `Bearer ${token}` }
                      });
                      if (res.ok) {
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `Form16_Bulk_${selectedFY}.zip`;
                        a.click();
                        URL.revokeObjectURL(url);
                        toast.success("Bulk Form 16 ZIP downloaded");
                      } else {
                        const data = await res.json().catch(() => ({}));
                        toast.error(data.detail || "Failed to generate bulk Form 16");
                      }
                    } catch { toast.error("Error downloading bulk Form 16"); }
                  }} data-testid="download-bulk-form16-btn">
                    <Download className="h-4 w-4 mr-2" /> Download All Form 16s (ZIP)
                  </Button>
                  <Button variant="outline" onClick={handleExportTdsData}>
                    <Download className="h-4 w-4 mr-2" /> Export TDS Data CSV
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* My Payslips */}
        <TabsContent value="my-payroll" className="space-y-4">
          {myPayroll.length === 0 ? (
            <Card className="bg-bw-off-black border-bw-white/10">
              <CardContent className="flex flex-col items-center justify-center h-48 text-bw-white/[0.45]">
                <DollarSign className="h-12 w-12 mb-4 opacity-50" />
                <p>No payslips available yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {myPayroll.map((record) => (
                <Card key={record.payroll_id} className="bg-bw-off-black border-bw-white/10">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{record.month} {record.year}</span>
                      <Badge className={record.status === "paid" ? "badge-success" : "bg-bw-amber/10"}>
                        {record.status || "generated"}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Salary Breakdown */}
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-bw-white/[0.65]">Gross Salary</span>
                        <span>{formatCurrency(record.earnings?.gross || 0)}</span>
                      </div>
                      <div className="flex justify-between text-bw-red">
                        <span>Deductions (PF + TDS + PT)</span>
                        <span>-{formatCurrency(record.deductions?.total || 0)}</span>
                      </div>
                      <div className="flex justify-between font-bold text-lg border-t border-bw-white/10 pt-2">
                        <span>Net Salary</span>
                        <span className="text-bw-volt">{formatCurrency(record.net_salary)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* TDS Challan Modal */}
      <Dialog open={showChallanModal} onOpenChange={setShowChallanModal}>
        <DialogContent className="bg-bw-off-black border-bw-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Landmark className="h-5 w-5" /> Mark TDS Deposited
            </DialogTitle>
            <DialogDescription>
              Record TDS challan details after depositing to government
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Challan Number *</Label>
              <Input 
                className="font-mono bg-bw-black border-bw-white/10"
                placeholder="e.g., 1234567890"
                value={challanForm.challan_number}
                onChange={(e) => setChallanForm({...challanForm, challan_number: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label>BSR Code of Bank Branch *</Label>
              <Input 
                className="font-mono bg-bw-black border-bw-white/10"
                placeholder="e.g., 0510021"
                value={challanForm.bsr_code}
                onChange={(e) => setChallanForm({...challanForm, bsr_code: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label>Date of Deposit</Label>
              <Input 
                type="date"
                className="bg-bw-black border-bw-white/10"
                value={challanForm.deposit_date}
                onChange={(e) => setChallanForm({...challanForm, deposit_date: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label>Amount Deposited</Label>
              <Input 
                type="number"
                className="font-mono bg-bw-black border-bw-white/10"
                value={challanForm.amount}
                onChange={(e) => setChallanForm({...challanForm, amount: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div className="space-y-2">
              <Label>Payment Mode</Label>
              <Select value={challanForm.payment_mode} onValueChange={(v) => setChallanForm({...challanForm, payment_mode: v})}>
                <SelectTrigger className="bg-bw-black border-bw-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="net_banking">Net Banking</SelectItem>
                  <SelectItem value="neft">NEFT</SelectItem>
                  <SelectItem value="rtgs">RTGS</SelectItem>
                  <SelectItem value="cheque">Cheque</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowChallanModal(false)}>Cancel</Button>
            <Button className="bg-bw-volt text-bw-black hover:bg-bw-volt-hover" onClick={handleRecordChallan}>
              <Save className="h-4 w-4 mr-2" /> Record Challan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
