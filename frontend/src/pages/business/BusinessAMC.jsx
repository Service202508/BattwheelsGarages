import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  Shield, Calendar, Car, Clock, AlertCircle, CheckCircle,
  Loader2, FileText, IndianRupee, Plus, ArrowRight, Sparkles
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  active: "bg-bw-volt/10 text-bw-volt text-700",
  expired: "bg-bw-red/10 text-bw-red border border-bw-red/25",
  pending: "bg-amber-100 text-amber-700",
  cancelled: "bg-white/5 text-slate-600",
};

export default function BusinessAMC({ user }) {
  const [contracts, setContracts] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedContract, setSelectedContract] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  useEffect(() => {
    fetchAMCData();
  }, []);

  const fetchAMCData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/business/amc`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setContracts(data.contracts || []);
        setPlans(data.available_plans || []);
      }
    } catch (error) {
      console.error("Failed to fetch AMC data:", error);
      toast.error("Failed to load AMC contracts");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  const getDaysRemaining = (endDate) => {
    if (!endDate) return 0;
    const end = new Date(endDate);
    const now = new Date();
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return Math.max(0, diff);
  };

  const getContractProgress = (startDate, endDate) => {
    if (!startDate || !endDate) return 0;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const now = new Date();
    const total = end - start;
    const elapsed = now - start;
    return Math.min(100, Math.max(0, (elapsed / total) * 100));
  };

  const stats = {
    active: contracts.filter(c => c.status === "active").length,
    total: contracts.length,
    totalValue: contracts.reduce((sum, c) => sum + (c.contract_value || 0), 0)
  };

  return (
    <div className="space-y-6" data-testid="business-amc">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">AMC Contracts</h1>
          <p className="text-slate-500">Annual Maintenance Contracts for your fleet</p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700 hover:shadow-[0_0_20px_rgba(99,102,241,0.30)]">
          <Plus className="h-4 w-4 mr-2" />
          Request New AMC
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active Contracts</p>
                <p className="text-2xl font-bold text-bw-volt text-600">{stats.active}</p>
              </div>
              <div className="p-3 rounded bg-bw-volt/[0.08]">
                <Shield className="h-5 w-5 text-bw-volt text-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Contracts</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <div className="p-3 rounded bg-indigo-50">
                <FileText className="h-5 w-5 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Contract Value</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(stats.totalValue)}</p>
              </div>
              <div className="p-3 rounded bg-bw-purple/[0.08]">
                <IndianRupee className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Contracts */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : contracts.length === 0 ? (
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="py-12 text-center">
            <Shield className="h-16 w-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No AMC Contracts</h3>
            <p className="text-slate-500 mb-4">
              Protect your fleet with an Annual Maintenance Contract
            </p>
            <Button className="bg-indigo-600 hover:bg-indigo-700">
              <Plus className="h-4 w-4 mr-2" />
              Request AMC Quote
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {contracts.map((contract) => {
            const daysRemaining = getDaysRemaining(contract.end_date);
            const progress = getContractProgress(contract.start_date, contract.end_date);
            
            return (
              <Card 
                key={contract.amc_id || contract.contract_id} 
                className="bg-bw-panel border-white/[0.07] border-200 hover:border-bw-volt/20 transition-colors cursor-pointer"
                onClick={() => { setSelectedContract(contract); setShowDetailDialog(true); }}
                data-testid={`amc-card-${contract.amc_id || contract.contract_id}`}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded bg-indigo-50">
                        <Shield className="h-6 w-6 text-indigo-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">{contract.plan_name || "AMC Contract"}</h3>
                        <p className="text-sm text-slate-500">{contract.contract_id}</p>
                      </div>
                    </div>
                    <Badge className={statusColors[contract.status] || statusColors.active}>
                      {contract.status}
                    </Badge>
                  </div>
                  
                  {/* Vehicles Covered */}
                  <div className="flex items-center gap-2 mb-3 text-sm text-slate-600">
                    <Car className="h-4 w-4 text-slate-400" />
                    <span>{contract.vehicles_covered?.length || 0} vehicles covered</span>
                  </div>
                  
                  {/* Contract Period */}
                  <div className="flex items-center gap-2 mb-3 text-sm text-slate-600">
                    <Calendar className="h-4 w-4 text-slate-400" />
                    <span>{formatDate(contract.start_date)} - {formatDate(contract.end_date)}</span>
                  </div>
                  
                  {/* Progress */}
                  {contract.status === "active" && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-slate-500 mb-1">
                        <span>Contract Progress</span>
                        <span>{daysRemaining} days remaining</span>
                      </div>
                      <Progress value={progress} className="h-2" />
                    </div>
                  )}
                  
                  {/* Services Used */}
                  {contract.services_used !== undefined && (
                    <div className="flex items-center justify-between pt-3 border-t border-white/[0.07] border-100">
                      <span className="text-sm text-slate-500">Services Used</span>
                      <span className="font-medium text-slate-900">
                        {contract.services_used} / {contract.max_services || "Unlimited"}
                      </span>
                    </div>
                  )}
                  
                  {/* Value */}
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm text-slate-500">Contract Value</span>
                    <span className="font-bold text-indigo-600">
                      {formatCurrency(contract.contract_value)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Available Plans */}
      {plans.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-bold text-slate-900 mb-4">Available AMC Plans</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {plans.map((plan) => (
              <Card key={plan.plan_id} className="bg-bw-panel border-white/[0.07] border-200 hover:border-indigo-200 transition-colors">
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-indigo-50">
                      <Sparkles className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{plan.name}</h3>
                      <p className="text-xs text-slate-500">{plan.duration_months} months</p>
                    </div>
                  </div>
                  
                  <p className="text-sm text-slate-600 mb-4">{plan.description}</p>
                  
                  <ul className="space-y-2 mb-4">
                    {plan.features?.slice(0, 4).map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-slate-600">
                        <CheckCircle className="h-4 w-4 text-bw-volt text-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  
                  <div className="flex items-center justify-between pt-4 border-t border-white/[0.07] border-100">
                    <span className="text-2xl font-bold text-indigo-600">
                      {formatCurrency(plan.price)}
                    </span>
                    <Button size="sm" variant="outline">
                      Get Quote
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Contract Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Contract Details</DialogTitle>
            <DialogDescription>
              {selectedContract?.contract_id}
            </DialogDescription>
          </DialogHeader>
          
          {selectedContract && (
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-between p-4 rounded bg-indigo-50">
                <div>
                  <p className="text-sm text-indigo-600">Plan</p>
                  <p className="font-semibold text-indigo-700">{selectedContract.plan_name}</p>
                </div>
                <Badge className={statusColors[selectedContract.status]}>
                  {selectedContract.status}
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-slate-50">
                  <p className="text-xs text-slate-500">Start Date</p>
                  <p className="font-medium text-slate-900">{formatDate(selectedContract.start_date)}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50">
                  <p className="text-xs text-slate-500">End Date</p>
                  <p className="font-medium text-slate-900">{formatDate(selectedContract.end_date)}</p>
                </div>
              </div>
              
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 mb-2">Vehicles Covered</p>
                <div className="flex flex-wrap gap-2">
                  {selectedContract.vehicles_covered?.map((v, idx) => (
                    <Badge key={idx} variant="outline">
                      <Car className="h-3 w-3 mr-1" />
                      {v}
                    </Badge>
                  )) || <span className="text-slate-400">No vehicles</span>}
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 rounded-lg bg-bw-volt/[0.08]">
                <span className="text-sm text-bw-volt text-700">Contract Value</span>
                <span className="text-xl font-bold text-bw-volt text-700">
                  {formatCurrency(selectedContract.contract_value)}
                </span>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              Close
            </Button>
            <Button className="bg-indigo-600 hover:bg-indigo-700">
              <FileText className="h-4 w-4 mr-2" />
              Download Contract
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
