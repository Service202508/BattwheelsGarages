import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { format } from "date-fns";
import { 
  Plus, Search, Loader2, Users, UserPlus, Edit, Trash2, Eye,
  Building2, Briefcase, CreditCard, Shield, Phone, Mail, MapPin,
  Calendar, IndianRupee, BadgeCheck, AlertCircle, Save, KeyRound
} from "lucide-react";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const statusColors = {
  active: "bg-[rgba(34,197,94,0.20)] text-green-400",
  inactive: "bg-[rgba(17,24,32,0.2)] text-[rgba(244,246,240,0.45)]",
  terminated: "bg-[rgba(255,59,47,0.20)] text-red-400",
  resigned: "bg-[rgba(234,179,8,0.20)] text-yellow-400",
  on_notice: "bg-[rgba(255,140,0,0.20)] text-orange-400"
};

const roleColors = {
  admin: "bg-[rgba(139,92,246,0.20)] text-purple-400",
  manager: "bg-blue-500/20 text-blue-400",
  technician: "bg-cyan-500/20 text-cyan-400",
  accountant: "bg-[rgba(200,255,0,0.20)] text-[#C8FF00]",
  customer_support: "bg-pink-500/20 text-pink-400"
};

const employmentTypes = [
  { value: "full_time", label: "Full Time" },
  { value: "part_time", label: "Part Time" },
  { value: "contract", label: "Contract" },
  { value: "intern", label: "Intern" },
  { value: "probation", label: "Probation" }
];

const departments = [
  { value: "operations", label: "Operations" },
  { value: "hr", label: "Human Resources" },
  { value: "finance", label: "Finance" },
  { value: "service", label: "Service" },
  { value: "sales", label: "Sales" },
  { value: "administration", label: "Administration" }
];

const shifts = [
  { value: "general", label: "General (9 AM - 6 PM)" },
  { value: "morning", label: "Morning (6 AM - 2 PM)" },
  { value: "evening", label: "Evening (2 PM - 10 PM)" },
  { value: "night", label: "Night (10 PM - 6 AM)" }
];

const roles = [
  { value: "admin", label: "Admin", description: "Full access to all modules" },
  { value: "manager", label: "Manager", description: "HR + Reports access" },
  { value: "technician", label: "Technician", description: "Tickets + Job Cards access" },
  { value: "accountant", label: "Accountant", description: "Finance modules only" },
  { value: "customer_support", label: "Customer Support", description: "Tickets only" }
];

const states = [
  "Andhra Pradesh", "Karnataka", "Kerala", "Tamil Nadu", "Telangana",
  "Maharashtra", "Gujarat", "Rajasthan", "Delhi", "Uttar Pradesh",
  "Bihar", "West Bengal", "Madhya Pradesh", "Punjab", "Haryana"
];

const initialFormData = {
  // Personal
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "",
  personal_email: "",
  phone: "",
  alternate_phone: "",
  current_address: "",
  permanent_address: "",
  city: "",
  state: "",
  pincode: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  emergency_contact_relation: "",
  // Employment
  employee_code: "",
  work_email: "",
  department: "operations",
  designation: "",
  employment_type: "full_time",
  joining_date: "",
  probation_period_months: 0,
  reporting_manager_id: "",
  work_location: "office",
  shift: "general",
  // Role
  system_role: "technician",
  password: "",
  // Salary
  basic_salary: 0,
  hra: 0,
  da: 0,
  conveyance: 0,
  medical_allowance: 0,
  special_allowance: 0,
  other_allowances: 0,
  // Compliance
  pan_number: "",
  aadhaar_number: "",
  pf_number: "",
  uan: "",
  esi_number: "",
  pf_enrolled: false,
  esi_enrolled: false,
  // Bank
  bank_name: "",
  account_number: "",
  ifsc_code: "",
  branch_name: "",
  account_type: "savings"
};

