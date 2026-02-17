import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, Users, Search, Edit, Trash2, Building2, User, Phone, Mail, Globe, 
  MapPin, Tag, Shield, FileText, RefreshCw, CheckCircle, XCircle, Eye,
  UserPlus, Home, Truck, CreditCard, MoreVertical, Send, Key, ChevronRight,
  Receipt, ShoppingCart, History, DollarSign, Clock, TrendingUp, AlertTriangle,
  Download, Upload
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";

const gstTreatmentLabels = {
  registered: "Registered Business",
  unregistered: "Unregistered Business",
  consumer: "Consumer",
  overseas: "Overseas",
  sez: "SEZ"
};

const gstTreatmentColors = {
  registered: "bg-green-100 text-green-700",
  unregistered: "bg-yellow-100 text-yellow-700",
  consumer: "bg-blue-100 text-blue-700",
  overseas: "bg-purple-100 text-purple-700",
  sez: "bg-orange-100 text-orange-700"
};

export default function CustomersEnhanced() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("customers");
  const [customers, setCustomers] = useState([]);
  const [tags, setTags] = useState([]);
  const [summary, setSummary] = useState(null);
  const [syncReport, setSyncReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("active");
  const [gstFilter, setGstFilter] = useState("all");

  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPersonDialog, setShowPersonDialog] = useState(false);
  const [showAddressDialog, setShowAddressDialog] = useState(false);
  const [showTagDialog, setShowTagDialog] = useState(false);
  const [showStatementDialog, setShowStatementDialog] = useState(false);
  const [showCreditDialog, setShowCreditDialog] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [editMode, setEditMode] = useState(false);

  // Form states
  const [newCustomer, setNewCustomer] = useState({
    display_name: "", company_name: "", first_name: "", last_name: "",
    email: "", phone: "", mobile: "", website: "",
    currency_code: "INR", payment_terms: 30, credit_limit: 0,
    opening_balance: 0, opening_balance_type: "credit",
    gstin: "", pan: "", place_of_supply: "", gst_treatment: "registered",
    customer_type: "business", customer_segment: "", industry: "",
    notes: "", tags: [], custom_fields: {}
  });
  const [newTag, setNewTag] = useState({ name: "", description: "", color: "#3B82F6" });
  const [newPerson, setNewPerson] = useState({ 
    first_name: "", last_name: "", email: "", phone: "", 
    designation: "", department: "", is_primary: false 
  });
  const [newAddress, setNewAddress] = useState({ 
    address_type: "billing", attention: "", street: "", street2: "", 
    city: "", state: "", state_code: "", zip_code: "", country: "India", 
    phone: "", is_default: false 
  });
  const [newCredit, setNewCredit] = useState({ amount: 0, reason: "", reference_number: "", date: "" });
  const [statementRequest, setStatementRequest] = useState({ start_date: "", end_date: "", email_to: "" });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchCustomers(), fetchSummary(), fetchTags()]);
    setLoading(false);
  }, []);

  const fetchCustomers = async () => {
    try {
      let url = `${API}/customers-enhanced/?per_page=100&status=${statusFilter}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (gstFilter !== "all") url += `&gst_treatment=${gstFilter}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setCustomers(data.customers || []);
    } catch (e) { console.error("Failed to fetch customers:", e); }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/customers-enhanced/summary`, { headers });
      const data = await res.json();
      setSummary(data.summary || null);
    } catch (e) { console.error("Failed to fetch summary:", e); }
  };

  const fetchTags = async () => {
    try {
      const res = await fetch(`${API}/customers-enhanced/tags/all`, { headers });
      const data = await res.json();
      setTags(data.tags || []);
    } catch (e) { console.error("Failed to fetch tags:", e); }
  };

  const fetchSyncReport = async () => {
    try {
      const res = await fetch(`${API}/customers-enhanced/check-sync`, { headers });
      const data = await res.json();
      setSyncReport(data.sync_report || null);
    } catch (e) { toast.error("Failed to fetch sync report"); }
  };

  const fetchCustomerDetail = async (customerId) => {
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}`, { headers });
      const data = await res.json();
      setSelectedCustomer(data.customer);
      setShowDetailDialog(true);
    } catch (e) { toast.error("Failed to fetch customer details"); }
  };

  // Validate GSTIN
  const validateGstin = async (gstin) => {
    if (!gstin || gstin.length < 15) return;
    try {
      const res = await fetch(`${API}/customers-enhanced/validate-gstin/${gstin}`, { headers });
      const data = await res.json();
      if (data.result?.valid) {
        toast.success(`Valid GSTIN: ${data.result.state_name}`);
        setNewCustomer(prev => ({
          ...prev,
          gstin: data.result.gstin,
          pan: data.result.pan,
          place_of_supply: data.result.state_code
        }));
      } else {
        toast.error(`Invalid GSTIN: ${data.result?.error || 'Unknown error'}`);
      }
    } catch (e) { toast.error("GSTIN validation failed"); }
  };

  // Customer CRUD
  const handleCreateCustomer = async () => {
    if (!newCustomer.display_name) return toast.error("Display name is required");
    try {
      const res = await fetch(`${API}/customers-enhanced/`, { method: "POST", headers, body: JSON.stringify(newCustomer) });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Customer ${data.customer.customer_number} created`);
        resetCustomerForm();
        setActiveTab("customers");
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create customer");
      }
    } catch (e) { toast.error("Error creating customer"); }
  };

  const handleUpdateCustomer = async () => {
    if (!selectedCustomer) return;
    try {
      const res = await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}`, {
        method: "PUT", headers, body: JSON.stringify(newCustomer)
      });
      if (res.ok) {
        toast.success("Customer updated");
        setEditMode(false);
        fetchCustomerDetail(selectedCustomer.customer_id);
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to update");
      }
    } catch (e) { toast.error("Error updating customer"); }
  };

  const handleDeleteCustomer = async (customerId) => {
    if (!confirm("Delete this customer? This cannot be undone.")) return;
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Customer deleted");
        setShowDetailDialog(false);
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Cannot delete customer");
      }
    } catch (e) { toast.error("Error deleting customer"); }
  };

  // Status actions
  const handleActivate = async (customerId) => {
    try {
      await fetch(`${API}/customers-enhanced/${customerId}/activate`, { method: "POST", headers });
      toast.success("Customer activated");
      fetchCustomerDetail(customerId);
      fetchData();
    } catch (e) { toast.error("Error activating customer"); }
  };

  const handleDeactivate = async (customerId) => {
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}/deactivate`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Customer deactivated");
        fetchCustomerDetail(customerId);
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Cannot deactivate");
      }
    } catch (e) { toast.error("Error deactivating customer"); }
  };

  // Portal actions
  const handleEnablePortal = async (customerId) => {
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}/enable-portal`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success("Portal enabled, invite sent");
        fetchCustomerDetail(customerId);
      }
    } catch (e) { toast.error("Error enabling portal"); }
  };

  const handleDisablePortal = async (customerId) => {
    try {
      await fetch(`${API}/customers-enhanced/${customerId}/disable-portal`, { method: "POST", headers });
      toast.success("Portal disabled");
      fetchCustomerDetail(customerId);
    } catch (e) { toast.error("Error disabling portal"); }
  };

  // Statement
  const handleEmailStatement = async () => {
    if (!selectedCustomer) return;
    try {
      const res = await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}/email-statement`, {
        method: "POST", headers, body: JSON.stringify(statementRequest)
      });
      if (res.ok) {
        toast.success("Statement sent!");
        setShowStatementDialog(false);
        setStatementRequest({ start_date: "", end_date: "", email_to: "" });
      }
    } catch (e) { toast.error("Error sending statement"); }
  };

  // Persons
  const handleAddPerson = async () => {
    if (!selectedCustomer || !newPerson.first_name) return toast.error("First name required");
    try {
      const res = await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}/persons`, {
        method: "POST", headers, body: JSON.stringify(newPerson)
      });
      if (res.ok) {
        toast.success("Person added");
        setShowPersonDialog(false);
        setNewPerson({ first_name: "", last_name: "", email: "", phone: "", designation: "", department: "", is_primary: false });
        fetchCustomerDetail(selectedCustomer.customer_id);
      }
    } catch (e) { toast.error("Error adding person"); }
  };

  const handleDeletePerson = async (personId) => {
    if (!selectedCustomer || !confirm("Delete this contact person?")) return;
    try {
      await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}/persons/${personId}`, { method: "DELETE", headers });
      toast.success("Person deleted");
      fetchCustomerDetail(selectedCustomer.customer_id);
    } catch (e) { toast.error("Error deleting person"); }
  };

  // Addresses
  const handleAddAddress = async () => {
    if (!selectedCustomer) return;
    try {
      const res = await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}/addresses`, {
        method: "POST", headers, body: JSON.stringify(newAddress)
      });
      if (res.ok) {
        toast.success("Address added");
        setShowAddressDialog(false);
        setNewAddress({ address_type: "billing", attention: "", street: "", street2: "", city: "", state: "", state_code: "", zip_code: "", country: "India", phone: "", is_default: false });
        fetchCustomerDetail(selectedCustomer.customer_id);
      }
    } catch (e) { toast.error("Error adding address"); }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!selectedCustomer || !confirm("Delete this address?")) return;
    try {
      await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}/addresses/${addressId}`, { method: "DELETE", headers });
      toast.success("Address deleted");
      fetchCustomerDetail(selectedCustomer.customer_id);
    } catch (e) { toast.error("Error deleting address"); }
  };

  // Credits
  const handleAddCredit = async () => {
    if (!selectedCustomer || !newCredit.amount) return toast.error("Amount is required");
    try {
      const res = await fetch(`${API}/customers-enhanced/${selectedCustomer.customer_id}/credits`, {
        method: "POST", headers, body: JSON.stringify(newCredit)
      });
      if (res.ok) {
        toast.success("Credit added");
        setShowCreditDialog(false);
        setNewCredit({ amount: 0, reason: "", reference_number: "", date: "" });
        fetchCustomerDetail(selectedCustomer.customer_id);
      }
    } catch (e) { toast.error("Error adding credit"); }
  };

  // Sync to Contacts
  const handleSyncToContacts = async (customerId) => {
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}/sync-to-contacts`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.action === "created" ? "Customer synced to contacts system!" : "Contact updated from customer data");
        fetchCustomerDetail(customerId);
      } else {
        toast.error(data.detail || "Sync failed");
      }
    } catch (e) { toast.error("Error syncing customer"); }
  };

  // Check contact link
  const checkContactLink = async (customerId) => {
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}/contact-link`, { headers });
      const data = await res.json();
      return data.is_linked;
    } catch (e) { return false; }
  };

  // Tags
  const handleCreateTag = async () => {
    if (!newTag.name) return toast.error("Tag name is required");
    try {
      const res = await fetch(`${API}/customers-enhanced/tags`, { method: "POST", headers, body: JSON.stringify(newTag) });
      if (res.ok) {
        toast.success("Tag created");
        setShowTagDialog(false);
        setNewTag({ name: "", description: "", color: "#3B82F6" });
        fetchTags();
      }
    } catch (e) { toast.error("Error creating tag"); }
  };

  // Quick Actions
  const handleQuickEstimate = async (customerId) => {
    try {
      const res = await fetch(`${API}/customers-enhanced/${customerId}/quick-estimate`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok && data.redirect) {
        setShowDetailDialog(false);
        navigate(data.redirect);
      }
    } catch (e) { toast.error("Error"); }
  };

  const resetCustomerForm = () => {
    setNewCustomer({
      display_name: "", company_name: "", first_name: "", last_name: "",
      email: "", phone: "", mobile: "", website: "",
      currency_code: "INR", payment_terms: 30, credit_limit: 0,
      opening_balance: 0, opening_balance_type: "credit",
      gstin: "", pan: "", place_of_supply: "", gst_treatment: "registered",
      customer_type: "business", customer_segment: "", industry: "",
      notes: "", tags: [], custom_fields: {}
    });
  };

  const startEdit = () => {
    if (selectedCustomer) {
      setNewCustomer({
        display_name: selectedCustomer.display_name || "",
        company_name: selectedCustomer.company_name || "",
        first_name: selectedCustomer.first_name || "",
        last_name: selectedCustomer.last_name || "",
        email: selectedCustomer.email || "",
        phone: selectedCustomer.phone || "",
        mobile: selectedCustomer.mobile || "",
        website: selectedCustomer.website || "",
        currency_code: selectedCustomer.currency_code || "INR",
        payment_terms: selectedCustomer.payment_terms || 30,
        credit_limit: selectedCustomer.credit_limit || 0,
        gstin: selectedCustomer.gstin || "",
        pan: selectedCustomer.pan || "",
        place_of_supply: selectedCustomer.place_of_supply || "",
        gst_treatment: selectedCustomer.gst_treatment || "registered",
        customer_type: selectedCustomer.customer_type || "business",
        customer_segment: selectedCustomer.customer_segment || "",
        industry: selectedCustomer.industry || "",
        notes: selectedCustomer.notes || "",
        tags: selectedCustomer.tags || []
      });
      setEditMode(true);
    }
  };

  return (
    <div className="space-y-6" data-testid="customers-enhanced-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customer Management</h1>
          <p className="text-gray-500 text-sm mt-1">Manage customers, portal access, statements, and credits</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchSyncReport} variant="outline" className="gap-2">
            <Shield className="h-4 w-4" /> Sync Check
          </Button>
          <Button onClick={fetchData} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <Users className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="text-xs text-gray-500">Total</p>
                  <p className="text-xl font-bold">{summary.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-green-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Active</p>
              <p className="text-lg font-bold text-green-700">{summary.active}</p>
            </CardContent>
          </Card>
          <Card className="bg-gray-100">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Inactive</p>
              <p className="text-lg font-bold text-gray-600">{summary.inactive}</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">With GSTIN</p>
              <p className="text-lg font-bold text-blue-700">{summary.with_gstin}</p>
            </CardContent>
          </Card>
          <Card className="bg-purple-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Portal Enabled</p>
              <p className="text-lg font-bold text-purple-700">{summary.with_portal}</p>
            </CardContent>
          </Card>
          <Card className="bg-yellow-50">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">New This Month</p>
              <p className="text-lg font-bold text-yellow-700">{summary.new_this_month}</p>
            </CardContent>
          </Card>
          <Card className="bg-red-50 border-red-200">
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Total Receivable</p>
              <p className="text-lg font-bold text-red-700">₹{(summary.total_receivable || 0).toLocaleString('en-IN')}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-gray-500">Credit Limit</p>
              <p className="text-lg font-bold">₹{(summary.total_credit_limit || 0).toLocaleString('en-IN')}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sync Report */}
      {syncReport && (
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><Shield className="h-4 w-4" /> Sync & Data Quality Report</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Missing GSTIN (Registered)</p>
                <p className="font-bold text-orange-600">{syncReport.data_quality?.missing_gstin_registered || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Missing Email</p>
                <p className="font-bold text-orange-600">{syncReport.data_quality?.missing_email || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Linked to Invoices</p>
                <p className="font-bold text-green-600">{syncReport.linkages?.linked_to_invoices || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">No Transactions</p>
                <p className="font-bold text-gray-600">{syncReport.linkages?.no_transactions || 0}</p>
              </div>
            </div>
            {syncReport.suggestions?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-blue-200">
                <p className="font-medium text-blue-800 mb-2">Suggestions:</p>
                <ul className="text-xs text-blue-700 space-y-1">
                  {syncReport.suggestions.map((s, i) => <li key={i}>• {s}</li>)}
                </ul>
              </div>
            )}
            <Button variant="ghost" size="sm" className="mt-2" onClick={() => setSyncReport(null)}>Dismiss</Button>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
          <TabsTrigger value="tags">Tags</TabsTrigger>
        </TabsList>

        {/* Customers Tab */}
        <TabsContent value="customers" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-2xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchCustomers()} placeholder="Search customers..." className="pl-10" data-testid="search-customers" />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setTimeout(fetchCustomers, 100); }}>
                <SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
              <Select value={gstFilter} onValueChange={(v) => { setGstFilter(v); setTimeout(fetchCustomers, 100); }}>
                <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All GST</SelectItem>
                  <SelectItem value="registered">Registered</SelectItem>
                  <SelectItem value="unregistered">Unregistered</SelectItem>
                  <SelectItem value="consumer">Consumer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setActiveTab("create")} className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black gap-2" data-testid="new-customer-btn">
              <Plus className="h-4 w-4" /> New Customer
            </Button>
          </div>

          {loading ? <div className="text-center py-8">Loading...</div> : customers.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-gray-500"><Users className="h-12 w-12 mx-auto mb-4 text-gray-300" /><p>No customers found</p></CardContent></Card>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Customer</th>
                    <th className="px-4 py-3 text-left font-medium">Email / Phone</th>
                    <th className="px-4 py-3 text-left font-medium">GSTIN</th>
                    <th className="px-4 py-3 text-left font-medium">GST Treatment</th>
                    <th className="px-4 py-3 text-right font-medium">Outstanding</th>
                    <th className="px-4 py-3 text-center font-medium">Portal</th>
                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map(cust => (
                    <tr key={cust.customer_id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => fetchCustomerDetail(cust.customer_id)} data-testid={`customer-row-${cust.customer_id}`}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {cust.customer_type === "business" ? <Building2 className="h-4 w-4 text-gray-400" /> : <User className="h-4 w-4 text-gray-400" />}
                          <div>
                            <p className="font-medium">{cust.display_name}</p>
                            {cust.company_name && <p className="text-xs text-gray-500">{cust.company_name}</p>}
                          </div>
                          {!cust.is_active && <Badge variant="outline" className="text-xs">Inactive</Badge>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {cust.email && <p className="text-xs">{cust.email}</p>}
                        {cust.phone && <p className="text-xs">{cust.phone}</p>}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{cust.gstin || '-'}</td>
                      <td className="px-4 py-3">
                        <Badge className={gstTreatmentColors[cust.gst_treatment]}>{gstTreatmentLabels[cust.gst_treatment] || cust.gst_treatment}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right font-medium">
                        <span className={cust.outstanding_balance > 0 ? "text-red-600" : "text-green-600"}>
                          ₹{(cust.outstanding_balance || 0).toLocaleString('en-IN')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {cust.portal_enabled ? <CheckCircle className="h-4 w-4 text-green-500 mx-auto" /> : <XCircle className="h-4 w-4 text-gray-300 mx-auto" />}
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchCustomerDetail(cust.customer_id)}><Eye className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* Create Tab */}
        <TabsContent value="create" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Create New Customer</CardTitle>
              <CardDescription>Add a new customer with all details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <Label>Display Name *</Label>
                  <Input value={newCustomer.display_name} onChange={(e) => setNewCustomer({...newCustomer, display_name: e.target.value})} placeholder="Customer display name" data-testid="customer-display-name" />
                </div>
                <div>
                  <Label>Customer Type</Label>
                  <Select value={newCustomer.customer_type} onValueChange={(v) => setNewCustomer({...newCustomer, customer_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="business">Business</SelectItem>
                      <SelectItem value="individual">Individual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div><Label>First Name</Label><Input value={newCustomer.first_name} onChange={(e) => setNewCustomer({...newCustomer, first_name: e.target.value})} /></div>
                <div><Label>Last Name</Label><Input value={newCustomer.last_name} onChange={(e) => setNewCustomer({...newCustomer, last_name: e.target.value})} /></div>
                <div><Label>Company Name</Label><Input value={newCustomer.company_name} onChange={(e) => setNewCustomer({...newCustomer, company_name: e.target.value})} /></div>
                <div><Label>Industry</Label><Input value={newCustomer.industry} onChange={(e) => setNewCustomer({...newCustomer, industry: e.target.value})} placeholder="e.g., Automotive" /></div>
              </div>

              <Separator />

              {/* Contact Info */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div><Label>Email</Label><Input type="email" value={newCustomer.email} onChange={(e) => setNewCustomer({...newCustomer, email: e.target.value})} /></div>
                <div><Label>Phone</Label><Input value={newCustomer.phone} onChange={(e) => setNewCustomer({...newCustomer, phone: e.target.value})} /></div>
                <div><Label>Mobile</Label><Input value={newCustomer.mobile} onChange={(e) => setNewCustomer({...newCustomer, mobile: e.target.value})} /></div>
                <div><Label>Website</Label><Input value={newCustomer.website} onChange={(e) => setNewCustomer({...newCustomer, website: e.target.value})} /></div>
              </div>

              <Separator />

              {/* GST Info */}
              <div>
                <h4 className="font-medium mb-3">GST Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label>GSTIN</Label>
                    <Input value={newCustomer.gstin} onChange={(e) => setNewCustomer({...newCustomer, gstin: e.target.value.toUpperCase()})} onBlur={(e) => validateGstin(e.target.value)} placeholder="07AAACH1234L1Z2" className="font-mono" />
                  </div>
                  <div>
                    <Label>PAN</Label>
                    <Input value={newCustomer.pan} onChange={(e) => setNewCustomer({...newCustomer, pan: e.target.value.toUpperCase()})} placeholder="AAACH1234L" className="font-mono" disabled={!!newCustomer.gstin} />
                  </div>
                  <div>
                    <Label>Place of Supply</Label>
                    <Input value={newCustomer.place_of_supply} onChange={(e) => setNewCustomer({...newCustomer, place_of_supply: e.target.value})} placeholder="DL" disabled={!!newCustomer.gstin} />
                  </div>
                  <div>
                    <Label>GST Treatment</Label>
                    <Select value={newCustomer.gst_treatment} onValueChange={(v) => setNewCustomer({...newCustomer, gst_treatment: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="registered">Registered Business</SelectItem>
                        <SelectItem value="unregistered">Unregistered Business</SelectItem>
                        <SelectItem value="consumer">Consumer</SelectItem>
                        <SelectItem value="overseas">Overseas</SelectItem>
                        <SelectItem value="sez">SEZ</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Financial */}
              <div>
                <h4 className="font-medium mb-3">Financial Terms</h4>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label>Currency</Label>
                    <Select value={newCustomer.currency_code} onValueChange={(v) => setNewCustomer({...newCustomer, currency_code: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="INR">INR - Indian Rupee</SelectItem>
                        <SelectItem value="USD">USD - US Dollar</SelectItem>
                        <SelectItem value="EUR">EUR - Euro</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Payment Terms (Days)</Label>
                    <Input type="number" value={newCustomer.payment_terms} onChange={(e) => setNewCustomer({...newCustomer, payment_terms: parseInt(e.target.value) || 0})} min="0" />
                  </div>
                  <div>
                    <Label>Credit Limit</Label>
                    <Input type="number" value={newCustomer.credit_limit} onChange={(e) => setNewCustomer({...newCustomer, credit_limit: parseFloat(e.target.value) || 0})} min="0" />
                  </div>
                  <div>
                    <Label>Opening Balance</Label>
                    <div className="flex gap-2">
                      <Input type="number" value={newCustomer.opening_balance} onChange={(e) => setNewCustomer({...newCustomer, opening_balance: parseFloat(e.target.value) || 0})} className="flex-1" />
                      <Select value={newCustomer.opening_balance_type} onValueChange={(v) => setNewCustomer({...newCustomer, opening_balance_type: v})}>
                        <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="credit">CR</SelectItem>
                          <SelectItem value="debit">DR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Notes */}
              <div>
                <Label>Notes</Label>
                <Textarea value={newCustomer.notes} onChange={(e) => setNewCustomer({...newCustomer, notes: e.target.value})} rows={3} />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={resetCustomerForm}>Reset</Button>
                <Button onClick={handleCreateCustomer} className="bg-[#22EDA9] text-black" data-testid="create-customer-submit">Create Customer</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tags Tab */}
        <TabsContent value="tags" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-medium">Customer Tags</h3>
            <Button onClick={() => setShowTagDialog(true)} className="gap-2"><Plus className="h-4 w-4" /> New Tag</Button>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {tags.map(tag => (
              <Card key={tag.tag_id}>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: tag.color }} />
                    <span className="font-medium">{tag.name}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{tag.customer_count || 0} customers</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={(open) => { setShowDetailDialog(open); if (!open) { setSelectedCustomer(null); setEditMode(false); } }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedCustomer && !editMode && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedCustomer.customer_type === "business" ? <Building2 className="h-5 w-5" /> : <User className="h-5 w-5" />}
                      {selectedCustomer.display_name}
                      {!selectedCustomer.is_active && <Badge variant="outline" className="text-xs">Inactive</Badge>}
                    </DialogTitle>
                    <DialogDescription>{selectedCustomer.customer_number} • {selectedCustomer.company_name}</DialogDescription>
                  </div>
                  <Badge className={gstTreatmentColors[selectedCustomer.gst_treatment]}>{gstTreatmentLabels[selectedCustomer.gst_treatment]}</Badge>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Contact & GST Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div><p className="text-gray-500">Email</p><p className="font-medium">{selectedCustomer.email || '-'}</p></div>
                  <div><p className="text-gray-500">Phone</p><p className="font-medium">{selectedCustomer.phone || selectedCustomer.mobile || '-'}</p></div>
                  <div><p className="text-gray-500">GSTIN</p><p className="font-mono text-xs">{selectedCustomer.gstin || '-'}</p></div>
                  <div><p className="text-gray-500">Payment Terms</p><p className="font-medium">{selectedCustomer.payment_terms} days</p></div>
                </div>

                <Separator />

                {/* Balance & Aging */}
                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2"><DollarSign className="h-4 w-4" /> Balance & Aging</h4>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <div className="bg-blue-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500">Outstanding</p>
                      <p className="text-lg font-bold text-blue-700">₹{(selectedCustomer.balance_details?.net_balance || 0).toLocaleString('en-IN')}</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500">Current</p>
                      <p className="font-bold text-green-700">₹{(selectedCustomer.aging?.current || 0).toLocaleString('en-IN')}</p>
                    </div>
                    <div className="bg-yellow-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500">1-30 Days</p>
                      <p className="font-bold text-yellow-700">₹{(selectedCustomer.aging?.["1_30"] || 0).toLocaleString('en-IN')}</p>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500">31-60 Days</p>
                      <p className="font-bold text-orange-700">₹{(selectedCustomer.aging?.["31_60"] || 0).toLocaleString('en-IN')}</p>
                    </div>
                    <div className="bg-red-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-500">90+ Days</p>
                      <p className="font-bold text-red-700">₹{(selectedCustomer.aging?.over_90 || 0).toLocaleString('en-IN')}</p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Contact Persons */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium flex items-center gap-2"><UserPlus className="h-4 w-4" /> Contact Persons ({selectedCustomer.persons?.length || 0})</h4>
                    <Button size="sm" variant="outline" onClick={() => setShowPersonDialog(true)}><Plus className="h-3 w-3 mr-1" /> Add</Button>
                  </div>
                  {selectedCustomer.persons?.length > 0 ? (
                    <div className="space-y-2">
                      {selectedCustomer.persons.map(p => (
                        <div key={p.person_id} className="flex items-center justify-between bg-gray-50 rounded-lg p-2 text-sm">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-gray-400" />
                            <span className="font-medium">{p.first_name} {p.last_name}</span>
                            {p.is_primary && <Badge variant="outline" className="text-xs">Primary</Badge>}
                            {p.designation && <span className="text-gray-500">• {p.designation}</span>}
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-500">
                            {p.email && <span><Mail className="h-3 w-3 inline mr-1" />{p.email}</span>}
                            {p.phone && <span><Phone className="h-3 w-3 inline mr-1" />{p.phone}</span>}
                            <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => handleDeletePerson(p.person_id)}><Trash2 className="h-3 w-3 text-red-500" /></Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : <p className="text-sm text-gray-500">No contact persons</p>}
                </div>

                <Separator />

                {/* Addresses */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium flex items-center gap-2"><MapPin className="h-4 w-4" /> Addresses ({selectedCustomer.addresses?.length || 0})</h4>
                    <Button size="sm" variant="outline" onClick={() => setShowAddressDialog(true)}><Plus className="h-3 w-3 mr-1" /> Add</Button>
                  </div>
                  {selectedCustomer.addresses?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {selectedCustomer.addresses.map(a => (
                        <div key={a.address_id} className="bg-gray-50 rounded-lg p-3 text-sm">
                          <div className="flex justify-between items-start">
                            <div className="flex items-center gap-2 mb-1">
                              {a.address_type === "billing" ? <Home className="h-4 w-4 text-blue-500" /> : <Truck className="h-4 w-4 text-green-500" />}
                              <span className="font-medium capitalize">{a.address_type}</span>
                              {a.is_default && <Badge variant="outline" className="text-xs">Default</Badge>}
                            </div>
                            <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => handleDeleteAddress(a.address_id)}><Trash2 className="h-3 w-3 text-red-500" /></Button>
                          </div>
                          <p className="text-gray-600">{a.street}{a.street2 && `, ${a.street2}`}</p>
                          <p className="text-gray-600">{a.city}{a.state && `, ${a.state}`} {a.zip_code}</p>
                          <p className="text-gray-600">{a.country}</p>
                        </div>
                      ))}
                    </div>
                  ) : <p className="text-sm text-gray-500">No addresses</p>}
                </div>

                <Separator />

                {/* Credits */}
                {selectedCustomer.credits?.length > 0 && (
                  <>
                    <div>
                      <h4 className="font-medium flex items-center gap-2 mb-2"><CreditCard className="h-4 w-4" /> Available Credits</h4>
                      <div className="space-y-2">
                        {selectedCustomer.credits.map(c => (
                          <div key={c.credit_id} className="flex justify-between items-center bg-green-50 rounded-lg p-2 text-sm">
                            <span>{c.credit_id} - {c.reason || 'Credit Note'}</span>
                            <span className="font-bold text-green-700">₹{c.balance?.toLocaleString('en-IN')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Transaction Counts */}
                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-2"><History className="h-4 w-4" /> Transactions</h4>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div className="bg-gray-50 rounded-lg p-2 text-center">
                      <p className="text-gray-500">Estimates</p>
                      <p className="font-bold">{selectedCustomer.transaction_counts?.estimates_count || 0}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2 text-center">
                      <p className="text-gray-500">Sales Orders</p>
                      <p className="font-bold">{selectedCustomer.transaction_counts?.salesorders_count || 0}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2 text-center">
                      <p className="text-gray-500">Invoices</p>
                      <p className="font-bold">{selectedCustomer.transaction_counts?.invoices_count || 0}</p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={startEdit}><Edit className="h-4 w-4 mr-1" /> Edit</Button>
                  
                  {selectedCustomer.is_active ? (
                    <>
                      {selectedCustomer.portal_enabled ? (
                        <Button variant="outline" onClick={() => handleDisablePortal(selectedCustomer.customer_id)}><Key className="h-4 w-4 mr-1" /> Disable Portal</Button>
                      ) : (
                        <Button variant="outline" onClick={() => handleEnablePortal(selectedCustomer.customer_id)}><Key className="h-4 w-4 mr-1" /> Enable Portal</Button>
                      )}
                      <Button variant="outline" onClick={() => { setStatementRequest({...statementRequest, email_to: selectedCustomer.email || ""}); setShowStatementDialog(true); }}><Send className="h-4 w-4 mr-1" /> Email Statement</Button>
                      <Button variant="outline" onClick={() => setShowCreditDialog(true)}><CreditCard className="h-4 w-4 mr-1" /> Add Credit</Button>
                      <Button 
                        variant="outline" 
                        className="bg-blue-50 hover:bg-blue-100 border-blue-200"
                        onClick={() => handleQuickEstimate(selectedCustomer.customer_id)}
                      >
                        <FileText className="h-4 w-4 mr-1" /> Quick Estimate
                      </Button>
                      {!selectedCustomer.transaction_counts?.has_contact_link && (
                        <Button 
                          variant="outline" 
                          className="bg-purple-50 hover:bg-purple-100 border-purple-200"
                          onClick={() => handleSyncToContacts(selectedCustomer.customer_id)}
                        >
                          <RefreshCw className="h-4 w-4 mr-1" /> Sync to Contacts
                        </Button>
                      )}
                      <Button variant="outline" onClick={() => handleDeactivate(selectedCustomer.customer_id)}><XCircle className="h-4 w-4 mr-1" /> Deactivate</Button>
                    </>
                  ) : (
                    <Button variant="outline" onClick={() => handleActivate(selectedCustomer.customer_id)}><CheckCircle className="h-4 w-4 mr-1" /> Activate</Button>
                  )}
                  
                  <Button variant="destructive" onClick={() => handleDeleteCustomer(selectedCustomer.customer_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                </div>

                {/* History */}
                {selectedCustomer.history?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-2">Recent Activity</h4>
                      <div className="space-y-1 text-sm">
                        {selectedCustomer.history.slice(0, 5).map((h, idx) => (
                          <div key={idx} className="flex justify-between text-gray-600">
                            <span>{h.action}: {h.details}</span>
                            <span className="text-xs">{new Date(h.timestamp).toLocaleString('en-IN')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          )}

          {/* Edit Mode */}
          {selectedCustomer && editMode && (
            <>
              <DialogHeader>
                <DialogTitle>Edit Customer</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Display Name *</Label><Input value={newCustomer.display_name} onChange={(e) => setNewCustomer({...newCustomer, display_name: e.target.value})} /></div>
                  <div><Label>Company Name</Label><Input value={newCustomer.company_name} onChange={(e) => setNewCustomer({...newCustomer, company_name: e.target.value})} /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Email</Label><Input value={newCustomer.email} onChange={(e) => setNewCustomer({...newCustomer, email: e.target.value})} /></div>
                  <div><Label>Phone</Label><Input value={newCustomer.phone} onChange={(e) => setNewCustomer({...newCustomer, phone: e.target.value})} /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>GSTIN</Label><Input value={newCustomer.gstin} onChange={(e) => setNewCustomer({...newCustomer, gstin: e.target.value.toUpperCase()})} className="font-mono" /></div>
                  <div>
                    <Label>GST Treatment</Label>
                    <Select value={newCustomer.gst_treatment} onValueChange={(v) => setNewCustomer({...newCustomer, gst_treatment: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="registered">Registered</SelectItem>
                        <SelectItem value="unregistered">Unregistered</SelectItem>
                        <SelectItem value="consumer">Consumer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Payment Terms (Days)</Label><Input type="number" value={newCustomer.payment_terms} onChange={(e) => setNewCustomer({...newCustomer, payment_terms: parseInt(e.target.value) || 0})} /></div>
                  <div><Label>Credit Limit</Label><Input type="number" value={newCustomer.credit_limit} onChange={(e) => setNewCustomer({...newCustomer, credit_limit: parseFloat(e.target.value) || 0})} /></div>
                </div>
                <div><Label>Notes</Label><Textarea value={newCustomer.notes} onChange={(e) => setNewCustomer({...newCustomer, notes: e.target.value})} rows={2} /></div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditMode(false)}>Cancel</Button>
                <Button onClick={handleUpdateCustomer} className="bg-[#22EDA9] text-black">Save Changes</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Person Dialog */}
      <Dialog open={showPersonDialog} onOpenChange={setShowPersonDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Contact Person</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>First Name *</Label><Input value={newPerson.first_name} onChange={(e) => setNewPerson({...newPerson, first_name: e.target.value})} /></div>
              <div><Label>Last Name</Label><Input value={newPerson.last_name} onChange={(e) => setNewPerson({...newPerson, last_name: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Email</Label><Input type="email" value={newPerson.email} onChange={(e) => setNewPerson({...newPerson, email: e.target.value})} /></div>
              <div><Label>Phone</Label><Input value={newPerson.phone} onChange={(e) => setNewPerson({...newPerson, phone: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Designation</Label><Input value={newPerson.designation} onChange={(e) => setNewPerson({...newPerson, designation: e.target.value})} /></div>
              <div><Label>Department</Label><Input value={newPerson.department} onChange={(e) => setNewPerson({...newPerson, department: e.target.value})} /></div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={newPerson.is_primary} onCheckedChange={(c) => setNewPerson({...newPerson, is_primary: c})} />
              <Label>Primary Contact</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPersonDialog(false)}>Cancel</Button>
            <Button onClick={handleAddPerson} className="bg-[#22EDA9] text-black">Add Person</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Address Dialog */}
      <Dialog open={showAddressDialog} onOpenChange={setShowAddressDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Address</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Address Type</Label>
                <Select value={newAddress.address_type} onValueChange={(v) => setNewAddress({...newAddress, address_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="billing">Billing</SelectItem>
                    <SelectItem value="shipping">Shipping</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Attention</Label><Input value={newAddress.attention} onChange={(e) => setNewAddress({...newAddress, attention: e.target.value})} /></div>
            </div>
            <div><Label>Street</Label><Input value={newAddress.street} onChange={(e) => setNewAddress({...newAddress, street: e.target.value})} /></div>
            <div><Label>Street Line 2</Label><Input value={newAddress.street2} onChange={(e) => setNewAddress({...newAddress, street2: e.target.value})} /></div>
            <div className="grid grid-cols-3 gap-4">
              <div><Label>City</Label><Input value={newAddress.city} onChange={(e) => setNewAddress({...newAddress, city: e.target.value})} /></div>
              <div><Label>State</Label><Input value={newAddress.state} onChange={(e) => setNewAddress({...newAddress, state: e.target.value})} /></div>
              <div><Label>ZIP Code</Label><Input value={newAddress.zip_code} onChange={(e) => setNewAddress({...newAddress, zip_code: e.target.value})} /></div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={newAddress.is_default} onCheckedChange={(c) => setNewAddress({...newAddress, is_default: c})} />
              <Label>Set as Default</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddressDialog(false)}>Cancel</Button>
            <Button onClick={handleAddAddress} className="bg-[#22EDA9] text-black">Add Address</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Tag Dialog */}
      <Dialog open={showTagDialog} onOpenChange={setShowTagDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Tag</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>Tag Name *</Label><Input value={newTag.name} onChange={(e) => setNewTag({...newTag, name: e.target.value})} /></div>
            <div><Label>Description</Label><Input value={newTag.description} onChange={(e) => setNewTag({...newTag, description: e.target.value})} /></div>
            <div>
              <Label>Color</Label>
              <div className="flex items-center gap-2">
                <input type="color" value={newTag.color} onChange={(e) => setNewTag({...newTag, color: e.target.value})} className="h-10 w-20" />
                <Input value={newTag.color} onChange={(e) => setNewTag({...newTag, color: e.target.value})} className="w-28" />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTagDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateTag} className="bg-[#22EDA9] text-black">Create Tag</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Statement Dialog */}
      <Dialog open={showStatementDialog} onOpenChange={setShowStatementDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Email Statement</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>Email To</Label><Input value={statementRequest.email_to} onChange={(e) => setStatementRequest({...statementRequest, email_to: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Start Date</Label><Input type="date" value={statementRequest.start_date} onChange={(e) => setStatementRequest({...statementRequest, start_date: e.target.value})} /></div>
              <div><Label>End Date</Label><Input type="date" value={statementRequest.end_date} onChange={(e) => setStatementRequest({...statementRequest, end_date: e.target.value})} /></div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStatementDialog(false)}>Cancel</Button>
            <Button onClick={handleEmailStatement} className="bg-[#22EDA9] text-black">Send Statement</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Credit Dialog */}
      <Dialog open={showCreditDialog} onOpenChange={setShowCreditDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Customer Credit</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>Amount *</Label><Input type="number" value={newCredit.amount} onChange={(e) => setNewCredit({...newCredit, amount: parseFloat(e.target.value) || 0})} min="0" /></div>
            <div><Label>Reason</Label><Input value={newCredit.reason} onChange={(e) => setNewCredit({...newCredit, reason: e.target.value})} placeholder="e.g., Advance payment" /></div>
            <div><Label>Reference #</Label><Input value={newCredit.reference_number} onChange={(e) => setNewCredit({...newCredit, reference_number: e.target.value})} /></div>
            <div><Label>Date</Label><Input type="date" value={newCredit.date} onChange={(e) => setNewCredit({...newCredit, date: e.target.value})} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreditDialog(false)}>Cancel</Button>
            <Button onClick={handleAddCredit} className="bg-[#22EDA9] text-black">Add Credit</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
