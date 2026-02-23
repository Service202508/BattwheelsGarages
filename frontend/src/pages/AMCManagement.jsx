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
  Search, Filter, Zap, Users, Phone, FileText, Settings,
  IndianRupee, Sparkles
} from "lucide-react";
import { API } from "@/App";

export default function AMCManagement({ user }) {
  const [plansByCategory, setPlansByCategory] = useState(null);
  const [subscriptions, setSubscriptions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("subscriptions");
  
  // Vehicle category and billing filters
  const [vehicleCategory, setVehicleCategory] = useState("2W");
  const [billingFrequency, setBillingFrequency] = useState("monthly");
  
  // Dialog states
  const [showAddPlan, setShowAddPlan] = useState(false);
  const [showAddSubscription, setShowAddSubscription] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [showSeedDialog, setShowSeedDialog] = useState(false);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  
  // Form states
  const [planForm, setPlanForm] = useState({
    name: "",
    description: "",
    tier: "starter",
    vehicle_category: "2W",
    billing_frequency: "monthly",
    duration_months: 1,
    price: 0,
    annual_price: 0,
    periodic_services_per_month: 1,
    breakdown_visits_per_month: 2,
    max_service_visits: 12,
    includes_parts: false,
    parts_discount_percent: 0,
    priority_support: false,
    priority_response_minutes: 0,
    roadside_assistance: true,
    fleet_dashboard: false,
    dedicated_manager: false,
    custom_sla: false,
    telematics_integration: false,
    digital_service_history: true,
    oem_support: "standard"
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
      
      // Fetch plans by category
      const plansRes = await fetch(`${API}/amc/plans-by-category`, { headers, credentials: "include" });
      if (plansRes.ok) setPlansByCategory(await plansRes.json());
      
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

  const handleSeedOfficialPlans = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/amc/seed-official-plans`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      
      if (response.ok) {
        const result = await response.json();
        toast.success(`${result.plans_created} official plans imported!`);
        setShowSeedDialog(false);
        fetchData();
      } else {
        toast.error("Failed to import plans");
      }
    } catch (error) {
      toast.error("Failed to import plans");
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
      active: { color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]", label: "Active" },
      expiring: { color: "bg-orange-100 text-[#FF8C00]", label: "Expiring" },
      expired: { color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]", label: "Expired" },
      cancelled: { color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]", label: "Cancelled" }
    };
    const config = configs[status] || configs.active;
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  const getTierColor = (tier) => {
    const colors = {
      starter: "from-gray-600 to-gray-700",
      fleet_essential: "from-blue-600 to-blue-700",
      fleet_pro: "from-purple-600 to-purple-700",
      enterprise: "from-emerald-600 to-emerald-700"
    };
    return colors[tier] || colors.starter;
  };

  const getTierLabel = (tier) => {
    const labels = {
      starter: "Starter",
      fleet_essential: "Fleet Essential",
      fleet_pro: "Fleet Essential Pro",
      enterprise: "Enterprise"
    };
    return labels[tier] || tier;
  };

  const filteredSubscriptions = subscriptions.filter(sub => {
    const matchesStatus = statusFilter === "all" || sub.status === statusFilter;
    const matchesSearch = !searchTerm || 
      sub.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sub.vehicle_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sub.plan_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Get current plans based on selected category and billing
  const currentPlans = plansByCategory?.[vehicleCategory]?.[billingFrequency] || [];

  // Count subscriptions by vehicle type
  const twoWheelerCount = subscriptions.filter(s => 
    s.status === "active" && (s.vehicle_category === "2W" || s.vehicle_model?.toLowerCase().includes("ather") || s.vehicle_model?.toLowerCase().includes("ola"))
  ).length;
  const threeWheelerCount = subscriptions.filter(s => 
    s.status === "active" && s.vehicle_category === "3W"
  ).length;
  const fourWheelerCount = subscriptions.filter(s => 
    s.status === "active" && (s.vehicle_category === "4W" || s.vehicle_model?.toLowerCase().includes("nexon") || s.vehicle_model?.toLowerCase().includes("tata"))
  ).length;

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
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Annual Maintenance Contracts (AMC)</h1>
          <p className="text-[rgba(244,246,240,0.35)]">Manage subscription plans from battwheelsgarages.in</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowSeedDialog(true)}>
            <Download className="h-4 w-4 mr-2" />
            Import Official Plans
          </Button>
          <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" onClick={() => setShowAddSubscription(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add AMC
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Bike className="h-5 w-5 text-blue-500" />
              <span className="text-[rgba(244,246,240,0.35)]">2-Wheeler AMCs</span>
            </div>
            <p className="text-3xl font-bold mt-2">{twoWheelerCount}</p>
            <p className="text-xs text-[rgba(244,246,240,0.45)]">Ather, Ola, TVS, Hero</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Truck className="h-5 w-5 text-orange-500" />
              <span className="text-[rgba(244,246,240,0.35)]">3-Wheeler AMCs</span>
            </div>
            <p className="text-3xl font-bold mt-2">{threeWheelerCount}</p>
            <p className="text-xs text-[rgba(244,246,240,0.45)]">E-Rickshaws, Cargo</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Car className="h-5 w-5 text-purple-500" />
              <span className="text-[rgba(244,246,240,0.35)]">4-Wheeler AMCs</span>
            </div>
            <p className="text-3xl font-bold mt-2">{fourWheelerCount}</p>
            <p className="text-xs text-[rgba(244,246,240,0.45)]">Tata, MG, Hyundai</p>
          </CardContent>
        </Card>
        <Card className="bg-[rgba(200,255,0,0.08)] border-[rgba(200,255,0,0.20)]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <IndianRupee className="h-5 w-5 text-[#C8FF00] text-600" />
              <span className="text-[rgba(244,246,240,0.35)]">Total Revenue</span>
            </div>
            <p className="text-3xl font-bold mt-2 text-[#C8FF00] text-700">
              ₹{(analytics?.total_revenue || 0).toLocaleString()}
            </p>
            <p className="text-xs text-[rgba(244,246,240,0.45)]">{analytics?.total_active || 0} active subscriptions</p>
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
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
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
                <div className="text-center py-8 text-[rgba(244,246,240,0.45)]">
                  <Shield className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
                  <p>No AMCs found.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Customer</TableHead>
                      <TableHead>Vehicle No.</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Billing</TableHead>
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
                        <TableCell>
                          <Badge variant="outline">{sub.vehicle_category || "2W"}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="capitalize">
                            {sub.billing_frequency || "monthly"}
                          </Badge>
                        </TableCell>
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
          {/* Category and Billing Selectors */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex bg-[rgba(255,255,255,0.05)] rounded-lg p-1">
                {["2W", "3W", "4W"].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setVehicleCategory(cat)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                      vehicleCategory === cat 
                        ? "bg-[#111820] text-[#F4F6F0] shadow-sm" 
                        : "text-[rgba(244,246,240,0.35)] hover:text-[#F4F6F0]"
                    }`}
                  >
                    {cat === "2W" && <Bike className="h-4 w-4 inline mr-1" />}
                    {cat === "3W" && <Truck className="h-4 w-4 inline mr-1" />}
                    {cat === "4W" && <Car className="h-4 w-4 inline mr-1" />}
                    {cat === "2W" ? "2 Wheeler" : cat === "3W" ? "3 Wheeler" : "4 Wheeler"}
                  </button>
                ))}
              </div>
              
              <div className="flex bg-[rgba(255,255,255,0.05)] rounded-lg p-1">
                <button
                  onClick={() => setBillingFrequency("monthly")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    billingFrequency === "monthly" 
                      ? "bg-[#111820] text-[#F4F6F0] shadow-sm" 
                      : "text-[rgba(244,246,240,0.35)] hover:text-[#F4F6F0]"
                  }`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setBillingFrequency("annual")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    billingFrequency === "annual" 
                      ? "bg-[#C8FF00] text-[#080C0F] font-bold" 
                      : "text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0]"
                  }`}
                >
                  <Sparkles className="h-3 w-3 inline mr-1" />
                  Annual Save 25%
                </button>
              </div>
            </div>
            
            <Button variant="outline" onClick={() => setShowSeedDialog(true)}>
              <Download className="h-4 w-4 mr-2" />
              Sync from battwheelsgarages.in
            </Button>
          </div>
          
          {/* Plans Grid */}
          {currentPlans.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Shield className="h-16 w-16 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
                <h3 className="text-lg font-semibold text-[#F4F6F0] mb-2">No Plans Found</h3>
                <p className="text-[rgba(244,246,240,0.35)] mb-4">
                  Import official Battwheels plans to get started.
                </p>
                <Button onClick={() => setShowSeedDialog(true)}>
                  <Download className="h-4 w-4 mr-2" />
                  Import Official Plans
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-3 gap-6">
              {currentPlans.map((plan) => (
                <Card key={plan.plan_id} className={`overflow-hidden ${!plan.is_active ? 'opacity-60' : ''}`}>
                  {plan.tier === "fleet_essential" && (
                    <div className="bg-blue-600 text-white text-center text-xs font-bold py-1">
                      MOST POPULAR
                    </div>
                  )}
                  {plan.tier === "fleet_pro" && (
                    <div className="bg-purple-600 text-white text-center text-xs font-bold py-1">
                      ENTERPRISE GRADE
                    </div>
                  )}
                  
                  <div className={`bg-gradient-to-r ${getTierColor(plan.tier)} p-5 text-white`}>
                    <h3 className="font-bold text-lg">{getTierLabel(plan.tier)}</h3>
                    <p className="text-sm opacity-80 mt-1">{plan.description}</p>
                  </div>
                  
                  <CardContent className="p-5 space-y-4">
                    {/* Pricing */}
                    <div className="text-center">
                      <div className="flex items-baseline justify-center gap-1">
                        <span className="text-sm text-[rgba(244,246,240,0.45)]">₹</span>
                        <span className="text-4xl font-bold">{plan.price.toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-[rgba(244,246,240,0.45)]">
                        /{billingFrequency === "monthly" ? "month" : "year"}/vehicle
                      </p>
                      {billingFrequency === "monthly" && plan.annual_price && (
                        <p className="text-xs text-[#C8FF00] text-600 mt-1">
                          or ₹{plan.annual_price.toLocaleString()} annually
                        </p>
                      )}
                    </div>
                    
                    {/* Features */}
                    <ul className="space-y-2.5 text-sm">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                        <span>{plan.periodic_services_per_month} periodic service{plan.periodic_services_per_month > 1 ? 's' : ''}/month</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                        <span>
                          {plan.breakdown_visits_per_month >= 999 
                            ? "Unlimited breakdown visits" 
                            : `${plan.breakdown_visits_per_month} breakdown visits/month`
                          }
                        </span>
                      </li>
                      {plan.digital_service_history && (
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                          <span>Digital service history</span>
                        </li>
                      )}
                      {plan.priority_support && (
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                          <span>Priority support ({plan.priority_response_minutes}-min response)</span>
                        </li>
                      )}
                      {plan.fleet_dashboard && (
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                          <span>Fleet dashboard access</span>
                        </li>
                      )}
                      {plan.dedicated_manager && (
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                          <span>Dedicated service manager</span>
                        </li>
                      )}
                      {plan.custom_sla && (
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                          <span>Custom SLAs & uptime guarantees</span>
                        </li>
                      )}
                      {plan.telematics_integration && (
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500 mt-0.5 flex-shrink-0" />
                          <span>Telematics integration</span>
                        </li>
                      )}
                    </ul>
                    
                    {/* Stats */}
                    <div className="pt-3 border-t">
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">
                        {plan.active_subscriptions || 0} active subscriptions
                      </p>
                    </div>
                    
                    {/* Actions */}
                    <Button 
                      className={`w-full ${
                        plan.tier === "fleet_pro" 
                          ? "bg-purple-600 hover:bg-purple-700" 
                          : plan.tier === "fleet_essential"
                          ? "bg-blue-600 hover:bg-blue-700"
                          : "bg-[#0D1317] hover:bg-[#080C0F]"
                      }`}
                      onClick={() => {
                        setSubscriptionForm({ ...subscriptionForm, plan_id: plan.plan_id });
                        setShowAddSubscription(true);
                      }}
                    >
                      {plan.tier === "fleet_pro" ? "Contact Sales" : "Subscribe Customer"}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          
          {/* Enterprise Card */}
          <Card className="bg-gradient-to-r from-gray-900 to-gray-800 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold">Need a Custom Enterprise Plan?</h3>
                  <p className="text-[rgba(244,246,240,0.20)] mt-1">
                    For large fleets (50+ vehicles), custom SLAs, dedicated onsite teams, or OEM partnerships.
                  </p>
                </div>
                <Button variant="outline" className="border-white text-white hover:bg-[#111820] hover:text-[#F4F6F0]">
                  <Phone className="h-4 w-4 mr-2" />
                  Contact Sales Team
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bulk Upload Tab */}
        <TabsContent value="bulk">
          <Card>
            <CardHeader>
              <CardTitle>Bulk Upload AMCs</CardTitle>
              <CardDescription>
                Upload a CSV file to add multiple AMCs at once. Required columns: CustomerId, VehicleNumber, PlanId, StartDate.
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

      {/* Seed Official Plans Dialog */}
      <Dialog open={showSeedDialog} onOpenChange={setShowSeedDialog}>
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Import Official Battwheels Plans</DialogTitle>
            <DialogDescription>
              Import subscription plans from battwheelsgarages.in. This will create plans for all vehicle categories (2W, 3W, 4W) with monthly and annual billing options.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-900">Plans to be imported:</h4>
              <ul className="text-sm text-blue-800 mt-2 space-y-1">
                <li>• <strong>Starter</strong> - ₹499/mo or ₹4,499/year (2W pricing)</li>
                <li>• <strong>Fleet Essential</strong> - ₹699/mo or ₹5,599/year (2W pricing)</li>
                <li>• <strong>Fleet Essential Pro</strong> - ₹799/mo or ₹6,499/year (2W pricing)</li>
              </ul>
              <p className="text-xs text-[#3B9EFF] mt-2">
                * 3W plans are 1.5x, 4W plans are 2x the 2W pricing
              </p>
            </div>
            
            <div className="flex items-center gap-2 text-sm text-[rgba(244,246,240,0.35)]">
              <Zap className="h-4 w-4 text-[#C8FF00] text-500" />
              <span>Source: battwheelsgarages.in/plans</span>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSeedDialog(false)}>
              Cancel
            </Button>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" onClick={handleSeedOfficialPlans}>
              <Download className="h-4 w-4 mr-2" />
              Import Plans
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
                  {Object.entries(plansByCategory || {}).flatMap(([cat, freqs]) => 
                    Object.entries(freqs).flatMap(([freq, plans]) =>
                      plans.filter(p => p.is_active).map((plan) => (
                        <SelectItem key={plan.plan_id} value={plan.plan_id}>
                          {plan.name} - ₹{plan.price.toLocaleString()}/{freq === "monthly" ? "mo" : "yr"}
                        </SelectItem>
                      ))
                    )
                  )}
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
              className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold"
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
