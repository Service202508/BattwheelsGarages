import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { 
  Plus, Package, Calendar, DollarSign, TrendingDown, Trash2, 
  IndianRupee, Building, Car, Monitor, Settings, Calculator,
  AlertTriangle, CheckCircle, XCircle
} from "lucide-react";
import { API } from "@/App";
import PageHeader, { EmptyState } from "@/components/PageHeader";

const statusColors = {
  active: "bg-green-100 text-green-700",
  fully_depreciated: "bg-blue-100 text-blue-700",
  disposed: "bg-gray-100 text-gray-600",
  written_off: "bg-red-100 text-red-700"
};

const assetTypeIcons = {
  furniture: Package,
  vehicle: Car,
  computer: Monitor,
  equipment: Settings,
  building: Building,
  land: Building,
  software: Monitor,
  other: Package
};

const assetTypes = [
  { value: "furniture", label: "Furniture & Fixtures" },
  { value: "vehicle", label: "Vehicles" },
  { value: "computer", label: "Computers & Electronics" },
  { value: "equipment", label: "Equipment & Machinery" },
  { value: "building", label: "Buildings" },
  { value: "land", label: "Land" },
  { value: "software", label: "Software & Licenses" },
  { value: "other", label: "Other Assets" }
];

const depreciationMethods = [
  { value: "straight_line", label: "Straight Line" },
  { value: "declining_balance", label: "Declining Balance" },
  { value: "units_of_production", label: "Units of Production" },
  { value: "sum_of_years", label: "Sum of Years' Digits" }
];

