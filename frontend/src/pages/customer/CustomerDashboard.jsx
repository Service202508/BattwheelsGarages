import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Car, ClipboardList, FileText, CreditCard, Shield, 
  ArrowRight, AlertCircle, CheckCircle, Clock, Phone
} from "lucide-react";
import { API } from "@/App";

export default function CustomerDashboard({ user }) {
  const [dashboard, setDashboard] = useState(null);
  const [recentServices, setRecentServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
    fetchRecentServices();
  }, []);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/dashboard`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setDashboard(data);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentServices = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/service-history?limit=3`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setRecentServices(data);
      }
    } catch (error) {
      console.error("Failed to fetch recent services:", error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      open: "bg-yellow-100 text-[#EAB308]",
      in_progress: "bg-blue-100 text-[#3B9EFF]",
      resolved: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
      closed: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]"
    };
    return colors[status] || "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customer-dashboard">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-1">
          Welcome back, {user?.name?.split(" ")[0] || "Customer"}!
        </h1>
        <p className="text-[#C8FF00] text-100">
          Manage your vehicles, track services, and view invoices all in one place.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to="/customer/book-appointment">
            <Button className="bg-[#111820] text-[#C8FF00] text-700 hover:bg-[rgba(200,255,0,0.08)]">
              <Clock className="h-4 w-4 mr-2" />
              Book Service
            </Button>
          </Link>
          <Link to="/customer/request-callback">
            <Button variant="outline" className="border-white text-white hover:bg-[#111820]/10">
              <Phone className="h-4 w-4 mr-2" />
              Request Callback
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="hover:border-[rgba(255,255,255,0.12)] transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-[rgba(244,246,240,0.35)]">My Vehicles</CardTitle>
            <Car className="h-5 w-5 text-[#C8FF00] text-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{dashboard?.vehicles_count || 0}</p>
            <Link to="/customer/vehicles" className="text-sm text-[#C8FF00] text-600 hover:underline flex items-center mt-1">
              View all <ArrowRight className="h-3 w-3 ml-1" />
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-[rgba(255,255,255,0.12)] transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-[rgba(244,246,240,0.35)]">Active Services</CardTitle>
            <Clock className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{dashboard?.active_tickets || 0}</p>
            <Link to="/customer/service-history?status=in_progress" className="text-sm text-[#3B9EFF] hover:underline flex items-center mt-1">
              Track now <ArrowRight className="h-3 w-3 ml-1" />
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-[rgba(255,255,255,0.12)] transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-[rgba(244,246,240,0.35)]">Total Services</CardTitle>
            <ClipboardList className="h-5 w-5 text-purple-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{dashboard?.total_services || 0}</p>
            <Link to="/customer/service-history" className="text-sm text-purple-600 hover:underline flex items-center mt-1">
              View history <ArrowRight className="h-3 w-3 ml-1" />
            </Link>
          </CardContent>
        </Card>

        <Card className={`hover:border-[rgba(255,255,255,0.12)] transition-all ${dashboard?.pending_amount > 0 ? 'border-orange-200 bg-[rgba(255,140,0,0.08)]' : ''}`}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-[rgba(244,246,240,0.35)]">Pending Amount</CardTitle>
            <CreditCard className={`h-5 w-5 ${dashboard?.pending_amount > 0 ? 'text-orange-500' : 'text-[rgba(244,246,240,0.45)]'}`} />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">₹{(dashboard?.pending_amount || 0).toLocaleString()}</p>
            {dashboard?.pending_amount > 0 && (
              <Link to="/customer/payments" className="text-sm text-[#FF8C00] hover:underline flex items-center mt-1">
                Pay now <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            )}
          </CardContent>
        </Card>

        <Card className="hover:border-[rgba(255,255,255,0.12)] transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-[rgba(244,246,240,0.35)]">Active AMC</CardTitle>
            <Shield className="h-5 w-5 text-[#C8FF00] text-500" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{dashboard?.active_amc_plans || 0}</p>
            <Link to="/customer/amc" className="text-sm text-[#C8FF00] text-600 hover:underline flex items-center mt-1">
              Manage plans <ArrowRight className="h-3 w-3 ml-1" />
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Recent Services */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Services</CardTitle>
          <Link to="/customer/service-history">
            <Button variant="ghost" size="sm">
              View All <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {recentServices.length === 0 ? (
            <div className="text-center py-8 text-[rgba(244,246,240,0.45)]">
              <ClipboardList className="h-12 w-12 mx-auto mb-3 text-[rgba(244,246,240,0.20)]" />
              <p>No service history yet</p>
              <p className="text-sm">Your service records will appear here</p>
            </div>
          ) : (
            <div className="space-y-4">
              {recentServices.map((service) => (
                <div 
                  key={service.ticket_id}
                  className="flex items-center justify-between p-4 rounded-lg border bg-[#111820] hover:bg-[#111820] transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      service.status === 'resolved' || service.status === 'closed' 
                        ? 'bg-[rgba(34,197,94,0.10)]' 
                        : 'bg-blue-100'
                    }`}>
                      {service.status === 'resolved' || service.status === 'closed' 
                        ? <CheckCircle className="h-5 w-5 text-green-600" />
                        : <Clock className="h-5 w-5 text-[#3B9EFF]" />
                      }
                    </div>
                    <div>
                      <p className="font-medium text-[#F4F6F0]">{service.title}</p>
                      <div className="flex items-center gap-2 text-sm text-[rgba(244,246,240,0.45)]">
                        <span>{service.vehicle_number}</span>
                        <span>•</span>
                        <span>{new Date(service.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge className={getStatusColor(service.status)}>
                      {service.status?.replace("_", " ")}
                    </Badge>
                    <Link to={`/customer/service-history/${service.ticket_id}`}>
                      <Button variant="ghost" size="sm">
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Info Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Support Card */}
        <Card className="bg-gradient-to-br from-gray-50 to-gray-100">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-[#111820] shadow-sm">
                <Phone className="h-6 w-6 text-[#C8FF00] text-600" />
              </div>
              <div>
                <h3 className="font-semibold text-[#F4F6F0]">Need Help?</h3>
                <p className="text-sm text-[rgba(244,246,240,0.35)] mt-1">
                  Our support team is available 24/7 to assist you with any queries.
                </p>
                <div className="mt-3 space-y-1">
                  <p className="text-sm"><strong>Helpline:</strong> 1800-XXX-XXXX</p>
                  <p className="text-sm"><strong>Email:</strong> support@battwheels.in</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AMC Promo Card */}
        {(dashboard?.active_amc_plans || 0) === 0 && (
          <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-[rgba(200,255,0,0.20)]">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-[#111820] shadow-sm">
                  <Shield className="h-6 w-6 text-[#C8FF00] text-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-[#F4F6F0]">Get AMC Protection</h3>
                  <p className="text-sm text-[rgba(244,246,240,0.35)] mt-1">
                    Protect your EV with our Annual Maintenance Contract. Get priority service, discounts, and peace of mind.
                  </p>
                  <Link to="/customer/amc">
                    <Button size="sm" className="mt-3 bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                      Explore Plans
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
