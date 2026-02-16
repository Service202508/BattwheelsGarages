import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Plus, Package, Calendar, FileText, Trash2, AlertTriangle, Flame, Bug, Archive } from "lucide-react";
import { API } from "@/App";

const reasonIcons = {
  damaged: AlertTriangle,
  stolen: Bug,
  stock_on_fire: Flame,
  expired: Calendar,
  written_off: Archive,
  other: FileText
};

const reasonColors = {
  damaged: "bg-orange-100 text-orange-700",
  stolen: "bg-red-100 text-red-700",
  stock_on_fire: "bg-red-100 text-red-700",
  expired: "bg-yellow-100 text-yellow-700",
  written_off: "bg-gray-100 text-gray-700",
  other: "bg-blue-100 text-blue-700"
};

export default function InventoryAdjustments() {
  const [adjustments, setAdjustments] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const [newAdjustment, setNewAdjustment] = useState({
    adjustment_type: "quantity", reason: "damaged", description: "",
    reference_number: "", line_items: []
  });
  const [newLineItem, setNewLineItem] = useState({
    item_id: "", item_name: "", quantity_adjusted: 0, new_quantity: 0
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [adjRes, itemsRes] = await Promise.all([
        fetch(`${API}/zoho/inventory-adjustments`, { headers }),
        fetch(`${API}/zoho/items?item_type=goods&per_page=500`, { headers })
      ]);
      const [adjData, itemsData] = await Promise.all([adjRes.json(), itemsRes.json()]);
      setAdjustments(adjData.inventory_adjustments || []);
      setItems(itemsData.items || []);
    } catch (error) { console.error("Failed to fetch:", error); }
    finally { setLoading(false); }
  };

  const handleSelectItem = (itemId) => {
    const item = items.find(i => i.item_id === itemId);
    if (item) {
      setNewLineItem({
        item_id: item.item_id,
        item_name: item.name,
        quantity_adjusted: 0,
        new_quantity: item.stock_on_hand || 0
      });
    }
  };

  const handleAddLineItem = () => {
    if (!newLineItem.item_id) return toast.error("Select an item");
    if (newLineItem.new_quantity < 0) return toast.error("Quantity cannot be negative");
    
    // Check if item already exists
    if (newAdjustment.line_items.some(li => li.item_id === newLineItem.item_id)) {
      return toast.error("Item already added");
    }

    const item = items.find(i => i.item_id === newLineItem.item_id);
    const quantityAdjusted = newLineItem.new_quantity - (item?.stock_on_hand || 0);

    setNewAdjustment({
      ...newAdjustment,
      line_items: [...newAdjustment.line_items, {
        ...newLineItem,
        quantity_adjusted: quantityAdjusted
      }]
    });
    setNewLineItem({ item_id: "", item_name: "", quantity_adjusted: 0, new_quantity: 0 });
  };

  const handleCreate = async () => {
    if (!newAdjustment.reason) return toast.error("Select a reason");
    if (!newAdjustment.line_items.length) return toast.error("Add at least one item");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/inventory-adjustments`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newAdjustment)
      });
      if (res.ok) {
        toast.success("Inventory adjustment created");
        setShowCreateDialog(false);
        setNewAdjustment({ adjustment_type: "quantity", reason: "damaged", description: "", reference_number: "", line_items: [] });
        fetchData();
      }
    } catch { toast.error("Error creating adjustment"); }
  };

  return (
    <div className="space-y-6" data-testid="inventory-adjustments-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory Adjustments</h1>
          <p className="text-gray-500 text-sm mt-1">Adjust stock levels for damaged, expired, or written-off items</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#22EDA9] hover:bg-[#1DD69A] text-black" data-testid="create-adjustment-btn">
              <Plus className="h-4 w-4 mr-2" /> New Adjustment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Create Inventory Adjustment</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Adjustment Type</Label>
                  <Select value={newAdjustment.adjustment_type} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, adjustment_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quantity">Quantity Adjustment</SelectItem>
                      <SelectItem value="value">Value Adjustment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Reason *</Label>
                  <Select value={newAdjustment.reason} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, reason: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="damaged">Damaged Goods</SelectItem>
                      <SelectItem value="stolen">Stolen</SelectItem>
                      <SelectItem value="stock_on_fire">Stock on Fire</SelectItem>
                      <SelectItem value="expired">Expired</SelectItem>
                      <SelectItem value="written_off">Written Off</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label>Reference Number</Label>
                <Input value={newAdjustment.reference_number} onChange={(e) => setNewAdjustment({ ...newAdjustment, reference_number: e.target.value })} placeholder="Optional reference" />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea value={newAdjustment.description} onChange={(e) => setNewAdjustment({ ...newAdjustment, description: e.target.value })} placeholder="Reason for adjustment..." />
              </div>

              <div className="border rounded-lg p-4 bg-gray-50">
                <h3 className="font-medium mb-3">Add Items to Adjust</h3>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="col-span-2">
                    <Select value={newLineItem.item_id} onValueChange={handleSelectItem}>
                      <SelectTrigger><SelectValue placeholder="Select item..." /></SelectTrigger>
                      <SelectContent>
                        {items.map(item => (
                          <SelectItem key={item.item_id} value={item.item_id}>
                            {item.name} (Stock: {item.stock_on_hand || 0})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Input 
                      type="number" 
                      value={newLineItem.new_quantity} 
                      onChange={(e) => setNewLineItem({ ...newLineItem, new_quantity: parseInt(e.target.value) || 0 })} 
                      placeholder="New Qty"
                      min={0}
                    />
                  </div>
                </div>
                <Button onClick={handleAddLineItem} className="bg-[#22EDA9] text-black w-full">Add Item</Button>
              </div>

              {newAdjustment.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Item</th>
                        <th className="px-4 py-2 text-right">Current Stock</th>
                        <th className="px-4 py-2 text-right">New Qty</th>
                        <th className="px-4 py-2 text-right">Change</th>
                        <th className="px-4 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {newAdjustment.line_items.map((li, idx) => {
                        const item = items.find(i => i.item_id === li.item_id);
                        return (
                          <tr key={idx} className="border-t">
                            <td className="px-4 py-2">{li.item_name}</td>
                            <td className="px-4 py-2 text-right">{item?.stock_on_hand || 0}</td>
                            <td className="px-4 py-2 text-right">{li.new_quantity}</td>
                            <td className="px-4 py-2 text-right">
                              <span className={li.quantity_adjusted < 0 ? "text-red-600" : "text-green-600"}>
                                {li.quantity_adjusted > 0 ? "+" : ""}{li.quantity_adjusted}
                              </span>
                            </td>
                            <td className="px-4 py-2">
                              <Button variant="ghost" size="icon" onClick={() => setNewAdjustment({
                                ...newAdjustment,
                                line_items: newAdjustment.line_items.filter((_, i) => i !== idx)
                              })}>
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button onClick={handleCreate} className="bg-[#22EDA9] text-black">Create Adjustment</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
        adjustments.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <Package className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No inventory adjustments found</p>
              <p className="text-sm mt-1">Create an adjustment to correct stock levels</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {adjustments.map(adj => {
              const Icon = reasonIcons[adj.reason] || FileText;
              return (
                <Card key={adj.adjustment_id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <div className={`p-2 rounded-lg ${reasonColors[adj.reason]?.replace('text-', 'bg-').replace('100', '50') || 'bg-gray-100'}`}>
                            <Icon className="h-5 w-5" />
                          </div>
                          <div>
                            <h3 className="font-semibold">{adj.adjustment_number}</h3>
                            <Badge className={reasonColors[adj.reason] || "bg-gray-100 text-gray-700"}>
                              {adj.reason?.replace(/_/g, ' ')}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex gap-4 text-sm text-gray-500 mt-2">
                          <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{adj.date}</span>
                          <span>{adj.line_items?.length || 0} items adjusted</span>
                          {adj.reference_number && <span>Ref: {adj.reference_number}</span>}
                        </div>
                        {adj.description && <p className="text-sm text-gray-600 mt-2">{adj.description}</p>}
                      </div>
                      <Badge variant="outline" className="capitalize">{adj.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )
      }
    </div>
  );
}