export default function Employees({ user }) {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(initialFormData);
  const [managers, setManagers] = useState([]);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("personal");
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);
  const [resetPasswordTarget, setResetPasswordTarget] = useState(null);
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetConfirmPassword, setResetConfirmPassword] = useState("");
  const [resettingPassword, setResettingPassword] = useState(false);

  // Auto-save for Employee form
  const employeePersistence = useFormPersistence(
    isEditing && selectedEmployee ? `employee_edit_${selectedEmployee.employee_id}` : 'employee_new',
    formData,
    initialFormData,
    {
      enabled: dialogOpen,
      isDialogOpen: dialogOpen,
      setFormData: setFormData,
      debounceMs: 2000,
      entityName: 'Employee'
    }
  );

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      let url = `${API}/employees`;
      const params = new URLSearchParams();
      if (departmentFilter && departmentFilter !== "all") params.append("department", departmentFilter);
      if (statusFilter && statusFilter !== "all") params.append("status", statusFilter);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await fetch(url, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      
      if (response.ok) {
        let data = await response.json();
        if (searchTerm) {
          const search = searchTerm.toLowerCase();
          data = data.filter(e => 
            e.full_name?.toLowerCase().includes(search) ||
            e.employee_code?.toLowerCase().includes(search) ||
            e.work_email?.toLowerCase().includes(search) ||
            e.phone?.includes(search)
          );
        }
        setEmployees(data);
      }
    } catch (error) {
      console.error("Failed to fetch employees:", error);
      toast.error("Failed to load employees");
    } finally {
      setLoading(false);
    }
  }, [departmentFilter, statusFilter, searchTerm]);

  const fetchManagers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/employees/managers/list`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        setManagers(await response.json());
      }
    } catch (error) {
      console.error("Failed to fetch managers:", error);
    }
  };

  useEffect(() => {
    fetchEmployees();
    fetchManagers();
  }, [fetchEmployees]);

  const handleOpenDialog = (employee = null) => {
    if (employee) {
      setIsEditing(true);
      setSelectedEmployee(employee);
      setFormData({
        ...initialFormData,
        first_name: employee.first_name || "",
        last_name: employee.last_name || "",
        date_of_birth: employee.date_of_birth || "",
        gender: employee.gender || "",
        personal_email: employee.personal_email || "",
        phone: employee.phone || "",
        alternate_phone: employee.alternate_phone || "",
        current_address: employee.current_address || "",
        permanent_address: employee.permanent_address || "",
        city: employee.city || "",
        state: employee.state || "",
        pincode: employee.pincode || "",
        emergency_contact_name: employee.emergency_contact_name || "",
        emergency_contact_phone: employee.emergency_contact_phone || "",
        emergency_contact_relation: employee.emergency_contact_relation || "",
        employee_code: employee.employee_code || "",
        work_email: employee.work_email || "",
        department: employee.department || "operations",
        designation: employee.designation || "",
        employment_type: employee.employment_type || "full_time",
        joining_date: employee.joining_date || "",
        probation_period_months: employee.probation_period_months || 0,
        reporting_manager_id: employee.reporting_manager_id || "",
        work_location: employee.work_location || "office",
        shift: employee.shift || "general",
        system_role: employee.system_role || "technician",
        basic_salary: employee.salary?.basic_salary || 0,
        hra: employee.salary?.hra || 0,
        da: employee.salary?.da || 0,
        conveyance: employee.salary?.conveyance || 0,
        medical_allowance: employee.salary?.medical_allowance || 0,
        special_allowance: employee.salary?.special_allowance || 0,
        other_allowances: employee.salary?.other_allowances || 0,
        pan_number: employee.compliance?.pan_number || "",
        aadhaar_number: employee.compliance?.aadhaar_number || "",
        pf_number: employee.compliance?.pf_number || "",
        uan: employee.compliance?.uan || "",
        esi_number: employee.compliance?.esi_number || "",
        pf_enrolled: employee.compliance?.pf_enrolled || false,
        esi_enrolled: employee.compliance?.esi_enrolled || false,
        bank_name: employee.bank_details?.bank_name || "",
        account_number: employee.bank_details?.account_number || "",
        ifsc_code: employee.bank_details?.ifsc_code || "",
        branch_name: employee.bank_details?.branch_name || "",
        account_type: employee.bank_details?.account_type || "savings"
      });
    } else {
      setIsEditing(false);
      setSelectedEmployee(null);
      setFormData(initialFormData);
    }
    setActiveTab("personal");
    setDialogOpen(true);
  };

  const handleViewEmployee = (employee) => {
    setSelectedEmployee(employee);
    setViewDialogOpen(true);
  };

  const calculateGrossSalary = () => {
    return (
      parseFloat(formData.basic_salary || 0) +
      parseFloat(formData.hra || 0) +
      parseFloat(formData.da || 0) +
      parseFloat(formData.conveyance || 0) +
      parseFloat(formData.medical_allowance || 0) +
      parseFloat(formData.special_allowance || 0) +
      parseFloat(formData.other_allowances || 0)
    );
  };

  const handleSubmit = async () => {
    // Validation
    if (!formData.first_name || !formData.last_name) {
      toast.error("First name and last name are required");
      setActiveTab("personal");
      return;
    }
    if (!formData.work_email || !formData.designation || !formData.joining_date) {
      toast.error("Work email, designation and joining date are required");
      setActiveTab("employment");
      return;
    }
    if (!isEditing && !formData.password) {
      toast.error("Password is required for new employees");
      setActiveTab("access");
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const url = isEditing 
        ? `${API}/employees/${selectedEmployee.employee_id}`
        : `${API}/employees`;
      
      // Create a proper copy of the form data, mapping fields to backend expected names
      const body = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        work_email: formData.work_email, // Backend expects 'work_email'
        phone: formData.phone,
        department: formData.department || "operations",
        designation: formData.designation,
        employment_type: formData.employment_type || "full_time",
        joining_date: formData.joining_date, // Backend expects 'joining_date'
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        reporting_manager_id: formData.reporting_manager_id,
        system_role: formData.system_role || "technician",
        basic_salary: parseFloat(formData.basic_salary) || 0,
        hra: parseFloat(formData.hra) || 0,
        da: parseFloat(formData.da) || 0,
        conveyance: parseFloat(formData.conveyance) || 0,
        medical_allowance: parseFloat(formData.medical_allowance) || 0,
        special_allowance: parseFloat(formData.special_allowance) || 0,
        other_allowances: parseFloat(formData.other_allowances) || 0,
        bank_name: formData.bank_name,
        account_number: formData.account_number,
        ifsc_code: formData.ifsc_code,
        branch_name: formData.branch_name,
        account_type: formData.account_type,
        pan_number: formData.pan_number,
        aadhaar_number: formData.aadhaar_number,
        pf_number: formData.pf_number,
        uan: formData.uan,
        esi_number: formData.esi_number,
        pf_enrolled: formData.pf_enrolled || false,
        esi_enrolled: formData.esi_enrolled || false,
        personal_email: formData.personal_email,
        current_address: formData.current_address,
        permanent_address: formData.permanent_address,
        city: formData.city,
        state: formData.state,
        pincode: formData.pincode,
        emergency_contact_name: formData.emergency_contact_name,
        emergency_contact_phone: formData.emergency_contact_phone,
        emergency_contact_relation: formData.emergency_contact_relation,
        employee_code: formData.employee_code,
        work_location: formData.work_location || "office",
        shift: formData.shift || "general",
        probation_period_months: parseInt(formData.probation_period_months) || 0,
      };

      // Add password only for new employees
      if (!isEditing && formData.password) {
        body.password = formData.password;
      }

      const response = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (response.ok) {
        toast.success(isEditing ? "Employee updated successfully" : "Employee created successfully");
        employeePersistence.onSuccessfulSave(); // Clear auto-saved draft
        setDialogOpen(false);
        fetchEmployees();
        fetchManagers();
      } else {
        const data = await response.json();
        toast.error(data.detail || "Failed to save employee");
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (employeeId) => {
    if (!confirm("Are you sure you want to deactivate this employee?")) return;
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/employees/${employeeId}`, {
        method: "DELETE",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        toast.success("Employee deactivated successfully");
        fetchEmployees();
      } else {
        toast.error("Failed to deactivate employee");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const handleResetPassword = async () => {
    if (!resetPasswordTarget) return;
    if (resetNewPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    if (resetNewPassword !== resetConfirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    setResettingPassword(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/employees/${resetPasswordTarget.employee_id}/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ new_password: resetNewPassword }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || "Password reset successfully");
        setResetPasswordOpen(false);
        setResetNewPassword("");
        setResetConfirmPassword("");
        setResetPasswordTarget(null);
      } else {
        toast.error(data.detail || "Failed to reset password");
      }
    } catch {
      toast.error("Network error. Please try again.");
    } finally {
      setResettingPassword(false);
    }
  };

  const openResetPassword = (employee) => {
    setResetPasswordTarget(employee);
    setResetNewPassword("");
    setResetConfirmPassword("");
    setResetPasswordOpen(true);
  };

  const grossSalary = calculateGrossSalary();

  return (
    <div className="space-y-4" data-testid="employees-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Employee Management</h1>
          <p className="text-muted-foreground">Manage employees, roles, salaries and compliance.</p>
        </div>
        <Button onClick={() => handleOpenDialog()} data-testid="add-employee-btn">
          <UserPlus className="mr-2 h-4 w-4" />
          Add Employee
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{employees.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <BadgeCheck className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{employees.filter(e => e.status === "active").length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Departments</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{new Set(employees.map(e => e.department)).size}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">On Notice</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{employees.filter(e => e.status === "on_notice").length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name, code, email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
            data-testid="search-input"
          />
        </div>
        <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Departments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {departments.map(d => (
              <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="on_notice">On Notice</SelectItem>
            <SelectItem value="terminated">Terminated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Employees Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : employees.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Users className="h-12 w-12 mb-4 opacity-50" />
              <p>No employees found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Designation</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joining Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((emp) => (
                  <TableRow key={emp.employee_id} data-testid={`employee-row-${emp.employee_id}`}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{emp.full_name}</p>
                        <p className="text-xs text-muted-foreground">{emp.work_email}</p>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono">{emp.employee_code}</TableCell>
                    <TableCell className="capitalize">{emp.department?.replace("_", " ")}</TableCell>
                    <TableCell>{emp.designation}</TableCell>
                    <TableCell>
                      <Badge className={roleColors[emp.system_role] || "bg-[#111820]0"}>
                        {emp.system_role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[emp.status] || "bg-[#111820]0"}>
                        {emp.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {emp.joining_date ? format(new Date(emp.joining_date), "MMM dd, yyyy") : "N/A"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="icon" onClick={() => handleViewEmployee(emp)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleOpenDialog(emp)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        {emp.work_email && (
                          <Button variant="ghost" size="icon" onClick={() => openResetPassword(emp)} title="Reset Password" data-testid={`reset-password-btn-${emp.employee_id}`}>
                            <KeyRound className="h-4 w-4 text-yellow-500" />
                          </Button>
                        )}
                        {emp.status === "active" && (
                          <Button variant="ghost" size="icon" onClick={() => handleDelete(emp.employee_id)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Employee Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => {
        if (!open && employeePersistence.isDirty) {
          employeePersistence.setShowCloseConfirm(true);
        } else {
          setDialogOpen(open);
          if (!open) employeePersistence.clearSavedData();
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col overflow-y-auto">
          <DialogHeader>
            <div className="flex justify-between items-start">
              <div>
                <DialogTitle>{isEditing ? "Edit Employee" : "Add New Employee"}</DialogTitle>
                <DialogDescription>
                  {isEditing ? "Update employee information" : "Fill in all required details to create a new employee"}
                </DialogDescription>
              </div>
              <AutoSaveIndicator 
                lastSaved={employeePersistence.lastSaved} 
                isSaving={employeePersistence.isSaving} 
                isDirty={employeePersistence.isDirty} 
              />
            </div>
          </DialogHeader>
          
          {/* Draft Recovery Banner */}
          <DraftRecoveryBanner
            show={employeePersistence.showRecoveryBanner}
            savedAt={employeePersistence.savedDraftInfo?.timestamp}
            onRestore={employeePersistence.handleRestoreDraft}
            onDiscard={employeePersistence.handleDiscardDraft}
          />
          
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            <TabsList className="grid grid-cols-5 w-full">
              <TabsTrigger value="personal">Personal</TabsTrigger>
              <TabsTrigger value="employment">Employment</TabsTrigger>
              <TabsTrigger value="salary">Salary</TabsTrigger>
              <TabsTrigger value="compliance">Compliance</TabsTrigger>
              <TabsTrigger value="access">Bank & Access</TabsTrigger>
            </TabsList>
            
            <ScrollArea className="flex-1 pr-4">
              {/* Personal Information Tab */}
              <TabsContent value="personal" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input
                      id="first_name"
                      value={formData.first_name}
                      onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                      placeholder="John"
                      data-testid="first-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input
                      id="last_name"
                      value={formData.last_name}
                      onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                      placeholder="Doe"
                      data-testid="last-name-input"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="date_of_birth">Date of Birth</Label>
                    <Input
                      id="date_of_birth"
                      type="date"
                      value={formData.date_of_birth}
                      onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gender">Gender</Label>
                    <Select value={formData.gender} onValueChange={(v) => setFormData({...formData, gender: v})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select gender" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Male</SelectItem>
                        <SelectItem value="female">Female</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      placeholder="+91 98765 43210"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="personal_email">Personal Email</Label>
                    <Input
                      id="personal_email"
                      type="email"
                      value={formData.personal_email}
                      onChange={(e) => setFormData({...formData, personal_email: e.target.value})}
                      placeholder="john.personal@email.com"
                    />
                  </div>
                </div>
                
                <Separator />
                <h4 className="font-semibold">Address</h4>
                
                <div className="space-y-2">
                  <Label htmlFor="current_address">Current Address</Label>
                  <Input
                    id="current_address"
                    value={formData.current_address}
                    onChange={(e) => setFormData({...formData, current_address: e.target.value})}
                    placeholder="Street address, Area"
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      value={formData.city}
                      onChange={(e) => setFormData({...formData, city: e.target.value})}
                      placeholder="Bangalore"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state">State</Label>
                    <Select value={formData.state} onValueChange={(v) => setFormData({...formData, state: v})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select state" />
                      </SelectTrigger>
                      <SelectContent>
                        {states.map(s => (
                          <SelectItem key={s} value={s}>{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pincode">Pincode</Label>
                    <Input
                      id="pincode"
                      value={formData.pincode}
                      onChange={(e) => setFormData({...formData, pincode: e.target.value})}
                      placeholder="560001"
                    />
                  </div>
                </div>
                
                <Separator />
                <h4 className="font-semibold">Emergency Contact</h4>
                
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="emergency_contact_name">Contact Name</Label>
                    <Input
                      id="emergency_contact_name"
                      value={formData.emergency_contact_name}
                      onChange={(e) => setFormData({...formData, emergency_contact_name: e.target.value})}
                      placeholder="Jane Doe"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emergency_contact_phone">Contact Phone</Label>
                    <Input
                      id="emergency_contact_phone"
                      value={formData.emergency_contact_phone}
                      onChange={(e) => setFormData({...formData, emergency_contact_phone: e.target.value})}
                      placeholder="+91 98765 43211"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emergency_contact_relation">Relation</Label>
                    <Input
                      id="emergency_contact_relation"
                      value={formData.emergency_contact_relation}
                      onChange={(e) => setFormData({...formData, emergency_contact_relation: e.target.value})}
                      placeholder="Spouse"
                    />
                  </div>
                </div>
              </TabsContent>

              {/* Employment Tab */}
              <TabsContent value="employment" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="employee_code">Employee Code</Label>
                    <Input
                      id="employee_code"
                      value={formData.employee_code}
                      onChange={(e) => setFormData({...formData, employee_code: e.target.value})}
                      placeholder="Auto-generated if empty"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="work_email">Work Email *</Label>
                    <Input
                      id="work_email"
                      type="email"
                      value={formData.work_email}
                      onChange={(e) => setFormData({...formData, work_email: e.target.value})}
                      placeholder="john@battwheels.in"
                      disabled={isEditing}
                      data-testid="work-email-input"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="department">Department *</Label>
                    <Select value={formData.department} onValueChange={(v) => setFormData({...formData, department: v})}>
                      <SelectTrigger data-testid="department-select">
                        <SelectValue placeholder="Select department" />
                      </SelectTrigger>
                      <SelectContent>
                        {departments.map(d => (
                          <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="designation">Designation *</Label>
                    <Input
                      id="designation"
                      value={formData.designation}
                      onChange={(e) => setFormData({...formData, designation: e.target.value})}
                      placeholder="Senior Technician"
                      data-testid="designation-input"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="employment_type">Employment Type</Label>
                    <Select value={formData.employment_type} onValueChange={(v) => setFormData({...formData, employment_type: v})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {employmentTypes.map(t => (
                          <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="joining_date">Joining Date *</Label>
                    <Input
                      id="joining_date"
                      type="date"
                      value={formData.joining_date}
                      onChange={(e) => setFormData({...formData, joining_date: e.target.value})}
                      data-testid="joining-date-input"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="reporting_manager">Reporting Manager</Label>
                    <Select value={formData.reporting_manager_id || "none"} onValueChange={(v) => setFormData({...formData, reporting_manager_id: v === "none" ? "" : v})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select manager" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        {managers.map(m => (
                          <SelectItem key={m.employee_id} value={m.employee_id}>
                            {m.full_name} - {m.designation}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shift">Shift</Label>
                    <Select value={formData.shift} onValueChange={(v) => setFormData({...formData, shift: v})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select shift" />
                      </SelectTrigger>
                      <SelectContent>
                        {shifts.map(s => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </TabsContent>

              {/* Salary Tab */}
              <TabsContent value="salary" className="space-y-4 mt-4">
                <Card className="bg-muted/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Salary Structure (Monthly)</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="basic_salary">Basic Salary</Label>
                        <div className="relative">
                          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="basic_salary"
                            type="number"
                            value={formData.basic_salary}
                            onChange={(e) => setFormData({...formData, basic_salary: parseFloat(e.target.value) || 0})}
                            className="pl-10"
                            placeholder="25000"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="hra">HRA (House Rent Allowance)</Label>
                        <div className="relative">
                          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="hra"
                            type="number"
                            value={formData.hra}
                            onChange={(e) => setFormData({...formData, hra: parseFloat(e.target.value) || 0})}
                            className="pl-10"
                            placeholder="10000"
                          />
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="da">DA (Dearness Allowance)</Label>
                        <div className="relative">
                          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="da"
                            type="number"
                            value={formData.da}
                            onChange={(e) => setFormData({...formData, da: parseFloat(e.target.value) || 0})}
                            className="pl-10"
                            placeholder="5000"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="conveyance">Conveyance</Label>
                        <div className="relative">
                          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="conveyance"
                            type="number"
                            value={formData.conveyance}
                            onChange={(e) => setFormData({...formData, conveyance: parseFloat(e.target.value) || 0})}
                            className="pl-10"
                            placeholder="1600"
                          />
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="medical_allowance">Medical Allowance</Label>
                        <div className="relative">
                          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="medical_allowance"
                            type="number"
                            value={formData.medical_allowance}
                            onChange={(e) => setFormData({...formData, medical_allowance: parseFloat(e.target.value) || 0})}
                            className="pl-10"
                            placeholder="1250"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="special_allowance">Special Allowance</Label>
                        <div className="relative">
                          <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="special_allowance"
                            type="number"
                            value={formData.special_allowance}
                            onChange={(e) => setFormData({...formData, special_allowance: parseFloat(e.target.value) || 0})}
                            className="pl-10"
                            placeholder="5000"
                          />
                        </div>
                      </div>
                    </div>
                    
                    <Separator />
                    
                    <div className="flex justify-between items-center py-2 px-4 bg-primary/10 rounded-lg">
                      <span className="font-semibold">Gross Salary (CTC)</span>
                      <span className="text-xl font-bold">₹{grossSalary.toLocaleString()}</span>
                    </div>
                    
                    <p className="text-sm text-muted-foreground">
                      * Deductions (PF, ESI, Professional Tax, TDS) will be auto-calculated based on compliance settings
                    </p>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Compliance Tab */}
              <TabsContent value="compliance" className="space-y-4 mt-4">
                <Card className="bg-muted/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Statutory Compliance (India)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="pan_number">PAN Number</Label>
                        <Input
                          id="pan_number"
                          value={formData.pan_number}
                          onChange={(e) => setFormData({...formData, pan_number: e.target.value.toUpperCase()})}
                          placeholder="ABCDE1234F"
                          maxLength={10}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="aadhaar_number">Aadhaar Number</Label>
                        <Input
                          id="aadhaar_number"
                          value={formData.aadhaar_number}
                          onChange={(e) => setFormData({...formData, aadhaar_number: e.target.value})}
                          placeholder="1234 5678 9012"
                          maxLength={14}
                        />
                      </div>
                    </div>
                    
                    <Separator />
                    <h4 className="font-semibold">Provident Fund (PF)</h4>
                    
                    <div className="flex items-center gap-4">
                      <input
                        type="checkbox"
                        id="pf_enrolled"
                        checked={formData.pf_enrolled}
                        onChange={(e) => setFormData({...formData, pf_enrolled: e.target.checked})}
                        className="h-4 w-4"
                      />
                      <Label htmlFor="pf_enrolled">Enrolled in PF (12% of Basic deducted)</Label>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="pf_number">PF Number</Label>
                        <Input
                          id="pf_number"
                          value={formData.pf_number}
                          onChange={(e) => setFormData({...formData, pf_number: e.target.value})}
                          placeholder="KA/BNG/12345/67890"
                          disabled={!formData.pf_enrolled}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="uan">UAN (Universal Account Number)</Label>
                        <Input
                          id="uan"
                          value={formData.uan}
                          onChange={(e) => setFormData({...formData, uan: e.target.value})}
                          placeholder="100123456789"
                          disabled={!formData.pf_enrolled}
                        />
                      </div>
                    </div>
                    
                    <Separator />
                    <h4 className="font-semibold">ESI (Employee State Insurance)</h4>
                    
                    <div className="flex items-center gap-4">
                      <input
                        type="checkbox"
                        id="esi_enrolled"
                        checked={formData.esi_enrolled}
                        onChange={(e) => setFormData({...formData, esi_enrolled: e.target.checked})}
                        className="h-4 w-4"
                      />
                      <Label htmlFor="esi_enrolled">Enrolled in ESI (0.75% deducted if Gross ≤ ₹21,000)</Label>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="esi_number">ESI Number</Label>
                      <Input
                        id="esi_number"
                        value={formData.esi_number}
                        onChange={(e) => setFormData({...formData, esi_number: e.target.value})}
                        placeholder="12-34-567890-123-4567"
                        disabled={!formData.esi_enrolled}
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Bank & Access Tab */}
              <TabsContent value="access" className="space-y-4 mt-4">
                <Card className="bg-muted/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <CreditCard className="h-5 w-5" />
                      Bank Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="bank_name">Bank Name</Label>
                        <Input
                          id="bank_name"
                          value={formData.bank_name}
                          onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
                          placeholder="State Bank of India"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="account_number">Account Number</Label>
                        <Input
                          id="account_number"
                          value={formData.account_number}
                          onChange={(e) => setFormData({...formData, account_number: e.target.value})}
                          placeholder="1234567890123"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="ifsc_code">IFSC Code</Label>
                        <Input
                          id="ifsc_code"
                          value={formData.ifsc_code}
                          onChange={(e) => setFormData({...formData, ifsc_code: e.target.value.toUpperCase()})}
                          placeholder="SBIN0001234"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="branch_name">Branch Name</Label>
                        <Input
                          id="branch_name"
                          value={formData.branch_name}
                          onChange={(e) => setFormData({...formData, branch_name: e.target.value})}
                          placeholder="MG Road Branch"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-muted/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      System Access & Role
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="system_role">System Role *</Label>
                      <Select value={formData.system_role} onValueChange={(v) => setFormData({...formData, system_role: v})}>
                        <SelectTrigger data-testid="role-select">
                          <SelectValue placeholder="Select role" />
                        </SelectTrigger>
                        <SelectContent>
                          {roles.map(r => (
                            <SelectItem key={r.value} value={r.value}>
                              <div>
                                <span className="font-medium">{r.label}</span>
                                <span className="text-xs text-muted-foreground ml-2">- {r.description}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {!isEditing && (
                      <div className="space-y-2">
                        <Label htmlFor="password">Login Password *</Label>
                        <Input
                          id="password"
                          type="password"
                          value={formData.password}
                          onChange={(e) => setFormData({...formData, password: e.target.value})}
                          placeholder="Set initial password"
                          data-testid="password-input"
                        />
                        <p className="text-xs text-muted-foreground">
                          Employee will use this password with their work email to login
                        </p>
                      </div>
                    )}
                    
                    <div className="p-4 bg-background rounded-lg border">
                      <h4 className="font-semibold mb-2">Role Permissions</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {formData.system_role === "admin" && (
                          <>
                            <li>✓ Full access to all modules</li>
                            <li>✓ User & Employee management</li>
                            <li>✓ System configuration</li>
                          </>
                        )}
                        {formData.system_role === "manager" && (
                          <>
                            <li>✓ HR module access</li>
                            <li>✓ Reports & Analytics</li>
                            <li>✓ Approve leaves & expenses</li>
                          </>
                        )}
                        {formData.system_role === "technician" && (
                          <>
                            <li>✓ View & update tickets</li>
                            <li>✓ Job card management</li>
                            <li>✓ Inventory view</li>
                          </>
                        )}
                        {formData.system_role === "accountant" && (
                          <>
                            <li>✓ Finance modules</li>
                            <li>✓ Invoices & Expenses</li>
                            <li>✓ Accounting & Reports</li>
                          </>
                        )}
                        {formData.system_role === "customer_support" && (
                          <>
                            <li>✓ Create & view tickets</li>
                            <li>✓ Customer communication</li>
                          </>
                        )}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </ScrollArea>
          </Tabs>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={saving} data-testid="save-employee-btn">
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {isEditing ? "Update Employee" : "Create Employee"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Employee Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Employee Details</DialogTitle>
          </DialogHeader>
          
          {selectedEmployee && (
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center gap-4">
                <div className="h-16 w-16 bg-primary/20 rounded-full flex items-center justify-center text-2xl font-bold">
                  {selectedEmployee.first_name?.[0]}{selectedEmployee.last_name?.[0]}
                </div>
                <div>
                  <h2 className="text-xl font-bold">{selectedEmployee.full_name}</h2>
                  <p className="text-muted-foreground">{selectedEmployee.designation} - {selectedEmployee.department}</p>
                  <div className="flex gap-2 mt-1">
                    <Badge className={roleColors[selectedEmployee.system_role]}>{selectedEmployee.system_role}</Badge>
                    <Badge className={statusColors[selectedEmployee.status]}>{selectedEmployee.status}</Badge>
                  </div>
                </div>
              </div>
              
              <Separator />
              
              {/* Contact */}
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2"><Phone className="h-4 w-4" /> Contact</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted-foreground">Work Email:</span> {selectedEmployee.work_email}</div>
                  <div><span className="text-muted-foreground">Phone:</span> {selectedEmployee.phone || "N/A"}</div>
                  <div><span className="text-muted-foreground">Personal Email:</span> {selectedEmployee.personal_email || "N/A"}</div>
                </div>
              </div>
              
              {/* Employment */}
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2"><Briefcase className="h-4 w-4" /> Employment</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted-foreground">Employee Code:</span> {selectedEmployee.employee_code}</div>
                  <div><span className="text-muted-foreground">Joining Date:</span> {selectedEmployee.joining_date}</div>
                  <div><span className="text-muted-foreground">Employment Type:</span> {selectedEmployee.employment_type}</div>
                  <div><span className="text-muted-foreground">Shift:</span> {selectedEmployee.shift}</div>
                  <div><span className="text-muted-foreground">Manager:</span> {selectedEmployee.reporting_manager_name || "N/A"}</div>
                </div>
              </div>
              
              {/* Salary */}
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2"><IndianRupee className="h-4 w-4" /> Salary</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted-foreground">Gross Salary:</span> ₹{selectedEmployee.salary?.gross_salary?.toLocaleString() || 0}</div>
                  <div><span className="text-muted-foreground">Net Salary:</span> ₹{selectedEmployee.salary?.net_salary?.toLocaleString() || 0}</div>
                  <div><span className="text-muted-foreground">Basic:</span> ₹{selectedEmployee.salary?.basic_salary?.toLocaleString() || 0}</div>
                  <div><span className="text-muted-foreground">PF Deduction:</span> ₹{selectedEmployee.salary?.pf_deduction?.toLocaleString() || 0}</div>
                </div>
              </div>
              
              {/* Compliance */}
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2"><Shield className="h-4 w-4" /> Compliance</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted-foreground">PAN:</span> {selectedEmployee.compliance?.pan_number || "N/A"}</div>
                  <div><span className="text-muted-foreground">Aadhaar:</span> {selectedEmployee.compliance?.aadhaar_number || "N/A"}</div>
                  <div><span className="text-muted-foreground">PF Enrolled:</span> {selectedEmployee.compliance?.pf_enrolled ? "Yes" : "No"}</div>
                  <div><span className="text-muted-foreground">ESI Enrolled:</span> {selectedEmployee.compliance?.esi_enrolled ? "Yes" : "No"}</div>
                </div>
              </div>
              
              {/* Bank */}
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2"><CreditCard className="h-4 w-4" /> Bank Details</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-muted-foreground">Bank:</span> {selectedEmployee.bank_details?.bank_name || "N/A"}</div>
                  <div><span className="text-muted-foreground">Account:</span> {selectedEmployee.bank_details?.account_number || "N/A"}</div>
                  <div><span className="text-muted-foreground">IFSC:</span> {selectedEmployee.bank_details?.ifsc_code || "N/A"}</div>
                </div>
              </div>

              {/* Actions */}
              {selectedEmployee.work_email && (
                <div className="pt-2 border-t border-white/10">
                  <Button
                    variant="outline"
                    onClick={() => { setViewDialogOpen(false); openResetPassword(selectedEmployee); }}
                    data-testid="detail-reset-password-btn"
                  >
                    <KeyRound className="h-4 w-4 mr-2" /> Reset Login Password
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Employee Close Confirmation */}
      <FormCloseConfirmDialog
        open={employeePersistence.showCloseConfirm}
        onClose={() => employeePersistence.setShowCloseConfirm(false)}
        onSave={async () => {
          await handleSubmit();
        }}
        onDiscard={() => {
          employeePersistence.clearSavedData();
          setDialogOpen(false);
        }}
        isSaving={saving}
        entityName="Employee"
      />

      {/* Reset Password Dialog */}
      <Dialog open={resetPasswordOpen} onOpenChange={setResetPasswordOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-yellow-500" />
              Reset Employee Password
            </DialogTitle>
            <DialogDescription>
              Set a new login password for <span className="font-medium text-foreground">{resetPasswordTarget?.full_name || resetPasswordTarget?.work_email}</span>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="reset-new-pw">New Password</Label>
              <Input
                id="reset-new-pw"
                type="password"
                value={resetNewPassword}
                onChange={(e) => setResetNewPassword(e.target.value)}
                placeholder="Min 6 characters"
                data-testid="admin-reset-new-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="reset-confirm-pw">Confirm Password</Label>
              <Input
                id="reset-confirm-pw"
                type="password"
                value={resetConfirmPassword}
                onChange={(e) => setResetConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                data-testid="admin-reset-confirm-password"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResetPasswordOpen(false)}>Cancel</Button>
            <Button
              onClick={handleResetPassword}
              disabled={resettingPassword || !resetNewPassword || !resetConfirmPassword}
              data-testid="admin-reset-submit-btn"
            >
              {resettingPassword ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Resetting...</> : "Reset Password"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
