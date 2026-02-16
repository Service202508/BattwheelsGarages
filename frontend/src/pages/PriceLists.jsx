import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Plus, List, IndianRupee, Edit, Trash2, Tag, Package } from "lucide-react";
import { API } from "@/App";

export default function PriceLists() {
  const [priceLists, setPriceLists] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showAddItemDialog, setShowAddItemDialog] = useState(false);
  const [selectedPriceList, setSelectedPriceList] = useState(null);

  const [newPriceList, setNewPriceList] = useState({
    price_list_name: "", description: "", currency_code: "INR",
    price_type: "sales", is_default: false, round_off_to: "never"
  });

  const [newPriceItem, setNewPriceItem] = useState({ item_id: "", custom_rate: 0 });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [plRes, itemsRes] = await Promise.all([
        fetch(`${API}/zoho/price-lists`, { headers }),
        fetch(`${API}/zoho/items?per_page=500`, { headers })
      ]);
      const [plData, itemsData] = await Promise.all([plRes.json(), itemsRes.json()]);
      setPriceLists(plData.price_lists || []);
      setItems(itemsData.items || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!newPriceList.price_list_name) return toast.error("Enter price list name");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/price-lists`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newPriceList)
      });
      if (res.ok) {
        toast.success("Price list created");
        setShowCreateDialog(false);
        setNewPriceList({ price_list_name: "", description: "", currency_code: "INR", price_type: "sales", is_default: false, round_off_to: "never" });
        fetchData();
      }
    } catch { toast.error("Error creating price list"); }
  };

  const handleAddItem = async () => {
    if (!newPriceItem.item_id || newPriceItem.custom_rate <= 0) return toast.error("Select item and enter rate");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/price-lists/${selectedPriceList.price_list_id}/items?item_id=${newPriceItem.item_id}&custom_rate=${newPriceItem.custom_rate}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Item added to price list");
        setShowAddItemDialog(false);
        setNewPriceItem({ item_id: "", custom_rate: 0 });
        fetchData();
      }
    } catch { toast.error("Error adding item"); }
  };

  const handleRemoveItem = async (priceListId, itemId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API}/zoho/price-lists/${priceListId}/items/${itemId}`, {
        method: "DELETE", headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Item removed from price list");
      fetchData();
    } catch { toast.error("Error removing item"); }
  };

  return (
    <div className="space-y-6" data-testid="price-lists-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Price Lists</h1>
          <p className="text-gray-500 text-sm mt-1">Manage custom pricing for items</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black" data-testid="create-pricelist-btn">
              <Plus className="h-4 w-4 mr-2" /> New Price List
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Create Price List</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Price List Name *</Label>
                <Input value={newPriceList.price_list_name} onChange={(e) => setNewPriceList({ ...newPriceList, price_list_name: e.target.value })} placeholder="e.g., Wholesale Prices" />
              </div>
              <div>
                <Label>Description</Label>
                <Input value={newPriceList.description} onChange={(e) => setNewPriceList({ ...newPriceList, description: e.target.value })} placeholder="Optional description" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Price Type</Label>
                  <Select value={newPriceList.price_type} onValueChange={(v) => setNewPriceList({ ...newPriceList, price_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sales">Sales</SelectItem>
                      <SelectItem value="purchase">Purchase</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Round Off To</Label>
                  <Select value={newPriceList.round_off_to} onValueChange={(v) => setNewPriceList({ ...newPriceList, round_off_to: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="never">Never</SelectItem>
                      <SelectItem value="nearest_1">Nearest ₹1</SelectItem>
                      <SelectItem value="nearest_5">Nearest ₹5</SelectItem>
                      <SelectItem value="nearest_10">Nearest ₹10</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={newPriceList.is_default} onCheckedChange={(v) => setNewPriceList({ ...newPriceList, is_default: v })} />
                <Label>Set as default price list</Label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreate} className="bg-[#22EDA9] text-black">Create Price List</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        priceLists.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <List className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No price lists found</p>
              <p className="text-sm mt-1">Create a price list to set custom pricing for different customers</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {priceLists.map(pl => (
              <Card key={pl.price_list_id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[#22EDA9]/10 rounded-lg">
                        <List className="h-5 w-5 text-[#22EDA9]" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{pl.price_list_name}</CardTitle>
                        {pl.description && <p className="text-sm text-gray-500">{pl.description}</p>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="capitalize">{pl.price_type}</Badge>
                      {pl.is_default && <Badge className="bg-blue-100 text-blue-700">Default</Badge>}
                      <Button size="sm" variant="outline" onClick={() => { setSelectedPriceList(pl); setShowAddItemDialog(true); }}>
                        <Plus className="h-4 w-4 mr-1" /> Add Item
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {pl.items?.length > 0 ? (
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left">Item</th>
                            <th className="px-4 py-2 text-right">Custom Rate</th>
                            <th className="px-4 py-2 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {pl.items.map(item => {
                            const itemDetails = items.find(i => i.item_id === item.item_id);
                            return (
                              <tr key={item.item_id} className="border-t">
                                <td className="px-4 py-2">
                                  <div className="flex items-center gap-2">
                                    <Package className="h-4 w-4 text-gray-400" />
                                    <span>{itemDetails?.name || item.item_id}</span>
                                  </div>
                                </td>
                                <td className="px-4 py-2 text-right font-medium">₹{item.custom_rate?.toLocaleString('en-IN')}</td>
                                <td className="px-4 py-2 text-right">
                                  <Button size="icon" variant="ghost" onClick={() => handleRemoveItem(pl.price_list_id, item.item_id)}>
                                    <Trash2 className="h-4 w-4 text-red-500" />
                                  </Button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-6 text-gray-400 text-sm">
                      No items added to this price list yet
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )
      }

      {/* Add Item to Price List Dialog */}
      <Dialog open={showAddItemDialog} onOpenChange={setShowAddItemDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Item to Price List</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Select Item *</Label>
              <Select value={newPriceItem.item_id} onValueChange={(v) => {
                const item = items.find(i => i.item_id === v);
                setNewPriceItem({ ...newPriceItem, item_id: v, custom_rate: item?.rate || 0 });
              }}>
                <SelectTrigger><SelectValue placeholder="Choose an item" /></SelectTrigger>
                <SelectContent>
                  {items.map(item => (
                    <SelectItem key={item.item_id} value={item.item_id}>
                      {item.name} (₹{item.rate})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Custom Rate *</Label>
              <Input type="number" value={newPriceItem.custom_rate} onChange={(e) => setNewPriceItem({ ...newPriceItem, custom_rate: parseFloat(e.target.value) })} />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowAddItemDialog(false)}>Cancel</Button>
            <Button onClick={handleAddItem} className="bg-[#22EDA9] text-black">Add Item</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
