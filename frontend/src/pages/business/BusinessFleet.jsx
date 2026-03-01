import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import {
  Car, Plus, Search, Loader2, MoreVertical, Trash2,
  AlertCircle, CheckCircle, Wrench, Filter, RefreshCw, User, Phone
} from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { API, getAuthHeaders } from "@/App";

const statusColors = {
  active: "bg-bw-volt/10 text-bw-volt text-700",
  inactive: "bg-white/5 text-slate-600",
  in_service: "bg-amber-100 text-amber-700",
};

export default function BusinessFleet({ user }) {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [vehicleCategories, setVehicleCategories] = useState([]);
  const [vehicleModels, setVehicleModels] = useState([]);
  
  const [formData, setFormData] = useState({
    vehicle_number: "",
    vehicle_category: "",
    vehicle_model_id: "",
    vehicle_model_name: "",
    vehicle_oem: "",
    year_of_manufacture: "",
    chassis_number: "",
    battery_serial: "",
    driver_name: "",
    driver_phone: ""
  });

  useEffect(() => {
    fetchFleet();
    fetchMasterData();
  }, []);

  const fetchFleet = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/business/fleet`, {
        headers: getAuthHeaders(),
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setVehicles(data.vehicles || []);
      }
    } catch (error) {
      console.error("Failed to fetch fleet:", error);
      toast.error("Failed to load fleet vehicles");
    } finally {
      setLoading(false);
    }
  };

  const fetchMasterData = async () => {
    try {
      const [categoriesRes, modelsRes] = await Promise.all([
        fetch(`${API}/master-data/vehicle-categories`),
        fetch(`${API}/master-data/vehicle-models`)
      ]);
      
      if (categoriesRes.ok) {
        const data = await categoriesRes.json();
        setVehicleCategories(data.categories || []);
      }
      if (modelsRes.ok) {
        const data = await modelsRes.json();
        setVehicleModels(data.models || []);
      }
    } catch (error) {
      console.error("Failed to fetch master data:", error);
    }
  };

  const handleAddVehicle = async () => {
    if (!formData.vehicle_number || !formData.vehicle_category || !formData.vehicle_model_name) {
      toast.error("Please fill in all required fields");
      return;
    }
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/business/fleet`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        toast.success("Vehicle added to fleet successfully");
        setShowAddDialog(false);
        setFormData({
          vehicle_number: "",
          vehicle_category: "",
          vehicle_model_id: "",
          vehicle_model_name: "",
          vehicle_oem: "",
          year_of_manufacture: "",
          chassis_number: "",
          battery_serial: "",
          driver_name: "",
          driver_phone: ""
        });
        fetchFleet();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to add vehicle");
      }
    } catch (error) {
      toast.error("Failed to add vehicle");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveVehicle = async (vehicleId) => {
    if (!confirm("Are you sure you want to remove this vehicle from the fleet?")) return;
    
    try {
      const res = await fetch(`${API}/business/fleet/${vehicleId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
        credentials: "include"
      });
      
      if (res.ok) {
        toast.success("Vehicle removed from fleet");
        fetchFleet();
      } else {
        toast.error("Failed to remove vehicle");
      }
    } catch (error) {
      toast.error("Failed to remove vehicle");
    }
  };

  const handleModelSelect = (modelId) => {
    const model = vehicleModels.find(m => m.model_id === modelId);
    if (model) {
      setFormData(prev => ({
        ...prev,
        vehicle_model_id: modelId,
        vehicle_model_name: model.name,
        vehicle_oem: model.oem,
        vehicle_category: model.category_id || prev.vehicle_category
      }));
    }
  };

  const filteredVehicles = vehicles.filter(v => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      v.vehicle_number?.toLowerCase().includes(search) ||
      v.vehicle_model?.toLowerCase().includes(search) ||
      v.driver_name?.toLowerCase().includes(search)
    );
  });

  const stats = {
    total: vehicles.length,
    active: vehicles.filter(v => v.status === "active").length,
    inService: vehicles.filter(v => v.active_service).length
  };

  return (
    <div className="space-y-6" data-testid="business-fleet">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Fleet Management</h1>
          <p className="text-slate-500">Manage your fleet vehicles</p>
        </div>
        <Button 
          onClick={() => setShowAddDialog(true)}
          className="bg-indigo-600 hover:bg-indigo-700 hover:shadow-[0_0_20px_rgba(99,102,241,0.30)]"
          data-testid="add-vehicle-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Vehicle
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Vehicles</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <div className="p-3 rounded bg-indigo-50">
                <Car className="h-5 w-5 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active</p>
                <p className="text-2xl font-bold text-bw-volt text-600">{stats.active}</p>
              </div>
              <div className="p-3 rounded bg-bw-volt/[0.08]">
                <CheckCircle className="h-5 w-5 text-bw-volt text-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">In Service</p>
                <p className="text-2xl font-bold text-amber-600">{stats.inService}</p>
              </div>
              <div className="p-3 rounded bg-amber-50">
                <Wrench className="h-5 w-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search & Filter */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search vehicles..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Button variant="outline" onClick={fetchFleet}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Vehicles Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : filteredVehicles.length === 0 ? (
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <CardContent className="py-12 text-center">
            <Car className="h-16 w-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No vehicles found</h3>
            <p className="text-slate-500">
              {searchTerm ? "Try adjusting your search" : "Add your first vehicle to get started"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-bw-panel border-white/[0.07] border-200">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Vehicle</TableHead>
                <TableHead>Model / OEM</TableHead>
                <TableHead>Driver</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Active Service</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredVehicles.map((vehicle) => (
                <TableRow key={vehicle.vehicle_id} data-testid={`vehicle-row-${vehicle.vehicle_id}`}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-indigo-50">
                        <Car className="h-5 w-5 text-indigo-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{vehicle.vehicle_number}</p>
                        <p className="text-xs text-slate-500">{vehicle.vehicle_category}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <p className="font-medium text-slate-900">{vehicle.vehicle_model}</p>
                    <p className="text-xs text-slate-500">{vehicle.vehicle_oem}</p>
                  </TableCell>
                  <TableCell>
                    {vehicle.driver_name ? (
                      <div>
                        <div className="flex items-center gap-1 text-sm text-slate-700">
                          <User className="h-3 w-3" />
                          {vehicle.driver_name}
                        </div>
                        {vehicle.driver_phone && (
                          <div className="flex items-center gap-1 text-xs text-slate-500">
                            <Phone className="h-3 w-3" />
                            {vehicle.driver_phone}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={statusColors[vehicle.status] || statusColors.active}>
                      {vehicle.status || "active"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {vehicle.active_service ? (
                      <Badge className="bg-amber-100 text-amber-700">
                        {vehicle.active_service.ticket_id}
                      </Badge>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem 
                          onClick={() => handleRemoveVehicle(vehicle.vehicle_id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Remove
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Add Vehicle Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Vehicle to Fleet</DialogTitle>
            <DialogDescription>Add a new vehicle to your fleet for service tracking</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Vehicle Number *</Label>
                <Input
                  placeholder="e.g., MH12AB1234"
                  value={formData.vehicle_number}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_number: e.target.value.toUpperCase() }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Vehicle Category *</Label>
                <Select 
                  value={formData.vehicle_category}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, vehicle_category: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {vehicleCategories.map(cat => (
                      <SelectItem key={cat.category_id} value={cat.category_id}>
                        {cat.name}
                      </SelectItem>
                    ))}
                    <SelectItem value="2W_EV">2-Wheeler EV</SelectItem>
                    <SelectItem value="3W_EV">3-Wheeler EV</SelectItem>
                    <SelectItem value="4W_EV">4-Wheeler EV</SelectItem>
                    <SelectItem value="COMM_EV">Commercial EV</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Vehicle Model *</Label>
                <Select 
                  value={formData.vehicle_model_id}
                  onValueChange={handleModelSelect}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {vehicleModels.map(model => (
                      <SelectItem key={model.model_id} value={model.model_id}>
                        {model.oem} - {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Or Enter Model Name</Label>
                <Input
                  placeholder="Model name"
                  value={formData.vehicle_model_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_model_name: e.target.value }))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>OEM</Label>
                <Input
                  placeholder="e.g., Tata, Ola, Ather"
                  value={formData.vehicle_oem}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_oem: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Year of Manufacture</Label>
                <Input
                  type="number"
                  placeholder="e.g., 2024"
                  value={formData.year_of_manufacture}
                  onChange={(e) => setFormData(prev => ({ ...prev, year_of_manufacture: e.target.value }))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Driver Name</Label>
                <Input
                  placeholder="Driver name"
                  value={formData.driver_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, driver_name: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Driver Phone</Label>
                <Input
                  placeholder="Phone number"
                  value={formData.driver_phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, driver_phone: e.target.value }))}
                />
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleAddVehicle}
              disabled={submitting}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              Add Vehicle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
