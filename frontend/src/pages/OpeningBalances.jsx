import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { 
  Plus, RefreshCw, Loader2, Users, Building2, 
  Landmark, IndianRupee, Calendar
} from "lucide-react";
import { API } from "@/App";

export default function OpeningBalances() {
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("customer");
  const [customers, setCustomers] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [accounts, setAccounts] = useState([]);
  
  const [formData, setFormData] = useState({
    entity_type: "customer",
    entity_id: "",
    entity_name: "",
    opening_balance: 0,
    as_of_date: new Date().toISOString().split('T')[0],
    notes: ""
  });

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchBalances();
    fetchEntities();
  }, [activeTab]);

  const fetchBalances = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/zoho/opening-balances?entity_type=${activeTab}`, { headers });
      const data = await res.json();
      setBalances(data.opening_balances || []);
    } catch (error) {
      console.error("Error fetching opening balances:", error);
      toast.error("Failed to load opening balances");
    } finally {
      setLoading(false);
    }
  };

  const fetchEntities = async () => {
    try {
      // Fetch customers
      const custRes = await fetch(`${API}/zoho/contacts?contact_type=customer`, { headers });
      const custData = await custRes.json();
      setCustomers(custData.contacts || []);
      
      // Fetch vendors
      const vendRes = await fetch(`${API}/zoho/contacts?contact_type=vendor`, { headers });
      const vendData = await vendRes.json();
      setVendors(vendData.contacts || []);
      
      // Fetch accounts
      const accRes = await fetch(`${API}/zoho/chartofaccounts`, { headers });
      const accData = await accRes.json();
      setAccounts(accData.accounts || []);
    } catch (error) {
      console.error("Error fetching entities:", error);
    }
  };

  const handleCreate = async () => {
    if (!formData.entity_id || !formData.opening_balance || !formData.as_of_date) {
      toast.error("Please fill all required fields");
      return;
    }

    try {
      // Get entity name
      let entityName = "";
      if (formData.entity_type === "customer") {
        entityName = customers.find(c => c.contact_id === formData.entity_id)?.contact_name || "";
      } else if (formData.entity_type === "vendor") {
        entityName = vendors.find(v => v.contact_id === formData.entity_id)?.contact_name || "";
      } else {
        entityName = accounts.find(a => a.account_id === formData.entity_id)?.account_name || "";
      }

      const payload = {
        ...formData,
        entity_name: entityName
      };

      const res = await fetch(`${API}/zoho/opening-balances`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Opening balance set successfully");
        setDialogOpen(false);
        fetchBalances();
        resetForm();
      } else {
        toast.error(data.message || "Failed to set opening balance");
      }
    } catch (error) {
      toast.error("Failed to set opening balance");
    }
  };

  const resetForm = () => {
    setFormData({
      entity_type: activeTab,
      entity_id: "",
      entity_name: "",
      opening_balance: 0,
      as_of_date: new Date().toISOString().split('T')[0],
      notes: ""
    });
  };

  const getEntityOptions = () => {
    switch (formData.entity_type) {
      case "customer":
        return customers.map(c => ({ id: c.contact_id, name: c.contact_name }));
      case "vendor":
        return vendors.map(v => ({ id: v.contact_id, name: v.contact_name }));
      case "account":
        return accounts.map(a => ({ id: a.account_id, name: a.account_name }));
      default:
        return [];
    }
  };

  const formatCurrency = (value) => `₹${(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const getEntityIcon = (type) => {
    switch (type) {
      case "customer": return <Users className="h-4 w-4" />;
      case "vendor": return <Building2 className="h-4 w-4" />;
      case "account": return <Landmark className="h-4 w-4" />;
      default: return null;
    }
  };

  const getEntityTypeBadge = (type) => {
    const styles = {
      customer: "bg-blue-100 text-blue-800",
      vendor: "bg-orange-100 text-orange-800",
      account: "bg-purple-100 text-purple-800"
    };
    return <Badge className={styles[type] || "bg-gray-100"}>{type}</Badge>;
  };

  // Calculate totals
  const totals = balances.reduce((acc, b) => {
    if (b.opening_balance >= 0) {
      acc.debit += b.opening_balance;
    } else {
      acc.credit += Math.abs(b.opening_balance);
    }
    return acc;
  }, { debit: 0, credit: 0 });

  return (
    <div className="space-y-6" data-testid="opening-balances-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Opening Balances</h1>
          <p className="text-gray-500 text-sm mt-1">Set initial balances for customers, vendors, and accounts</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchBalances}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#22EDA9] hover:bg-[#1dd699] text-black" data-testid="new-opening-balance-btn">
                <Plus className="h-4 w-4 mr-2" /> Set Opening Balance
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Set Opening Balance</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Entity Type *</Label>
                  <Select 
                    value={formData.entity_type} 
                    onValueChange={(v) => setFormData({...formData, entity_type: v, entity_id: ""})}
                  >
                    <SelectTrigger data-testid="entity-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="customer">Customer</SelectItem>
                      <SelectItem value="vendor">Vendor</SelectItem>
                      <SelectItem value="account">Account</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Select {formData.entity_type.charAt(0).toUpperCase() + formData.entity_type.slice(1)} *</Label>
                  <Select 
                    value={formData.entity_id} 
                    onValueChange={(v) => setFormData({...formData, entity_id: v})}
                  >
                    <SelectTrigger data-testid="entity-select">
                      <SelectValue placeholder={`Select ${formData.entity_type}`} />
                    </SelectTrigger>
                    <SelectContent>
                      {getEntityOptions().map(opt => (
                        <SelectItem key={opt.id} value={opt.id}>
                          {opt.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Opening Balance (₹) *</Label>
                    <Input
                      type="number"
                      value={formData.opening_balance}
                      onChange={(e) => setFormData({...formData, opening_balance: parseFloat(e.target.value) || 0})}
                      placeholder="Use negative for credit balance"
                      data-testid="opening-balance-input"
                    />
                    <p className="text-xs text-gray-500">Positive = Debit, Negative = Credit</p>
                  </div>
                  <div className="space-y-2">
                    <Label>As of Date *</Label>
                    <Input
                      type="date"
                      value={formData.as_of_date}
                      onChange={(e) => setFormData({...formData, as_of_date: e.target.value})}
                      data-testid="as-of-date-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    placeholder="Optional notes..."
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} className="bg-[#22EDA9] hover:bg-[#1dd699] text-black" data-testid="save-opening-balance-btn">
                  Set Balance
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <IndianRupee className="h-5 w-5 text-[#3B9EFF]" />
              </div>
              <div>
                <p className="text-xs text-[#3B9EFF]">Total Entries</p>
                <p className="text-xl font-bold text-blue-800">{balances.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <IndianRupee className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-green-600">Total Debit</p>
                <p className="text-xl font-bold text-green-800">{formatCurrency(totals.debit)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-[rgba(255,59,47,0.08)] border-red-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <IndianRupee className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-xs text-red-600">Total Credit</p>
                <p className="text-xl font-bold text-red-800">{formatCurrency(totals.credit)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="customer" className="gap-2" data-testid="customer-tab">
            <Users className="h-4 w-4" /> Customers
          </TabsTrigger>
          <TabsTrigger value="vendor" className="gap-2" data-testid="vendor-tab">
            <Building2 className="h-4 w-4" /> Vendors
          </TabsTrigger>
          <TabsTrigger value="account" className="gap-2" data-testid="account-tab">
            <Landmark className="h-4 w-4" /> Accounts
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-[#22EDA9]" />
                </div>
              ) : balances.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  {getEntityIcon(activeTab)}
                  <p className="mt-4">No opening balances set for {activeTab}s</p>
                  <p className="text-sm">Set opening balances to start with accurate financial data</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-50">
                      <TableHead>Entity Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Opening Balance</TableHead>
                      <TableHead>As of Date</TableHead>
                      <TableHead>Notes</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {balances.map((bal) => (
                      <TableRow key={bal.opening_balance_id}>
                        <TableCell className="font-medium">{bal.entity_name}</TableCell>
                        <TableCell>{getEntityTypeBadge(bal.entity_type)}</TableCell>
                        <TableCell className={`text-right font-medium ${bal.opening_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {bal.opening_balance >= 0 ? '' : '-'}{formatCurrency(Math.abs(bal.opening_balance))}
                          <span className="text-xs text-gray-500 ml-1">
                            ({bal.opening_balance >= 0 ? 'Dr' : 'Cr'})
                          </span>
                        </TableCell>
                        <TableCell>{bal.as_of_date}</TableCell>
                        <TableCell className="max-w-[150px] truncate">{bal.notes || "-"}</TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {bal.created_time ? new Date(bal.created_time).toLocaleDateString() : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