export default function FixedAssets() {
  const [assets, setAssets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showDepreciateDialog, setShowDepreciateDialog] = useState(false);
  const [showDisposeDialog, setShowDisposeDialog] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [filterType, setFilterType] = useState("");

  const [newAsset, setNewAsset] = useState({
    asset_name: "",
    asset_type: "equipment",
    description: "",
    purchase_date: new Date().toISOString().split("T")[0],
    purchase_price: 0,
    useful_life_years: 5,
    salvage_value: 0,
    depreciation_method: "straight_line",
    location: "",
    serial_number: "",
    warranty_expiry: ""
  });

  const [depreciationAmount, setDepreciationAmount] = useState(0);
  const [depreciationPeriod, setDepreciationPeriod] = useState(new Date().toISOString().slice(0, 7));

  const [disposeData, setDisposeData] = useState({
    disposal_date: new Date().toISOString().split("T")[0],
    disposal_amount: 0,
    reason: ""
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      const [assetsRes, summaryRes] = await Promise.all([
        fetch(`${API}/zoho/fixed-assets?per_page=100`, { headers }),
        fetch(`${API}/zoho/fixed-assets/summary`, { headers })
      ]);
      const [assetsData, summaryData] = await Promise.all([
        assetsRes.json(), summaryRes.json()
      ]);
      setAssets(assetsData.fixed_assets || []);
      setSummary(summaryData.summary || null);
    } catch (error) {
      console.error("Failed to fetch:", error);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newAsset.asset_name) return toast.error("Enter asset name");
    if (newAsset.purchase_price <= 0) return toast.error("Enter purchase price");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/fixed-assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newAsset)
      });
      if (res.ok) {
        toast.success("Fixed asset created");
        setShowCreateDialog(false);
        setNewAsset({
          asset_name: "", asset_type: "equipment", description: "",
          purchase_date: new Date().toISOString().split("T")[0],
          purchase_price: 0, useful_life_years: 5, salvage_value: 0,
          depreciation_method: "straight_line", location: "",
          serial_number: "", warranty_expiry: ""
        });
        fetchData();
      } else {
        toast.error("Failed to create asset");
      }
    } catch {
      toast.error("Error creating asset");
    }
  };

  const handleDepreciate = async () => {
    if (!selectedAsset) return;
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        period: depreciationPeriod,
        ...(depreciationAmount > 0 ? { amount: depreciationAmount } : {})
      });
      const res = await fetch(`${API}/zoho/fixed-assets/${selectedAsset.asset_id}/depreciate?${params}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Depreciation of ₹${data.entry?.amount?.toLocaleString()} recorded`);
        setShowDepreciateDialog(false);
        setDepreciationAmount(0);
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to record depreciation");
      }
    } catch {
      toast.error("Error recording depreciation");
    }
  };

  const handleDispose = async () => {
    if (!selectedAsset) return;
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        disposal_date: disposeData.disposal_date,
        disposal_amount: disposeData.disposal_amount,
        reason: disposeData.reason
      });
      const res = await fetch(`${API}/zoho/fixed-assets/${selectedAsset.asset_id}/dispose?${params}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const gainLoss = data.disposal?.gain_loss || 0;
        toast.success(`Asset disposed. ${gainLoss >= 0 ? `Gain: ₹${gainLoss.toLocaleString()}` : `Loss: ₹${Math.abs(gainLoss).toLocaleString()}`}`);
        setShowDisposeDialog(false);
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error("Failed to dispose asset");
      }
    } catch {
      toast.error("Error disposing asset");
    }
  };

  const handleWriteOff = async (assetId) => {
    if (!confirm("Write off this asset? This will record its remaining book value as a loss.")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/fixed-assets/${assetId}/write-off?reason=Asset write-off`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Asset written off");
        setShowDetailDialog(false);
        fetchData();
      }
    } catch {
      toast.error("Failed to write off");
    }
  };

  const handleDelete = async (assetId) => {
    if (!confirm("Delete this asset permanently?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/zoho/fixed-assets/${assetId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Asset deleted");
        setShowDetailDialog(false);
        fetchData();
      }
    } catch {
      toast.error("Failed to delete");
    }
  };

  const openDetail = (asset) => {
    setSelectedAsset(asset);
    setShowDetailDialog(true);
    setDisposeData({
      disposal_date: new Date().toISOString().split("T")[0],
      disposal_amount: asset.book_value,
      reason: ""
    });
  };

  const filteredAssets = filterType 
    ? assets.filter(a => a.asset_type === filterType)
    : assets;

  const activeAssets = filteredAssets.filter(a => a.status === "active");
  const depreciatedAssets = filteredAssets.filter(a => a.status === "fully_depreciated");
  const disposedAssets = filteredAssets.filter(a => ["disposed", "written_off"].includes(a.status));

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6" data-testid="fixed-assets-page">
      {/* Header */}
      <PageHeader
        title="Fixed Assets"
        description="Track and depreciate your business assets"
        icon={Package}
        actions={
          <Button 
            onClick={() => setShowCreateDialog(true)}
            className="bg-[#22EDA9] text-gray-900 hover:bg-[#1DD69A] font-semibold shadow-lg shadow-[#22EDA9]/20" 
            data-testid="create-asset-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Fixed Asset
          </Button>
        }
      />

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add Fixed Asset</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Asset Name *</Label>
                  <Input
                    value={newAsset.asset_name}
                    onChange={e => setNewAsset({ ...newAsset, asset_name: e.target.value })}
                    placeholder="e.g., Dell Laptop"
                  />
                </div>
                <div>
                  <Label>Asset Type</Label>
                  <Select
                    value={newAsset.asset_type}
                    onValueChange={v => setNewAsset({ ...newAsset, asset_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {assetTypes.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label>Description</Label>
                <Textarea
                  value={newAsset.description}
                  onChange={e => setNewAsset({ ...newAsset, description: e.target.value })}
                  placeholder="Optional description"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Purchase Date *</Label>
                  <Input
                    type="date"
                    value={newAsset.purchase_date}
                    onChange={e => setNewAsset({ ...newAsset, purchase_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Purchase Price *</Label>
                  <Input
                    type="number"
                    value={newAsset.purchase_price}
                    onChange={e => setNewAsset({ ...newAsset, purchase_price: parseFloat(e.target.value) || 0 })}
                    placeholder="₹"
                  />
                </div>
                <div>
                  <Label>Salvage Value</Label>
                  <Input
                    type="number"
                    value={newAsset.salvage_value}
                    onChange={e => setNewAsset({ ...newAsset, salvage_value: parseFloat(e.target.value) || 0 })}
                    placeholder="₹"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Useful Life (Years)</Label>
                  <Input
                    type="number"
                    min="1"
                    value={newAsset.useful_life_years}
                    onChange={e => setNewAsset({ ...newAsset, useful_life_years: parseInt(e.target.value) || 1 })}
                  />
                </div>
                <div>
                  <Label>Depreciation Method</Label>
                  <Select
                    value={newAsset.depreciation_method}
                    onValueChange={v => setNewAsset({ ...newAsset, depreciation_method: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {depreciationMethods.map(m => (
                        <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Location</Label>
                  <Input
                    value={newAsset.location}
                    onChange={e => setNewAsset({ ...newAsset, location: e.target.value })}
                    placeholder="e.g., Head Office"
                  />
                </div>
                <div>
                  <Label>Serial Number</Label>
                  <Input
                    value={newAsset.serial_number}
                    onChange={e => setNewAsset({ ...newAsset, serial_number: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Warranty Expiry</Label>
                  <Input
                    type="date"
                    value={newAsset.warranty_expiry}
                    onChange={e => setNewAsset({ ...newAsset, warranty_expiry: e.target.value })}
                  />
                </div>
              </div>

              {/* Calculation Preview */}
              {newAsset.purchase_price > 0 && (
                <Card className="bg-gray-50">
                  <CardContent className="pt-4">
                    <h4 className="font-medium mb-2">Depreciation Preview</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Depreciable Value:</span>
                        <p className="font-medium">₹{(newAsset.purchase_price - newAsset.salvage_value).toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Annual Depreciation:</span>
                        <p className="font-medium">₹{((newAsset.purchase_price - newAsset.salvage_value) / newAsset.useful_life_years).toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Monthly Depreciation:</span>
                        <p className="font-medium">₹{((newAsset.purchase_price - newAsset.salvage_value) / newAsset.useful_life_years / 12).toLocaleString()}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              <Button className="w-full" onClick={handleCreate}>Add Asset</Button>
            </div>
          </DialogContent>
        </Dialog>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Package className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Assets</p>
                  <p className="text-2xl font-bold">{summary.total_assets}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Active</p>
                  <p className="text-2xl font-bold">{summary.active_assets}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <IndianRupee className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Purchase Value</p>
                  <p className="text-xl font-bold">₹{(summary.total_purchase_value || 0).toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <TrendingDown className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Depreciation</p>
                  <p className="text-xl font-bold">₹{(summary.total_accumulated_depreciation || 0).toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-teal-100 rounded-lg">
                  <DollarSign className="h-5 w-5 text-teal-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Book Value</p>
                  <p className="text-xl font-bold">₹{(summary.total_book_value || 0).toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-4 items-center">
        <Label>Filter by Type:</Label>
        <Select value={filterType || "all"} onValueChange={(v) => setFilterType(v === "all" ? "" : v)}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {assetTypes.map(t => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {filterType && (
          <Button variant="ghost" size="sm" onClick={() => setFilterType("")}>
            Clear Filter
          </Button>
        )}
      </div>

      {/* Assets Tabs */}
      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active">Active ({activeAssets.length})</TabsTrigger>
          <TabsTrigger value="depreciated">Fully Depreciated ({depreciatedAssets.length})</TabsTrigger>
          <TabsTrigger value="disposed">Disposed ({disposedAssets.length})</TabsTrigger>
        </TabsList>

        {[
          { key: "active", data: activeAssets },
          { key: "depreciated", data: depreciatedAssets },
          { key: "disposed", data: disposedAssets }
        ].map(({ key, data }) => (
          <TabsContent key={key} value={key}>
            <Card>
              <CardContent className="p-0">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium">Asset</th>
                      <th className="text-left p-4 font-medium">Type</th>
                      <th className="text-left p-4 font-medium">Purchase Date</th>
                      <th className="text-right p-4 font-medium">Purchase Price</th>
                      <th className="text-right p-4 font-medium">Book Value</th>
                      <th className="text-center p-4 font-medium">Status</th>
                      <th className="text-right p-4 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map(asset => {
                      const Icon = assetTypeIcons[asset.asset_type] || Package;
                      return (
                        <tr key={asset.asset_id} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => openDetail(asset)}>
                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <div className="p-2 bg-gray-100 rounded">
                                <Icon className="h-4 w-4 text-gray-600" />
                              </div>
                              <div>
                                <div className="font-medium">{asset.asset_name}</div>
                                <div className="text-sm text-gray-500">{asset.asset_number}</div>
                              </div>
                            </div>
                          </td>
                          <td className="p-4 capitalize">{asset.asset_type?.replace("_", " ")}</td>
                          <td className="p-4">{asset.purchase_date}</td>
                          <td className="p-4 text-right">₹{asset.purchase_price?.toLocaleString()}</td>
                          <td className="p-4 text-right font-medium">₹{asset.book_value?.toLocaleString()}</td>
                          <td className="p-4 text-center">
                            <Badge className={statusColors[asset.status]}>{asset.status?.replace("_", " ")}</Badge>
                          </td>
                          <td className="p-4 text-right">
                            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); openDetail(asset); }}>
                              View
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                    {data.length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-gray-500">
                          No assets found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* Asset Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedAsset && (
            <>
              <DialogHeader>
                <DialogTitle>{selectedAsset.asset_name}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {/* Asset Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-500">Asset Number</Label>
                    <p className="font-medium">{selectedAsset.asset_number}</p>
                  </div>
                  <div>
                    <Label className="text-gray-500">Type</Label>
                    <p className="font-medium capitalize">{selectedAsset.asset_type?.replace("_", " ")}</p>
                  </div>
                  <div>
                    <Label className="text-gray-500">Purchase Date</Label>
                    <p className="font-medium">{selectedAsset.purchase_date}</p>
                  </div>
                  <div>
                    <Label className="text-gray-500">Location</Label>
                    <p className="font-medium">{selectedAsset.location || "-"}</p>
                  </div>
                </div>

                {/* Financial Info */}
                <Card className="bg-gray-50">
                  <CardContent className="pt-4">
                    <h4 className="font-medium mb-3">Financial Details</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label className="text-gray-500 text-sm">Purchase Price</Label>
                        <p className="font-bold text-lg">₹{selectedAsset.purchase_price?.toLocaleString()}</p>
                      </div>
                      <div>
                        <Label className="text-gray-500 text-sm">Accumulated Depreciation</Label>
                        <p className="font-bold text-lg text-orange-600">₹{selectedAsset.accumulated_depreciation?.toLocaleString()}</p>
                      </div>
                      <div>
                        <Label className="text-gray-500 text-sm">Book Value</Label>
                        <p className="font-bold text-lg text-green-600">₹{selectedAsset.book_value?.toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div>
                        <Label className="text-gray-500 text-sm">Salvage Value</Label>
                        <p className="font-medium">₹{selectedAsset.salvage_value?.toLocaleString()}</p>
                      </div>
                      <div>
                        <Label className="text-gray-500 text-sm">Useful Life</Label>
                        <p className="font-medium">{selectedAsset.useful_life_years} years</p>
                      </div>
                      <div>
                        <Label className="text-gray-500 text-sm">Annual Depreciation</Label>
                        <p className="font-medium">₹{selectedAsset.annual_depreciation?.toLocaleString()}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Depreciation History */}
                {selectedAsset.depreciation_entries?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Depreciation History</h4>
                    <div className="border rounded-lg max-h-40 overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="text-left p-2">Period</th>
                            <th className="text-right p-2">Amount</th>
                            <th className="text-right p-2">Book Value After</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedAsset.depreciation_entries.map((entry, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="p-2">{entry.period}</td>
                              <td className="p-2 text-right">₹{entry.amount?.toLocaleString()}</td>
                              <td className="p-2 text-right">₹{entry.book_value_after?.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Actions */}
                {selectedAsset.status === "active" && (
                  <div className="flex gap-2">
                    <Button onClick={() => setShowDepreciateDialog(true)} className="flex-1">
                      <Calculator className="h-4 w-4 mr-2" />
                      Record Depreciation
                    </Button>
                    <Button variant="outline" onClick={() => setShowDisposeDialog(true)} className="flex-1">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Dispose/Sell
                    </Button>
                    <Button variant="destructive" onClick={() => handleWriteOff(selectedAsset.asset_id)}>
                      <XCircle className="h-4 w-4 mr-2" />
                      Write Off
                    </Button>
                  </div>
                )}

                <Button variant="ghost" className="w-full text-red-500" onClick={() => handleDelete(selectedAsset.asset_id)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Asset
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Depreciate Dialog */}
      <Dialog open={showDepreciateDialog} onOpenChange={setShowDepreciateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Depreciation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Period (Month)</Label>
              <Input
                type="month"
                value={depreciationPeriod}
                onChange={e => setDepreciationPeriod(e.target.value)}
              />
            </div>
            <div>
              <Label>Amount (leave 0 for auto-calculate)</Label>
              <Input
                type="number"
                value={depreciationAmount}
                onChange={e => setDepreciationAmount(parseFloat(e.target.value) || 0)}
                placeholder={`Auto: ₹${(selectedAsset?.annual_depreciation / 12)?.toLocaleString() || 0}/month`}
              />
            </div>
            <Button className="w-full" onClick={handleDepreciate}>
              Record Depreciation
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dispose Dialog */}
      <Dialog open={showDisposeDialog} onOpenChange={setShowDisposeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dispose/Sell Asset</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Disposal Date</Label>
              <Input
                type="date"
                value={disposeData.disposal_date}
                onChange={e => setDisposeData({ ...disposeData, disposal_date: e.target.value })}
              />
            </div>
            <div>
              <Label>Sale/Disposal Amount</Label>
              <Input
                type="number"
                value={disposeData.disposal_amount}
                onChange={e => setDisposeData({ ...disposeData, disposal_amount: parseFloat(e.target.value) || 0 })}
              />
              <p className="text-sm text-gray-500 mt-1">
                Book Value: ₹{selectedAsset?.book_value?.toLocaleString()} | 
                {disposeData.disposal_amount >= (selectedAsset?.book_value || 0) 
                  ? ` Gain: ₹${(disposeData.disposal_amount - (selectedAsset?.book_value || 0)).toLocaleString()}`
                  : ` Loss: ₹${((selectedAsset?.book_value || 0) - disposeData.disposal_amount).toLocaleString()}`
                }
              </p>
            </div>
            <div>
              <Label>Reason</Label>
              <Input
                value={disposeData.reason}
                onChange={e => setDisposeData({ ...disposeData, reason: e.target.value })}
                placeholder="e.g., Sold to third party"
              />
            </div>
            <Button className="w-full" onClick={handleDispose}>
              Dispose Asset
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
