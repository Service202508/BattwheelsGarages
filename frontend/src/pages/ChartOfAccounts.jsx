import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Plus, Layers, TrendingUp, TrendingDown, Wallet, DollarSign, PiggyBank } from "lucide-react";
import { API } from "@/App";

const accountTypeColors = {
  asset: "bg-green-100 text-green-700",
  liability: "bg-red-100 text-red-700",
  equity: "bg-blue-100 text-blue-700",
  income: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] text-700",
  expense: "bg-orange-100 text-orange-700"
};

const accountTypeIcons = {
  asset: TrendingUp,
  liability: TrendingDown,
  equity: PiggyBank,
  income: DollarSign,
  expense: Wallet
};

export default function ChartOfAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [activeTab, setActiveTab] = useState("all");

  const [newAccount, setNewAccount] = useState({
    account_name: "", account_code: "", account_type: "asset", description: ""
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/chartofaccounts`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setAccounts(data.chartofaccounts || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!newAccount.account_name) return toast.error("Enter account name");
    if (!newAccount.account_type) return toast.error("Select account type");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/chartofaccounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newAccount)
      });
      if (res.ok) {
        toast.success("Account created");
        setShowCreateDialog(false);
        setNewAccount({ account_name: "", account_code: "", account_type: "asset", description: "" });
        fetchData();
      }
    } catch { toast.error("Error creating account"); }
  };

  const filteredAccounts = activeTab === "all" ? accounts : accounts.filter(a => a.account_type === activeTab);

  const groupedAccounts = filteredAccounts.reduce((acc, account) => {
    const type = account.account_type || "other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(account);
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="chart-of-accounts-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F4F6F0]">Chart of Accounts</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your account structure</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black" data-testid="create-account-btn">
              <Plus className="h-4 w-4 mr-2" /> New Account
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Account</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Account Name *</Label>
                <Input value={newAccount.account_name} onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })} placeholder="e.g., Cash in Hand" />
              </div>
              <div>
                <Label>Account Code</Label>
                <Input value={newAccount.account_code} onChange={(e) => setNewAccount({ ...newAccount, account_code: e.target.value })} placeholder="e.g., 1001" />
              </div>
              <div>
                <Label>Account Type *</Label>
                <Select value={newAccount.account_type} onValueChange={(v) => setNewAccount({ ...newAccount, account_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="asset">Asset</SelectItem>
                    <SelectItem value="liability">Liability</SelectItem>
                    <SelectItem value="equity">Equity</SelectItem>
                    <SelectItem value="income">Income</SelectItem>
                    <SelectItem value="expense">Expense</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Description</Label>
                <Input value={newAccount.description} onChange={(e) => setNewAccount({ ...newAccount, description: e.target.value })} placeholder="Optional description" />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreate} className="bg-[#22EDA9] text-black">Create Account</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="asset">Assets</TabsTrigger>
          <TabsTrigger value="liability">Liabilities</TabsTrigger>
          <TabsTrigger value="equity">Equity</TabsTrigger>
          <TabsTrigger value="income">Income</TabsTrigger>
          <TabsTrigger value="expense">Expense</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
            Object.keys(groupedAccounts).length === 0 ? <Card><CardContent className="py-12 text-center text-gray-500">No accounts found</CardContent></Card> :
            <div className="space-y-6">
              {Object.entries(groupedAccounts).map(([type, accs]) => {
                const Icon = accountTypeIcons[type] || Layers;
                return (
                  <Card key={type}>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center gap-2 capitalize">
                        <Icon className="h-5 w-5" /> {type} Accounts
                        <Badge variant="outline">{accs.length}</Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {accs.map(account => (
                          <div key={account.account_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                            <div className="flex items-center gap-3">
                              {account.account_code && <span className="text-xs font-mono bg-gray-200 px-2 py-1 rounded">{account.account_code}</span>}
                              <div>
                                <p className="font-medium">{account.account_name}</p>
                                {account.description && <p className="text-xs text-gray-500">{account.description}</p>}
                              </div>
                            </div>
                            <Badge className={accountTypeColors[account.account_type]}>{account.account_type}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          }
        </TabsContent>
      </Tabs>
    </div>
  );
}
