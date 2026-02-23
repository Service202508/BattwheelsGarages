import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Search, Plus, Phone, Mail, Building2, MapPin, 
  FileText, IndianRupee, Filter, MoreVertical, Edit, Eye
} from "lucide-react";
import { API } from "@/App";

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [total, setTotal] = useState(0);

  const [newCustomer, setNewCustomer] = useState({
    display_name: "",
    company_name: "",
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    gstin: "",
    billing_address: "",
    billing_city: "",
    billing_state: "",
    billing_pincode: "",
    payment_terms: 15
  });

  useEffect(() => {
    fetchCustomers();
  }, [search]);

  const fetchCustomers = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/books/customers?search=${search}&limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setCustomers(data.customers || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("Failed to fetch customers:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomer = async () => {
    if (!newCustomer.display_name) {
      toast.error("Display name is required");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/books/customers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newCustomer)
      });

      if (res.ok) {
        toast.success("Customer added successfully");
        setShowAddDialog(false);
        setNewCustomer({
          display_name: "", company_name: "", first_name: "", last_name: "",
          phone: "", email: "", gstin: "", billing_address: "",
          billing_city: "", billing_state: "", billing_pincode: "", payment_terms: 15
        });
        fetchCustomers();
      } else {
        toast.error("Failed to add customer");
      }
    } catch (error) {
      toast.error("Error adding customer");
    }
  };

  return (
    <div className="space-y-6" data-testid="customers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Customers</h1>
          <p className="text-[rgba(244,246,240,0.45)] text-sm mt-1">{total} customers in database</p>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="add-customer-btn">
              <Plus className="h-4 w-4 mr-2" />
              Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Customer</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="col-span-2">
                <Label>Display Name *</Label>
                <Input
                  value={newCustomer.display_name}
                  onChange={(e) => setNewCustomer({...newCustomer, display_name: e.target.value})}
                  placeholder="Customer display name"
                />
              </div>
              <div>
                <Label>First Name</Label>
                <Input
                  value={newCustomer.first_name}
                  onChange={(e) => setNewCustomer({...newCustomer, first_name: e.target.value})}
                />
              </div>
              <div>
                <Label>Last Name</Label>
                <Input
                  value={newCustomer.last_name}
                  onChange={(e) => setNewCustomer({...newCustomer, last_name: e.target.value})}
                />
              </div>
              <div>
                <Label>Company Name</Label>
                <Input
                  value={newCustomer.company_name}
                  onChange={(e) => setNewCustomer({...newCustomer, company_name: e.target.value})}
                />
              </div>
              <div>
                <Label>Phone</Label>
                <Input
                  value={newCustomer.phone}
                  onChange={(e) => setNewCustomer({...newCustomer, phone: e.target.value})}
                />
              </div>
              <div>
                <Label>Email</Label>
                <Input
                  type="email"
                  value={newCustomer.email}
                  onChange={(e) => setNewCustomer({...newCustomer, email: e.target.value})}
                />
              </div>
              <div>
                <Label>GSTIN</Label>
                <Input
                  value={newCustomer.gstin}
                  onChange={(e) => setNewCustomer({...newCustomer, gstin: e.target.value})}
                  placeholder="22AAAAA0000A1Z5"
                />
              </div>
              <div className="col-span-2">
                <Label>Billing Address</Label>
                <Input
                  value={newCustomer.billing_address}
                  onChange={(e) => setNewCustomer({...newCustomer, billing_address: e.target.value})}
                />
              </div>
              <div>
                <Label>City</Label>
                <Input
                  value={newCustomer.billing_city}
                  onChange={(e) => setNewCustomer({...newCustomer, billing_city: e.target.value})}
                />
              </div>
              <div>
                <Label>State</Label>
                <Input
                  value={newCustomer.billing_state}
                  onChange={(e) => setNewCustomer({...newCustomer, billing_state: e.target.value})}
                />
              </div>
              <div>
                <Label>Pincode</Label>
                <Input
                  value={newCustomer.billing_pincode}
                  onChange={(e) => setNewCustomer({...newCustomer, billing_pincode: e.target.value})}
                />
              </div>
              <div>
                <Label>Payment Terms (days)</Label>
                <Input
                  type="number"
                  value={newCustomer.payment_terms}
                  onChange={(e) => setNewCustomer({...newCustomer, payment_terms: parseInt(e.target.value)})}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
              <Button onClick={handleAddCustomer} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">
                Add Customer
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
        <Input
          placeholder="Search customers by name, phone, company..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="customer-search"
        />
      </div>

      {/* Customer List */}
      {loading ? (
        <div className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading customers...</div>
      ) : customers.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
            No customers found. Add your first customer to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {customers.map((customer) => (
            <Card key={customer.customer_id} className="border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.2)] transition-colors" data-testid={`customer-card-${customer.customer_id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-[#F4F6F0]">{customer.display_name}</h3>
                      {customer.company_name && (
                        <Badge variant="outline" className="text-xs">
                          <Building2 className="h-3 w-3 mr-1" />
                          {customer.company_name}
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-[rgba(244,246,240,0.45)]">
                      {customer.phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="h-3.5 w-3.5" />
                          {customer.phone}
                        </span>
                      )}
                      {customer.email && (
                        <span className="flex items-center gap-1">
                          <Mail className="h-3.5 w-3.5" />
                          {customer.email}
                        </span>
                      )}
                      {customer.billing_city && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {customer.billing_city}, {customer.billing_state}
                        </span>
                      )}
                    </div>
                    {customer.gstin && (
                      <div className="mt-2 text-xs text-[rgba(244,246,240,0.45)]">
                        GSTIN: {customer.gstin}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">Outstanding</p>
                      <p className={`font-semibold ${customer.outstanding_balance > 0 ? 'text-[#FF8C00]' : 'text-green-600'}`}>
                        ₹{(customer.outstanding_balance || 0).toLocaleString('en-IN')}
                      </p>
                    </div>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={() => setSelectedCustomer(customer)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-lg">
                        <DialogHeader>
                          <DialogTitle>{customer.display_name}</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">Customer ID</p>
                              <p className="font-medium">{customer.customer_id}</p>
                            </div>
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">Company</p>
                              <p className="font-medium">{customer.company_name || '-'}</p>
                            </div>
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">Phone</p>
                              <p className="font-medium">{customer.phone || '-'}</p>
                            </div>
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">Email</p>
                              <p className="font-medium">{customer.email || '-'}</p>
                            </div>
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">GSTIN</p>
                              <p className="font-medium">{customer.gstin || '-'}</p>
                            </div>
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">Payment Terms</p>
                              <p className="font-medium">{customer.payment_terms || 15} days</p>
                            </div>
                            <div className="col-span-2">
                              <p className="text-[rgba(244,246,240,0.45)]">Billing Address</p>
                              <p className="font-medium">
                                {customer.billing_address || '-'}
                                {customer.billing_city && `, ${customer.billing_city}`}
                                {customer.billing_state && `, ${customer.billing_state}`}
                                {customer.billing_pincode && ` - ${customer.billing_pincode}`}
                              </p>
                            </div>
                            <div>
                              <p className="text-[rgba(244,246,240,0.45)]">Outstanding Balance</p>
                              <p className={`font-semibold text-lg ${customer.outstanding_balance > 0 ? 'text-[#FF8C00]' : 'text-green-600'}`}>
                                ₹{(customer.outstanding_balance || 0).toLocaleString('en-IN')}
                              </p>
                            </div>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
