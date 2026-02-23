import { useState, useEffect } from "react";
import { API, getAuthHeaders } from "@/App";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  CreditCard, 
  Check, 
  X, 
  Zap, 
  Users, 
  FileText, 
  Ticket, 
  Car, 
  Bot,
  ArrowRight,
  Crown,
  Sparkles,
  Building2,
  Clock,
  AlertTriangle,
  ChevronRight,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";

export default function SubscriptionManagement() {
  const [subscription, setSubscription] = useState(null);
  const [entitlements, setEntitlements] = useState(null);
  const [limits, setLimits] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    setLoading(true);
    try {
      const [subRes, entRes, limRes, plansRes] = await Promise.all([
        fetch(`${API}/subscriptions/current`, { headers: getAuthHeaders() }),
        fetch(`${API}/subscriptions/entitlements`, { headers: getAuthHeaders() }),
        fetch(`${API}/subscriptions/limits`, { headers: getAuthHeaders() }),
        fetch(`${API}/subscriptions/plans/compare`)
      ]);

      if (subRes.ok) setSubscription(await subRes.json());
      if (entRes.ok) setEntitlements(await entRes.json());
      if (limRes.ok) setLimits(await limRes.json());
      if (plansRes.ok) setPlans(await plansRes.json());
    } catch (error) {
      console.error("Failed to fetch subscription data:", error);
      toast.error("Failed to load subscription data");
    } finally {
      setLoading(false);
    }
  };

  const getPlanBadgeColor = (planCode) => {
    const colors = {
      free: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
      starter: "bg-blue-100 text-[#3B9EFF]",
      professional: "bg-purple-100 text-[#8B5CF6]",
      enterprise: "bg-amber-100 text-amber-700"
    };
    return colors[planCode] || "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]";
  };

  const getStatusBadge = (status) => {
    const badges = {
      trialing: { color: "bg-blue-100 text-[#3B9EFF]", icon: Clock, label: "Trial" },
      active: { color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]", icon: Check, label: "Active" },
      past_due: { color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]", icon: AlertTriangle, label: "Past Due" },
      canceled: { color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]", icon: X, label: "Canceled" },
      suspended: { color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]", icon: AlertTriangle, label: "Suspended" }
    };
    return badges[status] || badges.active;
  };

  const formatLimit = (limitData) => {
    if (!limitData) return "N/A";
    if (limitData.limit === "unlimited") return "Unlimited";
    if (typeof limitData.limit === "number") return limitData.limit.toLocaleString();
    return limitData.limit;
  };

  const handleUpgrade = async (planCode) => {
    try {
      const response = await fetch(`${API}/subscriptions/change-plan?plan_code=${planCode}`, {
        method: "POST",
        headers: getAuthHeaders()
      });

      if (response.ok) {
        toast.success(`Successfully upgraded to ${planCode} plan!`);
        setUpgradeDialogOpen(false);
        fetchSubscriptionData();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to change plan");
      }
    } catch (error) {
      toast.error("Failed to change plan");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-[rgba(244,246,240,0.45)]" />
      </div>
    );
  }

  const statusBadge = subscription ? getStatusBadge(subscription.status) : null;
  const StatusIcon = statusBadge?.icon;

  return (
    <div className="space-y-6" data-testid="subscription-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#F4F6F0]">Subscription & Billing</h1>
          <p className="text-[rgba(244,246,240,0.45)] mt-1">Manage your subscription plan and usage</p>
        </div>
        <Button onClick={fetchSubscriptionData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Current Plan Card */}
      {subscription && (
        <Card data-testid="current-plan-card">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
                  <Crown className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {subscription.plan?.name || "Plan"}
                    <Badge className={getPlanBadgeColor(subscription.plan?.code)}>
                      {subscription.plan?.code?.toUpperCase()}
                    </Badge>
                  </CardTitle>
                  <CardDescription className="flex items-center gap-2 mt-1">
                    {StatusIcon && <StatusIcon className="h-4 w-4" />}
                    {statusBadge?.label}
                    {subscription.is_in_trial && (
                      <span className="text-[#3B9EFF]">
                        • Trial ends {new Date(subscription.trial_end).toLocaleDateString()}
                      </span>
                    )}
                  </CardDescription>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-[#F4F6F0]">
                  ₹{subscription.plan?.price_monthly?.toLocaleString() || 0}
                  <span className="text-sm font-normal text-[rgba(244,246,240,0.45)]">/month</span>
                </div>
                {subscription.billing_cycle === "annual" && (
                  <p className="text-sm text-green-600">Save 17% with annual billing</p>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="text-sm text-[rgba(244,246,240,0.45)]">
                Current period: {subscription.current_period_start ? new Date(subscription.current_period_start).toLocaleDateString() : "N/A"} - {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "N/A"}
              </div>
              <Dialog open={upgradeDialogOpen} onOpenChange={setUpgradeDialogOpen}>
                <DialogTrigger asChild>
                  <Button data-testid="upgrade-plan-btn">
                    <Sparkles className="h-4 w-4 mr-2" />
                    {subscription.plan?.code === "enterprise" ? "Manage Plan" : "Upgrade Plan"}
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Choose Your Plan</DialogTitle>
                    <DialogDescription>
                      Select the plan that best fits your business needs
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                    {plans.map((plan) => (
                      <Card 
                        key={plan.code} 
                        className={`relative cursor-pointer transition-all hover:border-[rgba(200,255,0,0.2)] ${
                          subscription.plan?.code === plan.code 
                            ? "ring-2 ring-indigo-500" 
                            : ""
                        }`}
                        onClick={() => setSelectedPlan(plan.code)}
                      >
                        {plan.code === "professional" && (
                          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                            <Badge className="bg-indigo-600 text-white">Most Popular</Badge>
                          </div>
                        )}
                        <CardHeader className="pb-2">
                          <CardTitle className="text-lg">{plan.name}</CardTitle>
                          <div className="mt-2">
                            <span className="text-3xl font-bold">₹{plan.price_monthly.toLocaleString()}</span>
                            <span className="text-[rgba(244,246,240,0.45)]">/mo</span>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <p className="text-sm text-[rgba(244,246,240,0.45)]">{plan.description}</p>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-center gap-2">
                              <Check className="h-4 w-4 text-green-500" />
                              {plan.limits?.max_users === -1 ? "Unlimited" : plan.limits?.max_users} users
                            </li>
                            <li className="flex items-center gap-2">
                              <Check className="h-4 w-4 text-green-500" />
                              {plan.limits?.max_invoices_per_month === -1 ? "Unlimited" : plan.limits?.max_invoices_per_month} invoices/mo
                            </li>
                            <li className="flex items-center gap-2">
                              <Check className="h-4 w-4 text-green-500" />
                              {plan.support_level} support
                            </li>
                          </ul>
                          <Button 
                            className="w-full mt-4"
                            variant={subscription.plan?.code === plan.code ? "outline" : "default"}
                            disabled={subscription.plan?.code === plan.code}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleUpgrade(plan.code);
                            }}
                          >
                            {subscription.plan?.code === plan.code ? "Current Plan" : "Select Plan"}
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="usage" className="space-y-4">
        <TabsList>
          <TabsTrigger value="usage" data-testid="usage-tab">Usage & Limits</TabsTrigger>
          <TabsTrigger value="features" data-testid="features-tab">Features</TabsTrigger>
        </TabsList>

        {/* Usage Tab */}
        <TabsContent value="usage" className="space-y-4">
          {limits && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Invoices */}
              <Card data-testid="invoices-usage-card">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-500" />
                      <span className="font-medium">Invoices</span>
                    </div>
                    <span className="text-sm text-[rgba(244,246,240,0.45)]">
                      {limits.limits?.invoices?.current || 0} / {formatLimit(limits.limits?.invoices)}
                    </span>
                  </div>
                  <Progress 
                    value={limits.limits?.invoices?.percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                    {limits.limits?.invoices?.remaining === "unlimited" 
                      ? "Unlimited remaining" 
                      : `${limits.limits?.invoices?.remaining || 0} remaining this month`}
                  </p>
                </CardContent>
              </Card>

              {/* Tickets */}
              <Card data-testid="tickets-usage-card">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Ticket className="h-5 w-5 text-purple-500" />
                      <span className="font-medium">Service Tickets</span>
                    </div>
                    <span className="text-sm text-[rgba(244,246,240,0.45)]">
                      {limits.limits?.tickets?.current || 0} / {formatLimit(limits.limits?.tickets)}
                    </span>
                  </div>
                  <Progress 
                    value={limits.limits?.tickets?.percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                    {limits.limits?.tickets?.remaining === "unlimited" 
                      ? "Unlimited remaining" 
                      : `${limits.limits?.tickets?.remaining || 0} remaining this month`}
                  </p>
                </CardContent>
              </Card>

              {/* Vehicles */}
              <Card data-testid="vehicles-usage-card">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Car className="h-5 w-5 text-green-500" />
                      <span className="font-medium">Vehicles</span>
                    </div>
                    <span className="text-sm text-[rgba(244,246,240,0.45)]">
                      {limits.limits?.vehicles?.current || 0} / {formatLimit(limits.limits?.vehicles)}
                    </span>
                  </div>
                  <Progress 
                    value={limits.limits?.vehicles?.percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                    {limits.limits?.vehicles?.remaining === "unlimited" 
                      ? "Unlimited" 
                      : `${limits.limits?.vehicles?.remaining || 0} slots available`}
                  </p>
                </CardContent>
              </Card>

              {/* AI Calls */}
              <Card data-testid="ai-calls-usage-card">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Bot className="h-5 w-5 text-amber-500" />
                      <span className="font-medium">AI Calls</span>
                    </div>
                    <span className="text-sm text-[rgba(244,246,240,0.45)]">
                      {limits.limits?.ai_calls?.current || 0} / {formatLimit(limits.limits?.ai_calls)}
                    </span>
                  </div>
                  <Progress 
                    value={limits.limits?.ai_calls?.percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                    {limits.limits?.ai_calls?.remaining === "unlimited" 
                      ? "Unlimited remaining" 
                      : `${limits.limits?.ai_calls?.remaining || 0} calls remaining`}
                  </p>
                </CardContent>
              </Card>

              {/* Users */}
              <Card data-testid="users-limit-card">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Users className="h-5 w-5 text-indigo-500" />
                      <span className="font-medium">Team Members</span>
                    </div>
                    <span className="text-sm text-[rgba(244,246,240,0.45)]">
                      Limit: {formatLimit(limits.limits?.users)}
                    </span>
                  </div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                    Maximum users allowed on your plan
                  </p>
                </CardContent>
              </Card>

              {/* Storage */}
              <Card data-testid="storage-limit-card">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-rose-500" />
                      <span className="font-medium">Storage</span>
                    </div>
                    <span className="text-sm text-[rgba(244,246,240,0.45)]">
                      {formatLimit(limits.limits?.storage_gb)} GB
                    </span>
                  </div>
                  <p className="text-xs text-[rgba(244,246,240,0.45)] mt-2">
                    Document and file storage limit
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Billing Period Info */}
          {limits && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Billing Period</h3>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">
                      {limits.period?.start ? new Date(limits.period.start).toLocaleDateString() : "N/A"} - {limits.period?.end ? new Date(limits.period.end).toLocaleDateString() : "N/A"}
                    </p>
                  </div>
                  <Badge variant="outline" className="capitalize">{limits.billing_cycle}</Badge>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features" className="space-y-4">
          {entitlements && (
            <div className="space-y-6">
              {/* Feature Categories */}
              {[
                { 
                  title: "Operations", 
                  icon: Ticket, 
                  features: ["ops_tickets", "ops_vehicles", "ops_estimates", "ops_amc"]
                },
                { 
                  title: "Finance", 
                  icon: CreditCard, 
                  features: ["finance_invoicing", "finance_recurring_invoices", "finance_payments", "finance_bills", "finance_expenses", "finance_banking", "finance_gst"]
                },
                { 
                  title: "Inventory", 
                  icon: Building2, 
                  features: ["inventory_tracking", "inventory_serial_batch", "inventory_multi_warehouse", "inventory_stock_transfers"]
                },
                { 
                  title: "HR & Payroll", 
                  icon: Users, 
                  features: ["hr_employees", "hr_attendance", "hr_leave", "hr_payroll"]
                },
                { 
                  title: "Intelligence (EFI)", 
                  icon: Bot, 
                  features: ["efi_failure_intelligence", "efi_ai_guidance", "efi_knowledge_brain", "efi_expert_escalation"]
                },
                { 
                  title: "Integrations", 
                  icon: Zap, 
                  features: ["integrations_zoho_sync", "integrations_api_access", "integrations_webhooks"]
                },
                { 
                  title: "Portals", 
                  icon: Building2, 
                  features: ["portal_customer", "portal_business", "portal_technician"]
                },
                { 
                  title: "Advanced Features", 
                  icon: Sparkles, 
                  features: ["advanced_reports", "advanced_custom_fields", "advanced_workflow_automation", "advanced_pdf_templates", "advanced_audit_logs", "advanced_white_label", "advanced_sso"]
                }
              ].map((category) => {
                const CategoryIcon = category.icon;
                const enabledCount = category.features.filter(f => entitlements.features?.[f]).length;
                
                return (
                  <Card key={category.title}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CategoryIcon className="h-5 w-5 text-indigo-500" />
                          <CardTitle className="text-base">{category.title}</CardTitle>
                        </div>
                        <Badge variant="outline">
                          {enabledCount}/{category.features.length} enabled
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {category.features.map((feature) => {
                          const isEnabled = entitlements.features?.[feature];
                          const featureName = feature
                            .replace(/^(ops_|finance_|inventory_|hr_|efi_|integrations_|portal_|advanced_)/, "")
                            .replace(/_/g, " ")
                            .replace(/\b\w/g, l => l.toUpperCase());
                          
                          return (
                            <div 
                              key={feature}
                              className={`flex items-center gap-2 p-2 rounded-lg ${
                                isEnabled 
                                  ? "bg-[rgba(34,197,94,0.08)] text-green-700" 
                                  : "bg-[#111820] text-[rgba(244,246,240,0.45)]"
                              }`}
                            >
                              {isEnabled ? (
                                <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                              ) : (
                                <X className="h-4 w-4 text-[rgba(244,246,240,0.20)] flex-shrink-0" />
                              )}
                              <span className="text-sm truncate">{featureName}</span>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
