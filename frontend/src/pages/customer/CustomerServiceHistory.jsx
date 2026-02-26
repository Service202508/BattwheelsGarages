import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { 
  Search, Filter, ClipboardList, Clock, CheckCircle, AlertCircle,
  Car, User, Calendar, ArrowRight, FileText, ChevronRight
} from "lucide-react";
import { API } from "@/App";

export default function CustomerServiceHistory({ user }) {
  const [searchParams] = useSearchParams();
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState(null);
  const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "all");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchServices();
  }, [statusFilter]);

  const fetchServices = async () => {
    try {
      const token = localStorage.getItem("token");
      let url = `${API}/customer/service-history?limit=50`;
      if (statusFilter && statusFilter !== "all") {
        url += `&status=${statusFilter}`;
      }
      const vehicleId = searchParams.get("vehicle_id");
      if (vehicleId) {
        url += `&vehicle_id=${vehicleId}`;
      }
      
      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setServices(data);
      }
    } catch (error) {
      console.error("Failed to fetch services:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchServiceDetail = async (ticketId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/customer/service-history/${ticketId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedService(data);
      }
    } catch (error) {
      console.error("Failed to fetch service detail:", error);
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      open: { color: "bg-yellow-100 text-[#EAB308]", icon: AlertCircle, label: "Open" },
      technician_assigned: { color: "bg-blue-100 text-[#3B9EFF]", icon: User, label: "Assigned" },
      estimate_shared: { color: "bg-purple-100 text-[#8B5CF6]", icon: FileText, label: "Estimate Shared" },
      estimate_approved: { color: "bg-indigo-100 text-indigo-700", icon: CheckCircle, label: "Approved" },
      in_progress: { color: "bg-[rgba(255,140,0,0.10)] text-[#FF8C00]", icon: Clock, label: "In Progress" },
      resolved: { color: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]", icon: CheckCircle, label: "Resolved" },
      closed: { color: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]", icon: CheckCircle, label: "Closed" }
    };
    return configs[status] || configs.open;
  };

  const filteredServices = services.filter(s => 
    s.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.vehicle_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.ticket_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customer-service-history">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Service History</h1>
          <p className="text-[rgba(244,246,240,0.35)]">Track all your vehicle services and repairs</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
              <Input
                placeholder="Search by ticket ID, vehicle, or issue..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Services List */}
      {filteredServices.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ClipboardList className="h-16 w-16 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
            <h3 className="text-lg font-semibold text-[#F4F6F0] mb-2">No Services Found</h3>
            <p className="text-[rgba(244,246,240,0.35)]">
              {searchTerm || statusFilter !== "all" 
                ? "Try adjusting your filters"
                : "Your service history will appear here"
              }
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredServices.map((service) => {
            const statusConfig = getStatusConfig(service.status);
            const StatusIcon = statusConfig.icon;
            
            return (
              <Card 
                key={service.ticket_id}
                className="hover:border-[rgba(255,255,255,0.12)] transition-all cursor-pointer"
                onClick={() => fetchServiceDetail(service.ticket_id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4 flex-1">
                      <div className={`p-3 rounded-xl ${statusConfig.color.split(" ")[0]}`}>
                        <StatusIcon className={`h-5 w-5 ${statusConfig.color.split(" ")[1]}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-[#F4F6F0] truncate">{service.title}</h3>
                          <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                        </div>
                        <p className="text-sm text-[rgba(244,246,240,0.35)] line-clamp-2 mb-2">{service.description}</p>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                          <span className="flex items-center gap-1">
                            <Car className="h-4 w-4" />
                            {service.vehicle_number}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {new Date(service.created_at).toLocaleDateString()}
                          </span>
                          {service.technician_name && (
                            <span className="flex items-center gap-1">
                              <User className="h-4 w-4" />
                              {service.technician_name}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      {service.total_cost > 0 && (
                        <p className="font-semibold text-[#F4F6F0]">₹{service.total_cost.toLocaleString()}</p>
                      )}
                      <ChevronRight className="h-5 w-5 text-[rgba(244,246,240,0.45)] mt-2 ml-auto" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Service Detail Dialog */}
      <Dialog open={!!selectedService} onOpenChange={() => setSelectedService(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedService && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <span>Service Details</span>
                  <Badge className={getStatusConfig(selectedService.status).color}>
                    {getStatusConfig(selectedService.status).label}
                  </Badge>
                </DialogTitle>
              </DialogHeader>
              
              <div className="space-y-6 py-4">
                {/* Ticket Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">Ticket ID</p>
                    <p className="font-mono font-medium">{selectedService.ticket_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">Vehicle</p>
                    <p className="font-medium">{selectedService.vehicle_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">Created</p>
                    <p className="font-medium">{new Date(selectedService.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">Technician</p>
                    <p className="font-medium">{selectedService.technician_name || "Not assigned"}</p>
                  </div>
                </div>

                {/* Issue */}
                <div>
                  <h4 className="font-semibold text-[#F4F6F0] mb-2">Issue Reported</h4>
                  <p className="text-[rgba(244,246,240,0.35)]">{selectedService.title}</p>
                  {selectedService.description && (
                    <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">{selectedService.description}</p>
                  )}
                </div>

                {/* Status Timeline */}
                {selectedService.status_history && selectedService.status_history.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-[#F4F6F0] mb-3">Service Timeline</h4>
                    <div className="space-y-3">
                      {selectedService.status_history.map((item, index) => (
                        <div key={index} className="flex items-start gap-3">
                          <div className="flex flex-col items-center">
                            <div className="h-3 w-3 rounded-full bg-[rgba(200,255,0,0.08)]0"></div>
                            {index < selectedService.status_history.length - 1 && (
                              <div className="w-0.5 h-8 bg-[#141E27] mt-1"></div>
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-[#F4F6F0]">
                              {getStatusConfig(item.status).label}
                            </p>
                            <p className="text-sm text-[rgba(244,246,240,0.45)]">
                              {new Date(item.timestamp).toLocaleString()}
                              {item.updated_by && ` • ${item.updated_by}`}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cost */}
                {selectedService.total_cost > 0 && (
                  <div className="bg-[#111820] rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[rgba(244,246,240,0.35)]">Total Cost</span>
                      <span className="text-xl font-bold text-[#F4F6F0]">
                        ₹{selectedService.total_cost.toLocaleString()}
                      </span>
                    </div>
                  </div>
                )}

                {/* Invoice Link */}
                {selectedService.invoice_id && (
                  <Link to={`/customer/invoices/${selectedService.invoice_id}`}>
                    <Button variant="outline" className="w-full">
                      <FileText className="h-4 w-4 mr-2" />
                      View Invoice
                    </Button>
                  </Link>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
