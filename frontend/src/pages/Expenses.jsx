import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Search, Receipt, TrendingDown, Calendar } from "lucide-react";
import { API } from "@/App";

export default function Expenses({ user }) {
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [formData, setFormData] = useState({
    expense_date: new Date().toISOString().split('T')[0],
    description: "",
    expense_account: "Office Supplies",
    vendor_id: "",
    amount: 0,
    tax_amount: 0,
    reference_number: "",
    is_billable: false
  });

  useEffect(() => {
    fetchExpenses();
    fetchSummary();
  }, []);

  const fetchExpenses = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/expenses`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setExpenses(data);
      }
    } catch (error) {
      console.error("Failed to fetch expenses:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/expenses/summary`, {
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      console.error("Failed to fetch summary:", error);
    }
  };

  const handleSubmit = async () => {
    if (!formData.expense_account || formData.amount <= 0) {
      toast.error("Account and amount are required");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API}/expenses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Expense recorded");
        fetchExpenses();
        fetchSummary();
        setIsAddOpen(false);
        setFormData({
          expense_date: new Date().toISOString().split('T')[0],
          description: "",
          expense_account: "Office Supplies",
          vendor_id: "",
          amount: 0,
          tax_amount: 0,
          reference_number: "",
          is_billable: false
        });
      } else {
        toast.error("Failed to record expense");
      }
    } catch (error) {
      toast.error("Error recording expense");
    }
  };

  const filteredExpenses = expenses.filter(e =>
    e.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.expense_account?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.vendor_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="expenses-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Expenses</h1>
          <p className="text-muted-foreground">Track and manage business expenses.</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-expense-btn">
              <Plus className="mr-2 h-4 w-4" />
              Add Expense
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Record New Expense</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Input
                    type="date"
                    value={formData.expense_date}
                    onChange={(e) => setFormData({...formData, expense_date: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Account</Label>
                  <Select 
                    value={formData.expense_account} 
                    onValueChange={(value) => setFormData({...formData, expense_account: value})}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Office Supplies">Office Supplies</SelectItem>
                      <SelectItem value="Travel Expense">Travel Expense</SelectItem>
                      <SelectItem value="Automobile Expense">Automobile Expense</SelectItem>
                      <SelectItem value="IT and Internet Expenses">IT and Internet</SelectItem>
                      <SelectItem value="Rent Expense">Rent</SelectItem>
                      <SelectItem value="Telephone Expense">Telephone</SelectItem>
                      <SelectItem value="Cost of Goods Sold">Cost of Goods Sold</SelectItem>
                      <SelectItem value="Other Expenses">Other Expenses</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Enter expense description"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Amount (₹)</Label>
                  <Input
                    type="number"
                    value={formData.amount}
                    onChange={(e) => setFormData({...formData, amount: parseFloat(e.target.value) || 0})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tax (₹)</Label>
                  <Input
                    type="number"
                    value={formData.tax_amount}
                    onChange={(e) => setFormData({...formData, tax_amount: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Reference Number</Label>
                <Input
                  value={formData.reference_number}
                  onChange={(e) => setFormData({...formData, reference_number: e.target.value})}
                  placeholder="Bill/Receipt number"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAddOpen(false)}>Cancel</Button>
              <Button onClick={handleSubmit}>Record Expense</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="stats-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{(summary?.total_expenses || 0).toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card className="stats-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Entries</CardTitle>
            <Receipt className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.expense_count || expenses.length}</div>
          </CardContent>
        </Card>
        <Card className="stats-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
            <Calendar className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.by_account?.length || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search expenses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Expenses Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-pulse text-muted-foreground">Loading expenses...</div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredExpenses.slice(0, 50).map((expense) => (
                  <TableRow key={expense.expense_id}>
                    <TableCell>{expense.expense_date?.split('T')[0] || '-'}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{expense.description || '-'}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{expense.expense_account}</Badge>
                    </TableCell>
                    <TableCell>{expense.vendor_name || '-'}</TableCell>
                    <TableCell className="text-right font-medium">
                      ₹{(expense.amount || 0).toLocaleString()}
                    </TableCell>
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
