import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Search, Car, Battery, Zap, Edit } from "lucide-react";
import { API } from "@/App";

const statusColors = {
  active: "badge-success",
  in_workshop: "badge-warning",
  serviced: "badge-info",
};

export default function Vehicles({ user }) {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [formData, setFormData] = useState({
    owner_name: "",
    make: "",
    model: "",
    year: new Date().getFullYear(),
    registration_number: "",
    battery_capacity: 0,
  });

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/vehicles`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
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

  const handleSubmit = async () => {
    if (!formData.make || !formData.model || !formData.registration_number) {
      toast.error("Please fill in required fields");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/vehicles`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Vehicle added!");
        fetchVehicles();
        resetForm();
      } else {
        toast.error("Failed to add vehicle");
      }
    } catch (error) {
      toast.error("Network error");
    }
  };

  const updateStatus = async (vehicleId, status) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/vehicles/${vehicleId}/status?status=${status}`, {
        method: "PUT",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include",
      });
      if (response.ok) {
        toast.success("Status updated");
        fetchVehicles();
      }
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  const resetForm = () => {
    setFormData({
      owner_name: "",
      make: "",
      model: "",
      year: new Date().getFullYear(),
      registration_number: "",
      battery_capacity: 0,
    });
    setIsAddOpen(false);
  };

  const filteredVehicles = vehicles.filter(v =>
    v.make?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.model?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.registration_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="vehicles-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Vehicles</h1>
          <p className="text-muted-foreground mt-1">Manage registered EVs in the system.</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="glow-primary" data-testid="add-vehicle-btn">
              <Plus className="h-4 w-4 mr-2" />
              Add Vehicle
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card border-white/10 max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Vehicle</DialogTitle>
              <DialogDescription>Register a new EV in the system.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Owner Name</Label>
                <Input
                  value={formData.owner_name}
                  onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                  className="bg-background/50"
                  data-testid="owner-name-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Make *</Label>
                  <Input
                    value={formData.make}
                    onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                    placeholder="e.g., Tata"
                    className="bg-background/50"
                    data-testid="make-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Model *</Label>
                  <Input
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    placeholder="e.g., Nexon EV"
                    className="bg-background/50"
                    data-testid="model-input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Year</Label>
                  <Input
                    type="number"
                    value={formData.year}
                    onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                    className="bg-background/50"
                    data-testid="year-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Battery Capacity (kWh)</Label>
                  <Input
                    type="number"
                    value={formData.battery_capacity}
                    onChange={(e) => setFormData({ ...formData, battery_capacity: parseFloat(e.target.value) })}
                    className="bg-background/50"
                    data-testid="battery-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Registration Number *</Label>
                <Input
                  value={formData.registration_number}
                  onChange={(e) => setFormData({ ...formData, registration_number: e.target.value.toUpperCase() })}
                  placeholder="e.g., MH12AB1234"
                  className="bg-background/50"
                  data-testid="registration-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={resetForm} className="border-white/10">
                Cancel
              </Button>
              <Button onClick={handleSubmit} className="glow-primary" data-testid="save-vehicle-btn">
                Add Vehicle
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="metric-card card-hover">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Vehicles</p>
              <p className="text-2xl font-bold mono">{vehicles.length}</p>
            </div>
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Car className="h-5 w-5 text-primary" />
            </div>
          </CardContent>
        </Card>
        <Card className="metric-card card-hover">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">In Workshop</p>
              <p className="text-2xl font-bold mono">
                {vehicles.filter(v => v.current_status === "in_workshop").length}
              </p>
            </div>
            <div className="h-10 w-10 rounded-lg bg-chart-2/10 flex items-center justify-center">
              <Zap className="h-5 w-5 text-chart-2" />
            </div>
          </CardContent>
        </Card>
        <Card className="metric-card card-hover">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Avg Battery</p>
              <p className="text-2xl font-bold mono">
                {vehicles.length > 0 
                  ? Math.round(vehicles.reduce((acc, v) => acc + (v.battery_capacity || 0), 0) / vehicles.length)
                  : 0} kWh
              </p>
            </div>
            <div className="h-10 w-10 rounded-lg bg-chart-3/10 flex items-center justify-center">
              <Battery className="h-5 w-5 text-chart-3" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search vehicles..."
              className="pl-10 bg-background/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="search-vehicles-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Vehicles Table */}
      <Card className="border-white/10 bg-card/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading vehicles...</div>
          ) : filteredVehicles.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No vehicles found. Add your first vehicle to get started.
            </div>
          ) : (
            <Table className="data-table">
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Registration</TableHead>
                  <TableHead>Battery</TableHead>
                  <TableHead>Status</TableHead>
                  {(user?.role === "admin" || user?.role === "technician") && (
                    <TableHead className="text-right">Actions</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredVehicles.map((vehicle) => (
                  <TableRow key={vehicle.vehicle_id} className="border-white/10">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Car className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{vehicle.make} {vehicle.model}</p>
                          <p className="text-xs text-muted-foreground">{vehicle.year}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{vehicle.owner_name || "-"}</TableCell>
                    <TableCell className="mono text-sm">{vehicle.registration_number}</TableCell>
                    <TableCell className="mono">{vehicle.battery_capacity} kWh</TableCell>
                    <TableCell>
                      <Badge className={statusColors[vehicle.current_status]} variant="outline">
                        {vehicle.current_status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    {(user?.role === "admin" || user?.role === "technician") && (
                      <TableCell className="text-right">
                        <select
                          value={vehicle.current_status}
                          onChange={(e) => updateStatus(vehicle.vehicle_id, e.target.value)}
                          className="bg-background/50 border border-white/10 rounded px-2 py-1 text-sm"
                        >
                          <option value="active">Active</option>
                          <option value="in_workshop">In Workshop</option>
                          <option value="serviced">Serviced</option>
                        </select>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
