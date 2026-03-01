import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Plus, Percent, Layers } from "lucide-react";
import { API } from "@/App";

export default function Taxes() {
  const [taxes, setTaxes] = useState([]);
  const [taxGroups, setTaxGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTaxDialog, setShowTaxDialog] = useState(false);
  const [showGroupDialog, setShowGroupDialog] = useState(false);

  const [newTax, setNewTax] = useState({ tax_name: "", tax_percentage: 0, tax_type: "tax", is_default: false, description: "" });
  const [newGroup, setNewGroup] = useState({ group_name: "", tax_ids: [], description: "" });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [taxRes, groupRes] = await Promise.all([
        fetch(`${API}/zoho/taxes`, { headers }),
        fetch(`${API}/zoho/tax-groups`, { headers })
      ]);
      const [taxData, groupData] = await Promise.all([taxRes.json(), groupRes.json()]);
      setTaxes(taxData.taxes || []);
      setTaxGroups(groupData.tax_groups || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleCreateTax = async () => {
    if (!newTax.tax_name) return toast.error("Enter tax name");
    if (newTax.tax_percentage <= 0) return toast.error("Enter tax percentage");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/taxes`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newTax)
      });
      if (res.ok) {
        toast.success("Tax created");
        setShowTaxDialog(false);
        setNewTax({ tax_name: "", tax_percentage: 0, tax_type: "tax", is_default: false, description: "" });
        fetchData();
      }
    } catch { toast.error("Error creating tax"); }
  };

  const handleCreateGroup = async () => {
    if (!newGroup.group_name) return toast.error("Enter group name");
    if (!newGroup.tax_ids.length) return toast.error("Select at least one tax");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/tax-groups`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newGroup)
      });
      if (res.ok) {
        toast.success("Tax group created");
        setShowGroupDialog(false);
        setNewGroup({ group_name: "", tax_ids: [], description: "" });
        fetchData();
      }
    } catch { toast.error("Error creating tax group"); }
  };

  const handleDeleteTax = async (taxId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/taxes/${taxId}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      toast.success("Tax deleted");
      fetchData();
    } catch { toast.error("Error deleting tax"); }
  };

  return (
    <div className="space-y-6" data-testid="taxes-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-bw-white">Taxes</h1>
          <p className="text-bw-white/[0.45] text-sm mt-1">Configure tax rates & groups</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showGroupDialog} onOpenChange={setShowGroupDialog}>
            <DialogTrigger asChild>
              <Button variant="outline"><Layers className="h-4 w-4 mr-2" /> New Tax Group</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create Tax Group</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>Group Name *</Label>
                  <Input value={newGroup.group_name} onChange={(e) => setNewGroup({ ...newGroup, group_name: e.target.value })} placeholder="e.g., GST 18%" />
                </div>
                <div>
                  <Label>Select Taxes *</Label>
                  <div className="space-y-2 mt-2">
                    {taxes.map(tax => (
                      <div key={tax.tax_id} className="flex items-center gap-2">
                        <Switch
                          checked={newGroup.tax_ids.includes(tax.tax_id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setNewGroup({ ...newGroup, tax_ids: [...newGroup.tax_ids, tax.tax_id] });
                            } else {
                              setNewGroup({ ...newGroup, tax_ids: newGroup.tax_ids.filter(id => id !== tax.tax_id) });
                            }
                          }}
                        />
                        <span>{tax.tax_name} ({tax.tax_percentage}%)</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <Label>Description</Label>
                  <Input value={newGroup.description} onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowGroupDialog(false)}>Cancel</Button>
                <Button onClick={handleCreateGroup} className="bg-bw-volt text-bw-black font-bold">Create Group</Button>
              </div>
            </DialogContent>
          </Dialog>
          <Dialog open={showTaxDialog} onOpenChange={setShowTaxDialog}>
            <DialogTrigger asChild>
              <Button className="bg-bw-volt hover:bg-bw-volt-hover text-bw-black font-bold" data-testid="create-tax-btn">
                <Plus className="h-4 w-4 mr-2" /> New Tax
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create Tax</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>Tax Name *</Label>
                  <Input value={newTax.tax_name} onChange={(e) => setNewTax({ ...newTax, tax_name: e.target.value })} placeholder="e.g., CGST" />
                </div>
                <div>
                  <Label>Tax Percentage *</Label>
                  <Input type="number" value={newTax.tax_percentage} onChange={(e) => setNewTax({ ...newTax, tax_percentage: parseFloat(e.target.value) })} step={0.1} />
                </div>
                <div>
                  <Label>Tax Type</Label>
                  <Select value={newTax.tax_type} onValueChange={(v) => setNewTax({ ...newTax, tax_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tax">Tax</SelectItem>
                      <SelectItem value="compound_tax">Compound Tax</SelectItem>
                      <SelectItem value="cess">Cess</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={newTax.is_default} onCheckedChange={(v) => setNewTax({ ...newTax, is_default: v })} />
                  <Label>Set as default tax</Label>
                </div>
                <div>
                  <Label>Description</Label>
                  <Input value={newTax.description} onChange={(e) => setNewTax({ ...newTax, description: e.target.value })} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowTaxDialog(false)}>Cancel</Button>
                <Button onClick={handleCreateTax} className="bg-bw-volt text-bw-black font-bold">Create Tax</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs defaultValue="taxes">
        <TabsList>
          <TabsTrigger value="taxes">Individual Taxes</TabsTrigger>
          <TabsTrigger value="groups">Tax Groups</TabsTrigger>
        </TabsList>

        <TabsContent value="taxes" className="mt-6">
          {loading ? <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div> :
            taxes.length === 0 ? <Card><CardContent className="py-12 text-center text-bw-white/[0.45]">No taxes configured</CardContent></Card> :
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {taxes.map(tax => (
                <Card key={tax.tax_id} className="border border-white/[0.07] hover:border-bw-volt/20 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-bw-volt/10 rounded-lg">
                          <Percent className="h-5 w-5 text-bw-volt" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{tax.tax_name}</h3>
                          <p className="text-sm text-bw-white/[0.45]">{tax.tax_type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold">{tax.tax_percentage}%</p>
                        {tax.is_default && <Badge className="bg-blue-100 text-bw-blue">Default</Badge>}
                      </div>
                    </div>
                    {tax.description && <p className="text-sm text-bw-white/[0.45] mt-3">{tax.description}</p>}
                  </CardContent>
                </Card>
              ))}
            </div>
          }
        </TabsContent>

        <TabsContent value="groups" className="mt-6">
          {loading ? <div className="text-center py-12 text-bw-white/[0.45]">Loading...</div> :
            taxGroups.length === 0 ? <Card><CardContent className="py-12 text-center text-bw-white/[0.45]">No tax groups configured</CardContent></Card> :
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {taxGroups.map(group => (
                <Card key={group.tax_group_id} className="border border-white/[0.07] hover:border-bw-volt/20 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <Layers className="h-5 w-5 text-bw-blue" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{group.group_name}</h3>
                          {group.description && <p className="text-sm text-bw-white/[0.45]">{group.description}</p>}
                        </div>
                      </div>
                      <p className="text-2xl font-bold text-bw-volt">{group.combined_rate}%</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {group.taxes?.map(tax => (
                        <Badge key={tax.tax_id} variant="outline">{tax.tax_name} ({tax.tax_percentage}%)</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          }
        </TabsContent>
      </Tabs>
    </div>
  );
}
