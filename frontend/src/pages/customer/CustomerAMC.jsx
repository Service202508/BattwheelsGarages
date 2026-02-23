import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { 
  Shield, Car, Calendar, CheckCircle, AlertCircle, Clock,
  Wrench, Gift, Phone, RefreshCw, ArrowRight, Sparkles
} from "lucide-react";
import { API } from "@/App";

export default function CustomerAMC({ user }) {
  const [subscriptions, setSubscriptions] = useState([]);
  const [availablePlans, setAvailablePlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    fetchSubscriptions();
    fetchAvailablePlans();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/amc`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data);
      }
    } catch (error) {
      console.error("Failed to fetch subscriptions:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailablePlans = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/amc-plans`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setAvailablePlans(data);
      }
    } catch (error) {
      console.error("Failed to fetch plans:", error);
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      active: { color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)] border-green-200", icon: CheckCircle, label: "Active" },
      expiring: { color: "bg-orange-100 text-[#FF8C00] border-orange-200", icon: AlertCircle, label: "Expiring Soon" },
      expired: { color: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)] border-red-200", icon: Clock, label: "Expired" },
      cancelled: { color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)] border-gray-200", icon: Clock, label: "Cancelled" }
    };
    return configs[status] || configs.active;
  };

  const getTierColor = (tier) => {
    const colors = {
      basic: "from-gray-500 to-gray-600",
      plus: "from-blue-500 to-blue-600",
      premium: "from-purple-500 to-purple-600"
    };
    return colors[tier?.toLowerCase()] || colors.basic;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customer-amc">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#F4F6F0]">AMC Plans</h1>
        <p className="text-[rgba(244,246,240,0.35)]">Manage your Annual Maintenance Contracts</p>
      </div>

      {/* Active Subscriptions */}
      {subscriptions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-[#F4F6F0]">Your Subscriptions</h2>
          
          {subscriptions.map((sub) => {
            const statusConfig = getStatusConfig(sub.status);
            const StatusIcon = statusConfig.icon;
            const usagePercent = (sub.services_used / sub.max_services) * 100;
            
            return (
              <Card key={sub.subscription_id} className="overflow-hidden">
                {/* Header Band */}
                <div className={`bg-gradient-to-r ${getTierColor(sub.plan_tier)} p-4 text-white`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Shield className="h-6 w-6" />
                      <div>
                        <h3 className="font-bold text-lg">{sub.plan_name}</h3>
                        <p className="text-white/80 text-sm">{sub.vehicle_number} • {sub.vehicle_model}</p>
                      </div>
                    </div>
                    <Badge className={`${statusConfig.color} border`}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {statusConfig.label}
                    </Badge>
                  </div>
                </div>

                <CardContent className="p-6 space-y-6">
                  {/* Validity & Usage */}
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-[rgba(244,246,240,0.45)] mb-1">Validity Period</p>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                        <span className="font-medium">
                          {new Date(sub.start_date).toLocaleDateString()} - {new Date(sub.end_date).toLocaleDateString()}
                        </span>
                      </div>
                      {sub.status === 'expiring' && (
                        <p className="text-[#FF8C00] text-sm mt-1 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          Expires in {Math.ceil((new Date(sub.end_date) - new Date()) / (1000 * 60 * 60 * 24))} days
                        </p>
                      )}
                    </div>
                    
                    <div>
                      <p className="text-sm text-[rgba(244,246,240,0.45)] mb-1">Service Usage</p>
                      <div className="flex items-center gap-3">
                        <Progress value={usagePercent} className="flex-1 h-2" />
                        <span className="font-medium text-sm whitespace-nowrap">
                          {sub.services_used} / {sub.max_services} used
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Features */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 rounded-lg bg-[#111820]">
                      <Wrench className="h-5 w-5 mx-auto mb-1 text-[#C8FF00] text-600" />
                      <p className="text-sm font-medium">{sub.max_services} Services</p>
                    </div>
                    {sub.includes_parts && (
                      <div className="text-center p-3 rounded-lg bg-[#111820]">
                        <Gift className="h-5 w-5 mx-auto mb-1 text-[#C8FF00] text-600" />
                        <p className="text-sm font-medium">{sub.parts_discount_percent}% Parts Discount</p>
                      </div>
                    )}
                    <div className="text-center p-3 rounded-lg bg-[#111820]">
                      <Phone className="h-5 w-5 mx-auto mb-1 text-[#C8FF00] text-600" />
                      <p className="text-sm font-medium">Priority Support</p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-[#111820]">
                      <Car className="h-5 w-5 mx-auto mb-1 text-[#C8FF00] text-600" />
                      <p className="text-sm font-medium">Roadside Assist</p>
                    </div>
                  </div>

                  {/* Actions */}
                  {(sub.status === 'expiring' || sub.status === 'expired') && (
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Renew Plan
                      </Button>
                      <Button variant="outline">
                        View Details
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Available Plans */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-[#F4F6F0]">
          {subscriptions.length > 0 ? "Upgrade or Add Another Plan" : "Available AMC Plans"}
        </h2>
        
        {availablePlans.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <Shield className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
              <p className="text-[rgba(244,246,240,0.35)]">No plans available at the moment</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {availablePlans.map((plan) => (
              <Card 
                key={plan.plan_id} 
                className={`overflow-hidden hover:shadow-lg transition-shadow ${
                  plan.tier === 'premium' ? 'ring-2 ring-purple-500' : ''
                }`}
              >
                {plan.tier === 'premium' && (
                  <div className="bg-[rgba(139,92,246,0.08)]0 text-white text-center text-xs font-bold py-1">
                    <Sparkles className="h-3 w-3 inline mr-1" />
                    MOST POPULAR
                  </div>
                )}
                
                <div className={`bg-gradient-to-r ${getTierColor(plan.tier)} p-6 text-white text-center`}>
                  <Shield className="h-10 w-10 mx-auto mb-2" />
                  <h3 className="font-bold text-xl">{plan.name}</h3>
                  <p className="text-white/80 text-sm capitalize">{plan.tier} Tier</p>
                </div>

                <CardContent className="p-6">
                  <div className="text-center mb-6">
                    <p className="text-4xl font-bold text-[#F4F6F0]">
                      ₹{plan.price.toLocaleString()}
                    </p>
                    <p className="text-[rgba(244,246,240,0.45)]">for {plan.duration_months} months</p>
                  </div>

                  <ul className="space-y-3 mb-6">
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500" />
                      {plan.max_service_visits} Free Services
                    </li>
                    {plan.includes_parts && (
                      <li className="flex items-center gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500" />
                        {plan.parts_discount_percent}% Discount on Parts
                      </li>
                    )}
                    {plan.priority_support && (
                      <li className="flex items-center gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500" />
                        Priority Support
                      </li>
                    )}
                    {plan.roadside_assistance && (
                      <li className="flex items-center gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-[#C8FF00] text-500" />
                        24/7 Roadside Assistance
                      </li>
                    )}
                  </ul>

                  <Button 
                    className={`w-full ${
                      plan.tier === 'premium' 
                        ? 'bg-[#8B5CF6] hover:bg-[#7c3aed] text-white font-bold' 
                        : 'bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold'
                    }`}
                    onClick={() => setSelectedPlan(plan)}
                  >
                    Select Plan
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Plan Selection Dialog */}
      <Dialog open={!!selectedPlan} onOpenChange={() => setSelectedPlan(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Subscribe to {selectedPlan?.name}</DialogTitle>
            <DialogDescription>
              Contact our team to complete your AMC subscription
            </DialogDescription>
          </DialogHeader>
          
          {selectedPlan && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-[#111820] rounded-lg">
                <h4 className="font-semibold mb-2">Plan Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[rgba(244,246,240,0.35)]">Plan</span>
                    <span className="font-medium">{selectedPlan.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[rgba(244,246,240,0.35)]">Duration</span>
                    <span className="font-medium">{selectedPlan.duration_months} months</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[rgba(244,246,240,0.35)]">Services Included</span>
                    <span className="font-medium">{selectedPlan.max_service_visits}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2 mt-2">
                    <span className="font-semibold">Total</span>
                    <span className="font-bold text-lg">₹{selectedPlan.price.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">How to Subscribe</h4>
                <ol className="text-sm text-blue-800 space-y-2">
                  <li>1. Call us at <span className="font-mono">1800-XXX-XXXX</span></li>
                  <li>2. Visit any Battwheels service center</li>
                  <li>3. Request a callback and we'll reach out</li>
                </ol>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setSelectedPlan(null)}>
                  Cancel
                </Button>
                <Button className="flex-1 bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                  <Phone className="h-4 w-4 mr-2" />
                  Request Callback
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
