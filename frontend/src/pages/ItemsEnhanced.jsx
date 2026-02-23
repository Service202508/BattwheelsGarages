import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { 
  Plus, Package, Search, Edit, Trash2, Warehouse, FolderTree, Tags, 
  AlertTriangle, ArrowUpDown, BarChart3, RefreshCw, MoreHorizontal,
  Download, Upload, Copy, CheckCircle2, XCircle, Filter, SortAsc, SortDesc,
  History, Settings, FileText, Image as ImageIcon, ChevronDown, QrCode,
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Barcode, Users,
  Camera, Eye, EyeOff, Lock, FileSpreadsheet, Columns, Save
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const itemTypeColors = {
  inventory: "bg-blue-100 text-[#3B9EFF]",
  non_inventory: "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]",
  service: "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]",
  sales: "bg-purple-100 text-[#8B5CF6]",
  sales_and_purchases: "bg-orange-100 text-[#FF8C00]"
};

const itemTypeLabels = {
  inventory: "Inventory",
  non_inventory: "Non-Inventory",
  service: "Service",
  sales: "Sales Only",
  sales_and_purchases: "Sales & Purchases"
};

const UNITS = [
  { value: "pcs", label: "Pieces (pcs)" },
  { value: "nos", label: "Numbers (nos)" },
  { value: "kg", label: "Kilograms (kg)" },
  { value: "g", label: "Grams (g)" },
  { value: "ltr", label: "Liters (ltr)" },
  { value: "ml", label: "Milliliters (ml)" },
  { value: "m", label: "Meters (m)" },
  { value: "cm", label: "Centimeters (cm)" },
  { value: "sqft", label: "Square Feet (sqft)" },
  { value: "hrs", label: "Hours (hrs)" },
  { value: "box", label: "Box" },
  { value: "set", label: "Set" }
];

export default function ItemsEnhanced() {
  const [activeTab, setActiveTab] = useState("items");
  const [items, setItems] = useState([]);
  const [groups, setGroups] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [adjustments, setAdjustments] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [stockSummary, setStockSummary] = useState(null);
  const [itemHistory, setItemHistory] = useState([]);
  const [customFields, setCustomFields] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Phase 2: Reports and Barcode
  const [salesReport, setSalesReport] = useState(null);
  const [purchasesReport, setPurchasesReport] = useState(null);
  const [valuationReport, setValuationReport] = useState(null);
  const [barcodeSearch, setBarcodeSearch] = useState("");
  const [barcodeResult, setBarcodeResult] = useState(null);
  const [contacts, setContacts] = useState([]);
  
  // Phase 3: Preferences and Field Config
  const [preferences, setPreferences] = useState(null);
  const [fieldConfig, setFieldConfig] = useState([]);
  const [isScannerActive, setIsScannerActive] = useState(false);
  const videoRef = useRef(null);
  const scannerRef = useRef(null);
  
  // Filters and sorting
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterGroup, setFilterGroup] = useState("");
  const [filterActive, setFilterActive] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [sortOrder, setSortOrder] = useState("asc");
  
  // Selection for bulk actions
  const [selectedItems, setSelectedItems] = useState([]);
  const [selectAll, setSelectAll] = useState(false);

  // Dialogs
  const [showItemDialog, setShowItemDialog] = useState(false);
  const [showGroupDialog, setShowGroupDialog] = useState(false);
  const [showWarehouseDialog, setShowWarehouseDialog] = useState(false);
  const [showPriceListDialog, setShowPriceListDialog] = useState(false);
  const [showAdjustmentDialog, setShowAdjustmentDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showPreferencesDialog, setShowPreferencesDialog] = useState(false);
  const [showCustomFieldDialog, setShowCustomFieldDialog] = useState(false);
  const [showBarcodeDialog, setShowBarcodeDialog] = useState(false);
  const [showFieldConfigDialog, setShowFieldConfigDialog] = useState(false);
  const [showScannerDialog, setShowScannerDialog] = useState(false);
  const [showBulkPriceDialog, setShowBulkPriceDialog] = useState(false);
  const [showAssignPriceListDialog, setShowAssignPriceListDialog] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [viewItem, setViewItem] = useState(null);
  const [selectedPriceList, setSelectedPriceList] = useState(null);

  // Form states - Full Zoho Books compatible fields
  const initialItemData = {
    // Basic Info
    name: "", sku: "", description: "", item_type: "inventory", product_type: "goods",
    group_id: "", group_name: "",
    
    // Sales Information
    rate: 0, sales_rate: 0, sales_description: "",
    sales_account: "", sales_account_id: "", sales_account_code: "",
    
    // Purchase Information
    purchase_rate: 0, purchase_description: "",
    purchase_account: "", purchase_account_id: "", purchase_account_code: "",
    
    // Inventory Account
    inventory_account: "", inventory_account_id: "", inventory_account_code: "",
    inventory_valuation_method: "fifo",
    
    // Inventory Levels
    opening_stock: 0, opening_stock_value: 0, opening_stock_rate: 0,
    stock_on_hand: 0, reorder_level: 10,
    
    // Units
    unit: "pcs", usage_unit: "pcs", unit_name: "Pieces",
    
    // Tax Information
    taxable: true, tax_preference: "taxable", taxability_type: "Goods",
    exemption_reason: "", tax_id: "", tax_percentage: 18,
    
    // GST Taxes
    intra_state_tax_name: "GST", intra_state_tax_rate: 18, intra_state_tax_type: "percentage",
    inter_state_tax_name: "IGST", inter_state_tax_rate: 18, inter_state_tax_type: "percentage",
    
    // HSN/SAC
    hsn_code: "", sac_code: "",
    
    // Vendor
    vendor: "", preferred_vendor_id: "", preferred_vendor_name: "",
    
    // Location
    location_name: "", warehouse_id: "",
    
    // Sync Info
    source: "Manual", reference_id: "", zoho_item_id: "", last_sync_time: "",
    
    // Status & Flags
    status: "active", is_active: true,
    sellable: true, purchasable: true, track_inventory: true,
    
    // Custom Fields
    custom_fields: {}
  };
  
  const [newItem, setNewItem] = useState(initialItemData);
  
  // Auto-save for Item form
  const itemPersistence = useFormPersistence(
    'item_new',
    newItem,
    initialItemData,
    {
      enabled: showItemDialog && !editItem,
      isDialogOpen: showItemDialog,
      setFormData: setNewItem,
      debounceMs: 2000,
      entityName: 'Item'
    }
  );
  
  const [newGroup, setNewGroup] = useState({ name: "", description: "", parent_group_id: "" });
  const [newWarehouse, setNewWarehouse] = useState({ name: "", location: "", is_primary: false });
  const [newPriceList, setNewPriceList] = useState({ 
    name: "", description: "", price_list_type: "sales",
    pricing_scheme: "percentage", discount_percentage: 0, markup_percentage: 0 
  });
  const [newAdjustment, setNewAdjustment] = useState({ 
    item_id: "", warehouse_id: "", adjustment_type: "add", 
    quantity: 0, reason: "other", notes: "" 
  });
  const [newCustomField, setNewCustomField] = useState({
    field_name: "", field_type: "text", is_required: false,
    show_in_list: false, show_in_pdf: false, dropdown_options: []
  });
  const [importFile, setImportFile] = useState(null);
  const [importOverwrite, setImportOverwrite] = useState(false);

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchItems();
  }, [filterType, filterGroup, filterActive, sortBy, sortOrder]);

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([
      fetchItems(), fetchGroups(), fetchWarehouses(), 
      fetchPriceLists(), fetchAdjustments(), fetchLowStock(), 
      fetchStockSummary(), fetchCustomFields(), fetchPreferences(),
      fetchFieldConfig()
    ]);
    setLoading(false);
  };

  const fetchPreferences = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/preferences`, { headers });
      const data = await res.json();
      setPreferences(data.preferences || {});
    } catch (e) { console.error("Failed to fetch preferences:", e); }
  };

  const fetchFieldConfig = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/field-config`, { headers });
      const data = await res.json();
      setFieldConfig(data.field_config || []);
    } catch (e) { console.error("Failed to fetch field config:", e); }
  };

  const fetchItems = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (filterType) params.append("item_type", filterType);
      if (filterGroup) params.append("group_id", filterGroup);
      if (filterActive !== "") params.append("is_active", filterActive);
      params.append("sort_by", sortBy);
      params.append("sort_order", sortOrder);
      
      const url = `${API}/items-enhanced/?${params.toString()}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setItems(data.items || []);
    } catch (e) { console.error("Failed to fetch items:", e); }
  };

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/groups?include_inactive=true`, { headers });
      const data = await res.json();
      setGroups(data.groups || []);
    } catch (e) { console.error("Failed to fetch groups:", e); }
  };

  const fetchWarehouses = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/warehouses?include_inactive=true`, { headers });
      const data = await res.json();
      setWarehouses(data.warehouses || []);
    } catch (e) { console.error("Failed to fetch warehouses:", e); }
  };

  const fetchPriceLists = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists?include_inactive=true`, { headers });
      const data = await res.json();
      setPriceLists(data.price_lists || []);
    } catch (e) { console.error("Failed to fetch price lists:", e); }
  };

  const fetchAdjustments = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/adjustments`, { headers });
      const data = await res.json();
      setAdjustments(data.adjustments || []);
    } catch (e) { console.error("Failed to fetch adjustments:", e); }
  };

  const fetchLowStock = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/low-stock`, { headers });
      const data = await res.json();
      setLowStockItems(data.low_stock_items || []);
    } catch (e) { console.error("Failed to fetch low stock:", e); }
  };

  const fetchStockSummary = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/reports/stock-summary`, { headers });
      const data = await res.json();
      setStockSummary(data.stock_summary || null);
    } catch (e) { console.error("Failed to fetch stock summary:", e); }
  };

  const fetchCustomFields = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/custom-fields`, { headers });
      const data = await res.json();
      setCustomFields(data.custom_fields || []);
    } catch (e) { console.error("Failed to fetch custom fields:", e); }
  };

  const fetchItemHistory = async (itemId) => {
    try {
      const res = await fetch(`${API}/items-enhanced/history?item_id=${itemId}`, { headers });
      const data = await res.json();
      setItemHistory(data.history || []);
    } catch (e) { console.error("Failed to fetch history:", e); }
  };

  // Phase 2: Fetch reports
  const fetchSalesReport = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/reports/sales-by-item`, { headers });
      const data = await res.json();
      setSalesReport(data.report || null);
    } catch (e) { console.error("Failed to fetch sales report:", e); }
  };

  const fetchPurchasesReport = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/reports/purchases-by-item`, { headers });
      const data = await res.json();
      setPurchasesReport(data.report || null);
    } catch (e) { console.error("Failed to fetch purchases report:", e); }
  };

  const fetchValuationReport = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/reports/inventory-valuation`, { headers });
      const data = await res.json();
      setValuationReport(data.report || null);
    } catch (e) { console.error("Failed to fetch valuation report:", e); }
  };

  const fetchContacts = async () => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/`, { headers });
      const data = await res.json();
      setContacts(data.contacts || []);
    } catch (e) { console.error("Failed to fetch contacts:", e); }
  };

  // Phase 2: Barcode lookup
  const handleBarcodeLookup = async () => {
    if (!barcodeSearch.trim()) return;
    try {
      const res = await fetch(`${API}/items-enhanced/lookup/barcode/${encodeURIComponent(barcodeSearch)}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setBarcodeResult(data.item);
        toast.success(`Found: ${data.item.name}`);
      } else {
        setBarcodeResult(null);
        toast.error("Item not found with this barcode/SKU");
      }
    } catch (e) { 
      setBarcodeResult(null);
      toast.error("Lookup failed"); 
    }
  };

  // Phase 2: Assign price list to contact
  const handleAssignPriceList = async (contactId, salesPriceListId, purchasePriceListId) => {
    try {
      const res = await fetch(`${API}/items-enhanced/contact-price-lists`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          contact_id: contactId,
          sales_price_list_id: salesPriceListId || null,
          purchase_price_list_id: purchasePriceListId || null
        })
      });
      if (res.ok) {
        toast.success("Price list assigned to contact");
        setShowAssignPriceListDialog(false);
      } else {
        toast.error("Failed to assign price list");
      }
    } catch (e) { toast.error("Error assigning price list"); }
  };

  // Phase 2: Bulk set prices
  const handleBulkSetPrices = async (priceListId, percentage) => {
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists/${priceListId}/set-prices`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          price_list_id: priceListId,
          pricing_method: "percentage",
          percentage: parseFloat(percentage) || 0,
          items: []
        })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Prices updated: ${data.results.created} created, ${data.results.updated} updated`);
        setShowBulkPriceDialog(false);
        fetchPriceLists();
      }
    } catch (e) { toast.error("Error setting bulk prices"); }
  };

  // Phase 2: Generate barcode
  const handleGenerateBarcode = async (itemId) => {
    try {
      const res = await fetch(`${API}/items-enhanced/barcodes`, {
        method: "POST",
        headers,
        body: JSON.stringify({ item_id: itemId, barcode_type: "CODE128" })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Barcode generated: ${data.barcode.barcode_value}`);
        fetchItems();
      }
    } catch (e) { toast.error("Error generating barcode"); }
  };

  // Phase 3: Save preferences
  const handleSavePreferences = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/preferences`, {
        method: "PUT",
        headers,
        body: JSON.stringify(preferences)
      });
      if (res.ok) {
        toast.success("Preferences saved");
        setShowPreferencesDialog(false);
      }
    } catch (e) { toast.error("Error saving preferences"); }
  };

  // Phase 3: Save field configuration
  const handleSaveFieldConfig = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/field-config`, {
        method: "PUT",
        headers,
        body: JSON.stringify(fieldConfig)
      });
      if (res.ok) {
        toast.success("Field configuration saved");
        setShowFieldConfigDialog(false);
      }
    } catch (e) { toast.error("Error saving field config"); }
  };

  // Phase 3: Toggle field visibility
  const toggleFieldConfig = (fieldName, property) => {
    setFieldConfig(prev => prev.map(f => 
      f.field_name === fieldName ? { ...f, [property]: !f[property] } : f
    ));
  };

  // Phase 3: Barcode Scanner
  const startScanner = async () => {
    try {
      const { BrowserMultiFormatReader } = await import('@zxing/browser');
      const codeReader = new BrowserMultiFormatReader();
      scannerRef.current = codeReader;
      
      const videoInputDevices = await codeReader.listVideoInputDevices();
      if (videoInputDevices.length === 0) {
        toast.error("No camera found");
        return;
      }
      
      setIsScannerActive(true);
      
      codeReader.decodeFromVideoDevice(
        videoInputDevices[0].deviceId,
        videoRef.current,
        (result, error) => {
          if (result) {
            const barcode = result.getText();
            setBarcodeSearch(barcode);
            stopScanner();
            handleBarcodeLookup();
          }
        }
      );
    } catch (e) {
      console.error("Scanner error:", e);
      toast.error("Failed to start camera");
    }
  };

  const stopScanner = () => {
    if (scannerRef.current) {
      scannerRef.current.reset();
      scannerRef.current = null;
    }
    setIsScannerActive(false);
  };

  // Generate SKU
  const handleGenerateSKU = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/generate-sku`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setNewItem({ ...newItem, sku: data.sku });
        toast.success(`Generated SKU: ${data.sku}`);
      } else {
        toast.error(data.message || "SKU generation disabled");
      }
    } catch (e) { toast.error("Failed to generate SKU"); }
  };

  // CRUD operations
  const handleCreateItem = async () => {
    if (!newItem.name) return toast.error("Item name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/`, { method: "POST", headers, body: JSON.stringify(newItem) });
      if (res.ok) {
        toast.success("Item created successfully");
        itemPersistence.onSuccessfulSave();
        setShowItemDialog(false);
        resetItemForm();
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to create item");
      }
    } catch (e) { toast.error("Error creating item"); }
  };

  const handleUpdateItem = async () => {
    if (!editItem) return;
    try {
      const res = await fetch(`${API}/items-enhanced/${editItem.item_id}`, { 
        method: "PUT", headers, body: JSON.stringify(editItem) 
      });
      if (res.ok) {
        toast.success("Item updated");
        setEditItem(null);
        fetchData();
      }
    } catch (e) { toast.error("Error updating item"); }
  };

  const handleDeleteItem = async (itemId) => {
    if (!confirm("Are you sure you want to delete this item?")) return;
    try {
      const res = await fetch(`${API}/items-enhanced/${itemId}`, { method: "DELETE", headers });
      if (res.ok) { 
        toast.success("Item deleted"); 
        fetchData(); 
      } else { 
        const err = await res.json(); 
        toast.error(err.detail || "Cannot delete item"); 
      }
    } catch (e) { toast.error("Error deleting item"); }
  };

  const handleCloneItem = async (item) => {
    try {
      const res = await fetch(`${API}/items-enhanced/bulk-action`, {
        method: "POST", headers,
        body: JSON.stringify({ item_ids: [item.item_id], action: "clone" })
      });
      if (res.ok) {
        toast.success("Item cloned");
        fetchData();
      }
    } catch (e) { toast.error("Error cloning item"); }
  };

  const handleBulkAction = async (action) => {
    if (selectedItems.length === 0) return toast.error("No items selected");
    
    const confirmMsg = action === "delete" 
      ? `Delete ${selectedItems.length} items? This cannot be undone.`
      : `${action.charAt(0).toUpperCase() + action.slice(1)} ${selectedItems.length} items?`;
    
    if (!confirm(confirmMsg)) return;
    
    try {
      const res = await fetch(`${API}/items-enhanced/bulk-action`, {
        method: "POST", headers,
        body: JSON.stringify({ item_ids: selectedItems, action })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`${data.results.success} items processed`);
        if (data.results.errors.length > 0) {
          data.results.errors.forEach(err => toast.error(err));
        }
        setSelectedItems([]);
        setSelectAll(false);
        fetchData();
      }
    } catch (e) { toast.error("Error performing bulk action"); }
  };

  const handleExport = async (format = "csv") => {
    try {
      const params = new URLSearchParams();
      params.append("format", format);
      if (filterType) params.append("item_type", filterType);
      if (filterGroup) params.append("group_id", filterGroup);
      
      const res = await fetch(`${API}/items-enhanced/export?${params.toString()}`, { headers });
      
      if (format === "json") {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data.items, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `items_export_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
      } else {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `items_export_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
      }
      toast.success("Export completed");
    } catch (e) { toast.error("Export failed"); }
  };

  const handleImport = async () => {
    if (!importFile) return toast.error("Please select a file");
    
    const formData = new FormData();
    formData.append("file", importFile);
    formData.append("overwrite_existing", importOverwrite.toString());
    
    try {
      const res = await fetch(`${API}/items-enhanced/import?overwrite_existing=${importOverwrite}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Import complete: ${data.results.created} created, ${data.results.updated} updated`);
        if (data.results.errors.length > 0) {
          data.results.errors.slice(0, 3).forEach(err => toast.error(err));
        }
        setShowImportDialog(false);
        setImportFile(null);
        fetchData();
      } else {
        toast.error(data.detail || "Import failed");
      }
    } catch (e) { toast.error("Import failed"); }
  };

  const handleDownloadTemplate = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/export/template`, { headers });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "items_import_template.csv";
      a.click();
      toast.success("Template downloaded");
    } catch (e) { toast.error("Failed to download template"); }
  };

  // Group operations
  const handleCreateGroup = async () => {
    if (!newGroup.name) return toast.error("Group name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/groups`, { method: "POST", headers, body: JSON.stringify(newGroup) });
      if (res.ok) {
        toast.success("Item group created");
        setShowGroupDialog(false);
        setNewGroup({ name: "", description: "", parent_group_id: "" });
        fetchGroups();
      }
    } catch (e) { toast.error("Error creating group"); }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!confirm("Delete this group?")) return;
    try {
      const res = await fetch(`${API}/items-enhanced/groups/${groupId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Group deleted"); fetchGroups(); }
      else { const err = await res.json(); toast.error(err.detail || "Cannot delete group"); }
    } catch (e) { toast.error("Error deleting group"); }
  };

  // Warehouse operations
  const handleCreateWarehouse = async () => {
    if (!newWarehouse.name) return toast.error("Warehouse name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/warehouses`, { method: "POST", headers, body: JSON.stringify(newWarehouse) });
      if (res.ok) {
        toast.success("Warehouse created");
        setShowWarehouseDialog(false);
        setNewWarehouse({ name: "", location: "", is_primary: false });
        fetchWarehouses();
      }
    } catch (e) { toast.error("Error creating warehouse"); }
  };

  // Price List operations
  const handleCreatePriceList = async () => {
    if (!newPriceList.name) return toast.error("Price list name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists`, { method: "POST", headers, body: JSON.stringify(newPriceList) });
      if (res.ok) {
        toast.success("Price list created");
        setShowPriceListDialog(false);
        setNewPriceList({ name: "", description: "", price_list_type: "sales", pricing_scheme: "percentage", discount_percentage: 0, markup_percentage: 0 });
        fetchPriceLists();
      }
    } catch (e) { toast.error("Error creating price list"); }
  };

  const handleDeletePriceList = async (pricelistId) => {
    if (!confirm("Delete this price list?")) return;
    try {
      const res = await fetch(`${API}/items-enhanced/price-lists/${pricelistId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Price list deleted"); fetchPriceLists(); }
    } catch (e) { toast.error("Error deleting price list"); }
  };

  // Adjustment operations
  const handleCreateAdjustment = async () => {
    if (!newAdjustment.item_id || !newAdjustment.warehouse_id || newAdjustment.quantity <= 0) {
      return toast.error("Select item, warehouse and enter quantity > 0");
    }
    try {
      const res = await fetch(`${API}/items-enhanced/adjustments`, { method: "POST", headers, body: JSON.stringify(newAdjustment) });
      if (res.ok) {
        toast.success("Inventory adjusted");
        setShowAdjustmentDialog(false);
        setNewAdjustment({ item_id: "", warehouse_id: "", adjustment_type: "add", quantity: 0, reason: "other", notes: "" });
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to adjust inventory");
      }
    } catch (e) { toast.error("Error adjusting inventory"); }
  };

  // Custom Field operations
  const handleCreateCustomField = async () => {
    if (!newCustomField.field_name) return toast.error("Field name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/custom-fields`, { method: "POST", headers, body: JSON.stringify(newCustomField) });
      if (res.ok) {
        toast.success("Custom field created");
        setShowCustomFieldDialog(false);
        setNewCustomField({ field_name: "", field_type: "text", is_required: false, show_in_list: false, show_in_pdf: false, dropdown_options: [] });
        fetchCustomFields();
      }
    } catch (e) { toast.error("Error creating custom field"); }
  };

  const resetItemForm = () => {
    setNewItem(initialItemData);
  };

  const toggleItemSelection = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId) ? prev.filter(id => id !== itemId) : [...prev, itemId]
    );
  };

  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedItems([]);
    } else {
      setSelectedItems(items.map(i => i.item_id));
    }
    setSelectAll(!selectAll);
  };

  const inventoryItems = items.filter(i => i.item_type === "inventory" || i.item_type === "sales_and_purchases");

  return (
    <div className="space-y-6" data-testid="items-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Items"
        description="Manage products, services, and inventory"
        icon={Package}
        actions={
          <div className="flex gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2" data-testid="more-actions-btn">
                  <MoreHorizontal className="h-4 w-4" /> More
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuItem onClick={() => setShowImportDialog(true)}>
                  <Upload className="h-4 w-4 mr-2" /> Import Items
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport("csv")}>
                  <Download className="h-4 w-4 mr-2" /> Export to CSV
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport("json")}>
                  <FileText className="h-4 w-4 mr-2" /> Export to JSON
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => { setShowBarcodeDialog(true); setBarcodeResult(null); setBarcodeSearch(""); }}>
                  <QrCode className="h-4 w-4 mr-2" /> Barcode Lookup
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowScannerDialog(true)}>
                  <Camera className="h-4 w-4 mr-2" /> Scan Barcode
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => { fetchPreferences(); setShowPreferencesDialog(true); }}>
                  <Settings className="h-4 w-4 mr-2" /> Preferences
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => { fetchFieldConfig(); setShowFieldConfigDialog(true); }}>
                  <Columns className="h-4 w-4 mr-2" /> Field Configuration
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowCustomFieldDialog(true)}>
                  <Plus className="h-4 w-4 mr-2" /> Custom Fields
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button onClick={() => setShowItemDialog(true)} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2" data-testid="new-item-btn">
              <Plus className="h-4 w-4" /> New Item
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <StatCardGrid columns={6}>
        <StatCard title="Total Items" value={items.length} icon={Package} variant="info" />
        <StatCard title="Item Groups" value={groups.length} icon={FolderTree} variant="purple" />
        <StatCard title="Warehouses" value={warehouses.length} icon={Warehouse} variant="success" />
        <StatCard title="Price Lists" value={priceLists.length} icon={Tags} variant="warning" />
        <StatCard title="Low Stock" value={lowStockItems.length} icon={AlertTriangle} variant={lowStockItems.length > 0 ? "danger" : "default"} />
        <StatCard title="Stock Value" value={formatCurrencyCompact(stockSummary?.total_stock_value || 0)} icon={BarChart3} variant="teal" />
      </StatCardGrid>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => {
        setActiveTab(v);
        if (v === "reports" && !salesReport) {
          fetchSalesReport();
          fetchPurchasesReport();
          fetchValuationReport();
        }
      }}>
        <TabsList className="grid w-full grid-cols-7 lg:w-auto lg:inline-flex">
          <TabsTrigger value="items">Items</TabsTrigger>
          <TabsTrigger value="groups">Groups</TabsTrigger>
          <TabsTrigger value="warehouses">Warehouses</TabsTrigger>
          <TabsTrigger value="priceLists">Price Lists</TabsTrigger>
          <TabsTrigger value="adjustments">Adjustments</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Items Tab */}
        <TabsContent value="items" className="space-y-4">
          {/* Filters and Search */}
          <div className="flex flex-col lg:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 flex-wrap">
              <div className="relative flex-1 min-w-[200px] max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                <Input 
                  value={search} 
                  onChange={(e) => setSearch(e.target.value)} 
                  onKeyUp={(e) => e.key === 'Enter' && fetchItems()} 
                  placeholder="Search items..." 
                  className="pl-10" 
                  data-testid="search-items" 
                />
              </div>
              <Select value={filterType || "all"} onValueChange={(v) => setFilterType(v === "all" ? "" : v)}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="inventory">Inventory</SelectItem>
                  <SelectItem value="service">Service</SelectItem>
                  <SelectItem value="non_inventory">Non-Inventory</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterGroup || "all"} onValueChange={(v) => setFilterGroup(v === "all" ? "" : v)}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Groups" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Groups</SelectItem>
                  {groups.map(g => <SelectItem key={g.group_id} value={g.group_id}>{g.name}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={filterActive || "all"} onValueChange={(v) => setFilterActive(v === "all" ? "" : v)}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="true">Active</SelectItem>
                  <SelectItem value="false">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-1">
                    {sortOrder === "asc" ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
                    Sort
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => { setSortBy("name"); setSortOrder("asc"); }}>Name (A-Z)</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy("name"); setSortOrder("desc"); }}>Name (Z-A)</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy("sales_rate"); setSortOrder("asc"); }}>Price (Low-High)</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy("sales_rate"); setSortOrder("desc"); }}>Price (High-Low)</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy("stock_on_hand"); setSortOrder("asc"); }}>Stock (Low-High)</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => { setSortBy("created_time"); setSortOrder("desc"); }}>Newest First</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Bulk Actions */}
          {selectedItems.length > 0 && (
            <div className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg">
              <span className="text-sm font-medium text-[#3B9EFF]">{selectedItems.length} items selected</span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handleBulkAction("activate")}>
                  <CheckCircle2 className="h-4 w-4 mr-1" /> Activate
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleBulkAction("deactivate")}>
                  <XCircle className="h-4 w-4 mr-1" /> Deactivate
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleBulkAction("clone")}>
                  <Copy className="h-4 w-4 mr-1" /> Clone
                </Button>
                <Button size="sm" variant="destructive" onClick={() => handleBulkAction("delete")}>
                  <Trash2 className="h-4 w-4 mr-1" /> Delete
                </Button>
              </div>
              <Button size="sm" variant="ghost" onClick={() => { setSelectedItems([]); setSelectAll(false); }}>
                Clear
              </Button>
            </div>
          )}

          {/* Items — Table (desktop) / Cards (mobile) */}
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : items.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]">
                <Package className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" />
                <p>No items found</p>
                <Button onClick={() => setShowItemDialog(true)} className="mt-4">Create your first item</Button>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Desktop Table */}
              <div className="hidden md:block border rounded-lg overflow-hidden bg-[#111820]">
                <table className="w-full text-sm">
                  <thead className="bg-[#111820] border-b">
                    <tr>
                      <th className="px-4 py-3 text-left w-10">
                        <Checkbox checked={selectAll} onCheckedChange={toggleSelectAll} />
                      </th>
                      <th className="px-4 py-3 text-left font-medium">Item</th>
                      <th className="px-4 py-3 text-left font-medium">SKU</th>
                      <th className="px-4 py-3 text-left font-medium">Type</th>
                      <th className="px-4 py-3 text-left font-medium">Group</th>
                      <th className="px-4 py-3 text-right font-medium">Purchase Rate</th>
                      <th className="px-4 py-3 text-right font-medium">Selling Rate</th>
                      <th className="px-4 py-3 text-right font-medium">Stock</th>
                      <th className="px-4 py-3 text-center font-medium">Status</th>
                      <th className="px-4 py-3 text-right font-medium w-20">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map(item => (
                      <tr key={item.item_id} className="border-t hover:bg-[#111820]" data-testid={`item-row-${item.item_id}`}>
                        <td className="px-4 py-3">
                          <Checkbox
                            checked={selectedItems.includes(item.item_id)}
                            onCheckedChange={() => toggleItemSelection(item.item_id)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            {item.image_url ? (
                              <img src={item.image_url} alt="" className="w-10 h-10 rounded object-cover" />
                            ) : (
                              <div className="w-10 h-10 rounded bg-[rgba(255,255,255,0.05)] flex items-center justify-center">
                                <Package className="h-5 w-5 text-[rgba(244,246,240,0.45)]" />
                              </div>
                            )}
                            <div>
                              <p className="font-medium hover:text-[#3B9EFF] cursor-pointer" onClick={() => setViewItem(item)}>{item.name}</p>
                              {item.hsn_code && <p className="text-xs text-[rgba(244,246,240,0.45)]">HSN: {item.hsn_code}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-[rgba(244,246,240,0.35)]">{item.sku || '-'}</td>
                        <td className="px-4 py-3">
                          <Badge className={itemTypeColors[item.item_type] || "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]"}>
                            {itemTypeLabels[item.item_type] || item.item_type}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-[rgba(244,246,240,0.35)]">{item.group_name || '-'}</td>
                        <td className="px-4 py-3 text-right text-[rgba(244,246,240,0.35)]">₹{(item.purchase_rate || 0).toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 text-right font-medium">₹{(item.sales_rate || item.rate || 0).toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 text-right">
                          {(item.item_type === "inventory" || item.item_type === "sales_and_purchases") ? (
                            <span className={(item.total_stock || item.stock_on_hand || 0) <= (item.reorder_level || 0) ? "text-[#FF3B2F] font-medium" : ""}>
                              {item.total_stock ?? item.stock_on_hand ?? 0} {item.unit}
                            </span>
                          ) : '-'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge className={item.is_active !== false ? "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]" : "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.45)]"}>
                            {item.is_active !== false ? "Active" : "Inactive"}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button size="icon" variant="ghost">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => setEditItem(item)}>
                                <Edit className="h-4 w-4 mr-2" /> Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleCloneItem(item)}>
                                <Copy className="h-4 w-4 mr-2" /> Clone
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => { setViewItem(item); fetchItemHistory(item.item_id); }}>
                                <History className="h-4 w-4 mr-2" /> History
                              </DropdownMenuItem>
                              {(item.item_type === "inventory" || item.item_type === "sales_and_purchases") && (
                                <DropdownMenuItem onClick={() => {
                                  const adjUrl = `/inventory-adjustments?quick_adjust=${item.item_id}&item_name=${encodeURIComponent(item.name)}&stock=${item.stock_on_hand || item.quantity || 0}`;
                                  window.location.href = adjUrl;
                                }}>
                                  <ArrowUpDown className="h-4 w-4 mr-2" /> Adjust Stock
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-[#FF3B2F]" onClick={() => handleDeleteItem(item.item_id)}>
                                <Trash2 className="h-4 w-4 mr-2" /> Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden border rounded-lg overflow-hidden bg-[#111820] divide-y divide-[rgba(255,255,255,0.06)]">
                {items.map(item => {
                  const stock = item.total_stock ?? item.stock_on_hand ?? 0;
                  const isLowStock = stock <= (item.reorder_level || 0);
                  const isInventory = item.item_type === "inventory" || item.item_type === "sales_and_purchases";
                  return (
                    <div
                      key={item.item_id}
                      data-testid={`item-row-${item.item_id}`}
                      className="p-4"
                    >
                      {/* Top: Icon + Name + Type badge */}
                      <div className="flex items-start gap-3 mb-2">
                        <div className="w-9 h-9 rounded bg-[rgba(255,255,255,0.05)] flex items-center justify-center flex-shrink-0">
                          <Package className="h-4 w-4 text-[rgba(244,246,240,0.45)]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="font-medium text-[#F4F6F0] text-sm truncate">{item.name}</p>
                            <Badge className={itemTypeColors[item.item_type] || "bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]"} style={{ fontSize: "10px", padding: "1px 5px" }}>
                              {itemTypeLabels[item.item_type] || item.item_type}
                            </Badge>
                          </div>
                          <p className="text-xs text-[rgba(244,246,240,0.35)] font-mono mt-0.5">{item.sku || '—'}</p>
                        </div>
                      </div>

                      {/* Middle: Price + Stock */}
                      <div className="flex items-center gap-4 mb-3">
                        <div>
                          <p className="text-[10px] text-[rgba(244,246,240,0.35)] uppercase tracking-wide">Sell Price</p>
                          <p className="text-sm font-semibold text-[#F4F6F0]">₹{(item.sales_rate || item.rate || 0).toLocaleString('en-IN')}</p>
                        </div>
                        {isInventory && (
                          <div>
                            <p className="text-[10px] text-[rgba(244,246,240,0.35)] uppercase tracking-wide">Stock</p>
                            <p className={`text-sm font-semibold ${isLowStock ? "text-[#FF3B2F]" : "text-[#C8FF00]"}`}>
                              {stock} {item.unit || ""}
                            </p>
                          </div>
                        )}
                        <div className="ml-auto">
                          <Badge className={item.is_active !== false ? "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]" : "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.45)]"} style={{ fontSize: "10px" }}>
                            {item.is_active !== false ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                      </div>

                      {/* Bottom: Actions */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => setViewItem(item)}
                          style={{
                            flex: 1, minHeight: "44px",
                            background: "rgba(255,255,255,0.05)",
                            border: "1px solid rgba(255,255,255,0.10)",
                            borderRadius: "4px", color: "rgba(244,246,240,0.70)",
                            fontSize: "12px", fontFamily: "Syne, sans-serif",
                            cursor: "pointer"
                          }}
                        >
                          View
                        </button>
                        <button
                          onClick={() => setEditItem(item)}
                          style={{
                            flex: 1, minHeight: "44px",
                            background: "rgba(200,255,0,0.08)",
                            border: "1px solid rgba(200,255,0,0.20)",
                            borderRadius: "4px", color: "#C8FF00",
                            fontSize: "12px", fontFamily: "Syne, sans-serif",
                            cursor: "pointer"
                          }}
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </TabsContent>

        {/* Groups Tab */}
        <TabsContent value="groups" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowGroupDialog(true)} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2" data-testid="new-group-btn">
              <Plus className="h-4 w-4" /> New Group
            </Button>
          </div>
          {groups.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]"><FolderTree className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" /><p>No item groups yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map(group => (
                <Card key={group.group_id} data-testid={`group-card-${group.group_id}`}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg">{group.name}</CardTitle>
                      <Button size="icon" variant="ghost" onClick={() => handleDeleteGroup(group.group_id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-[rgba(244,246,240,0.35)] mb-2">{group.description || "No description"}</p>
                    <div className="flex justify-between text-sm">
                      <span className="text-[rgba(244,246,240,0.45)]">Items:</span>
                      <span className="font-medium">{group.item_count || 0}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Warehouses Tab */}
        <TabsContent value="warehouses" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowWarehouseDialog(true)} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2" data-testid="new-warehouse-btn">
              <Plus className="h-4 w-4" /> New Warehouse
            </Button>
          </div>
          {warehouses.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]"><Warehouse className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" /><p>No warehouses yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {warehouses.map(wh => (
                <Card key={wh.warehouse_id} className={wh.is_primary ? "border-green-300 bg-[rgba(34,197,94,0.08)]" : ""}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-lg">{wh.name}</CardTitle>
                      {wh.is_primary && <Badge className="bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)] text-xs">Primary</Badge>}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-[rgba(244,246,240,0.35)] mb-3">{wh.location || "No location set"}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-[rgba(255,255,255,0.05)] rounded p-2 text-center">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Items</p>
                        <p className="font-bold">{wh.total_items || 0}</p>
                      </div>
                      <div className="bg-[rgba(255,255,255,0.05)] rounded p-2 text-center">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Stock</p>
                        <p className="font-bold">{wh.total_stock || 0}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Price Lists Tab */}
        <TabsContent value="priceLists" className="space-y-4">
          <div className="flex justify-between">
            <div className="text-sm text-[rgba(244,246,240,0.45)]">
              Manage pricing strategies for customers and vendors
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => { fetchContacts(); setShowAssignPriceListDialog(true); }} className="gap-2">
                <Users className="h-4 w-4" /> Assign to Contact
              </Button>
              <Button onClick={() => setShowPriceListDialog(true)} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2" data-testid="new-pricelist-btn">
                <Plus className="h-4 w-4" /> New Price List
              </Button>
            </div>
          </div>
          {priceLists.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]"><Tags className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" /><p>No price lists yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {priceLists.map(pl => (
                <Card key={pl.pricelist_id} className="hover:border-blue-200 transition-colors">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{pl.name}</CardTitle>
                        <Badge className={pl.price_list_type === "sales" ? "bg-blue-100 text-[#3B9EFF]" : "bg-orange-100 text-[#FF8C00]"}>
                          {pl.price_list_type || "sales"}
                        </Badge>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button size="icon" variant="ghost"><MoreHorizontal className="h-4 w-4" /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => { setSelectedPriceList(pl); setShowBulkPriceDialog(true); }}>
                            <Tags className="h-4 w-4 mr-2" /> Set Bulk Prices
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-[#FF3B2F]" onClick={() => handleDeletePriceList(pl.pricelist_id)}>
                            <Trash2 className="h-4 w-4 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-[rgba(244,246,240,0.35)] mb-3">{pl.description || "No description"}</p>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="bg-[rgba(255,255,255,0.05)] rounded p-2 text-center">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Discount</p>
                        <p className="font-bold">{pl.discount_percentage || 0}%</p>
                      </div>
                      <div className="bg-[rgba(255,255,255,0.05)] rounded p-2 text-center">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Markup</p>
                        <p className="font-bold">{pl.markup_percentage || 0}%</p>
                      </div>
                      <div className="bg-[rgba(255,255,255,0.05)] rounded p-2 text-center">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Items</p>
                        <p className="font-bold">{pl.item_count || 0}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Adjustments Tab */}
        <TabsContent value="adjustments" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowAdjustmentDialog(true)} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2" data-testid="new-adjustment-btn">
              <Plus className="h-4 w-4" /> New Adjustment
            </Button>
          </div>
          {adjustments.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-[rgba(244,246,240,0.45)]"><ArrowUpDown className="h-12 w-12 mx-auto mb-4 text-[rgba(244,246,240,0.20)]" /><p>No inventory adjustments yet</p></CardContent></Card>
          ) : (
            <div className="border rounded-lg overflow-hidden bg-[#111820]">
              <table className="w-full text-sm">
                <thead className="bg-[#111820]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Item</th>
                    <th className="px-4 py-3 text-left font-medium">Warehouse</th>
                    <th className="px-4 py-3 text-center font-medium">Type</th>
                    <th className="px-4 py-3 text-right font-medium">Qty</th>
                    <th className="px-4 py-3 text-left font-medium">Reason</th>
                    <th className="px-4 py-3 text-right font-medium">Stock After</th>
                  </tr>
                </thead>
                <tbody>
                  {adjustments.map(adj => (
                    <tr key={adj.adjustment_id} className="border-t hover:bg-[#111820]">
                      <td className="px-4 py-3 text-[rgba(244,246,240,0.35)]">{new Date(adj.date || adj.created_time).toLocaleDateString('en-IN')}</td>
                      <td className="px-4 py-3 font-medium">{adj.item_name}</td>
                      <td className="px-4 py-3">{adj.warehouse_name}</td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={adj.adjustment_type === "add" ? "bg-[rgba(200,255,0,0.10)] text-[#C8FF00] border border-[rgba(200,255,0,0.25)]" : adj.adjustment_type === "value" ? "bg-blue-100 text-[#3B9EFF]" : "bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]"}>
                          {adj.adjustment_type === "add" ? "+" : adj.adjustment_type === "value" ? "Value" : "-"}{adj.adjustment_type !== "value" && adj.quantity}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">{adj.quantity}</td>
                      <td className="px-4 py-3 capitalize">{adj.reason}</td>
                      <td className="px-4 py-3 text-right font-medium">{adj.stock_after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* Reports Tab - Phase 2 */}
        <TabsContent value="reports" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Sales by Item Report */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <TrendingUp className="h-5 w-5 text-[#22C55E]" /> Sales by Item
                </CardTitle>
              </CardHeader>
              <CardContent>
                {salesReport ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-[rgba(34,197,94,0.08)] rounded p-2">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Total Revenue</p>
                        <p className="font-bold text-green-700">₹{(salesReport.summary?.total_revenue || 0).toLocaleString('en-IN')}</p>
                      </div>
                      <div className="bg-blue-50 rounded p-2">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Qty Sold</p>
                        <p className="font-bold text-[#3B9EFF]">{salesReport.summary?.total_quantity_sold || 0}</p>
                      </div>
                    </div>
                    <div className="border-t pt-2">
                      <p className="text-xs text-[rgba(244,246,240,0.45)] mb-2">Top Selling Items</p>
                      {(salesReport.items || []).slice(0, 5).map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1 border-b border-[rgba(255,255,255,0.07)]">
                          <span className="truncate flex-1">{item.item_name}</span>
                          <span className="text-[#22C55E] font-medium">₹{item.total_revenue?.toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-[rgba(244,246,240,0.45)] py-4 text-sm">Loading...</p>
                )}
              </CardContent>
            </Card>

            {/* Purchases by Item Report */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ShoppingCart className="h-5 w-5 text-[#FF8C00]" /> Purchases by Item
                </CardTitle>
              </CardHeader>
              <CardContent>
                {purchasesReport ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-[rgba(255,140,0,0.08)] rounded p-2">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Total Cost</p>
                        <p className="font-bold text-[#FF8C00]">₹{(purchasesReport.summary?.total_cost || 0).toLocaleString('en-IN')}</p>
                      </div>
                      <div className="bg-blue-50 rounded p-2">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Qty Purchased</p>
                        <p className="font-bold text-[#3B9EFF]">{purchasesReport.summary?.total_quantity_purchased || 0}</p>
                      </div>
                    </div>
                    <div className="border-t pt-2">
                      <p className="text-xs text-[rgba(244,246,240,0.45)] mb-2">Most Purchased Items</p>
                      {(purchasesReport.items || []).slice(0, 5).map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1 border-b border-[rgba(255,255,255,0.07)]">
                          <span className="truncate flex-1">{item.item_name}</span>
                          <span className="text-[#FF8C00] font-medium">₹{item.total_cost?.toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-[rgba(244,246,240,0.45)] py-4 text-sm">Loading...</p>
                )}
              </CardContent>
            </Card>

            {/* Inventory Valuation Report */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <DollarSign className="h-5 w-5 text-[#3B9EFF]" /> Inventory Valuation
                </CardTitle>
              </CardHeader>
              <CardContent>
                {valuationReport ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-blue-50 rounded p-2">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Total Value</p>
                        <p className="font-bold text-[#3B9EFF]">₹{(valuationReport.summary?.total_stock_value || 0).toLocaleString('en-IN')}</p>
                      </div>
                      <div className="bg-[rgba(139,92,246,0.08)] rounded p-2">
                        <p className="text-[rgba(244,246,240,0.45)] text-xs">Method</p>
                        <p className="font-bold text-[#8B5CF6]">{valuationReport.valuation_method || 'FIFO'}</p>
                      </div>
                    </div>
                    <div className="border-t pt-2">
                      <p className="text-xs text-[rgba(244,246,240,0.45)] mb-2">Highest Value Items</p>
                      {(valuationReport.items || []).slice(0, 5).map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1 border-b border-[rgba(255,255,255,0.07)]">
                          <span className="truncate flex-1">{item.item_name}</span>
                          <span className="text-[#3B9EFF] font-medium">₹{item.stock_value?.toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-[rgba(244,246,240,0.45)] py-4 text-sm">Loading...</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Detailed Reports Button Row */}
          <div className="flex gap-4 flex-wrap">
            <Button variant="outline" onClick={fetchSalesReport} className="gap-2">
              <RefreshCw className="h-4 w-4" /> Refresh Reports
            </Button>
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><History className="h-5 w-5" /> Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              {itemHistory.length === 0 ? (
                <p className="text-center text-[rgba(244,246,240,0.45)] py-8">Select an item to view its history</p>
              ) : (
                <div className="space-y-3">
                  {itemHistory.map((entry, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-[#111820] rounded-lg">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        entry.action === "created" ? "bg-[rgba(34,197,94,0.10)] text-[#22C55E]" :
                        entry.action === "updated" ? "bg-blue-100 text-[#3B9EFF]" :
                        entry.action === "stock_adjusted" ? "bg-orange-100 text-[#FF8C00]" :
                        "bg-[rgba(255,255,255,0.05)] text-[rgba(244,246,240,0.35)]"
                      }`}>
                        {entry.action === "created" && <Plus className="h-4 w-4" />}
                        {entry.action === "updated" && <Edit className="h-4 w-4" />}
                        {entry.action === "stock_adjusted" && <ArrowUpDown className="h-4 w-4" />}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium capitalize">{entry.action.replace("_", " ")}</p>
                        <p className="text-sm text-[rgba(244,246,240,0.45)]">{entry.user_name} • {new Date(entry.timestamp).toLocaleString('en-IN')}</p>
                        {Object.keys(entry.changes || {}).length > 0 && (
                          <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">{JSON.stringify(entry.changes)}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Item Dialog - Full Zoho Books Compatible */}
      <Dialog 
        open={showItemDialog} 
        onOpenChange={(open) => {
          if (!open && !editItem && itemPersistence.isDirty) {
            itemPersistence.setShowCloseConfirm(true);
          } else {
            if (!open && !editItem) itemPersistence.clearSavedData();
            setShowItemDialog(open);
          }
        }}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>Create New Item</DialogTitle>
                <DialogDescription>Add a new product or service - Zoho Books compatible</DialogDescription>
              </div>
              {!editItem && (
                <AutoSaveIndicator 
                  lastSaved={itemPersistence.lastSaved} 
                  isSaving={itemPersistence.isSaving} 
                  isDirty={itemPersistence.isDirty} 
                />
              )}
            </div>
          </DialogHeader>
          
          {!editItem && (
            <DraftRecoveryBanner
              show={itemPersistence.showRecoveryBanner}
              savedAt={itemPersistence.savedDraftInfo?.timestamp}
              onRestore={itemPersistence.handleRestoreDraft}
              onDiscard={itemPersistence.handleDiscardDraft}
            />
          )}
          
          <Tabs defaultValue="basic" className="w-full">
            <TabsList className="grid w-full grid-cols-5 mb-4">
              <TabsTrigger value="basic" className="text-xs">Basic</TabsTrigger>
              <TabsTrigger value="sales" className="text-xs">Sales</TabsTrigger>
              <TabsTrigger value="purchase" className="text-xs">Purchase</TabsTrigger>
              <TabsTrigger value="tax" className="text-xs">Tax/GST</TabsTrigger>
              <TabsTrigger value="inventory" className="text-xs">Inventory</TabsTrigger>
            </TabsList>

            {/* Basic Information Tab */}
            <TabsContent value="basic" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Item Type *</Label>
                  <Select value={newItem.item_type} onValueChange={(v) => setNewItem({ ...newItem, item_type: v, track_inventory: v === "inventory" || v === "goods" })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inventory">Inventory Item</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                      <SelectItem value="non_inventory">Non-Inventory Item</SelectItem>
                      <SelectItem value="goods">Goods</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Product Type</Label>
                  <Select value={newItem.product_type} onValueChange={(v) => setNewItem({ ...newItem, product_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="goods">Goods</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Item Name *</Label>
                  <Input value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} placeholder="Item name" data-testid="item-name-input" />
                </div>
                <div>
                  <Label>SKU</Label>
                  <Input value={newItem.sku} onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })} placeholder="SKU code" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Unit</Label>
                  <Select value={newItem.unit} onValueChange={(v) => setNewItem({ ...newItem, unit: v, usage_unit: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {UNITS.map(u => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Unit Name</Label>
                  <Input value={newItem.unit_name} onChange={(e) => setNewItem({ ...newItem, unit_name: e.target.value })} placeholder="e.g. Pieces, Hours" />
                </div>
                <div>
                  <Label>Item Group</Label>
                  <Select value={newItem.group_id || "none"} onValueChange={(v) => setNewItem({ ...newItem, group_id: v === "none" ? "" : v })}>
                    <SelectTrigger><SelectValue placeholder="Select group" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Group</SelectItem>
                      {groups.map(g => <SelectItem key={g.group_id} value={g.group_id}>{g.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label>Description</Label>
                <Textarea value={newItem.description} onChange={(e) => setNewItem({ ...newItem, description: e.target.value })} placeholder="Item description" rows={2} />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <Checkbox checked={newItem.sellable} onCheckedChange={(v) => setNewItem({ ...newItem, sellable: v })} />
                  <Label>Sellable</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox checked={newItem.purchasable} onCheckedChange={(v) => setNewItem({ ...newItem, purchasable: v })} />
                  <Label>Purchasable</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox checked={newItem.is_active} onCheckedChange={(v) => setNewItem({ ...newItem, is_active: v, status: v ? "active" : "inactive" })} />
                  <Label>Active</Label>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Vendor</Label>
                  <Input value={newItem.vendor} onChange={(e) => setNewItem({ ...newItem, vendor: e.target.value, preferred_vendor_name: e.target.value })} placeholder="Preferred vendor name" />
                </div>
                <div>
                  <Label>Reference ID (External)</Label>
                  <Input value={newItem.reference_id} onChange={(e) => setNewItem({ ...newItem, reference_id: e.target.value })} placeholder="External system ID" />
                </div>
              </div>
            </TabsContent>

            {/* Sales Information Tab */}
            <TabsContent value="sales" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Selling Rate *</Label>
                  <Input type="number" value={newItem.rate || newItem.sales_rate} onChange={(e) => setNewItem({ ...newItem, rate: parseFloat(e.target.value) || 0, sales_rate: parseFloat(e.target.value) || 0 })} />
                </div>
                <div>
                  <Label>Sales Account</Label>
                  <Input value={newItem.sales_account} onChange={(e) => setNewItem({ ...newItem, sales_account: e.target.value })} placeholder="e.g. Sales Revenue" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Account Code</Label>
                  <Input value={newItem.sales_account_code} onChange={(e) => setNewItem({ ...newItem, sales_account_code: e.target.value })} placeholder="e.g. 4000" />
                </div>
                <div>
                  <Label>Sales Description</Label>
                  <Input value={newItem.sales_description} onChange={(e) => setNewItem({ ...newItem, sales_description: e.target.value })} placeholder="Description for invoices" />
                </div>
              </div>
            </TabsContent>

            {/* Purchase Information Tab */}
            <TabsContent value="purchase" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Purchase Rate (Cost)</Label>
                  <Input type="number" value={newItem.purchase_rate} onChange={(e) => setNewItem({ ...newItem, purchase_rate: parseFloat(e.target.value) || 0, opening_stock_rate: parseFloat(e.target.value) || 0 })} />
                </div>
                <div>
                  <Label>Purchase Account</Label>
                  <Input value={newItem.purchase_account} onChange={(e) => setNewItem({ ...newItem, purchase_account: e.target.value })} placeholder="e.g. Cost of Goods Sold" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Purchase Account Code</Label>
                  <Input value={newItem.purchase_account_code} onChange={(e) => setNewItem({ ...newItem, purchase_account_code: e.target.value })} placeholder="e.g. 5000" />
                </div>
                <div>
                  <Label>Purchase Description</Label>
                  <Input value={newItem.purchase_description} onChange={(e) => setNewItem({ ...newItem, purchase_description: e.target.value })} placeholder="Description for purchase orders" />
                </div>
              </div>
            </TabsContent>

            {/* Tax/GST Information Tab */}
            <TabsContent value="tax" className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Taxable</Label>
                  <Select value={newItem.taxable ? "Yes" : "No"} onValueChange={(v) => setNewItem({ ...newItem, taxable: v === "Yes", tax_preference: v === "Yes" ? "taxable" : "non_taxable" })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Yes">Yes</SelectItem>
                      <SelectItem value="No">No</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Taxability Type</Label>
                  <Select value={newItem.taxability_type} onValueChange={(v) => setNewItem({ ...newItem, taxability_type: v })}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Goods">Goods</SelectItem>
                      <SelectItem value="Service">Service</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>HSN/SAC Code</Label>
                  <Input value={newItem.hsn_code} onChange={(e) => setNewItem({ ...newItem, hsn_code: e.target.value })} placeholder="4-8 digit code" />
                </div>
              </div>
              {!newItem.taxable && (
                <div>
                  <Label>Exemption Reason</Label>
                  <Input value={newItem.exemption_reason} onChange={(e) => setNewItem({ ...newItem, exemption_reason: e.target.value })} placeholder="Reason for tax exemption" />
                </div>
              )}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-3">Intra-State Tax (Within State - CGST+SGST)</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Tax Name</Label>
                    <Input value={newItem.intra_state_tax_name} onChange={(e) => setNewItem({ ...newItem, intra_state_tax_name: e.target.value })} />
                  </div>
                  <div>
                    <Label>Tax Rate %</Label>
                    <Input type="number" value={newItem.intra_state_tax_rate} onChange={(e) => setNewItem({ ...newItem, intra_state_tax_rate: parseFloat(e.target.value) || 0, tax_percentage: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div>
                    <Label>Tax Type</Label>
                    <Select value={newItem.intra_state_tax_type} onValueChange={(v) => setNewItem({ ...newItem, intra_state_tax_type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">Percentage</SelectItem>
                        <SelectItem value="fixed">Fixed Amount</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-3">Inter-State Tax (Outside State - IGST)</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Tax Name</Label>
                    <Input value={newItem.inter_state_tax_name} onChange={(e) => setNewItem({ ...newItem, inter_state_tax_name: e.target.value })} />
                  </div>
                  <div>
                    <Label>Tax Rate %</Label>
                    <Input type="number" value={newItem.inter_state_tax_rate} onChange={(e) => setNewItem({ ...newItem, inter_state_tax_rate: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div>
                    <Label>Tax Type</Label>
                    <Select value={newItem.inter_state_tax_type} onValueChange={(v) => setNewItem({ ...newItem, inter_state_tax_type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">Percentage</SelectItem>
                        <SelectItem value="fixed">Fixed Amount</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Inventory Tab */}
            <TabsContent value="inventory" className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <Checkbox checked={newItem.track_inventory} onCheckedChange={(v) => setNewItem({ ...newItem, track_inventory: v })} />
                <Label>Track Inventory for this Item</Label>
              </div>
              {newItem.track_inventory && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Inventory Account</Label>
                      <Input value={newItem.inventory_account} onChange={(e) => setNewItem({ ...newItem, inventory_account: e.target.value })} placeholder="e.g. Inventory Asset" />
                    </div>
                    <div>
                      <Label>Inventory Account Code</Label>
                      <Input value={newItem.inventory_account_code} onChange={(e) => setNewItem({ ...newItem, inventory_account_code: e.target.value })} placeholder="e.g. 1200" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Valuation Method</Label>
                      <Select value={newItem.inventory_valuation_method} onValueChange={(v) => setNewItem({ ...newItem, inventory_valuation_method: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="fifo">FIFO (First In First Out)</SelectItem>
                          <SelectItem value="weighted_average">Weighted Average</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Location/Warehouse</Label>
                      <Select value={newItem.warehouse_id || "none"} onValueChange={(v) => {
                        const wh = warehouses.find(w => w.warehouse_id === v);
                        setNewItem({ ...newItem, warehouse_id: v === "none" ? "" : v, location_name: wh?.name || "" });
                      }}>
                        <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Primary Warehouse</SelectItem>
                          {warehouses.map(w => <SelectItem key={w.warehouse_id} value={w.warehouse_id}>{w.name}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="border-t pt-4">
                    <h4 className="text-sm font-medium mb-3">Opening Stock</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Opening Stock Qty</Label>
                        <Input type="number" value={newItem.opening_stock} onChange={(e) => {
                          const qty = parseFloat(e.target.value) || 0;
                          const rate = newItem.opening_stock_rate || newItem.purchase_rate;
                          setNewItem({ ...newItem, opening_stock: qty, opening_stock_value: qty * rate, stock_on_hand: qty });
                        }} />
                      </div>
                      <div>
                        <Label>Rate per Unit</Label>
                        <Input type="number" value={newItem.opening_stock_rate || newItem.purchase_rate} onChange={(e) => {
                          const rate = parseFloat(e.target.value) || 0;
                          setNewItem({ ...newItem, opening_stock_rate: rate, opening_stock_value: newItem.opening_stock * rate });
                        }} />
                      </div>
                      <div>
                        <Label>Opening Stock Value</Label>
                        <Input type="number" value={newItem.opening_stock_value} onChange={(e) => setNewItem({ ...newItem, opening_stock_value: parseFloat(e.target.value) || 0 })} className="bg-[#111820]" />
                      </div>
                    </div>
                  </div>
                  <div>
                    <Label>Reorder Point</Label>
                    <Input type="number" value={newItem.reorder_level} onChange={(e) => setNewItem({ ...newItem, reorder_level: parseFloat(e.target.value) || 0 })} placeholder="Alert when stock falls below this" />
                  </div>
                </>
              )}
            </TabsContent>
          </Tabs>
          <DialogFooter className="mt-4 pt-4 border-t">
            <Button 
              variant="outline" 
              onClick={() => {
                if (!editItem && itemPersistence.isDirty) {
                  itemPersistence.setShowCloseConfirm(true);
                } else {
                  setShowItemDialog(false);
                  resetItemForm();
                }
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateItem} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-item-submit">Create Item</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Item Unsaved Changes Confirmation Dialog */}
      <FormCloseConfirmDialog
        open={itemPersistence.showCloseConfirm}
        onClose={() => itemPersistence.setShowCloseConfirm(false)}
        onSave={handleCreateItem}
        onDiscard={() => {
          itemPersistence.clearSavedData();
          resetItemForm();
          setShowItemDialog(false);
        }}
        entityName="Item"
      />

      {/* Edit Item Dialog */}
      <Dialog open={!!editItem} onOpenChange={(open) => !open && setEditItem(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Edit Item</DialogTitle></DialogHeader>
          {editItem && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Item Type</Label>
                  <Select value={editItem.item_type} onValueChange={(v) => setEditItem({ ...editItem, item_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inventory">Inventory</SelectItem>
                      <SelectItem value="non_inventory">Non-Inventory</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Name *</Label><Input value={editItem.name} onChange={(e) => setEditItem({ ...editItem, name: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>SKU</Label><Input value={editItem.sku || ""} onChange={(e) => setEditItem({ ...editItem, sku: e.target.value })} /></div>
                <div><Label>HSN Code</Label><Input value={editItem.hsn_code || ""} onChange={(e) => setEditItem({ ...editItem, hsn_code: e.target.value })} /></div>
                <div><Label>Unit</Label><Input value={editItem.unit || ""} onChange={(e) => setEditItem({ ...editItem, unit: e.target.value })} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>Sales Rate</Label><Input type="number" value={editItem.sales_rate || 0} onChange={(e) => setEditItem({ ...editItem, sales_rate: parseFloat(e.target.value) || 0 })} /></div>
                <div><Label>Purchase Rate</Label><Input type="number" value={editItem.purchase_rate || 0} onChange={(e) => setEditItem({ ...editItem, purchase_rate: parseFloat(e.target.value) || 0 })} /></div>
                <div><Label>Tax %</Label><Input type="number" value={editItem.tax_percentage || 0} onChange={(e) => setEditItem({ ...editItem, tax_percentage: parseFloat(e.target.value) || 0 })} /></div>
              </div>
              {(editItem.item_type === "inventory" || editItem.item_type === "sales_and_purchases") && (
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Reorder Level</Label><Input type="number" value={editItem.reorder_level || 0} onChange={(e) => setEditItem({ ...editItem, reorder_level: parseInt(e.target.value) || 0 })} /></div>
                  <div>
                    <Label>Current Stock (read-only)</Label>
                    <Input type="number" value={editItem.total_stock ?? editItem.stock_on_hand ?? 0} disabled className="bg-[rgba(255,255,255,0.05)]" />
                    <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">Use Adjustments tab to modify stock</p>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditItem(null)}>Cancel</Button>
            <Button onClick={handleUpdateItem} className="bg-[#C8FF00] text-[#080C0F] font-bold">Update Item</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Group Dialog */}
      <Dialog open={showGroupDialog} onOpenChange={setShowGroupDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Item Group</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>Name *</Label><Input value={newGroup.name} onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })} placeholder="Group name" data-testid="group-name-input" /></div>
            <div><Label>Description</Label><Textarea value={newGroup.description} onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })} placeholder="Description" /></div>
            <div>
              <Label>Parent Group</Label>
              <Select value={newGroup.parent_group_id || "none"} onValueChange={(v) => setNewGroup({ ...newGroup, parent_group_id: v === "none" ? "" : v })}>
                <SelectTrigger><SelectValue placeholder="Select parent (optional)" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Parent</SelectItem>
                  {groups.map(g => <SelectItem key={g.group_id} value={g.group_id}>{g.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGroupDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateGroup} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-group-submit">Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Warehouse Dialog */}
      <Dialog open={showWarehouseDialog} onOpenChange={setShowWarehouseDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Warehouse</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>Name *</Label><Input value={newWarehouse.name} onChange={(e) => setNewWarehouse({ ...newWarehouse, name: e.target.value })} placeholder="Warehouse name" data-testid="warehouse-name-input" /></div>
            <div><Label>Location</Label><Input value={newWarehouse.location} onChange={(e) => setNewWarehouse({ ...newWarehouse, location: e.target.value })} placeholder="Address or location" /></div>
            <div className="flex items-center gap-2">
              <Checkbox checked={newWarehouse.is_primary} onCheckedChange={(v) => setNewWarehouse({ ...newWarehouse, is_primary: v })} />
              <Label>Primary Warehouse</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowWarehouseDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateWarehouse} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-warehouse-submit">Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Price List Dialog */}
      <Dialog open={showPriceListDialog} onOpenChange={setShowPriceListDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Price List</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>Name *</Label><Input value={newPriceList.name} onChange={(e) => setNewPriceList({ ...newPriceList, name: e.target.value })} placeholder="Price list name" data-testid="pricelist-name-input" /></div>
            <div><Label>Description</Label><Textarea value={newPriceList.description} onChange={(e) => setNewPriceList({ ...newPriceList, description: e.target.value })} placeholder="Description" /></div>
            <div>
              <Label>Type</Label>
              <Select value={newPriceList.price_list_type} onValueChange={(v) => setNewPriceList({ ...newPriceList, price_list_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales">Sales Price List</SelectItem>
                  <SelectItem value="purchase">Purchase Price List</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Discount %</Label><Input type="number" value={newPriceList.discount_percentage} onChange={(e) => setNewPriceList({ ...newPriceList, discount_percentage: parseFloat(e.target.value) || 0 })} /></div>
              <div><Label>Markup %</Label><Input type="number" value={newPriceList.markup_percentage} onChange={(e) => setNewPriceList({ ...newPriceList, markup_percentage: parseFloat(e.target.value) || 0 })} /></div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPriceListDialog(false)}>Cancel</Button>
            <Button onClick={handleCreatePriceList} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-pricelist-submit">Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Adjustment Dialog */}
      <Dialog open={showAdjustmentDialog} onOpenChange={setShowAdjustmentDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Inventory Adjustment</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Item *</Label>
              <Select value={newAdjustment.item_id} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, item_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                <SelectContent>
                  {inventoryItems.map(item => <SelectItem key={item.item_id} value={item.item_id}>{item.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Warehouse *</Label>
              <Select value={newAdjustment.warehouse_id} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, warehouse_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                <SelectContent>
                  {warehouses.map(wh => <SelectItem key={wh.warehouse_id} value={wh.warehouse_id}>{wh.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Adjustment Type *</Label>
                <Select value={newAdjustment.adjustment_type} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, adjustment_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="add">Add Stock</SelectItem>
                    <SelectItem value="subtract">Remove Stock</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Quantity *</Label>
                <Input type="number" min="1" value={newAdjustment.quantity} onChange={(e) => setNewAdjustment({ ...newAdjustment, quantity: parseInt(e.target.value) || 0 })} data-testid="adjustment-quantity-input" />
              </div>
            </div>
            <div>
              <Label>Reason</Label>
              <Select value={newAdjustment.reason} onValueChange={(v) => setNewAdjustment({ ...newAdjustment, reason: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="initial">Initial Stock</SelectItem>
                  <SelectItem value="purchase">Purchase</SelectItem>
                  <SelectItem value="sale">Sale</SelectItem>
                  <SelectItem value="damage">Damage</SelectItem>
                  <SelectItem value="recount">Physical Recount</SelectItem>
                  <SelectItem value="transfer">Transfer</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Notes</Label><Textarea value={newAdjustment.notes} onChange={(e) => setNewAdjustment({ ...newAdjustment, notes: e.target.value })} placeholder="Additional notes" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAdjustmentDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateAdjustment} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-adjustment-submit">Create Adjustment</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import Items</DialogTitle>
            <DialogDescription>Upload a CSV file to import items</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="border-2 border-dashed rounded-lg p-6 text-center">
              <Upload className="h-10 w-10 mx-auto text-[rgba(244,246,240,0.45)] mb-2" />
              <input type="file" accept=".csv" onChange={(e) => setImportFile(e.target.files?.[0] || null)} className="hidden" id="import-file" />
              <label htmlFor="import-file" className="cursor-pointer">
                <p className="text-sm text-[rgba(244,246,240,0.35)]">Click to select a CSV file</p>
                <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">Max file size: 1MB</p>
              </label>
              {importFile && <p className="mt-2 text-sm font-medium text-[#22C55E]">{importFile.name}</p>}
            </div>
            <div className="flex items-center gap-2">
              <Checkbox checked={importOverwrite} onCheckedChange={(v) => setImportOverwrite(v)} />
              <Label>Overwrite existing items (match by SKU or name)</Label>
            </div>
            <Button variant="link" onClick={handleDownloadTemplate} className="p-0 h-auto">
              <Download className="h-4 w-4 mr-1" /> Download import template
            </Button>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowImportDialog(false); setImportFile(null); }}>Cancel</Button>
            <Button onClick={handleImport} disabled={!importFile} className="bg-[#C8FF00] text-[#080C0F] font-bold">Import</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom Field Dialog */}
      <Dialog open={showCustomFieldDialog} onOpenChange={setShowCustomFieldDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Manage Custom Fields</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            {customFields.length > 0 && (
              <div className="border rounded-lg divide-y">
                {customFields.map(cf => (
                  <div key={cf.field_id} className="p-3 flex items-center justify-between">
                    <div>
                      <p className="font-medium">{cf.field_name}</p>
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">{cf.field_type} {cf.is_required && "• Required"}</p>
                    </div>
                    <Button size="sm" variant="ghost" onClick={async () => {
                      await fetch(`${API}/items-enhanced/custom-fields/${cf.field_id}`, { method: "DELETE", headers });
                      fetchCustomFields();
                    }}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                  </div>
                ))}
              </div>
            )}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Add New Field</h4>
              <div className="grid grid-cols-2 gap-3">
                <Input value={newCustomField.field_name} onChange={(e) => setNewCustomField({ ...newCustomField, field_name: e.target.value })} placeholder="Field name" />
                <Select value={newCustomField.field_type} onValueChange={(v) => setNewCustomField({ ...newCustomField, field_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text">Text</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="dropdown">Dropdown</SelectItem>
                    <SelectItem value="checkbox">Checkbox</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-4 mt-3">
                <div className="flex items-center gap-2">
                  <Checkbox checked={newCustomField.is_required} onCheckedChange={(v) => setNewCustomField({ ...newCustomField, is_required: v })} />
                  <Label className="text-sm">Required</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox checked={newCustomField.show_in_list} onCheckedChange={(v) => setNewCustomField({ ...newCustomField, show_in_list: v })} />
                  <Label className="text-sm">Show in List</Label>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCustomFieldDialog(false)}>Close</Button>
            <Button onClick={handleCreateCustomField} className="bg-[#C8FF00] text-[#080C0F] font-bold">Add Field</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Barcode Lookup Dialog - Phase 2 */}
      <Dialog open={showBarcodeDialog} onOpenChange={setShowBarcodeDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5" /> Barcode / SKU Lookup
            </DialogTitle>
            <DialogDescription>Scan or enter a barcode/SKU to find an item</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex gap-2">
              <Input 
                value={barcodeSearch} 
                onChange={(e) => setBarcodeSearch(e.target.value)}
                onKeyUp={(e) => e.key === 'Enter' && handleBarcodeLookup()}
                placeholder="Enter barcode or SKU..."
                autoFocus
                data-testid="barcode-input"
              />
              <Button onClick={handleBarcodeLookup} className="bg-[#C8FF00] text-[#080C0F] font-bold">
                <Search className="h-4 w-4" />
              </Button>
            </div>
            
            {barcodeResult && (
              <div className="border rounded-lg p-4 bg-[rgba(34,197,94,0.08)]">
                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 rounded bg-[#111820] flex items-center justify-center">
                    <Package className="h-6 w-6 text-[rgba(244,246,240,0.45)]" />
                  </div>
                  <div className="flex-1">
                    <p className="font-bold text-lg">{barcodeResult.name}</p>
                    <p className="text-sm text-[rgba(244,246,240,0.35)]">SKU: {barcodeResult.sku || '-'}</p>
                    <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                      <div>
                        <span className="text-[rgba(244,246,240,0.45)]">Price:</span>
                        <span className="font-medium ml-1">₹{(barcodeResult.sales_rate || 0).toLocaleString('en-IN')}</span>
                      </div>
                      <div>
                        <span className="text-[rgba(244,246,240,0.45)]">Stock:</span>
                        <span className="font-medium ml-1">{barcodeResult.stock_on_hand || barcodeResult.available_stock || 0} {barcodeResult.unit}</span>
                      </div>
                    </div>
                    {barcodeResult.hsn_code && (
                      <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">HSN: {barcodeResult.hsn_code}</p>
                    )}
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setEditItem(barcodeResult)}>
                    <Edit className="h-3 w-3 mr-1" /> Edit
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => { 
                    setNewAdjustment({ ...newAdjustment, item_id: barcodeResult.item_id }); 
                    setShowAdjustmentDialog(true); 
                    setShowBarcodeDialog(false);
                  }}>
                    <ArrowUpDown className="h-3 w-3 mr-1" /> Adjust Stock
                  </Button>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBarcodeDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Set Prices Dialog - Phase 2 */}
      <Dialog open={showBulkPriceDialog} onOpenChange={setShowBulkPriceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Set Bulk Prices</DialogTitle>
            <DialogDescription>
              Apply percentage markup/discount to all items in: {selectedPriceList?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Percentage Adjustment</Label>
              <div className="flex gap-2 mt-2">
                <Input 
                  type="number" 
                  placeholder="Enter percentage (e.g., 10 for +10%, -5 for -5%)"
                  id="bulk-price-percentage"
                />
              </div>
              <p className="text-xs text-[rgba(244,246,240,0.45)] mt-1">Positive = markup, Negative = discount</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBulkPriceDialog(false)}>Cancel</Button>
            <Button 
              onClick={() => {
                const percentage = document.getElementById('bulk-price-percentage')?.value;
                if (selectedPriceList) {
                  handleBulkSetPrices(selectedPriceList.pricelist_id, percentage);
                }
              }}
              className="bg-[#C8FF00] text-[#080C0F] font-bold"
            >
              Apply to All Items
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Price List to Contact Dialog - Phase 2 */}
      <Dialog open={showAssignPriceListDialog} onOpenChange={setShowAssignPriceListDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Assign Price List to Contact</DialogTitle>
            <DialogDescription>Select a customer/vendor and assign their default price lists</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Contact</Label>
              <Select onValueChange={(v) => document.getElementById('assign-contact-id').value = v}>
                <SelectTrigger>
                  <SelectValue placeholder="Select contact" />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map(c => (
                    <SelectItem key={c.contact_id} value={c.contact_id}>
                      {c.company_name || c.contact_name || c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <input type="hidden" id="assign-contact-id" />
            </div>
            <div>
              <Label>Sales Price List</Label>
              <Select onValueChange={(v) => document.getElementById('assign-sales-pl').value = v}>
                <SelectTrigger>
                  <SelectValue placeholder="Select sales price list (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {priceLists.filter(p => p.price_list_type === "sales").map(pl => (
                    <SelectItem key={pl.pricelist_id} value={pl.pricelist_id}>{pl.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <input type="hidden" id="assign-sales-pl" />
            </div>
            <div>
              <Label>Purchase Price List</Label>
              <Select onValueChange={(v) => document.getElementById('assign-purchase-pl').value = v}>
                <SelectTrigger>
                  <SelectValue placeholder="Select purchase price list (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {priceLists.filter(p => p.price_list_type === "purchase").map(pl => (
                    <SelectItem key={pl.pricelist_id} value={pl.pricelist_id}>{pl.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <input type="hidden" id="assign-purchase-pl" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignPriceListDialog(false)}>Cancel</Button>
            <Button 
              onClick={() => {
                const contactId = document.getElementById('assign-contact-id')?.value;
                const salesPl = document.getElementById('assign-sales-pl')?.value;
                const purchasePl = document.getElementById('assign-purchase-pl')?.value;
                if (contactId) {
                  handleAssignPriceList(
                    contactId, 
                    salesPl === "none" ? null : salesPl,
                    purchasePl === "none" ? null : purchasePl
                  );
                } else {
                  toast.error("Please select a contact");
                }
              }}
              className="bg-[#C8FF00] text-[#080C0F] font-bold"
            >
              Assign Price List
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preferences Dialog - Phase 3 */}
      <Dialog open={showPreferencesDialog} onOpenChange={setShowPreferencesDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" /> Item Preferences
            </DialogTitle>
            <DialogDescription>Configure default settings for the Items module</DialogDescription>
          </DialogHeader>
          {preferences && (
            <div className="space-y-6 py-4">
              {/* SKU Settings */}
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[rgba(244,246,240,0.35)] border-b pb-2">SKU Settings</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label>Enable SKU</Label>
                    <Switch 
                      checked={preferences.enable_sku} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, enable_sku: v })} 
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Auto-generate SKU</Label>
                    <Switch 
                      checked={preferences.auto_generate_sku} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, auto_generate_sku: v })} 
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>SKU Prefix</Label>
                    <Input 
                      value={preferences.sku_prefix || "SKU-"} 
                      onChange={(e) => setPreferences({ ...preferences, sku_prefix: e.target.value })} 
                    />
                  </div>
                  <div>
                    <Label>Sequence Start</Label>
                    <Input 
                      type="number" 
                      value={preferences.sku_sequence_start || 1} 
                      onChange={(e) => setPreferences({ ...preferences, sku_sequence_start: parseInt(e.target.value) || 1 })} 
                    />
                  </div>
                </div>
              </div>

              {/* HSN/SAC Settings */}
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[rgba(244,246,240,0.35)] border-b pb-2">HSN/SAC Settings</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label>Require HSN/SAC</Label>
                    <Switch 
                      checked={preferences.require_hsn_sac} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, require_hsn_sac: v })} 
                    />
                  </div>
                  <div>
                    <Label>HSN Digits Required</Label>
                    <Select 
                      value={String(preferences.hsn_digits_required || 4)}
                      onValueChange={(v) => setPreferences({ ...preferences, hsn_digits_required: parseInt(v) })}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="4">4 digits</SelectItem>
                        <SelectItem value="6">6 digits</SelectItem>
                        <SelectItem value="8">8 digits</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Alerts */}
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[rgba(244,246,240,0.35)] border-b pb-2">Alerts & Notifications</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label>Low Stock Alerts</Label>
                    <Switch 
                      checked={preferences.enable_low_stock_alerts} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, enable_low_stock_alerts: v })} 
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Reorder Point Alerts</Label>
                    <Switch 
                      checked={preferences.enable_reorder_alerts} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, enable_reorder_alerts: v })} 
                    />
                  </div>
                </div>
              </div>

              {/* Defaults */}
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[rgba(244,246,240,0.35)] border-b pb-2">Default Values</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Default Unit</Label>
                    <Select 
                      value={preferences.default_unit || "pcs"}
                      onValueChange={(v) => setPreferences({ ...preferences, default_unit: v })}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {UNITS.map(u => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Default Item Type</Label>
                    <Select 
                      value={preferences.default_item_type || "inventory"}
                      onValueChange={(v) => setPreferences({ ...preferences, default_item_type: v })}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="inventory">Inventory</SelectItem>
                        <SelectItem value="service">Service</SelectItem>
                        <SelectItem value="non_inventory">Non-Inventory</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Default Tax Rate %</Label>
                    <Input 
                      type="number" 
                      value={preferences.default_tax_rate || 18} 
                      onChange={(e) => setPreferences({ ...preferences, default_tax_rate: parseFloat(e.target.value) || 18 })} 
                    />
                  </div>
                </div>
              </div>

              {/* Features */}
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[rgba(244,246,240,0.35)] border-b pb-2">Features</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="flex items-center justify-between">
                    <Label>Enable Images</Label>
                    <Switch 
                      checked={preferences.enable_images} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, enable_images: v })} 
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Enable Custom Fields</Label>
                    <Switch 
                      checked={preferences.enable_custom_fields} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, enable_custom_fields: v })} 
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Enable Barcode</Label>
                    <Switch 
                      checked={preferences.enable_barcode} 
                      onCheckedChange={(v) => setPreferences({ ...preferences, enable_barcode: v })} 
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreferencesDialog(false)}>Cancel</Button>
            <Button onClick={handleSavePreferences} className="bg-[#C8FF00] text-[#080C0F] font-bold gap-2">
              <Save className="h-4 w-4" /> Save Preferences
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Field Configuration Dialog - Phase 3 */}
      <Dialog open={showFieldConfigDialog} onOpenChange={setShowFieldConfigDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Columns className="h-5 w-5" /> Field Configuration
            </DialogTitle>
            <DialogDescription>Configure field visibility in list, form, and PDF exports</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#111820]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Field</th>
                    <th className="px-4 py-3 text-center font-medium">Active</th>
                    <th className="px-4 py-3 text-center font-medium">
                      <span className="flex items-center justify-center gap-1"><FileSpreadsheet className="h-4 w-4" /> List</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium">
                      <span className="flex items-center justify-center gap-1"><Edit className="h-4 w-4" /> Form</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium">
                      <span className="flex items-center justify-center gap-1"><FileText className="h-4 w-4" /> PDF</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium">Required</th>
                  </tr>
                </thead>
                <tbody>
                  {fieldConfig.map((field, idx) => (
                    <tr key={field.field_name} className={idx % 2 === 0 ? "bg-[#111820]" : "bg-[#111820]"}>
                      <td className="px-4 py-2 font-medium">{field.display_name || field.field_name}</td>
                      <td className="px-4 py-2 text-center">
                        <Switch 
                          checked={field.is_active !== false} 
                          onCheckedChange={() => toggleFieldConfig(field.field_name, 'is_active')}
                          disabled={field.is_mandatory}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Checkbox 
                          checked={field.show_in_list} 
                          onCheckedChange={() => toggleFieldConfig(field.field_name, 'show_in_list')}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Checkbox 
                          checked={field.show_in_form !== false} 
                          onCheckedChange={() => toggleFieldConfig(field.field_name, 'show_in_form')}
                          disabled={field.is_mandatory}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Checkbox 
                          checked={field.show_in_pdf} 
                          onCheckedChange={() => toggleFieldConfig(field.field_name, 'show_in_pdf')}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        {field.is_mandatory ? (
                          <Lock className="h-4 w-4 mx-auto text-[rgba(244,246,240,0.45)]" />
                        ) : (
                          <Checkbox 
                            checked={field.is_mandatory} 
                            onCheckedChange={() => toggleFieldConfig(field.field_name, 'is_mandatory')}
                          />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFieldConfigDialog(false)}>Cancel</Button>
            <Button onClick={handleSaveFieldConfig} className="bg-[#C8FF00] text-[#080C0F] font-bold gap-2">
              <Save className="h-4 w-4" /> Save Configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Barcode Scanner Dialog - Phase 3 */}
      <Dialog open={showScannerDialog} onOpenChange={(open) => {
        setShowScannerDialog(open);
        if (!open) stopScanner();
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Camera className="h-5 w-5" /> Barcode Scanner
            </DialogTitle>
            <DialogDescription>Point your camera at a barcode to scan</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
              <video 
                ref={videoRef} 
                className="w-full h-full object-cover"
                style={{ display: isScannerActive ? 'block' : 'none' }}
              />
              {!isScannerActive && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Button onClick={startScanner} className="gap-2">
                    <Camera className="h-4 w-4" /> Start Camera
                  </Button>
                </div>
              )}
            </div>
            {isScannerActive && (
              <div className="text-center">
                <p className="text-sm text-[rgba(244,246,240,0.45)] mb-2">Scanning... Point at barcode</p>
                <Button variant="outline" onClick={stopScanner}>Stop Scanner</Button>
              </div>
            )}
            {barcodeResult && (
              <div className="border rounded-lg p-3 bg-[rgba(34,197,94,0.08)]">
                <p className="font-medium">{barcodeResult.name}</p>
                <p className="text-sm text-[rgba(244,246,240,0.35)]">₹{(barcodeResult.sales_rate || 0).toLocaleString('en-IN')} • Stock: {barcodeResult.stock_on_hand || 0}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { stopScanner(); setShowScannerDialog(false); }}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Low Stock Alert Section */}
      {lowStockItems.length > 0 && (
        <Card className="border-red-200 bg-[rgba(255,59,47,0.08)]">
          <CardHeader>
            <CardTitle className="text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" /> Low Stock Alerts ({lowStockItems.length} items)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {lowStockItems.slice(0, 6).map(item => (
                <div key={item.item_id} className="bg-[#111820] rounded-lg p-3 border border-red-200">
                  <p className="font-medium text-sm">{item.name}</p>
                  <div className="flex justify-between mt-1 text-xs">
                    <span className="text-[rgba(244,246,240,0.45)]">Current: <span className="text-[#FF3B2F] font-bold">{item.current_stock}</span></span>
                    <span className="text-[rgba(244,246,240,0.45)]">Reorder: {item.reorder_level}</span>
                  </div>
                  <p className="text-xs text-[#FF3B2F] mt-1">Shortage: {item.shortage} units</p>
                </div>
              ))}
            </div>
            {lowStockItems.length > 6 && (
              <p className="text-sm text-[#FF3B2F] mt-3">+ {lowStockItems.length - 6} more items need attention</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
