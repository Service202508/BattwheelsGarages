import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Textarea } from "../components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator
} from "../components/ui/dropdown-menu";
import {
  Tabs, TabsContent, TabsList, TabsTrigger
} from "../components/ui/tabs";
import {
  Plus, Search, RefreshCw, Package, Trash2, MoreHorizontal,
  CheckCircle, XCircle, FileText, Calendar, Filter, Download,
  Upload, ArrowUp, ArrowDown, Eye, Edit, ShieldCheck, ShieldX,
  Settings, ClipboardList, BarChart3, AlertTriangle, Paperclip,
  FileDown, FileUp, Printer, Link2, ArrowUpDown
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_STYLES = {
  draft: "bg-yellow-100 text-yellow-800",
  adjusted: "bg-[rgba(34,197,94,0.10)] text-[#22C55E]",
  void: "bg-[rgba(255,59,47,0.10)] text-red-800"
};

const ACCOUNTS = [
  "Cost of Goods Sold",
  "Inventory Write-Off",
  "Damaged Goods Expense",
  "Stock Transfer",
  "Other Expense"
];

export default function InventoryAdjustments() {
  const [loading, setLoading] = useState(true);
  const [adjustments, setAdjustments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [reasons, setReasons] = useState([]);
  const [items, setItems] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 25, total: 0, total_pages: 0 });

  // Filters
  const [filters, setFilters] = useState({
    status: "", adjustment_type: "", reason: "",
    warehouse_id: "", search: "", date_from: "", date_to: ""
  });
  const [showFilters, setShowFilters] = useState(false);

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showReasonsDialog, setShowReasonsDialog] = useState(false);
  const [selectedAdj, setSelectedAdj] = useState(null);
  const [editMode, setEditMode] = useState(false);

  // Create form
  const [form, setForm] = useState({
    adjustment_type: "quantity",
    date: new Date().toISOString().split("T")[0],
    reference_number: "",
    account: "Cost of Goods Sold",
    reason: "",
    warehouse_id: "",
    warehouse_name: "",
    description: "",
    line_items: [],
    ticket_id: ""
  });

  // Line item add
  const [lineForm, setLineForm] = useState({ item_id: "", new_quantity: 0, new_value: 0 });

  // Reason management
  const [newReason, setNewReason] = useState({ name: "", description: "" });

  // Import/Export
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [importLoading, setImportLoading] = useState(false);

  // ABC Report
  const [showAbcDialog, setShowAbcDialog] = useState(false);
  const [abcReport, setAbcReport] = useState(null);
  const [abcDrillDown, setAbcDrillDown] = useState(null);
  const [abcDrillItem, setAbcDrillItem] = useState(null);

  // Quick adjust (from Items page)
  const [quickAdjustItem, setQuickAdjustItem] = useState(null);

  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  };

  const fetchData = useCallback(async (pg = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: pg, per_page: 25 });
      Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });

      const [adjRes, sumRes, reasonsRes, itemsRes, whRes] = await Promise.all([
        fetch(`${API}/inv-adjustments?${params}`, { headers }),
        fetch(`${API}/inv-adjustments/summary`, { headers }),
        fetch(`${API}/inv-adjustments/reasons`, { headers }),
        fetch(`${API}/items-enhanced/?per_page=500`, { headers }),
        fetch(`${API}/inventory-enhanced/warehouses`, { headers })
      ]);
      const [adjData, sumData, reasonsData, itemsData, whData] = await Promise.all([
        adjRes.json(), sumRes.json(), reasonsRes.json(), itemsRes.json(), whRes.json()
      ]);
      setAdjustments(adjData.adjustments || []);
      setPagination({ page: adjData.page, per_page: adjData.per_page, total: adjData.total, total_pages: adjData.total_pages });
      setSummary(sumData);
      setReasons(reasonsData.reasons || []);
      setItems(itemsData.items || []);
      setWarehouses(whData.warehouses || []);
    } catch (e) {
      console.error("Fetch error:", e);
    }
    setLoading(false);
  }, [filters]);

  useEffect(() => { fetchData(); }, []);

  // Handle quick adjust from Items page (URL params)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const quickItemId = params.get("quick_adjust");
    const itemName = params.get("item_name");
    const stock = parseFloat(params.get("stock") || "0");
    if (quickItemId) {
      setQuickAdjustItem({ item_id: quickItemId, name: itemName, stock });
      setForm(f => ({
        ...f,
        adjustment_type: "quantity",
        line_items: [{
          item_id: quickItemId,
          item_name: itemName || "",
          sku: "",
          quantity_available: stock,
          new_quantity: stock,
          quantity_adjusted: 0
        }]
      }));
      setShowCreateDialog(true);
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const applyFilters = () => fetchData(1);

  const clearFilters = () => {
    setFilters({ status: "", adjustment_type: "", reason: "", warehouse_id: "", search: "", date_from: "", date_to: "" });
    setTimeout(() => fetchData(1), 50);
  };

  // === Line Items ===
  const handleSelectItem = (itemId) => {
    const item = items.find(i => i.item_id === itemId);
    if (item) {
      setLineForm({
        item_id: itemId,
        new_quantity: item.stock_on_hand || item.quantity || 0,
        new_value: item.purchase_rate || 0
      });
    }
  };

  const addLineItem = () => {
    if (!lineForm.item_id) return toast.error("Select an item");
    if (form.line_items.some(l => l.item_id === lineForm.item_id)) return toast.error("Item already added");
    const item = items.find(i => i.item_id === lineForm.item_id);
    const available = item?.stock_on_hand || item?.quantity || 0;

    const newLine = {
      item_id: lineForm.item_id,
      item_name: item?.name || "",
      sku: item?.sku || "",
      quantity_available: available,
      new_quantity: form.adjustment_type === "quantity" ? lineForm.new_quantity : undefined,
      quantity_adjusted: form.adjustment_type === "quantity" ? (lineForm.new_quantity - available) : undefined,
      current_value: item?.purchase_rate || 0,
      new_value: form.adjustment_type === "value" ? lineForm.new_value : undefined,
      value_adjusted: form.adjustment_type === "value" ? (lineForm.new_value - (item?.purchase_rate || 0)) : undefined
    };
    setForm({ ...form, line_items: [...form.line_items, newLine] });
    setLineForm({ item_id: "", new_quantity: 0, new_value: 0 });
  };

  const removeLineItem = (idx) => {
    setForm({ ...form, line_items: form.line_items.filter((_, i) => i !== idx) });
  };

  const updateLineQty = (idx, newQty) => {
    const updated = [...form.line_items];
    updated[idx].new_quantity = newQty;
    updated[idx].quantity_adjusted = newQty - updated[idx].quantity_available;
    setForm({ ...form, line_items: updated });
  };

  const updateLineValue = (idx, newVal) => {
    const updated = [...form.line_items];
    updated[idx].new_value = newVal;
    updated[idx].value_adjusted = newVal - updated[idx].current_value;
    setForm({ ...form, line_items: updated });
  };

  // === CRUD ===
  const saveAdjustment = async (status = "draft") => {
    if (!form.reason) return toast.error("Select a reason");
    if (form.line_items.length === 0) return toast.error("Add at least one item");

    const payload = { ...form, status };
    try {
      const url = editMode && selectedAdj
        ? `${API}/inv-adjustments/${selectedAdj.adjustment_id}`
        : `${API}/inv-adjustments`;
      const method = editMode ? "PUT" : "POST";

      const res = await fetch(url, { method, headers, body: JSON.stringify(payload) });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message || "Saved");
        setShowCreateDialog(false);
        resetForm();
        fetchData();
      } else {
        toast.error(data.detail || "Failed to save");
      }
    } catch (e) {
      toast.error("Failed to save adjustment");
    }
  };

  const convertToAdjusted = async (adjId) => {
    try {
      const res = await fetch(`${API}/inv-adjustments/${adjId}/convert`, { method: "POST", headers });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Adjustment converted - stock updated");
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to convert");
      }
    } catch (e) { toast.error("Failed to convert"); }
  };

  const voidAdjustment = async (adjId) => {
    if (!confirm("Void this adjustment? Stock changes will be reversed.")) return;
    try {
      const res = await fetch(`${API}/inv-adjustments/${adjId}/void`, { method: "POST", headers });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Adjustment voided");
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to void");
      }
    } catch (e) { toast.error("Failed to void"); }
  };

  const deleteAdjustment = async (adjId) => {
    if (!confirm("Delete this draft adjustment?")) return;
    try {
      const res = await fetch(`${API}/inv-adjustments/${adjId}`, { method: "DELETE", headers });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Draft deleted");
        fetchData();
      } else {
        toast.error(data.detail || "Failed to delete");
      }
    } catch (e) { toast.error("Failed to delete"); }
  };

  const viewDetail = async (adjId) => {
    try {
      const res = await fetch(`${API}/inv-adjustments/${adjId}`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setSelectedAdj(data.adjustment);
        setShowDetailDialog(true);
      }
    } catch (e) { toast.error("Failed to load"); }
  };

  const openEditDialog = (adj) => {
    setEditMode(true);
    setForm({
      adjustment_type: adj.adjustment_type,
      date: adj.date,
      reference_number: adj.reference_number,
      account: adj.account,
      reason: adj.reason,
      warehouse_id: adj.warehouse_id || "",
      warehouse_name: adj.warehouse_name || "",
      description: adj.description || "",
      line_items: adj.line_items || []
    });
    setSelectedAdj(adj);
    setShowCreateDialog(true);
  };

  // === Reasons Management ===
  const createReason = async () => {
    if (!newReason.name) return toast.error("Enter reason name");
    try {
      const res = await fetch(`${API}/inv-adjustments/reasons`, {
        method: "POST", headers, body: JSON.stringify(newReason)
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success("Reason created");
        setNewReason({ name: "", description: "" });
        const r = await fetch(`${API}/inv-adjustments/reasons`, { headers });
        const rd = await r.json();
        setReasons(rd.reasons || []);
      }
    } catch (e) { toast.error("Failed to create reason"); }
  };

  const deleteReason = async (reasonId) => {
    try {
      await fetch(`${API}/inv-adjustments/reasons/${reasonId}`, { method: "DELETE", headers });
      const r = await fetch(`${API}/inv-adjustments/reasons`, { headers });
      const rd = await r.json();
      setReasons(rd.reasons || []);
      toast.success("Reason disabled");
    } catch (e) { toast.error("Failed"); }
  };

  const resetForm = () => {
    setForm({
      adjustment_type: "quantity",
      date: new Date().toISOString().split("T")[0],
      reference_number: "", account: "Cost of Goods Sold",
      reason: "", warehouse_id: "", warehouse_name: "",
      description: "", line_items: [], ticket_id: ""
    });
    setEditMode(false);
    setSelectedAdj(null);
    setQuickAdjustItem(null);
  };

  // === Export ===
  const handleExport = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
    const url = `${API}/inv-adjustments/export/csv?${params}`;
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "inventory_adjustments.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
    toast.success("Export started");
  };

  // === Import ===
  const handleImportValidate = async () => {
    if (!importFile) return toast.error("Select a CSV file");
    setImportLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", importFile);
      const res = await fetch(`${API}/inv-adjustments/import/validate`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
        body: formData
      });
      const data = await res.json();
      setImportPreview(data);
    } catch (e) { toast.error("Failed to validate file"); }
    setImportLoading(false);
  };

  const handleImportProcess = async () => {
    if (!importFile) return;
    setImportLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", importFile);
      const res = await fetch(`${API}/inv-adjustments/import/process`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
        body: formData
      });
      const data = await res.json();
      if (data.code === 0) {
        toast.success(data.message);
        setShowImportDialog(false);
        setImportFile(null);
        setImportPreview(null);
        fetchData();
      }
      if (data.errors?.length > 0) {
        data.errors.slice(0, 5).forEach(e => toast.error(e));
      }
    } catch (e) { toast.error("Import failed"); }
    setImportLoading(false);
  };

  // === PDF ===
  const downloadPdf = (adjId) => {
    window.open(`${API}/inv-adjustments/${adjId}/pdf`, "_blank");
  };

  // === ABC Report ===
  const loadAbcReport = async () => {
    try {
      const res = await fetch(`${API}/inv-adjustments/reports/abc-classification?period_days=90`, { headers });
      const data = await res.json();
      setAbcReport(data.report);
      setShowAbcDialog(true);
    } catch (e) { toast.error("Failed to load ABC report"); }
  };

  const loadAbcDrillDown = async (itemId) => {
    try {
      const res = await fetch(`${API}/inv-adjustments/reports/abc-classification/${itemId}`, { headers });
      const data = await res.json();
      setAbcDrillDown(data);
      setAbcDrillItem(itemId);
    } catch (e) { toast.error("Failed to load drill-down"); }
  };

  const fmt = (v) => `₹${(v || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

  return (
    <div className="p-6 space-y-6" data-testid="inventory-adjustments-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold" data-testid="page-title">Inventory Adjustments</h1>
          <p className="text-[rgba(244,246,240,0.45)]">Adjust stock quantities and values with full audit trail</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={loadAbcReport} data-testid="abc-report-btn">
            <BarChart3 className="h-4 w-4 mr-1" /> ABC Report
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowReasonsDialog(true)} data-testid="manage-reasons-btn">
            <Settings className="h-4 w-4 mr-1" /> Reasons
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <MoreHorizontal className="h-4 w-4 mr-1" /> More
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleExport}>
                <FileDown className="h-4 w-4 mr-2" /> Export CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => { setImportFile(null); setImportPreview(null); setShowImportDialog(true); }}>
                <FileUp className="h-4 w-4 mr-2" /> Import CSV
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => fetchData()}>
                <RefreshCw className="h-4 w-4 mr-2" /> Refresh
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button onClick={() => { resetForm(); setShowCreateDialog(true); }} data-testid="new-adjustment-btn">
            <Plus className="h-4 w-4 mr-2" /> New Adjustment
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3" data-testid="summary-cards">
          <Card>
            <CardContent className="p-3">
              <p className="text-xs text-[rgba(244,246,240,0.45)]">Total</p>
              <p className="text-xl font-bold">{summary.total}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(234,179,8,0.08)] border-yellow-200">
            <CardContent className="p-3">
              <p className="text-xs text-[#EAB308]">Draft</p>
              <p className="text-xl font-bold text-[#EAB308]">{summary.draft}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(34,197,94,0.08)] border-green-200">
            <CardContent className="p-3">
              <p className="text-xs text-[#22C55E]">Adjusted</p>
              <p className="text-xl font-bold text-green-700">{summary.adjusted}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(255,59,47,0.08)] border-red-200">
            <CardContent className="p-3">
              <p className="text-xs text-[#FF3B2F]">Voided</p>
              <p className="text-xl font-bold text-red-700">{summary.voided}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-xs text-[rgba(244,246,240,0.45)]">This Month</p>
              <p className="text-xl font-bold">{summary.this_month}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(200,255,0,0.08)] border-[rgba(200,255,0,0.20)]">
            <CardContent className="p-3">
              <p className="text-xs text-[#C8FF00] text-600">Total Increases</p>
              <p className="text-lg font-bold text-[#C8FF00] text-700">{summary.total_increases}</p>
            </CardContent>
          </Card>
          <Card className="bg-[rgba(255,140,0,0.08)] border-orange-200">
            <CardContent className="p-3">
              <p className="text-xs text-[#FF8C00]">Total Decreases</p>
              <p className="text-lg font-bold text-[#FF8C00]">{summary.total_decreases}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search & Filters */}
      <div className="space-y-3">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
            <Input
              placeholder="Search by reference, description, or reason..."
              className="pl-10"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && applyFilters()}
              data-testid="search-input"
            />
          </div>
          <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
            <Filter className="h-4 w-4 mr-1" /> Filters
          </Button>
          <Button variant="outline" onClick={applyFilters}>Search</Button>
        </div>

        {showFilters && (
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                <div>
                  <Label className="text-xs">Status</Label>
                  <Select value={filters.status || "all"} onValueChange={(v) => setFilters({ ...filters, status: v === "all" ? "" : v })}>
                    <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="draft">Draft</SelectItem>
                      <SelectItem value="adjusted">Adjusted</SelectItem>
                      <SelectItem value="void">Void</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">Type</Label>
                  <Select value={filters.adjustment_type || "all"} onValueChange={(v) => setFilters({ ...filters, adjustment_type: v === "all" ? "" : v })}>
                    <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="quantity">Quantity</SelectItem>
                      <SelectItem value="value">Value</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">Reason</Label>
                  <Select value={filters.reason || "all"} onValueChange={(v) => setFilters({ ...filters, reason: v === "all" ? "" : v })}>
                    <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Reasons</SelectItem>
                      {reasons.map(r => <SelectItem key={r.reason_id} value={r.name}>{r.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">From Date</Label>
                  <Input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
                </div>
                <div>
                  <Label className="text-xs">To Date</Label>
                  <Input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
                </div>
                <div className="flex items-end gap-2">
                  <Button size="sm" onClick={applyFilters}>Apply</Button>
                  <Button size="sm" variant="outline" onClick={clearFilters}>Clear</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Adjustments Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-center py-12 text-[rgba(244,246,240,0.45)]">Loading...</p>
          ) : adjustments.length === 0 ? (
            <div className="text-center py-12" data-testid="empty-state">
              <Package className="h-12 w-12 mx-auto text-[rgba(244,246,240,0.20)] mb-3" />
              <p className="text-[rgba(244,246,240,0.45)] font-medium">No inventory adjustments found</p>
              <p className="text-sm text-[rgba(244,246,240,0.45)] mb-4">Create an adjustment to correct stock levels or values</p>
              <Button onClick={() => { resetForm(); setShowCreateDialog(true); }}>
                <Plus className="h-4 w-4 mr-2" /> Create First Adjustment
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="adjustments-table">
                  <thead className="bg-[#111820] border-b">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-[rgba(244,246,240,0.35)]">Date</th>
                      <th className="px-4 py-3 text-left font-medium text-[rgba(244,246,240,0.35)]">Reference #</th>
                      <th className="px-4 py-3 text-left font-medium text-[rgba(244,246,240,0.35)]">Reason</th>
                      <th className="px-4 py-3 text-center font-medium text-[rgba(244,246,240,0.35)]">Type</th>
                      <th className="px-4 py-3 text-center font-medium text-[rgba(244,246,240,0.35)]">Items</th>
                      <th className="px-4 py-3 text-center font-medium text-[rgba(244,246,240,0.35)]">Status</th>
                      <th className="px-4 py-3 text-left font-medium text-[rgba(244,246,240,0.35)]">Description</th>
                      <th className="px-4 py-3 text-left font-medium text-[rgba(244,246,240,0.35)]">Created By</th>
                      <th className="px-4 py-3 text-right font-medium text-[rgba(244,246,240,0.35)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {adjustments.map((adj) => (
                      <tr key={adj.adjustment_id} className="hover:bg-[#111820]" data-testid={`row-${adj.adjustment_id}`}>
                        <td className="px-4 py-3 text-[rgba(244,246,240,0.35)]">{adj.date}</td>
                        <td className="px-4 py-3">
                          <button className="text-[#3B9EFF] hover:underline font-medium" onClick={() => viewDetail(adj.adjustment_id)} data-testid={`ref-link-${adj.adjustment_id}`}>
                            {adj.reference_number}
                          </button>
                        </td>
                        <td className="px-4 py-3">{adj.reason}</td>
                        <td className="px-4 py-3 text-center">
                          <Badge variant="outline" className="capitalize">{adj.adjustment_type}</Badge>
                        </td>
                        <td className="px-4 py-3 text-center">{adj.line_item_count || adj.line_items?.length || 0}</td>
                        <td className="px-4 py-3 text-center">
                          <Badge className={STATUS_STYLES[adj.status] || ""}>{adj.status}</Badge>
                        </td>
                        <td className="px-4 py-3 text-[rgba(244,246,240,0.45)] truncate max-w-[200px]">{adj.description}</td>
                        <td className="px-4 py-3 text-[rgba(244,246,240,0.45)]">{adj.created_by}</td>
                        <td className="px-4 py-3 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm"><MoreHorizontal className="h-4 w-4" /></Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => viewDetail(adj.adjustment_id)}>
                                <Eye className="h-4 w-4 mr-2" /> View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => downloadPdf(adj.adjustment_id)}>
                                <Printer className="h-4 w-4 mr-2" /> Download PDF
                              </DropdownMenuItem>
                              {adj.status === "draft" && (
                                <>
                                  <DropdownMenuItem onClick={() => openEditDialog(adj)}>
                                    <Edit className="h-4 w-4 mr-2" /> Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => convertToAdjusted(adj.adjustment_id)}>
                                    <ShieldCheck className="h-4 w-4 mr-2" /> Convert to Adjusted
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem className="text-[#FF3B2F]" onClick={() => deleteAdjustment(adj.adjustment_id)}>
                                    <Trash2 className="h-4 w-4 mr-2" /> Delete
                                  </DropdownMenuItem>
                                </>
                              )}
                              {adj.status === "adjusted" && (
                                <DropdownMenuItem className="text-[#FF3B2F]" onClick={() => voidAdjustment(adj.adjustment_id)}>
                                  <ShieldX className="h-4 w-4 mr-2" /> Void
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {/* Pagination */}
              {pagination.total_pages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <p className="text-sm text-[rgba(244,246,240,0.45)]">
                    Showing {(pagination.page - 1) * pagination.per_page + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total}
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={pagination.page <= 1} onClick={() => fetchData(pagination.page - 1)}>Previous</Button>
                    <Button variant="outline" size="sm" disabled={pagination.page >= pagination.total_pages} onClick={() => fetchData(pagination.page + 1)}>Next</Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ===== Create/Edit Dialog ===== */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => { if (!open) { resetForm(); } setShowCreateDialog(open); }}>
        <DialogContent className="max-w-4xl max-h-[92vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editMode ? "Edit" : "New"} Inventory Adjustment</DialogTitle>
            <DialogDescription>Record stock quantity or value corrections</DialogDescription>
          </DialogHeader>

          <div className="space-y-5">
            {/* Mode Toggle */}
            <div className="flex gap-3 p-3 bg-[#111820] rounded-lg">
              <Button variant={form.adjustment_type === "quantity" ? "default" : "outline"}
                onClick={() => setForm({ ...form, adjustment_type: "quantity", line_items: [] })}
                data-testid="mode-quantity">
                <ArrowUp className="h-4 w-4 mr-1" /> Quantity Adjustment
              </Button>
              <Button variant={form.adjustment_type === "value" ? "default" : "outline"}
                onClick={() => setForm({ ...form, adjustment_type: "value", line_items: [] })}
                data-testid="mode-value">
                <BarChart3 className="h-4 w-4 mr-1" /> Value Adjustment
              </Button>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Reference Number</Label>
                <Input
                  placeholder="Auto-generated if blank"
                  value={form.reference_number}
                  onChange={(e) => setForm({ ...form, reference_number: e.target.value })}
                  data-testid="form-reference"
                />
              </div>
              <div>
                <Label>Date *</Label>
                <Input type="date" value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  data-testid="form-date"
                />
              </div>
              <div>
                <Label>Account *</Label>
                <Select value={form.account} onValueChange={(v) => setForm({ ...form, account: v })}>
                  <SelectTrigger data-testid="form-account"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ACCOUNTS.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Reason *</Label>
                <Select value={form.reason || "none"} onValueChange={(v) => setForm({ ...form, reason: v === "none" ? "" : v })}>
                  <SelectTrigger data-testid="form-reason"><SelectValue placeholder="Select reason" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none" disabled>Select reason</SelectItem>
                    {reasons.map(r => <SelectItem key={r.reason_id} value={r.name}>{r.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Warehouse / Location</Label>
                <Select value={form.warehouse_id || "none"} onValueChange={(v) => {
                  const wh = warehouses.find(w => w.warehouse_id === v);
                  setForm({ ...form, warehouse_id: v === "none" ? "" : v, warehouse_name: wh?.name || "" });
                }}>
                  <SelectTrigger><SelectValue placeholder="Optional" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No warehouse</SelectItem>
                    {warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Description</Label>
                <Input placeholder="Additional notes..."
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Link to Ticket (optional)</Label>
                <Input placeholder="Ticket ID e.g. TKT-001"
                  value={form.ticket_id}
                  onChange={(e) => setForm({ ...form, ticket_id: e.target.value })}
                  data-testid="form-ticket-id"
                />
                <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">Optionally link this adjustment to a complaint/ticket</p>
              </div>
            </div>

            <Separator />

            {/* Line Items */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label className="text-base font-semibold">Adjustment Lines</Label>
              </div>

              {/* Add item row */}
              <div className="grid grid-cols-12 gap-2 mb-3 items-end">
                <div className="col-span-5">
                  <Label className="text-xs">Item</Label>
                  <Select value={lineForm.item_id || "none"} onValueChange={(v) => { if (v !== "none") handleSelectItem(v); }}>
                    <SelectTrigger data-testid="line-item-select"><SelectValue placeholder="Select item" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none" disabled>Select item</SelectItem>
                      {items.filter(i => !i.is_composite).map(i => (
                        <SelectItem key={i.item_id} value={i.item_id}>
                          {i.name} ({i.stock_on_hand || 0} in stock)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {form.adjustment_type === "quantity" ? (
                  <>
                    <div className="col-span-2">
                      <Label className="text-xs">Current Qty</Label>
                      <Input disabled value={lineForm.item_id ? (items.find(i => i.item_id === lineForm.item_id)?.stock_on_hand || 0) : ""} />
                    </div>
                    <div className="col-span-3">
                      <Label className="text-xs">New Quantity</Label>
                      <Input type="number" value={lineForm.new_quantity}
                        onChange={(e) => setLineForm({ ...lineForm, new_quantity: parseFloat(e.target.value) || 0 })}
                        data-testid="line-new-qty"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="col-span-2">
                      <Label className="text-xs">Current Cost</Label>
                      <Input disabled value={lineForm.item_id ? (items.find(i => i.item_id === lineForm.item_id)?.purchase_rate || 0) : ""} />
                    </div>
                    <div className="col-span-3">
                      <Label className="text-xs">New Cost</Label>
                      <Input type="number" value={lineForm.new_value}
                        onChange={(e) => setLineForm({ ...lineForm, new_value: parseFloat(e.target.value) || 0 })}
                        data-testid="line-new-value"
                      />
                    </div>
                  </>
                )}
                <div className="col-span-2">
                  <Button onClick={addLineItem} className="w-full" data-testid="add-line-btn">
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </div>
              </div>

              {/* Line items table */}
              {form.line_items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-3 py-2 text-left">Item</th>
                        <th className="px-3 py-2 text-left text-xs text-[rgba(244,246,240,0.45)]">SKU</th>
                        {form.adjustment_type === "quantity" ? (
                          <>
                            <th className="px-3 py-2 text-right">Available</th>
                            <th className="px-3 py-2 text-right">New Qty</th>
                            <th className="px-3 py-2 text-right">Change</th>
                          </>
                        ) : (
                          <>
                            <th className="px-3 py-2 text-right">Current Cost</th>
                            <th className="px-3 py-2 text-right">New Cost</th>
                            <th className="px-3 py-2 text-right">Change</th>
                          </>
                        )}
                        <th className="px-3 py-2"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {form.line_items.map((line, idx) => (
                        <tr key={idx}>
                          <td className="px-3 py-2 font-medium">{line.item_name}</td>
                          <td className="px-3 py-2 text-xs text-[rgba(244,246,240,0.45)] font-mono">{line.sku}</td>
                          {form.adjustment_type === "quantity" ? (
                            <>
                              <td className="px-3 py-2 text-right">{line.quantity_available}</td>
                              <td className="px-3 py-2 text-right">
                                <Input type="number" className="w-24 text-right h-8 inline" value={line.new_quantity ?? ""}
                                  onChange={(e) => updateLineQty(idx, parseFloat(e.target.value) || 0)} />
                              </td>
                              <td className="px-3 py-2 text-right">
                                <span className={line.quantity_adjusted < 0 ? "text-[#FF3B2F] font-medium" : line.quantity_adjusted > 0 ? "text-[#22C55E] font-medium" : ""}>
                                  {line.quantity_adjusted > 0 ? "+" : ""}{line.quantity_adjusted ?? 0}
                                </span>
                              </td>
                            </>
                          ) : (
                            <>
                              <td className="px-3 py-2 text-right">{fmt(line.current_value)}</td>
                              <td className="px-3 py-2 text-right">
                                <Input type="number" className="w-28 text-right h-8 inline" value={line.new_value ?? ""}
                                  onChange={(e) => updateLineValue(idx, parseFloat(e.target.value) || 0)} />
                              </td>
                              <td className="px-3 py-2 text-right">
                                <span className={line.value_adjusted < 0 ? "text-[#FF3B2F] font-medium" : line.value_adjusted > 0 ? "text-[#22C55E] font-medium" : ""}>
                                  {line.value_adjusted > 0 ? "+" : ""}{fmt(line.value_adjusted ?? 0)}
                                </span>
                              </td>
                            </>
                          )}
                          <td className="px-3 py-2 text-right">
                            <Button size="sm" variant="ghost" onClick={() => removeLineItem(idx)}>
                              <XCircle className="h-4 w-4 text-red-500" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="flex gap-2 sm:gap-2">
            <Button variant="outline" onClick={() => { resetForm(); setShowCreateDialog(false); }}>Cancel</Button>
            {!editMode && (
              <Button variant="outline" onClick={() => saveAdjustment("draft")} data-testid="save-draft-btn">
                <FileText className="h-4 w-4 mr-1" /> Save as Draft
              </Button>
            )}
            <Button onClick={() => saveAdjustment(editMode ? "draft" : "adjusted")} data-testid="save-adjusted-btn">
              <CheckCircle className="h-4 w-4 mr-1" /> {editMode ? "Update Draft" : "Convert to Adjusted"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== Detail Dialog ===== */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[92vh] overflow-y-auto">
          {selectedAdj && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  {selectedAdj.reference_number}
                  <Badge className={STATUS_STYLES[selectedAdj.status]}>{selectedAdj.status}</Badge>
                  <Badge variant="outline" className="capitalize">{selectedAdj.adjustment_type}</Badge>
                </DialogTitle>
                <DialogDescription>
                  {selectedAdj.date} | Account: {selectedAdj.account} | {selectedAdj.reason}
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="lines" className="mt-2">
                <TabsList>
                  <TabsTrigger value="lines">Line Items</TabsTrigger>
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="audit">Audit Trail</TabsTrigger>
                </TabsList>

                <TabsContent value="lines">
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-[#111820]">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          {selectedAdj.adjustment_type === "quantity" ? (
                            <>
                              <th className="px-3 py-2 text-right">Available</th>
                              <th className="px-3 py-2 text-right">New Qty</th>
                              <th className="px-3 py-2 text-right">Change</th>
                            </>
                          ) : (
                            <>
                              <th className="px-3 py-2 text-right">Current Cost</th>
                              <th className="px-3 py-2 text-right">New Cost</th>
                              <th className="px-3 py-2 text-right">Change</th>
                            </>
                          )}
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {(selectedAdj.line_items || []).map((line, idx) => (
                          <tr key={idx}>
                            <td className="px-3 py-2">
                              <div>
                                <p className="font-medium">{line.item_name}</p>
                                <p className="text-xs text-[rgba(244,246,240,0.45)] font-mono">{line.sku}</p>
                              </div>
                            </td>
                            {selectedAdj.adjustment_type === "quantity" ? (
                              <>
                                <td className="px-3 py-2 text-right">{line.quantity_available}</td>
                                <td className="px-3 py-2 text-right font-medium">{line.new_quantity}</td>
                                <td className="px-3 py-2 text-right">
                                  <span className={line.quantity_adjusted < 0 ? "text-[#FF3B2F] font-bold" : "text-[#22C55E] font-bold"}>
                                    {line.quantity_adjusted > 0 ? "+" : ""}{line.quantity_adjusted}
                                  </span>
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="px-3 py-2 text-right">{fmt(line.current_value)}</td>
                                <td className="px-3 py-2 text-right font-medium">{fmt(line.new_value)}</td>
                                <td className="px-3 py-2 text-right">
                                  <span className={line.value_adjusted < 0 ? "text-[#FF3B2F] font-bold" : "text-[#22C55E] font-bold"}>
                                    {line.value_adjusted > 0 ? "+" : ""}{fmt(line.value_adjusted)}
                                  </span>
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </TabsContent>

                <TabsContent value="details">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-3">
                      <div><span className="text-[rgba(244,246,240,0.45)]">Reference:</span> <span className="font-medium ml-2">{selectedAdj.reference_number}</span></div>
                      <div><span className="text-[rgba(244,246,240,0.45)]">Date:</span> <span className="ml-2">{selectedAdj.date}</span></div>
                      <div><span className="text-[rgba(244,246,240,0.45)]">Type:</span> <span className="ml-2 capitalize">{selectedAdj.adjustment_type}</span></div>
                      <div><span className="text-[rgba(244,246,240,0.45)]">Account:</span> <span className="ml-2">{selectedAdj.account}</span></div>
                      <div><span className="text-[rgba(244,246,240,0.45)]">Reason:</span> <span className="ml-2">{selectedAdj.reason}</span></div>
                    </div>
                    <div className="space-y-3">
                      <div><span className="text-[rgba(244,246,240,0.45)]">Warehouse:</span> <span className="ml-2">{selectedAdj.warehouse_name || "N/A"}</span></div>
                      <div><span className="text-[rgba(244,246,240,0.45)]">Created By:</span> <span className="ml-2">{selectedAdj.created_by}</span></div>
                      <div><span className="text-[rgba(244,246,240,0.45)]">Created At:</span> <span className="ml-2">{selectedAdj.created_at?.split("T")[0]}</span></div>
                      {selectedAdj.converted_at && <div><span className="text-[rgba(244,246,240,0.45)]">Converted:</span> <span className="ml-2">{selectedAdj.converted_at?.split("T")[0]}</span></div>}
                      {selectedAdj.voided_at && <div><span className="text-[rgba(244,246,240,0.45)]">Voided:</span> <span className="ml-2">{selectedAdj.voided_at?.split("T")[0]}</span></div>}
                      {selectedAdj.ticket_id && <div><span className="text-[rgba(244,246,240,0.45)]">Linked Ticket:</span> <span className="ml-2 text-[#3B9EFF]">{selectedAdj.ticket_id}</span></div>}
                    </div>
                  </div>
                  {selectedAdj.description && (
                    <div className="mt-4 p-3 bg-[#111820] rounded-lg">
                      <p className="text-sm text-[rgba(244,246,240,0.45)] mb-1">Description</p>
                      <p className="text-sm">{selectedAdj.description}</p>
                    </div>
                  )}
                  {/* Attachments */}
                  {selectedAdj.attachments?.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm text-[rgba(244,246,240,0.45)] mb-2 flex items-center gap-1"><Paperclip className="h-4 w-4" /> Attachments</p>
                      <div className="space-y-1">
                        {selectedAdj.attachments.map(att => (
                          <div key={att.attachment_id} className="flex items-center justify-between p-2 bg-[#111820] rounded">
                            <span className="text-sm">{att.filename} ({(att.size / 1024).toFixed(1)} KB)</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="audit">
                  {selectedAdj.audit_trail?.length > 0 ? (
                    <div className="space-y-2">
                      {selectedAdj.audit_trail.map((entry, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 bg-[#111820] rounded-lg text-sm">
                          <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                          <div>
                            <p className="font-medium">{entry.action}</p>
                            <p className="text-[rgba(244,246,240,0.45)]">{entry.details}</p>
                            <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">{entry.timestamp?.replace("T", " ").split(".")[0]} by {entry.user}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center py-6 text-[rgba(244,246,240,0.45)]">No audit entries</p>
                  )}
                </TabsContent>
              </Tabs>

              {/* Action Buttons */}
              <div className="flex justify-end gap-2 mt-4">
                <Button variant="outline" onClick={() => downloadPdf(selectedAdj.adjustment_id)} data-testid="detail-pdf-btn">
                  <Printer className="h-4 w-4 mr-1" /> PDF
                </Button>
                {selectedAdj.status === "draft" && (
                  <>
                    <Button variant="outline" onClick={() => { setShowDetailDialog(false); openEditDialog(selectedAdj); }}>
                      <Edit className="h-4 w-4 mr-1" /> Edit
                    </Button>
                    <Button onClick={() => convertToAdjusted(selectedAdj.adjustment_id)} data-testid="convert-btn">
                      <ShieldCheck className="h-4 w-4 mr-1" /> Convert to Adjusted
                    </Button>
                  </>
                )}
                {selectedAdj.status === "adjusted" && (
                  <Button variant="destructive" onClick={() => voidAdjustment(selectedAdj.adjustment_id)}>
                    <ShieldX className="h-4 w-4 mr-1" /> Void Adjustment
                  </Button>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ===== Reasons Management Dialog ===== */}
      <Dialog open={showReasonsDialog} onOpenChange={setShowReasonsDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Manage Adjustment Reasons</DialogTitle>
            <DialogDescription>Add, edit, or disable reasons for inventory adjustments</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input placeholder="New reason name" value={newReason.name}
                onChange={(e) => setNewReason({ ...newReason, name: e.target.value })}
                data-testid="new-reason-input"
              />
              <Button onClick={createReason} data-testid="add-reason-btn">
                <Plus className="h-4 w-4 mr-1" /> Add
              </Button>
            </div>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {reasons.map(r => (
                <div key={r.reason_id} className="flex items-center justify-between p-2 bg-[#111820] rounded">
                  <span className="text-sm font-medium">{r.name}</span>
                  <Button size="sm" variant="ghost" className="text-red-500 h-7" onClick={() => deleteReason(r.reason_id)}>
                    <XCircle className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ===== Import Dialog ===== */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Import Adjustments from CSV</DialogTitle>
            <DialogDescription>Upload a CSV file with adjustment data. Adjustments are created as drafts.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>CSV File</Label>
              <Input type="file" accept=".csv"
                onChange={(e) => { setImportFile(e.target.files?.[0] || null); setImportPreview(null); }}
                data-testid="import-file-input"
              />
              <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">
                Expected columns: Reference Number, Date, Type (quantity/value), Reason, Account, Item Name or Item ID, New Quantity, New Value, Description
              </p>
            </div>

            {importFile && !importPreview && (
              <Button onClick={handleImportValidate} disabled={importLoading} data-testid="validate-import-btn">
                {importLoading ? "Validating..." : "Validate File"}
              </Button>
            )}

            {importPreview && (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <Card>
                    <CardContent className="p-3 text-center">
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">Rows Found</p>
                      <p className="text-lg font-bold">{importPreview.row_count}</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-[rgba(34,197,94,0.08)]">
                    <CardContent className="p-3 text-center">
                      <p className="text-xs text-[#22C55E]">Items Matched</p>
                      <p className="text-lg font-bold text-green-700">{importPreview.items_found}</p>
                    </CardContent>
                  </Card>
                  <Card className={importPreview.items_not_found?.length > 0 ? "bg-[rgba(255,59,47,0.08)]" : ""}>
                    <CardContent className="p-3 text-center">
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">Unmatched Items</p>
                      <p className="text-lg font-bold">{importPreview.items_not_found?.length || 0}</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="text-xs text-[rgba(244,246,240,0.45)]">
                  Detected fields: {importPreview.available_fields?.join(", ")}
                </div>

                {importPreview.items_not_found?.length > 0 && (
                  <div className="p-3 bg-[rgba(234,179,8,0.08)] rounded-lg text-sm">
                    <p className="font-medium text-[#EAB308] flex items-center gap-1"><AlertTriangle className="h-4 w-4" /> Unmatched items:</p>
                    <p className="text-[#EAB308] mt-1">{importPreview.items_not_found.slice(0, 10).join(", ")}</p>
                  </div>
                )}

                {/* Preview table */}
                {importPreview.preview_rows?.length > 0 && (
                  <div className="border rounded-lg overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-[#111820]">
                        <tr>
                          {importPreview.available_fields?.map(f => (
                            <th key={f} className="px-2 py-1 text-left font-medium">{f}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {importPreview.preview_rows.map((row, i) => (
                          <tr key={i}>
                            {importPreview.available_fields?.map(f => (
                              <td key={f} className="px-2 py-1 truncate max-w-[120px]">{row[f]}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => { setImportPreview(null); setImportFile(null); }}>Cancel</Button>
                  <Button onClick={handleImportProcess} disabled={importLoading} data-testid="process-import-btn">
                    {importLoading ? "Importing..." : `Import ${importPreview.row_count} Rows`}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* ===== ABC Classification Report Dialog ===== */}
      <Dialog open={showAbcDialog} onOpenChange={(open) => { setShowAbcDialog(open); if (!open) { setAbcDrillDown(null); setAbcDrillItem(null); } }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>ABC Classification Report</DialogTitle>
            <DialogDescription>Items classified by adjustment activity (last 90 days)</DialogDescription>
          </DialogHeader>

          {abcDrillDown ? (
            <div className="space-y-4">
              <Button variant="outline" size="sm" onClick={() => { setAbcDrillDown(null); setAbcDrillItem(null); }}>
                Back to ABC Report
              </Button>
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-lg">{abcDrillDown.item?.name || abcDrillItem}</h3>
                <Badge variant="outline">{abcDrillDown.item?.sku}</Badge>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <Card><CardContent className="p-3 text-center"><p className="text-xs text-[rgba(244,246,240,0.45)]">Adjustments</p><p className="text-lg font-bold">{abcDrillDown.total_adjustments}</p></CardContent></Card>
                <Card className="bg-[rgba(34,197,94,0.08)]"><CardContent className="p-3 text-center"><p className="text-xs text-[#22C55E]">Qty Change</p><p className="text-lg font-bold text-green-700">{abcDrillDown.total_qty_change}</p></CardContent></Card>
                <Card className="bg-blue-50"><CardContent className="p-3 text-center"><p className="text-xs text-[#3B9EFF]">Value Change</p><p className="text-lg font-bold text-[#3B9EFF]">{fmt(abcDrillDown.total_value_change)}</p></CardContent></Card>
              </div>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[#111820]">
                    <tr>
                      <th className="px-3 py-2 text-left">Date</th>
                      <th className="px-3 py-2 text-left">Reference</th>
                      <th className="px-3 py-2 text-left">Reason</th>
                      <th className="px-3 py-2 text-center">Type</th>
                      <th className="px-3 py-2 text-right">Qty Change</th>
                      <th className="px-3 py-2 text-right">Value Change</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {(abcDrillDown.adjustments || []).map((a, i) => (
                      <tr key={i} className="hover:bg-[#111820]">
                        <td className="px-3 py-2">{a.date}</td>
                        <td className="px-3 py-2">
                          <button className="text-[#3B9EFF] hover:underline" onClick={() => { setShowAbcDialog(false); viewDetail(a.adjustment_id); }}>
                            {a.reference_number}
                          </button>
                        </td>
                        <td className="px-3 py-2">{a.reason}</td>
                        <td className="px-3 py-2 text-center capitalize">{a.type}</td>
                        <td className="px-3 py-2 text-right">
                          <span className={a.quantity_adjusted > 0 ? "text-[#22C55E]" : a.quantity_adjusted < 0 ? "text-[#FF3B2F]" : ""}>
                            {a.quantity_adjusted > 0 ? "+" : ""}{a.quantity_adjusted}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">{fmt(a.value_adjusted)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : abcReport ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {["A", "B", "C"].map(cls => (
                  <Card key={cls} className={cls === "A" ? "bg-[rgba(34,197,94,0.08)] border-green-200" : cls === "B" ? "bg-[rgba(234,179,8,0.08)] border-yellow-200" : "bg-[#111820]"}>
                    <CardContent className="p-3 text-center">
                      <p className="text-sm font-semibold">Class {cls}</p>
                      <p className="text-2xl font-bold">{abcReport.class_counts?.[cls] || 0}</p>
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">items</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm" data-testid="abc-report-table">
                  <thead className="bg-[#111820]">
                    <tr>
                      <th className="px-3 py-2 text-left">Item</th>
                      <th className="px-3 py-2 text-center">Adjustments</th>
                      <th className="px-3 py-2 text-right">Qty Adjusted</th>
                      <th className="px-3 py-2 text-right">% of Total</th>
                      <th className="px-3 py-2 text-right">Cumulative %</th>
                      <th className="px-3 py-2 text-center">Class</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {(abcReport.items || []).map((item, i) => (
                      <tr key={i} className="hover:bg-[#111820] cursor-pointer" onClick={() => loadAbcDrillDown(item._id)}>
                        <td className="px-3 py-2">
                          <span className="text-[#3B9EFF] hover:underline">{item.item_name || item._id}</span>
                        </td>
                        <td className="px-3 py-2 text-center">{item.adjustment_count}</td>
                        <td className="px-3 py-2 text-right">{item.total_qty_adjusted}</td>
                        <td className="px-3 py-2 text-right">{item.value_percentage}%</td>
                        <td className="px-3 py-2 text-right">{item.cumulative_percentage}%</td>
                        <td className="px-3 py-2 text-center">
                          <Badge className={item.classification === "A" ? "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]" : item.classification === "B" ? "bg-yellow-100 text-[#EAB308]" : "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]"}>
                            {item.classification}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {(abcReport.items || []).length === 0 && (
                <p className="text-center py-8 text-[rgba(244,246,240,0.45)]">No adjustment data in the last 90 days</p>
              )}
            </div>
          ) : (
            <p className="text-center py-8 text-[rgba(244,246,240,0.45)]">Loading report...</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
