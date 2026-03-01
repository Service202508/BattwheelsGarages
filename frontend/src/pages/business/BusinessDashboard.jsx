import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
  Car, Ticket, FileText, CreditCard, Shield, TrendingUp,
  Clock, AlertCircle, CheckCircle, ArrowRight, Loader2,
  IndianRupee, Plus, BarChart3, Wrench
} from "lucide-react";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  open: "bg-blue-100 text-bw-blue",
  in_progress: "bg-amber-100 text-amber-700",
  work_in_progress: "bg-amber-100 text-amber-700",
  completed: "bg-bw-volt/10 text-bw-volt text-700",
  pending: "bg-purple-100 text-bw-purple",
};

export default function BusinessDashboard({ user }) {
  const [dashboard, setDashboard] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [pendingInvoices, setPendingInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
    fetchRecentTickets();
    fetchPendingInvoices();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/business/dashboard`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentTickets = async () => {
    try {
      const res = await fetch(`${API}/business/tickets?status=active&limit=5`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setRecentTickets(data.tickets || []);
      }
    } catch (error) {
      console.error("Failed to fetch tickets:", error);
    }
  };

  const fetchPendingInvoices = async () => {
    try {
      const res = await fetch(`${API}/business/invoices?status=unpaid&limit=5`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setPendingInvoices(data.invoices || []);
      }
    } catch (error) {
      console.error("Failed to fetch invoices:", error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="business-dashboard">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Welcome, {dashboard?.business?.name || user?.name}
          </h1>
          <p className="text-slate-500 mt-1">
            Here's your fleet operations overview
          </p>
        </div>
        <Link to="/business/tickets/new">
          <Button className="bg-indigo-600 hover:bg-indigo-700 hover:shadow-[0_0_20px_rgba(99,102,241,0.30)]">
            <Plus className="h-4 w-4 mr-2" />
            Raise Service Ticket
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Fleet Vehicles</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">{dashboard?.fleet?.total_vehicles || 0}</p>
                <p className="text-xs text-slate-400 mt-1">{dashboard?.fleet?.active_services || 0} in service</p>
              </div>
              <div className="p-3 rounded bg-indigo-50">
                <Car className="h-6 w-6 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Open Tickets</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">{dashboard?.tickets?.open || 0}</p>
                <p className="text-xs text-slate-400 mt-1">{dashboard?.tickets?.in_progress || 0} in progress</p>
              </div>
              <div className="p-3 rounded bg-amber-50">
                <Ticket className="h-6 w-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Pending Approval</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">{dashboard?.tickets?.pending_estimate_approval || 0}</p>
                <p className="text-xs text-slate-400 mt-1">estimates waiting</p>
              </div>
              <div className="p-3 rounded bg-bw-purple/[0.08]">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Pending Payment</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">
                  {formatCurrency(dashboard?.financials?.pending_payment)}
                </p>
                <p className="text-xs text-slate-400 mt-1">to be paid</p>
              </div>
              <div className="p-3 rounded bg-bw-red/[0.08]">
                <CreditCard className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resolution TAT & AMC */}
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <Clock className="h-5 w-5 text-indigo-600" />
              Resolution TAT
            </CardTitle>
            <CardDescription>Average turnaround time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <p className="text-5xl font-bold text-indigo-600">
                {dashboard?.resolution_tat_hours || 0}
              </p>
              <p className="text-slate-500 mt-1">hours</p>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Target</span>
                <span className="text-slate-900 font-medium">24 hours</span>
              </div>
              <Progress 
                value={Math.min((24 / (dashboard?.resolution_tat_hours || 24)) * 100, 100)} 
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <Shield className="h-5 w-5 text-bw-volt text-600" />
              AMC Status
            </CardTitle>
            <CardDescription>Active contracts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <p className="text-5xl font-bold text-bw-volt text-600">
                {dashboard?.amc?.active_contracts || 0}
              </p>
              <p className="text-slate-500 mt-1">active AMC contracts</p>
            </div>
            <Link to="/business/amc">
              <Button variant="outline" className="w-full mt-2">
                View Contracts
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-bw-blue" />
              This Month
            </CardTitle>
            <CardDescription>Tickets resolved</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <p className="text-5xl font-bold text-bw-blue">
                {dashboard?.tickets?.resolved_this_month || 0}
              </p>
              <p className="text-slate-500 mt-1">tickets resolved</p>
            </div>
            <Link to="/business/reports">
              <Button variant="outline" className="w-full mt-2">
                View Reports
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tickets & Pending Invoices */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Tickets */}
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-slate-900">Active Service Tickets</CardTitle>
              <CardDescription>Recent service requests</CardDescription>
            </div>
            <Link to="/business/tickets">
              <Button variant="ghost" size="sm" className="text-indigo-600">
                View All <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentTickets.length === 0 ? (
              <div className="text-center py-8">
                <Ticket className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                <p className="text-slate-500">No active tickets</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentTickets.map((ticket) => (
                  <Link 
                    key={ticket.ticket_id}
                    to={`/business/tickets/${ticket.ticket_id}`}
                    className="block p-4 rounded border border-white/[0.07] border-200 hover:border-indigo-200 hover:bg-indigo-50/50 transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={statusColors[ticket.status] || statusColors.open}>
                            {ticket.status?.replace(/_/g, ' ')}
                          </Badge>
                          <span className="text-xs text-slate-400">{ticket.ticket_id}</span>
                        </div>
                        <h4 className="font-medium text-slate-900">{ticket.title}</h4>
                        <p className="text-sm text-slate-500 mt-1">{ticket.vehicle_number}</p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-slate-400" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Invoices */}
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-slate-900">Pending Invoices</CardTitle>
              <CardDescription>Invoices awaiting payment</CardDescription>
            </div>
            <Link to="/business/invoices">
              <Button variant="ghost" size="sm" className="text-indigo-600">
                View All <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {pendingInvoices.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                <p className="text-slate-500">No pending invoices</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingInvoices.map((invoice) => (
                  <div 
                    key={invoice.invoice_id}
                    className="p-4 rounded border border-white/[0.07] border-200 hover:border-indigo-200 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-slate-900">{invoice.invoice_number}</p>
                        <p className="text-sm text-slate-500">{invoice.date}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-indigo-600">{formatCurrency(invoice.balance)}</p>
                        <Badge variant="outline" className="text-xs">Due</Badge>
                      </div>
                    </div>
                  </div>
                ))}
                
                <Link to="/business/payments">
                  <Button className="w-full bg-indigo-600 hover:bg-indigo-700 mt-2">
                    <CreditCard className="h-4 w-4 mr-2" />
                    Make Payment
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Financial Summary */}
      <Card className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white border border-white/[0.13]">
        <CardContent className="p-6">
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <p className="text-indigo-100 text-sm font-medium">Total Invoiced (All Time)</p>
              <p className="text-3xl font-bold mt-2">{formatCurrency(dashboard?.financials?.total_invoiced)}</p>
            </div>
            <div>
              <p className="text-indigo-100 text-sm font-medium">Total Paid</p>
              <p className="text-3xl font-bold mt-2">{formatCurrency(dashboard?.financials?.total_paid)}</p>
            </div>
            <div>
              <p className="text-indigo-100 text-sm font-medium">Outstanding</p>
              <p className="text-3xl font-bold mt-2">{formatCurrency(dashboard?.financials?.pending_payment)}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
