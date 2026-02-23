import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Car, Battery, Calendar, Wrench, Shield, ArrowRight, 
  AlertCircle, CheckCircle
} from "lucide-react";
import { API } from "@/App";

export default function CustomerVehicles({ user }) {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/vehicles`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setVehicles(data);
      }
    } catch (error) {
      console.error("Failed to fetch vehicles:", error);
    } finally {
      setLoading(false);
    }
  };

  const getAMCStatusColor = (status) => {
    if (!status) return "";
    const colors = {
      active: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)] border-green-200",
      expiring: "bg-orange-100 text-[#FF8C00] border-orange-200",
      expired: "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)] border-red-200"
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
    <div className="space-y-6" data-testid="customer-vehicles">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">My Vehicles</h1>
          <p className="text-[rgba(244,246,240,0.35)]">Manage your registered EVs and view service details</p>
        </div>
      </div>

      {/* Vehicles Grid */}
      {vehicles.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Car className="h-16 w-16 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
            <h3 className="text-lg font-semibold text-[#F4F6F0] mb-2">No Vehicles Registered</h3>
            <p className="text-[rgba(244,246,240,0.35)] mb-4">
              Your registered vehicles will appear here. Contact support to add your vehicle.
            </p>
            <Link to="/customer/request-callback">
              <Button>Contact Support</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {vehicles.map((vehicle) => (
            <Card key={vehicle.vehicle_id} className="overflow-hidden hover:shadow-lg transition-shadow">
              {/* Vehicle Header */}
              <div className="bg-gradient-to-r from-gray-800 to-gray-900 p-4 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-[#111820]/10">
                      <Car className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="font-bold text-lg">{vehicle.registration_number}</p>
                      <p className="text-[rgba(244,246,240,0.20)] text-sm">{vehicle.make} {vehicle.model}</p>
                    </div>
                  </div>
                  {vehicle.amc_plan && (
                    <Badge className={getAMCStatusColor(vehicle.amc_plan.status)}>
                      <Shield className="h-3 w-3 mr-1" />
                      AMC {vehicle.amc_plan.status}
                    </Badge>
                  )}
                </div>
              </div>

              <CardContent className="p-4 space-y-4">
                {/* Vehicle Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 rounded-lg bg-[#111820]">
                    <p className="text-2xl font-bold text-[#F4F6F0]">{vehicle.total_services || 0}</p>
                    <p className="text-xs text-[rgba(244,246,240,0.35)]">Total Services</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-[#111820]">
                    <p className="text-2xl font-bold text-[#F4F6F0]">₹{(vehicle.total_service_cost || 0).toLocaleString()}</p>
                    <p className="text-xs text-[rgba(244,246,240,0.35)]">Total Spent</p>
                  </div>
                </div>

                {/* Vehicle Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-[rgba(244,246,240,0.35)] flex items-center gap-2">
                      <Battery className="h-4 w-4" /> Battery
                    </span>
                    <span className="font-medium">{vehicle.battery_capacity || "N/A"} kWh</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[rgba(244,246,240,0.35)] flex items-center gap-2">
                      <Calendar className="h-4 w-4" /> Year
                    </span>
                    <span className="font-medium">{vehicle.year || "N/A"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[rgba(244,246,240,0.35)] flex items-center gap-2">
                      <Wrench className="h-4 w-4" /> Last Service
                    </span>
                    <span className="font-medium">
                      {vehicle.last_service_date 
                        ? new Date(vehicle.last_service_date).toLocaleDateString() 
                        : "No service yet"
                      }
                    </span>
                  </div>
                </div>

                {/* AMC Info */}
                {vehicle.amc_plan && (
                  <div className={`p-3 rounded-lg border ${
                    vehicle.amc_plan.status === 'expiring' ? 'bg-[rgba(255,140,0,0.08)] border-orange-200' : 'bg-[rgba(200,255,0,0.08)] border-[rgba(200,255,0,0.20)]'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className={`h-4 w-4 ${
                          vehicle.amc_plan.status === 'expiring' ? 'text-[#FF8C00]' : 'text-[#C8FF00] text-600'
                        }`} />
                        <span className="font-medium text-sm">{vehicle.amc_plan.plan_name}</span>
                      </div>
                      <span className="text-xs text-[rgba(244,246,240,0.35)]">
                        Expires: {new Date(vehicle.amc_plan.end_date).toLocaleDateString()}
                      </span>
                    </div>
                    {vehicle.amc_plan.status === 'expiring' && (
                      <p className="text-xs text-[#FF8C00] mt-1 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Expiring soon - Renew now for uninterrupted coverage
                      </p>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Link to={`/customer/service-history?vehicle_id=${vehicle.vehicle_id}`} className="flex-1">
                    <Button variant="outline" className="w-full" size="sm">
                      Service History
                    </Button>
                  </Link>
                  <Link to="/customer/book-appointment" className="flex-1">
                    <Button className="w-full bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" size="sm">
                      Book Service
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
