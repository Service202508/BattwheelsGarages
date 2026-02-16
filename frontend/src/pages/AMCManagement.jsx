import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { 
  Plus, Download, Upload, Car, Bike, Truck, Shield, Calendar,
  CheckCircle, AlertCircle, Clock, Pencil, Trash2, RefreshCw,
  Search, Filter, MoreVertical
} from "lucide-react";
import { API } from "@/App";

export default function AMCManagement({ user }) {
  const [plans, setPlans] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("subscriptions");
  
  // Dialog states
  const [showAddPlan, setShowAddPlan] = useState(false);
  const [showAddSubscription, setShowAddSubscription] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  
  // Form states
  const [planForm, setPlanForm] = useState({
    name: "",
    description: "",
    tier: "basic",
    duration_months: 12,
    price: 0,
    max_service_visits: 4,
    includes_parts: false,
    parts_discount_percent: 0,
    priority_support: false,
    roadside_assistance: false
  });
  
  const [subscriptionForm, setSubscriptionForm] = useState({
    plan_id: "",
    customer_id: "",
    vehicle_id: "",
    start_date: "",
    amount_paid: 0,
    payment_status: "pending"
  });

  // Customers and vehicles for dropdowns
  const [customers, setCustomers] = useState([]);
  const [vehicles, setVehicles] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Fetch plans
      const plansRes = await fetch(`${API}/amc/plans?include_inactive=true`, { headers, credentials: "include" });
      if (plansRes.ok) setPlans(await plansRes.json());
      
      // Fetch subscriptions
      const subsRes = await fetch(`${API}/amc/subscriptions`, { headers, credentials: "include" });
      if (subsRes.ok) setSubscriptions(await subsRes.json());
      
      // Fetch analytics
      const analyticsRes = await fetch(`${API}/amc/analytics`, { headers, credentials: "include" });
      if (analyticsRes.ok) setAnalytics(await analyticsRes.json());
      
      // Fetch customers for dropdown
      const customersRes = await fetch(`${API}/customers`, { headers, credentials: "include" });
      if (customersRes.ok) setCustomers(await customersRes.json());
      
      // Fetch vehicles for dropdown
      const vehiclesRes = await fetch(`${API}/vehicles`, { headers, credentials: "include" });
      if (vehiclesRes.ok) setVehicles(await vehiclesRes.json());
      
    } catch (error) {
      console.error("Failed to fetch AMC data:", error);
      toast.error("Failed to load AMC data");
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/plans`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: "include",
        body: JSON.stringify(planForm)
      });
      
      if (response.ok) {
        toast.success("AMC Plan created successfully");
        setShowAddPlan(false);
        resetPlanForm();
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to create plan");
      }
    } catch (error) {
      toast.error("Failed to create plan");
    }
  };

  const handleUpdatePlan = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/plans/${editingPlan.plan_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: "include",
        body: JSON.stringify(planForm)
      });
      
      if (response.ok) {
        toast.success("AMC Plan updated successfully");
        setEditingPlan(null);
        resetPlanForm();
        fetchData();
      } else {
        toast.error("Failed to update plan");
      }
    } catch (error) {
      toast.error("Failed to update plan");
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!confirm("Are you sure you want to deactivate this plan?")) return;
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/plans/${planId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      
      if (response.ok) {
        toast.success("Plan deactivated");
        fetchData();
      } else {
        toast.error("Failed to deactivate plan");
      }
    } catch (error) {
      toast.error("Failed to deactivate plan");
    }
  };

  const handleCreateSubscription = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/subscriptions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: "include",
        body: JSON.stringify(subscriptionForm)
      });
      
      if (response.ok) {
        toast.success("AMC Subscription created successfully");
        setShowAddSubscription(false);
        resetSubscriptionForm();
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to create subscription");
      }
    } catch (error) {
      toast.error("Failed to create subscription");
    }
  };

  const handleCancelSubscription = async (subscriptionId) => {
    const reason = prompt("Please provide a reason for cancellation:");
    if (!reason) return;
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/subscriptions/${subscriptionId}/cancel`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: "include",
        body: JSON.stringify({ reason })
      });
      
      if (response.ok) {
        toast.success("Subscription cancelled");
        fetchData();
      } else {
        toast.error("Failed to cancel subscription");
      }
    } catch (error) {
      toast.error("Failed to cancel subscription");
    }
  };

  const handleRenewSubscription = async (subscriptionId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/subscriptions/${subscriptionId}/renew`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: "include",
        body: JSON.stringify({})
      });
      
      if (response.ok) {
        toast.success("Subscription renewed successfully");
        fetchData();
      } else {
        toast.error("Failed to renew subscription");
      }
    } catch (error) {
      toast.error("Failed to renew subscription");
    }
  };

  const resetPlanForm = () => {
    setPlanForm({
      name: "",
      description: "",
      tier: "basic",
      duration_months: 12,
      price: 0,
      max_service_visits: 4,
      includes_parts: false,
      parts_discount_percent: 0,
      priority_support: false,
      roadside_assistance: false
    });
  };

  const resetSubscriptionForm = () => {
    setSubscriptionForm({
      plan_id: "",
      customer_id: "",
      vehicle_id: "",
      start_date: "",
      amount_paid: 0,
      payment_status: "pending"
    });
  };

  const getStatusBadge = (status) => {
    const configs = {
      active: { color: "bg-green-100 text-green-700", label: "Active" },
      expiring: { color: "bg-orange-100 text-orange-700", label: "Expiring" },
      expired: { color: "bg-red-100 text-red-700", label: "Expired" },
      cancelled: { color: "bg-gray-100 text-gray-700", label: "Cancelled" }
    };
    const config = configs[status] || configs.active;
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  const filteredSubscriptions = subscriptions.filter(sub => {
    const matchesStatus = statusFilter === "all" || sub.status === statusFilter;
    const matchesSearch = !searchTerm || 
      sub.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sub.vehicle_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sub.plan_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Count subscriptions by vehicle type (simplified - based on plan tier for demo)
  const fourWheelerCount = subscriptions.filter(s => s.status === "active" && s.vehicle_model?.includes("Nexon")).length;
  const twoWheelerCount = subscriptions.filter(s => s.status === "active" && s.vehicle_model?.includes("Ather")).length;
  const commercialCount = 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="amc-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Annual Maintenance Contracts (AMC)</h1>
          <p className="text-gray-600">Manage all active and expired AMCs.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Download CSV
          </Button>
          <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => setShowAddSubscription(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add AMC
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Car className="h-5 w-5 text-gray-400" />
              <span className="text-gray-600">4-Wheeler AMCs</span>
            </div>
            <p className="text-3xl font-bold mt-2">{fourWheelerCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Bike className="h-5 w-5 text-gray-400" />
              <span className="text-gray-600">2-Wheeler AMCs</span>
            </div>
            <p className="text-3xl font-bold mt-2">{twoWheelerCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Truck className="h-5 w-5 text-gray-400" />
              <span className="text-gray-600">Commercial AMCs</span>
            </div>
            <p className="text-3xl font-bold mt-2">{commercialCount}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="subscriptions">AMC Subscriptions</TabsTrigger>
          <TabsTrigger value="plans">AMC Plans</TabsTrigger>
          <TabsTrigger value="bulk">Bulk Upload</TabsTrigger>
        </TabsList>

        {/* Subscriptions Tab */}
        <TabsContent value="subscriptions" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by customer, vehicle, or plan..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="expiring">Expiring</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Subscriptions Table */}
          <Card>
            <CardHeader>
              <CardTitle>AMC Subscriptions</CardTitle>
              <CardDescription>A list of all customer AMC subscriptions.</CardDescription>
            </CardHeader>
            <CardContent>
              {filteredSubscriptions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Shield className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No AMCs found.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Customer</TableHead>
                      <TableHead>Vehicle No.</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Start Date</TableHead>
                      <TableHead>End Date</TableHead>
                      <TableHead>Usage</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredSubscriptions.map((sub) => (
                      <TableRow key={sub.subscription_id}>
                        <TableCell className="font-medium">{sub.customer_name}</TableCell>
                        <TableCell className="font-mono">{sub.vehicle_number}</TableCell>
                        <TableCell>{sub.plan_name}</TableCell>
                        <TableCell>{new Date(sub.start_date).toLocaleDateString()}</TableCell>
                        <TableCell>{new Date(sub.end_date).toLocaleDateString()}</TableCell>
                        <TableCell>{sub.services_used}/{sub.max_services}</TableCell>
                        <TableCell>{getStatusBadge(sub.status)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            {(sub.status === "expiring" || sub.status === "expired") && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleRenewSubscription(sub.subscription_id)}
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                            )}
                            {sub.status === "active" && (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleCancelSubscription(sub.subscription_id)}
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
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
        </TabsContent>

        {/* Plans Tab */}
        <TabsContent value="plans" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAddPlan(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Plan
            </Button>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <Card key={plan.plan_id} className={`overflow-hidden ${!plan.is_active ? 'opacity-60' : ''}`}>
                <div className={`p-4 text-white ${
                  plan.tier === 'premium' ? 'bg-purple-600' :
                  plan.tier === 'plus' ? 'bg-blue-600' : 'bg-gray-600'
                }`}>
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-lg">{plan.name}</h3>
                    {!plan.is_active && <Badge variant="secondary">Inactive</Badge>}
                  </div>
                  <p className="text-sm opacity-80 capitalize">{plan.tier} Tier</p>
                </div>
                <CardContent className="p-4 space-y-3">
                  <div className="text-center">
                    <p className="text-3xl font-bold">₹{plan.price.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">{plan.duration_months} months</p>
                  </div>
                  <ul className="text-sm space-y-2">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      {plan.max_service_visits} Free Services
                    </li>
                    {plan.includes_parts && (
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        {plan.parts_discount_percent}% Parts Discount
                      </li>
                    )}
                    {plan.priority_support && (
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Priority Support
                      </li>
                    )}
                    {plan.roadside_assistance && (
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Roadside Assistance
                      </li>
                    )}
                  </ul>
                  <p className="text-xs text-gray-500">
                    {plan.active_subscriptions || 0} active subscriptions
                  </p>
                  <div className="flex gap-2 pt-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => {
                        setEditingPlan(plan);
                        setPlanForm(plan);
                      }}
                    >
                      <Pencil className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    {plan.is_active && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleDeletePlan(plan.plan_id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Bulk Upload Tab */}
        <TabsContent value="bulk">
          <Card>
            <CardHeader>
              <CardTitle>Bulk Upload AMCs</CardTitle>
              <CardDescription>
                Upload a CSV file to add multiple AMCs at once. Required columns: CustomerId, VehicleNumber, PlanName, StartDate.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Download Sample CSV
              </Button>
              <div>
                <Input type="file" accept=".csv" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add/Edit Plan Dialog */}
      <Dialog open={showAddPlan || !!editingPlan} onOpenChange={(open) => {
        if (!open) {
          setShowAddPlan(false);
          setEditingPlan(null);
          resetPlanForm();
        }
      }}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingPlan ? "Edit AMC Plan" : "Create AMC Plan"}</DialogTitle>
            <DialogDescription>
              Configure the plan details and pricing.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Plan Name</Label>
                <Input 
                  value={planForm.name}
                  onChange={(e) => setPlanForm({...planForm, name: e.target.value})}
                  placeholder="e.g., Premium Shield"
                />
              </div>
              <div className="space-y-2">
                <Label>Tier</Label>
                <Select 
                  value={planForm.tier} 
                  onValueChange={(v) => setPlanForm({...planForm, tier: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="plus">Plus</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea 
                value={planForm.description}
                onChange={(e) => setPlanForm({...planForm, description: e.target.value})}
                placeholder="Plan description..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Price (₹)</Label>
                <Input 
                  type="number"
                  value={planForm.price}
                  onChange={(e) => setPlanForm({...planForm, price: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div className="space-y-2">
                <Label>Duration (months)</Label>
                <Input 
                  type="number"
                  value={planForm.duration_months}
                  onChange={(e) => setPlanForm({...planForm, duration_months: parseInt(e.target.value) || 12})}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Max Service Visits</Label>
                <Input 
                  type="number"
                  value={planForm.max_service_visits}
                  onChange={(e) => setPlanForm({...planForm, max_service_visits: parseInt(e.target.value) || 0})}
                />
              </div>
              <div className="space-y-2">
                <Label>Parts Discount (%)</Label>
                <Input 
                  type="number"
                  value={planForm.parts_discount_percent}
                  onChange={(e) => setPlanForm({...planForm, parts_discount_percent: parseFloat(e.target.value) || 0})}
                />
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Include Parts Discount</Label>
                <Switch 
                  checked={planForm.includes_parts}
                  onCheckedChange={(v) => setPlanForm({...planForm, includes_parts: v})}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Priority Support</Label>
                <Switch 
                  checked={planForm.priority_support}
                  onCheckedChange={(v) => setPlanForm({...planForm, priority_support: v})}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Roadside Assistance</Label>
                <Switch 
                  checked={planForm.roadside_assistance}
                  onCheckedChange={(v) => setPlanForm({...planForm, roadside_assistance: v})}
                />
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowAddPlan(false);
              setEditingPlan(null);
              resetPlanForm();
            }}>
              Cancel
            </Button>
            <Button 
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={editingPlan ? handleUpdatePlan : handleCreatePlan}
            >
              {editingPlan ? "Update Plan" : "Create Plan"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Subscription Dialog */}
      <Dialog open={showAddSubscription} onOpenChange={setShowAddSubscription}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add AMC Subscription</DialogTitle>
            <DialogDescription>
              Create a new AMC subscription for a customer.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Select Plan</Label>
              <Select 
                value={subscriptionForm.plan_id}
                onValueChange={(v) => setSubscriptionForm({...subscriptionForm, plan_id: v})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a plan" />
                </SelectTrigger>
                <SelectContent>
                  {plans.filter(p => p.is_active).map((plan) => (
                    <SelectItem key={plan.plan_id} value={plan.plan_id}>
                      {plan.name} - ₹{plan.price.toLocaleString()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Customer</Label>
              <Select 
                value={subscriptionForm.customer_id}
                onValueChange={(v) => setSubscriptionForm({...subscriptionForm, customer_id: v})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select customer" />
                </SelectTrigger>
                <SelectContent>
                  {customers.map((customer) => (
                    <SelectItem key={customer.customer_id || customer.user_id} value={customer.customer_id || customer.user_id}>
                      {customer.name} - {customer.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Vehicle</Label>
              <Select 
                value={subscriptionForm.vehicle_id}
                onValueChange={(v) => setSubscriptionForm({...subscriptionForm, vehicle_id: v})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {vehicles.map((vehicle) => (
                    <SelectItem key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                      {vehicle.registration_number} - {vehicle.make} {vehicle.model}
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
                  value={subscriptionForm.start_date}
                  onChange={(e) => setSubscriptionForm({...subscriptionForm, start_date: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Amount Paid (₹)</Label>
                <Input 
                  type="number"
                  value={subscriptionForm.amount_paid}
                  onChange={(e) => setSubscriptionForm({...subscriptionForm, amount_paid: parseFloat(e.target.value) || 0})}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Payment Status</Label>
              <Select 
                value={subscriptionForm.payment_status}
                onValueChange={(v) => setSubscriptionForm({...subscriptionForm, payment_status: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="partial">Partial</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowAddSubscription(false);
              resetSubscriptionForm();
            }}>
              Cancel
            </Button>
            <Button 
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={handleCreateSubscription}
            >
              Create Subscription
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
