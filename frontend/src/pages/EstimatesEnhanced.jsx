import { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { useEstimateCalculations } from "@/hooks/useEstimateCalculations";
import { useEstimateFilters } from "@/hooks/useEstimateFilters";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, FileText, Search, Edit, Trash2, RefreshCw, Send, CheckCircle, XCircle, 
  Eye, Copy, ArrowRightLeft, Clock, Calendar, User, Building2, Package,
  TrendingUp, AlertTriangle, ChevronRight, Percent, IndianRupee, Share2, Download,
  Paperclip, Link, Settings, ExternalLink, Upload, X, FileUp, FileDown, ListChecks, 
  Palette, LayoutTemplate, CheckSquare, Ticket, Wrench, Save
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";
import { EstimateStatusBadge, EstimateLineItemRow, EstimateTotalsBlock, EstimateLineItemsTable } from "@/components/estimates";

export default function EstimatesEnhanced() {
  const [activeTab, setActiveTab] = useState("estimates");
  const [estimates, setEstimates] = useState([]);
  const [ticketEstimates, setTicketEstimates] = useState([]); // NEW: Ticket-linked estimates
  const [summary, setSummary] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showAttachmentDialog, setShowAttachmentDialog] = useState(false);
  const [showPreferencesDialog, setShowPreferencesDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showBulkActionDialog, setShowBulkActionDialog] = useState(false);
  const [showCustomFieldsDialog, setShowCustomFieldsDialog] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showAddItemDialog, setShowAddItemDialog] = useState(false);
  const [selectedEstimate, setSelectedEstimate] = useState(null);
  
  // Edit form state
  const [editEstimate, setEditEstimate] = useState(null);

  // Bulk selection
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkAction, setBulkAction] = useState("");

  // Share link state
  const [shareLink, setShareLink] = useState(null);
  const [shareLoading, setShareLoading] = useState(false);
  const [shareConfig, setShareConfig] = useState({
    expiry_days: 30,
    allow_accept: true,
    allow_decline: true,
    password_protected: false,
    password: ""
  });

  // Attachments state
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Preferences state
  const [preferences, setPreferences] = useState({
    auto_convert_on_accept: false,
    auto_convert_to: "draft_invoice",
    auto_send_converted: false,
    allow_public_accept: true,
    allow_public_decline: true,
    notify_on_view: true,
    notify_on_accept: true,
    notify_on_decline: true
  });

  // Custom fields state
  const [customFields, setCustomFields] = useState([]);
  const [newCustomField, setNewCustomField] = useState({
    field_name: "",
    field_type: "text",
    options: [],
    is_required: false,
    default_value: "",
    show_in_pdf: true,
    show_in_portal: true
  });

  // PDF Templates state
  const [pdfTemplates, setPdfTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("standard");

  // Import state
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);

  // Contact search
  const [contacts, setContacts] = useState([]);
  const [contactSearch, setContactSearch] = useState("");
  const [selectedContact, setSelectedContact] = useState(null);
  const [customerPricing, setCustomerPricing] = useState(null);

  // Items search
  const [items, setItems] = useState([]);
  const location = useLocation();

  // Quick Add Item state
  const [quickAddItem, setQuickAddItem] = useState({
    name: "", sku: "", rate: 0, description: "", unit: "pcs", 
    tax_percentage: 18, hsn_code: "", item_type: "product"
  });

  // Form states
  const [newEstimate, setNewEstimate] = useState({
    customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
    expiry_date: "", subject: "", salesperson_name: "", terms_and_conditions: "", notes: "",
    discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
    adjustment_description: "", line_items: []
  });
  const [newLineItem, setNewLineItem] = useState({
    item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0,
    discount_type: "percent", discount_percent: 0, discount_value: 0, tax_percentage: 18, hsn_code: ""
  });
  const [sendEmail, setSendEmail] = useState("");
  const [sendMessage, setSendMessage] = useState("");

  // Initial form data for comparison
  const initialEstimateData = {
    customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
    expiry_date: "", subject: "", salesperson_name: "", terms_and_conditions: "", notes: "",
    discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
    adjustment_description: "", line_items: []
  };

  // Auto-save for New Estimate form
  const newEstimatePersistence = useFormPersistence(
    'estimate_new',
    newEstimate,
    initialEstimateData,
    {
      enabled: activeTab === "create",
      isDialogOpen: activeTab === "create",
      setFormData: setNewEstimate,
      debounceMs: 2000,
      entityName: 'Estimate'
    }
  );

  // Auto-save for Edit Estimate dialog
  const editEstimatePersistence = useFormPersistence(
    editEstimate?.estimate_id ? `estimate_edit_${editEstimate.estimate_id}` : 'estimate_edit_temp',
    editEstimate,
    editEstimate,
    {
      enabled: showEditDialog && !!editEstimate,
      isDialogOpen: showEditDialog,
      setFormData: setEditEstimate,
      debounceMs: 2000,
      entityName: 'Estimate'
    }
  );

  const token = localStorage.getItem("token");
  const organizationId = localStorage.getItem("organization_id");
  const headers = { 
    Authorization: `Bearer ${token}`, 
    "Content-Type": "application/json",
    ...(organizationId && { "X-Organization-ID": organizationId })
  };

  // Handle URL params for Quick Quote from Contacts
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const customerId = params.get('customer_id');
    const customerName = params.get('customer_name');
    if (customerId && customerName) {
      setNewEstimate(prev => ({ ...prev, customer_id: customerId }));
      setContactSearch(decodeURIComponent(customerName));
      setSelectedContact({ contact_id: customerId, name: decodeURIComponent(customerName) });
      setActiveTab("create");
      // Clear URL params
      window.history.replaceState({}, '', '/estimates');
    }
  }, [location.search]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchEstimates(), fetchTicketEstimates(), fetchSummary(), fetchFunnel(), fetchItems()]);
    setLoading(false);
  }, []);

  const fetchEstimates = async () => {
    try {
      let url = `${API}/estimates-enhanced/?per_page=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setEstimates(data.estimates || []);
    } catch (e) { console.error("Failed to fetch estimates:", e); }
  };

  // NEW: Fetch ticket-linked estimates
  const fetchTicketEstimates = async () => {
    try {
      let url = `${API}/ticket-estimates?per_page=100`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      const res = await fetch(url, { headers });
      const data = await res.json();
      setTicketEstimates(data.estimates || []);
    } catch (e) { console.error("Failed to fetch ticket estimates:", e); }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/summary`, { headers });
      const data = await res.json();
      setSummary(data.summary || null);
    } catch (e) { console.error("Failed to fetch summary:", e); }
  };

  const fetchFunnel = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/reports/conversion-funnel`, { headers });
      const data = await res.json();
      setFunnel(data.funnel || null);
    } catch (e) { console.error("Failed to fetch funnel:", e); }
  };

  const fetchItems = async () => {
    try {
      const res = await fetch(`${API}/items-enhanced/?per_page=200`, { headers });
      const data = await res.json();
      setItems(data.items || []);
    } catch (e) { console.error("Failed to fetch items:", e); }
  };

  // Quick add new item
  const handleQuickAddItem = async () => {
    if (!quickAddItem.name) return toast.error("Item name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          name: quickAddItem.name,
          sku: quickAddItem.sku || `SKU-${Date.now()}`,
          description: quickAddItem.description,
          rate: quickAddItem.rate || 0,
          unit: quickAddItem.unit || "pcs",
          tax_percentage: quickAddItem.tax_percentage || 18,
          hsn_code: quickAddItem.hsn_code,
          item_type: quickAddItem.item_type || "product",
          status: "active"
        })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Item "${quickAddItem.name}" created`);
        setShowAddItemDialog(false);
        // Add the new item to the line items
        setNewLineItem({
          item_id: data.item?.item_id || "",
          name: quickAddItem.name,
          description: quickAddItem.description || "",
          quantity: 1,
          unit: quickAddItem.unit || "pcs",
          rate: quickAddItem.rate || 0,
          discount_type: "percent",
          discount_percent: 0,
          discount_value: 0,
          tax_percentage: quickAddItem.tax_percentage || 18,
          hsn_code: quickAddItem.hsn_code || ""
        });
        // Reset and refresh items
        setQuickAddItem({ name: "", sku: "", rate: 0, description: "", unit: "pcs", tax_percentage: 18, hsn_code: "", item_type: "product" });
        fetchItems();
      } else {
        toast.error(data.detail || "Failed to create item");
      }
    } catch (e) { toast.error("Error creating item"); }
  };

  const searchContacts = async (query) => {
    if (!query || query.length < 2) {
      setContacts([]);
      return;
    }
    try {
      const res = await fetch(`${API}/contact-integration/contacts/search?q=${encodeURIComponent(query)}&contact_type=customer&limit=10`, { headers });
      const data = await res.json();
      setContacts(data.contacts || []);
    } catch (e) { console.error("Failed to search contacts:", e); }
  };

  // Fetch customer pricing info (price list)
  const fetchCustomerPricing = async (customerId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/customer-pricing/${customerId}`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setCustomerPricing(data.pricing);
        if (data.pricing?.sales_price_list) {
          toast.info(`Price List: ${data.pricing.sales_price_list.name}`, { duration: 3000 });
        }
      }
    } catch (e) { console.error("Failed to fetch customer pricing:", e); }
  };

  // Fetch item price for selected customer
  const fetchItemPricing = async (itemId, customerId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/item-pricing/${itemId}?customer_id=${customerId || ""}`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        return data.item;
      }
    } catch (e) { console.error("Failed to fetch item pricing:", e); }
    return null;
  };

  const fetchEstimateDetail = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}`, { headers });
      const data = await res.json();
      setSelectedEstimate(data.estimate);
      setShowDetailDialog(true);
    } catch (e) { toast.error("Failed to fetch estimate details"); }
  };

  // CRUD
  const handleCreateEstimate = async () => {
    if (!newEstimate.customer_id) return toast.error("Please select a customer");
    if (newEstimate.line_items.length === 0) return toast.error("Add at least one line item");
    try {
      const res = await fetch(`${API}/estimates-enhanced/`, { method: "POST", headers, body: JSON.stringify(newEstimate) });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Estimate ${data.estimate.estimate_number} created`);
        setShowCreateDialog(false);
        newEstimatePersistence.onSuccessfulSave(); // Clear auto-saved draft
        resetForm();
        fetchData();
      } else {
        toast.error(data.detail || "Failed to create estimate");
      }
    } catch (e) { toast.error("Error creating estimate"); }
  };

  const handleDeleteEstimate = async (estimateId) => {
    if (!confirm("Delete this estimate?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Estimate deleted");
        setShowDetailDialog(false);
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Cannot delete estimate");
      }
    } catch (e) { toast.error("Error deleting estimate"); }
  };

  const handleSendEstimate = async () => {
    if (!selectedEstimate) return;
    try {
      const url = `${API}/estimates-enhanced/${selectedEstimate.estimate_id}/send?email_to=${encodeURIComponent(sendEmail)}&message=${encodeURIComponent(sendMessage)}`;
      const res = await fetch(url, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success("Estimate sent!");
        setShowSendDialog(false);
        setSendEmail("");
        setSendMessage("");
        fetchEstimateDetail(selectedEstimate.estimate_id);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to send estimate");
      }
    } catch (e) { toast.error("Error sending estimate"); }
  };

  // Share Link Functions
  const handleCreateShareLink = async () => {
    if (!selectedEstimate) return;
    setShareLoading(true);
    try {
      const res = await fetch(`${API}/estimates-enhanced/${selectedEstimate.estimate_id}/share`, {
        method: "POST",
        headers,
        body: JSON.stringify(shareConfig)
      });
      const data = await res.json();
      if (res.ok) {
        const fullUrl = `${window.location.origin}${data.share_link.public_url}`;
        setShareLink({ ...data.share_link, full_url: fullUrl });
        toast.success("Share link created!");
      } else {
        toast.error(data.detail || "Failed to create share link");
      }
    } catch (e) { toast.error("Error creating share link"); }
    finally { setShareLoading(false); }
  };

  const copyShareLink = () => {
    if (shareLink?.full_url) {
      navigator.clipboard.writeText(shareLink.full_url);
      toast.success("Link copied to clipboard!");
    }
  };

  // Attachment Functions
  const fetchAttachments = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/attachments`, { headers });
      const data = await res.json();
      setAttachments(data.attachments || []);
    } catch (e) { console.error("Failed to fetch attachments:", e); }
  };

  const handleUploadAttachment = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedEstimate) return;
    
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File size exceeds 10MB limit");
      return;
    }
    
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("uploaded_by", localStorage.getItem("user_name") || "user");
    
    try {
      const res = await fetch(`${API}/estimates-enhanced/${selectedEstimate.estimate_id}/attachments`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("File uploaded successfully");
        fetchAttachments(selectedEstimate.estimate_id);
      } else {
        toast.error(data.detail || "Failed to upload file");
      }
    } catch (e) { toast.error("Error uploading file"); }
    finally { setUploading(false); }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm("Delete this attachment?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${selectedEstimate.estimate_id}/attachments/${attachmentId}`, {
        method: "DELETE",
        headers
      });
      if (res.ok) {
        toast.success("Attachment deleted");
        fetchAttachments(selectedEstimate.estimate_id);
      } else {
        toast.error("Failed to delete attachment");
      }
    } catch (e) { toast.error("Error deleting attachment"); }
  };

  const downloadAttachment = (attachmentId, filename) => {
    const url = `${API}/estimates-enhanced/${selectedEstimate.estimate_id}/attachments/${attachmentId}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  };

  // PDF Functions
  const handleDownloadPDF = async (estimateId) => {
    try {
      toast.info("Generating PDF...");
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/pdf`, { headers });
      
      if (res.headers.get('content-type')?.includes('application/pdf')) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `Estimate_${estimateId}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        toast.success("PDF downloaded!");
      } else {
        // Server returned HTML for client-side rendering
        const data = await res.json();
        // Open HTML in new window for printing/PDF
        const printWindow = window.open('', '_blank');
        printWindow.document.write(data.html);
        printWindow.document.close();
        printWindow.print();
        toast.info("PDF preview opened in new window");
      }
    } catch (e) { 
      console.error("PDF error:", e);
      toast.error("Error generating PDF"); 
    }
  };

  // Preferences Functions
  const fetchPreferences = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/preferences`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setPreferences(data.preferences);
      }
    } catch (e) { console.error("Failed to fetch preferences:", e); }
  };

  const handleSavePreferences = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/preferences`, {
        method: "PUT",
        headers,
        body: JSON.stringify(preferences)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Preferences saved!");
        setShowPreferencesDialog(false);
      } else {
        toast.error(data.detail || "Failed to save preferences");
      }
    } catch (e) { toast.error("Error saving preferences"); }
  };

  // Bulk Actions Functions
  const toggleSelectAll = () => {
    if (selectedIds.length === estimates.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(estimates.map(e => e.estimate_id));
    }
  };

  const toggleSelect = (estimateId) => {
    setSelectedIds(prev => 
      prev.includes(estimateId) 
        ? prev.filter(id => id !== estimateId)
        : [...prev, estimateId]
    );
  };

  const handleBulkAction = async () => {
    if (selectedIds.length === 0) {
      toast.error("Select at least one estimate");
      return;
    }
    if (!bulkAction) {
      toast.error("Select an action");
      return;
    }
    
    try {
      const res = await fetch(`${API}/estimates-enhanced/bulk/action`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          estimate_ids: selectedIds,
          action: bulkAction,
          reason: "Bulk action from UI"
        })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`${data.updated || data.deleted || 0} estimates updated`);
        if (data.errors?.length > 0) {
          toast.warning(`${data.errors.length} failed: ${data.errors[0].error}`);
        }
        setSelectedIds([]);
        setBulkAction("");
        setShowBulkActionDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Bulk action failed");
      }
    } catch (e) { toast.error("Error performing bulk action"); }
  };

  // ========================= EDIT ESTIMATE =========================
  const handleOpenEdit = (estimate) => {
    // Normalize line items to include discount_type if not present
    const normalizedLineItems = (estimate.line_items || []).map(item => ({
      ...item,
      discount_type: item.discount_type || "percent",
      discount_percent: item.discount_percent || 0,
      discount_value: item.discount_value || 0
    }));
    
    setEditEstimate({
      estimate_id: estimate.estimate_id,
      reference_number: estimate.reference_number || "",
      estimate_date: estimate.estimate_date || "",
      expiry_date: estimate.expiry_date || "",
      payment_terms: estimate.payment_terms || 30,
      line_items: normalizedLineItems,
      discount_type: estimate.discount_type || "percentage",
      discount_value: estimate.discount_value || 0,
      shipping_charge: estimate.shipping_charge || 0,
      customer_notes: estimate.customer_notes || "",
      terms_conditions: estimate.terms_conditions || "",
      adjustment: estimate.adjustment || 0
    });
    // Reset edit search state
    setEditItemSearch("");
    setEditSearchResults([]);
    setEditActiveItemIndex(null);
    // Ensure items are loaded for search
    if (items.length === 0) {
      fetchItems();
    }
    setShowEditDialog(true);
  };

  // Edit item search state
  const [editItemSearch, setEditItemSearch] = useState("");
  const [editSearchResults, setEditSearchResults] = useState([]);
  const [editActiveItemIndex, setEditActiveItemIndex] = useState(null);

  const updateEditLineItem = (index, field, value) => {
    setEditEstimate(prev => {
      const updated = [...prev.line_items];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, line_items: updated };
    });
  };

  const addEditLineItem = () => {
    setEditEstimate(prev => ({
      ...prev,
      line_items: [...prev.line_items, { 
        name: "", description: "", quantity: 1, rate: 0, 
        tax_percentage: 18, unit: "pcs", item_id: "",
        discount_type: "percent", discount_percent: 0, discount_value: 0
      }]
    }));
    // Set focus to the new item
    setTimeout(() => {
      setEditActiveItemIndex(editEstimate?.line_items?.length || 0);
      setEditItemSearch("");
    }, 100);
  };

  // Select item from search results for edit dialog
  const selectEditItem = (item, index) => {
    setEditEstimate(prev => {
      const updated = [...prev.line_items];
      updated[index] = {
        ...updated[index],
        item_id: item.item_id,
        name: item.name,
        description: item.description || "",
        rate: item.rate || item.sales_rate || 0,
        unit: item.unit || "pcs",
        tax_percentage: item.tax_percentage || 18,
        hsn_code: item.hsn_code || ""
      };
      return { ...prev, line_items: updated };
    });
    setEditItemSearch("");
    setEditSearchResults([]);
    setEditActiveItemIndex(null);
  };

  const removeEditLineItem = (index) => {
    setEditEstimate(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const handleUpdateEstimate = async () => {
    if (!editEstimate) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${editEstimate.estimate_id}`, {
        method: "PUT",
        headers,
        body: JSON.stringify(editEstimate)
      });
      if (res.ok) {
        toast.success("Estimate updated successfully");
        editEstimatePersistence.onSuccessfulSave(); // Clear auto-saved draft
        setShowEditDialog(false);
        fetchEstimateDetail(editEstimate.estimate_id);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to update estimate");
      }
    } catch (e) {
      toast.error("Error updating estimate");
    }
  };

  // Custom Fields Functions
  const fetchCustomFields = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/custom-fields`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setCustomFields(data.custom_fields || []);
      }
    } catch (e) { console.error("Failed to fetch custom fields:", e); }
  };

  const handleAddCustomField = async () => {
    if (!newCustomField.field_name.trim()) {
      toast.error("Field name is required");
      return;
    }
    try {
      const res = await fetch(`${API}/estimates-enhanced/custom-fields`, {
        method: "POST",
        headers,
        body: JSON.stringify(newCustomField)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Custom field added!");
        setNewCustomField({
          field_name: "", field_type: "text", options: [], is_required: false,
          default_value: "", show_in_pdf: true, show_in_portal: true
        });
        fetchCustomFields();
      } else {
        toast.error(data.detail || "Failed to add custom field");
      }
    } catch (e) { toast.error("Error adding custom field"); }
  };

  const handleDeleteCustomField = async (fieldName) => {
    if (!confirm(`Delete custom field "${fieldName}"?`)) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/custom-fields/${encodeURIComponent(fieldName)}`, {
        method: "DELETE",
        headers
      });
      if (res.ok) {
        toast.success("Custom field deleted");
        fetchCustomFields();
      } else {
        toast.error("Failed to delete custom field");
      }
    } catch (e) { toast.error("Error deleting custom field"); }
  };

  // PDF Templates Functions
  const fetchPdfTemplates = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/templates`, { headers });
      const data = await res.json();
      if (data.code === 0) {
        setPdfTemplates(data.templates || []);
      }
    } catch (e) { console.error("Failed to fetch PDF templates:", e); }
  };

  const handleDownloadWithTemplate = async (estimateId, templateId) => {
    try {
      toast.info(`Generating PDF with ${templateId} template...`);
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/pdf/${templateId}`, { headers });
      
      if (res.headers.get('content-type')?.includes('application/pdf')) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `Estimate_${estimateId}_${templateId}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        toast.success("PDF downloaded!");
      } else {
        const data = await res.json();
        const printWindow = window.open('', '_blank');
        printWindow.document.write(data.html);
        printWindow.document.close();
        printWindow.print();
      }
    } catch (e) { toast.error("Error generating PDF"); }
  };

  // Import/Export Functions
  const handleExport = async (format = "csv") => {
    try {
      toast.info("Exporting estimates...");
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);
      params.append("format", format);
      
      const res = await fetch(`${API}/estimates-enhanced/export?${params.toString()}`, { headers });
      
      if (format === "csv") {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `estimates_export_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
        window.URL.revokeObjectURL(url);
        toast.success("Export downloaded!");
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data.estimates, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `estimates_export_${new Date().toISOString().slice(0, 10)}.json`;
        link.click();
        window.URL.revokeObjectURL(url);
        toast.success(`Exported ${data.count} estimates!`);
      }
    } catch (e) { toast.error("Export failed"); }
  };

  const handleImport = async () => {
    if (!importFile) {
      toast.error("Please select a file");
      return;
    }
    
    setImporting(true);
    const formData = new FormData();
    formData.append("file", importFile);
    
    try {
      const res = await fetch(`${API}/estimates-enhanced/import?skip_errors=true`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Imported ${data.imported} estimates!`);
        if (data.errors?.length > 0) {
          toast.warning(`${data.errors.length} rows had errors`);
        }
        setShowImportDialog(false);
        setImportFile(null);
        fetchData();
      } else {
        toast.error(data.detail || "Import failed");
      }
    } catch (e) { toast.error("Import error"); }
    finally { setImporting(false); }
  };

  const downloadImportTemplate = () => {
    window.open(`${API}/estimates-enhanced/import/template`, '_blank');
  };

  const handleMarkAccepted = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/mark-accepted`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Estimate marked as accepted");
        fetchEstimateDetail(estimateId);
        fetchData();
      }
    } catch (e) { toast.error("Error updating status"); }
  };

  const handleMarkDeclined = async (estimateId) => {
    const reason = prompt("Enter decline reason (optional):");
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/mark-declined?reason=${encodeURIComponent(reason || "")}`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Estimate marked as declined");
        fetchEstimateDetail(estimateId);
        fetchData();
      }
    } catch (e) { toast.error("Error updating status"); }
  };

  const handleConvertToInvoice = async (estimateId) => {
    if (!confirm("Convert this estimate to an invoice?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/convert-to-invoice`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Converted to Invoice ${data.invoice_number}`);
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to convert");
      }
    } catch (e) { toast.error("Error converting estimate"); }
  };

  const handleConvertToSO = async (estimateId) => {
    if (!confirm("Convert this estimate to a sales order?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/convert-to-sales-order`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Converted to Sales Order ${data.salesorder_number}`);
        setShowDetailDialog(false);
        fetchData();
      } else {
        toast.error(data.detail || "Failed to convert");
      }
    } catch (e) { toast.error("Error converting estimate"); }
  };

  const handleClone = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/clone`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Cloned as ${data.estimate_number}`);
        fetchData();
      }
    } catch (e) { toast.error("Error cloning estimate"); }
  };

  // Line items
  const addLineItem = () => {
    if (!newLineItem.name) return toast.error("Item name is required");
    
    const qty = newLineItem.quantity || 1;
    const rate = newLineItem.rate || 0;
    const grossAmount = qty * rate;
    
    // Calculate discount based on type
    let discountAmount = 0;
    if (newLineItem.discount_type === 'amount') {
      discountAmount = newLineItem.discount_value || 0;
    } else {
      discountAmount = (grossAmount * (newLineItem.discount_percent || 0)) / 100;
    }
    
    const taxableAmount = grossAmount - discountAmount;
    const taxAmount = taxableAmount * ((newLineItem.tax_percentage || 0) / 100);
    const total = taxableAmount + taxAmount;
    
    const item = {
      ...newLineItem,
      quantity: qty,
      rate: rate,
      gross_amount: grossAmount,
      discount: discountAmount,
      discount_type: newLineItem.discount_type || 'percent',
      discount_percent: newLineItem.discount_percent || 0,
      discount_value: newLineItem.discount_value || 0,
      taxable_amount: taxableAmount,
      tax_amount: taxAmount,
      total: total
    };
    
    setNewEstimate(prev => ({ ...prev, line_items: [...prev.line_items, item] }));
    setNewLineItem({ 
      item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0, 
      discount_type: "percent", discount_percent: 0, discount_value: 0, 
      tax_percentage: 18, hsn_code: "" 
    });
  };

  const removeLineItem = (index) => {
    setNewEstimate(prev => ({ ...prev, line_items: prev.line_items.filter((_, i) => i !== index) }));
  };

  const selectItem = async (item) => {
    // If a customer is selected, fetch the price with price list applied
    if (newEstimate.customer_id) {
      const pricedItem = await fetchItemPricing(item.item_id, newEstimate.customer_id);
      if (pricedItem) {
        setNewLineItem({
          item_id: pricedItem.item_id,
          name: pricedItem.name,
          description: pricedItem.description || "",
          quantity: 1,
          unit: pricedItem.unit || "pcs",
          rate: pricedItem.rate,  // Price list adjusted rate
          base_rate: pricedItem.base_rate,
          discount_percent: 0,
          tax_percentage: pricedItem.tax_percentage || 18,
          hsn_code: pricedItem.hsn_code || "",
          price_list_applied: pricedItem.price_list_name,
          discount_from_pricelist: pricedItem.discount_applied || 0,
          markup_from_pricelist: pricedItem.markup_applied || 0
        });
        
        // Show toast if price list was applied
        if (pricedItem.price_list_name) {
          if (pricedItem.discount_applied > 0) {
            toast.success(`Price adjusted: -₹${pricedItem.discount_applied} (${pricedItem.price_list_name})`, { duration: 2000 });
          } else if (pricedItem.markup_applied > 0) {
            toast.info(`Price adjusted: +₹${pricedItem.markup_applied} (${pricedItem.price_list_name})`, { duration: 2000 });
          }
        }
        return;
      }
    }
    
    // Fallback: use item's default price
    setNewLineItem({
      item_id: item.item_id,
      name: item.name,
      description: item.description || "",
      quantity: 1,
      unit: item.unit || "pcs",
      rate: item.rate || item.sales_rate || 0,
      discount_percent: 0,
      tax_percentage: item.tax_percentage || 18,
      hsn_code: item.hsn_code || ""
    });
  };

  const calculateTotals = () => {
    const subtotal = newEstimate.line_items.reduce((sum, item) => sum + (item.taxable_amount || 0), 0);
    const totalTax = newEstimate.line_items.reduce((sum, item) => sum + (item.tax_amount || 0), 0);
    let discount = 0;
    if (newEstimate.discount_type === "percent") discount = subtotal * (newEstimate.discount_value / 100);
    else if (newEstimate.discount_type === "amount") discount = newEstimate.discount_value;
    const grandTotal = subtotal - discount + totalTax + (newEstimate.shipping_charge || 0) + (newEstimate.adjustment || 0);
    return { subtotal, totalTax, discount, grandTotal };
  };

  const resetForm = () => {
    setNewEstimate({
      customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
      expiry_date: "", subject: "", salesperson_name: "", terms_and_conditions: "", notes: "",
      discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
      adjustment_description: "", line_items: []
    });
    setSelectedContact(null);
    setContactSearch("");
    setCustomerPricing(null);
  };

  const totals = calculateTotals();

  return (
    <div className="space-y-6" data-testid="estimates-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Estimates & Quotes"
        description="Create, send, and convert estimates to invoices"
        icon={FileText}
        actions={
          <Button onClick={fetchData} variant="outline" className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      {loading ? (
        <StatCardGrid columns={8}>
          {[...Array(8)].map((_, i) => (
            <StatCard key={i} loading title="" value="" />
          ))}
        </StatCardGrid>
      ) : summary && (
        <StatCardGrid columns={8}>
          <StatCard
            title="Total Estimates"
            value={summary.total}
            icon={FileText}
            variant="info"
          />
          <StatCard
            title="Draft"
            value={summary.by_status?.draft || 0}
            icon={Edit}
            variant="default"
          />
          <StatCard
            title="Sent"
            value={summary.by_status?.sent || 0}
            icon={Send}
            variant="info"
          />
          <StatCard
            title="Viewed"
            value={summary.by_status?.customer_viewed || 0}
            icon={Eye}
            variant="info"
            onClick={() => { setStatusFilter('customer_viewed'); fetchEstimates(); }}
            className="cursor-pointer hover:ring-2 hover:ring-cyan-300"
          />
          <StatCard
            title="Accepted"
            value={summary.by_status?.accepted || 0}
            icon={CheckCircle}
            variant="success"
          />
          <StatCard
            title="Expired"
            value={summary.by_status?.expired || 0}
            icon={Clock}
            variant="warning"
          />
          <StatCard
            title="Converted"
            value={summary.by_status?.converted || 0}
            icon={ArrowRightLeft}
            variant="purple"
          />
          <StatCard
            title="Total Value"
            value={formatCurrencyCompact(summary.total_value || 0)}
            icon={IndianRupee}
            variant="success"
          />
        </StatCardGrid>
      )}

      {/* Quick Actions Row */}
      <div className="flex flex-wrap justify-between items-center gap-2">
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handleExport("csv")}
            className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"
            data-testid="export-csv-btn"
          >
            <FileDown className="h-4 w-4" /> Export CSV
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowImportDialog(true)}
            className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"
            data-testid="import-btn"
          >
            <FileUp className="h-4 w-4" /> Import
          </Button>
          {selectedIds.length > 0 && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowBulkActionDialog(true)}
              className="gap-2 bg-[rgba(59,158,255,0.08)] border-[rgba(59,158,255,0.25)] text-[#3B9EFF] hover:bg-[rgba(59,158,255,0.15)]"
              data-testid="bulk-action-btn"
            >
              <ListChecks className="h-4 w-4" /> Bulk Actions ({selectedIds.length})
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => { fetchCustomFields(); setShowCustomFieldsDialog(true); }}
            className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"
            data-testid="custom-fields-btn"
          >
            <Edit className="h-4 w-4" /> Custom Fields
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => { fetchPdfTemplates(); setShowTemplateDialog(true); }}
            className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"
            data-testid="templates-btn"
          >
            <LayoutTemplate className="h-4 w-4" /> Templates
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => { fetchPreferences(); setShowPreferencesDialog(true); }}
            className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"
            data-testid="preferences-btn"
          >
            <Settings className="h-4 w-4" /> Preferences
          </Button>
        </div>
      </div>

      {/* Conversion Funnel */}
      {funnel && (
        <Card className="bg-[#111820] border border-[rgba(255,255,255,0.07)]">
          <CardHeader className="pb-2 border-b border-[rgba(255,255,255,0.07)]">
            <CardTitle className="text-sm flex items-center gap-2 text-[#F4F6F0]"><TrendingUp className="h-4 w-4 text-[#C8FF00]" /> Conversion Funnel</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between text-xs">
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Created</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.total_created}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-[rgba(255,255,255,0.15)]" />
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Sent</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.sent_to_customer}</p>
                <p className="text-[#3B9EFF] text-xs">{funnel.send_rate}%</p>
              </div>
              <ChevronRight className="h-4 w-4 text-[rgba(255,255,255,0.15)]" />
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Accepted</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.accepted}</p>
                <p className="text-[#C8FF00] text-xs">{funnel.acceptance_rate}%</p>
              </div>
              <ChevronRight className="h-4 w-4 text-[rgba(255,255,255,0.15)]" />
              <div className="text-center">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.45)]">Converted</p>
                <p className="text-xl font-bold text-[#F4F6F0]">{funnel.converted}</p>
                <p className="text-[#8B5CF6] text-xs">{funnel.conversion_rate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-[#111820] border border-[rgba(255,255,255,0.07)] p-1">
          <TabsTrigger value="estimates" className="data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">Estimates</TabsTrigger>
          <TabsTrigger value="ticket-estimates" className="flex items-center gap-1 data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">
            <Ticket className="h-4 w-4" />
            Ticket Estimates ({ticketEstimates.length})
          </TabsTrigger>
          <TabsTrigger value="create" className="data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">Create New</TabsTrigger>
        </TabsList>

        {/* Estimates Tab */}
        <TabsContent value="estimates" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.25)]" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchEstimates()} placeholder="Search estimates..." className="pl-10 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.25)] focus:border-[#C8FF00]" data-testid="search-estimates" />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setTimeout(fetchEstimates, 100); }}>
                <SelectTrigger className="w-36 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0]"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#111820] border-[rgba(255,255,255,0.1)]">
                  <SelectItem value="all" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">All Status</SelectItem>
                  <SelectItem value="draft" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Draft</SelectItem>
                  <SelectItem value="sent" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Sent</SelectItem>
                  <SelectItem value="customer_viewed" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Viewed</SelectItem>
                  <SelectItem value="accepted" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Accepted</SelectItem>
                  <SelectItem value="declined" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Declined</SelectItem>
                  <SelectItem value="expired" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Expired</SelectItem>
                  <SelectItem value="converted" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Converted</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setActiveTab("create")} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold gap-2 rounded-[3px] hover:shadow-[0_0_20px_rgba(200,255,0,0.3)]" data-testid="new-estimate-btn">
              <Plus className="h-4 w-4" /> New Estimate
            </Button>
          </div>

          {loading ? (
            <TableSkeleton columns={8} rows={5} />
          ) : estimates.length === 0 ? (
            <Card className="bg-[#111820] border-[rgba(255,255,255,0.07)]">
              <EmptyState
                icon={FileText}
                title="No estimates found"
                description="Create your first estimate to start quoting customers."
                actionLabel="New Estimate"
                onAction={() => setActiveTab("create")}
                actionIcon={Plus}
              />
            </Card>
          ) : (
            <div className="bg-[#0D1317] border border-[rgba(255,255,255,0.07)] rounded">
              <ResponsiveTable>
                <thead className="bg-[#111820] border-b border-[rgba(255,255,255,0.07)]">
                  <tr>
                    <th className="px-2 py-3 text-center w-10">
                      <input 
                        type="checkbox" 
                        checked={selectedIds.length === estimates.length && estimates.length > 0}
                        onChange={toggleSelectAll}
                        className="h-4 w-4 rounded border-[rgba(255,255,255,0.2)] bg-transparent"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Estimate #</th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Customer</th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Date</th>
                    <th className="px-4 py-3 text-left font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Expiry</th>
                    <th className="px-4 py-3 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Amount</th>
                    <th className="px-4 py-3 text-center font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Status</th>
                    <th className="px-4 py-3 text-right font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {estimates.map(est => (
                    <tr key={est.estimate_id} className={`border-b border-[rgba(255,255,255,0.04)] hover:bg-[rgba(200,255,0,0.03)] cursor-pointer transition-colors ${selectedIds.includes(est.estimate_id) ? 'bg-[rgba(59,158,255,0.08)]' : ''}`} onClick={() => fetchEstimateDetail(est.estimate_id)} data-testid={`estimate-row-${est.estimate_id}`}>
                      <td className="px-2 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                        <input 
                          type="checkbox" 
                          checked={selectedIds.includes(est.estimate_id)}
                          onChange={() => toggleSelect(est.estimate_id)}
                          className="h-4 w-4 rounded border-[rgba(255,255,255,0.2)] bg-transparent"
                        />
                      </td>
                      <td className="px-4 py-3 font-mono font-medium text-sm text-[#C8FF00] tracking-[0.06em]">{est.estimate_number}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-[#F4F6F0]">{est.customer_name}</td>
                      <td className="px-4 py-3 text-[rgba(244,246,240,0.45)] text-sm">{est.date}</td>
                      <td className="px-4 py-3 text-[rgba(244,246,240,0.45)] text-sm">{est.expiry_date}</td>
                      <td className="px-4 py-3 text-right font-bold text-sm text-[#C8FF00]">₹{(est.grand_total || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-center">
                        <EstimateStatusBadge status={est.status} />
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchEstimateDetail(est.estimate_id)} className="text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"><Eye className="h-4 w-4" /></Button>
                        <Button size="icon" variant="ghost" onClick={() => handleClone(est.estimate_id)} className="text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"><Copy className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </ResponsiveTable>
            </div>
          )}
        </TabsContent>

        {/* Ticket Estimates Tab */}
        <TabsContent value="ticket-estimates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ticket className="h-5 w-5" />
                Ticket-Linked Estimates
              </CardTitle>
              <CardDescription>
                Estimates created from service tickets. These are managed through the Job Card interface.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {ticketEstimates.length === 0 ? (
                <EmptyState 
                  icon={Ticket}
                  title="No Ticket Estimates"
                  description="Estimates will appear here when technicians are assigned to service tickets."
                />
              ) : (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820]">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium">Estimate #</th>
                        <th className="px-4 py-3 text-left font-medium">Linked Ticket</th>
                        <th className="px-4 py-3 text-left font-medium">Customer</th>
                        <th className="px-4 py-3 text-left font-medium">Vehicle</th>
                        <th className="px-4 py-3 text-left font-medium">Status</th>
                        <th className="px-4 py-3 text-right font-medium">Amount</th>
                        <th className="px-4 py-3 text-left font-medium">Created</th>
                        <th className="px-4 py-3 text-center font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ticketEstimates.map((est) => (
                        <tr key={est.estimate_id} className="border-b border-[rgba(255,255,255,0.04)] hover:bg-[#111820]">
                          <td className="px-4 py-3 font-mono text-sm">{est.estimate_number}</td>
                          <td className="px-4 py-3">
                            <a 
                              href={`/tickets?id=${est.ticket_id}`}
                              className="flex items-center gap-1 text-primary hover:underline"
                            >
                              <Ticket className="h-4 w-4" />
                              {est.ticket_id?.slice(0, 12)}...
                            </a>
                          </td>
                          <td className="px-4 py-3">{est.customer_name || '-'}</td>
                          <td className="px-4 py-3">
                            {est.vehicle_number ? (
                              <span>{est.vehicle_number} <span className="text-xs text-[rgba(244,246,240,0.45)]">{est.vehicle_model}</span></span>
                            ) : '-'}
                          </td>
                          <td className="px-4 py-3">
                            <Badge 
                              variant="outline" 
                              className={
                                est.status === 'approved' ? 'bg-[rgba(34,197,94,0.12)] text-[#22C55E] border-[rgba(34,197,94,0.25)]' :
                                est.status === 'sent' ? 'bg-[rgba(59,158,255,0.12)] text-[#3B9EFF] border-[rgba(59,158,255,0.25)]' :
                                est.locked_at ? 'bg-[rgba(255,140,0,0.12)] text-[#FF8C00] border-[rgba(255,140,0,0.25)]' :
                                'bg-[rgba(255,255,255,0.05)] text-[#F4F6F0]'
                              }
                            >
                              {est.locked_at ? 'Locked' : est.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-right font-mono font-semibold">
                            ₹{(est.grand_total || 0).toLocaleString('en-IN')}
                          </td>
                          <td className="px-4 py-3 text-xs text-[rgba(244,246,240,0.45)]">
                            {new Date(est.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex justify-center gap-1">
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => window.open(`/tickets?id=${est.ticket_id}`, '_blank')}
                                title="View Job Card"
                              >
                                <Wrench className="h-4 w-4" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => {
                                  setSelectedEstimate({
                                    ...est,
                                    is_ticket_estimate: true,
                                    estimate_number: est.estimate_number,
                                    status: est.status,
                                    customer_name: est.customer_name,
                                    line_items: est.line_items || [],
                                    date: est.created_at?.split('T')[0],
                                  });
                                  setShowDetailDialog(true);
                                }}
                                title="View Details"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Create Tab */}
        <TabsContent value="create" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Create New Estimate</CardTitle>
                  <CardDescription>Fill in the details and add line items</CardDescription>
                </div>
                <AutoSaveIndicator 
                  lastSaved={newEstimatePersistence.lastSaved} 
                  isSaving={newEstimatePersistence.isSaving} 
                  isDirty={newEstimatePersistence.isDirty} 
                />
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Draft Recovery Banner */}
              <DraftRecoveryBanner
                show={newEstimatePersistence.showRecoveryBanner}
                savedAt={newEstimatePersistence.savedDraftInfo?.timestamp}
                onRestore={newEstimatePersistence.handleRestoreDraft}
                onDiscard={newEstimatePersistence.handleDiscardDraft}
              />
              
              {/* Customer Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Customer *</Label>
                  <div className="relative">
                    <Input 
                      value={contactSearch} 
                      onChange={(e) => { setContactSearch(e.target.value); searchContacts(e.target.value); }}
                      placeholder="Search customer..."
                      data-testid="customer-search"
                    />
                    {contacts.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-[#111820] border border-[rgba(255,255,255,0.13)] rounded max-h-48 overflow-y-auto">
                        {contacts.map(c => (
                          <div 
                            key={c.contact_id} 
                            className="px-3 py-2 hover:bg-[rgba(255,255,255,0.05)] cursor-pointer"
                            onClick={() => {
                              setSelectedContact(c);
                              setNewEstimate(prev => ({ ...prev, customer_id: c.contact_id }));
                              setContactSearch(c.name);
                              setContacts([]);
                              // Fetch customer's price list info
                              fetchCustomerPricing(c.contact_id);
                            }}
                          >
                            <p className="font-medium">{c.name}</p>
                            <p className="text-xs text-[rgba(244,246,240,0.45)]">{c.company_name} {c.gstin && `• ${c.gstin}`}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedContact && (
                    <div className="mt-2 p-2 bg-[#111820] rounded text-xs">
                      <p><strong>{selectedContact.name}</strong></p>
                      {selectedContact.email && <p>{selectedContact.email}</p>}
                      {selectedContact.gstin && <p>GSTIN: {selectedContact.gstin}</p>}
                      {customerPricing?.sales_price_list && (
                        <div className="mt-1 flex items-center gap-1">
                          <Badge variant="outline" className="text-xs bg-[rgba(34,197,94,0.08)] text-[#22C55E] border-[rgba(34,197,94,0.25)]">
                            <IndianRupee className="h-3 w-3 mr-1" />
                            {customerPricing.sales_price_list.name}
                            {customerPricing.sales_price_list.discount_percentage > 0 && ` (-${customerPricing.sales_price_list.discount_percentage}%)`}
                            {customerPricing.sales_price_list.markup_percentage > 0 && ` (+${customerPricing.sales_price_list.markup_percentage}%)`}
                          </Badge>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Date</Label>
                    <Input type="date" value={newEstimate.date} onChange={(e) => setNewEstimate({...newEstimate, date: e.target.value})} />
                  </div>
                  <div>
                    <Label>Expiry Date</Label>
                    <Input type="date" value={newEstimate.expiry_date} onChange={(e) => setNewEstimate({...newEstimate, expiry_date: e.target.value})} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div><Label>Reference #</Label><Input value={newEstimate.reference_number} onChange={(e) => setNewEstimate({...newEstimate, reference_number: e.target.value})} placeholder="PO-123" /></div>
                <div><Label>Subject</Label><Input value={newEstimate.subject} onChange={(e) => setNewEstimate({...newEstimate, subject: e.target.value})} placeholder="Quote for..." /></div>
                <div><Label>Salesperson</Label><Input value={newEstimate.salesperson_name} onChange={(e) => setNewEstimate({...newEstimate, salesperson_name: e.target.value})} /></div>
              </div>

              <Separator />

              {/* Line Items - Enhanced Zoho-like Table */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium">Item Table</h4>
                  <Button variant="outline" size="sm" className="text-[#3B9EFF]" onClick={() => setShowBulkActionDialog(true)}>
                    <Settings className="h-4 w-4 mr-1" /> Bulk Actions
                  </Button>
                </div>
                
                {/* Enhanced Line Items Table */}
                <div className="border rounded-lg overflow-visible">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820] border-b">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium w-[280px]">ITEM DETAILS</th>
                        <th className="px-3 py-2 text-center font-medium w-20">QUANTITY</th>
                        <th className="px-3 py-2 text-center font-medium w-24">
                          <div className="flex items-center justify-center gap-1">
                            RATE <IndianRupee className="h-3 w-3" />
                          </div>
                        </th>
                        <th className="px-3 py-2 text-center font-medium w-28">DISCOUNT</th>
                        <th className="px-3 py-2 text-center font-medium w-32">TAX</th>
                        <th className="px-3 py-2 text-right font-medium w-24">AMOUNT</th>
                        <th className="px-3 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* Existing Line Items */}
                      {newEstimate.line_items.map((item, idx) => (
                        <EstimateLineItemRow 
                          key={idx}
                          item={item}
                          index={idx}
                          onRemove={removeLineItem}
                          readOnly={false}
                        />
                      ))}
                      
                      {/* New Item Row - Searchable */}
                      <tr className="border-t bg-[rgba(59,158,255,0.08)]/30">
                        <td className="px-3 py-2">
                          <div className="relative">
                            <div className="flex items-center gap-1">
                              <Package className="h-4 w-4 text-[rgba(244,246,240,0.25)]" />
                              <Input 
                                value={newLineItem.name}
                                onChange={(e) => {
                                  setNewLineItem({...newLineItem, name: e.target.value, item_id: ""});
                                  // Filter items based on search
                                }}
                                placeholder="Type or click to select an item..."
                                className="border-0 bg-transparent focus:ring-0 h-8"
                                data-testid="item-search-input"
                              />
                            </div>
                            {/* Item Search Dropdown */}
                            {newLineItem.name && newLineItem.name.length >= 1 && !newLineItem.item_id && (
                              <div className="absolute z-50 left-0 right-0 mt-1 bg-[#111820] border border-[rgba(255,255,255,0.13)] rounded max-h-64 overflow-y-auto">
                                {items
                                  .filter(item => item.name?.toLowerCase().includes(newLineItem.name.toLowerCase()) || item.sku?.toLowerCase().includes(newLineItem.name.toLowerCase()))
                                  .slice(0, 10)
                                  .map(item => (
                                    <div 
                                      key={item.item_id}
                                      className="px-3 py-2 hover:bg-[rgba(200,255,0,0.08)] cursor-pointer border-b last:border-0"
                                      onClick={() => selectItem(item)}
                                    >
                                      <div className="flex justify-between">
                                        <div>
                                          <div className="font-medium text-[#F4F6F0]">{item.name}</div>
                                          <div className="text-xs text-[rgba(244,246,240,0.45)]">
                                            {item.sku && <span>SKU: {item.sku}</span>}
                                            {item.rate && <span className="ml-2">Rate: ₹{item.rate?.toLocaleString('en-IN')}</span>}
                                          </div>
                                        </div>
                                        <div className="text-right">
                                          <div className={`text-sm font-medium ${(item.stock_on_hand || 0) < 0 ? 'text-red-500' : 'text-[rgba(244,246,240,0.45)]'}`}>
                                            {item.stock_on_hand !== undefined && (
                                              <>Stock on Hand<br/><span className={`font-bold ${(item.stock_on_hand || 0) < 0 ? 'text-red-500' : 'text-[#22C55E]'}`}>{item.stock_on_hand} {item.unit || 'pcs'}</span></>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                {/* Add New Item Option */}
                                <div 
                                  className="px-3 py-2 hover:bg-[rgba(59,158,255,0.08)] cursor-pointer border-t flex items-center gap-2 text-[#3B9EFF]"
                                  onClick={() => {
                                    setQuickAddItem({...quickAddItem, name: newLineItem.name});
                                    setShowAddItemDialog(true);
                                  }}
                                >
                                  <Plus className="h-4 w-4" />
                                  <span>Add New Item "{newLineItem.name}"</span>
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <Input 
                            type="number" 
                            value={newLineItem.quantity} 
                            onChange={(e) => setNewLineItem({...newLineItem, quantity: parseFloat(e.target.value) || 1})} 
                            min="1"
                            className="w-16 h-8 text-center mx-auto"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Input 
                            type="number" 
                            value={newLineItem.rate} 
                            onChange={(e) => setNewLineItem({...newLineItem, rate: parseFloat(e.target.value) || 0})} 
                            min="0"
                            className="w-20 h-8 text-center mx-auto"
                            placeholder="0.00"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1 justify-center">
                            <Input 
                              type="number" 
                              value={newLineItem.discount_type === 'amount' ? newLineItem.discount_value : newLineItem.discount_percent} 
                              onChange={(e) => {
                                const val = parseFloat(e.target.value) || 0;
                                if (newLineItem.discount_type === 'amount') {
                                  setNewLineItem({...newLineItem, discount_value: val, discount_percent: 0});
                                } else {
                                  setNewLineItem({...newLineItem, discount_percent: val, discount_value: 0});
                                }
                              }}
                              min="0"
                              className="w-14 h-8 text-center"
                            />
                            <Select 
                              value={newLineItem.discount_type || "percent"} 
                              onValueChange={(v) => setNewLineItem({...newLineItem, discount_type: v, discount_percent: 0, discount_value: 0})}
                            >
                              <SelectTrigger className="w-12 h-8 px-1">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="percent">%</SelectItem>
                                <SelectItem value="amount">₹</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <Select 
                            value={String(newLineItem.tax_percentage || 18)} 
                            onValueChange={(v) => setNewLineItem({...newLineItem, tax_percentage: parseFloat(v)})}
                          >
                            <SelectTrigger className="w-28 h-8 mx-auto">
                              <SelectValue placeholder="Select Tax" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">GST 0%</SelectItem>
                              <SelectItem value="5">GST 5%</SelectItem>
                              <SelectItem value="12">GST 12%</SelectItem>
                              <SelectItem value="18">GST 18%</SelectItem>
                              <SelectItem value="28">GST 28%</SelectItem>
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="px-3 py-2 text-right font-medium text-[rgba(244,246,240,0.25)]">
                          ₹{((newLineItem.quantity || 0) * (newLineItem.rate || 0)).toLocaleString('en-IN', {minimumFractionDigits: 2})}
                        </td>
                        <td className="px-3 py-2">
                          <Button size="sm" onClick={addLineItem} className="h-7 bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" disabled={!newLineItem.name}>
                            <Plus className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Totals */}
                <div className="flex justify-end mt-4">
                  <div className="w-64 space-y-2 text-sm">
                    <div className="flex justify-between"><span>Subtotal:</span><span>₹{totals.subtotal.toFixed(2)}</span></div>
                    <div className="flex justify-between items-center gap-2">
                      <span>Discount:</span>
                      <div className="flex gap-1">
                        <Select value={newEstimate.discount_type} onValueChange={(v) => setNewEstimate({...newEstimate, discount_type: v})}>
                          <SelectTrigger className="w-20 h-7"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="percent">%</SelectItem>
                            <SelectItem value="amount">₹</SelectItem>
                          </SelectContent>
                        </Select>
                        {newEstimate.discount_type !== "none" && (
                          <Input type="number" className="w-16 h-7" value={newEstimate.discount_value} onChange={(e) => setNewEstimate({...newEstimate, discount_value: parseFloat(e.target.value) || 0})} />
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between"><span>Tax:</span><span>₹{totals.totalTax.toFixed(2)}</span></div>
                    <div className="flex justify-between items-center">
                      <span>Shipping:</span>
                      <Input type="number" className="w-24 h-7" value={newEstimate.shipping_charge} onChange={(e) => setNewEstimate({...newEstimate, shipping_charge: parseFloat(e.target.value) || 0})} />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Adjustment:</span>
                      <Input type="number" className="w-24 h-7" value={newEstimate.adjustment} onChange={(e) => setNewEstimate({...newEstimate, adjustment: parseFloat(e.target.value) || 0})} />
                    </div>
                    <Separator />
                    <div className="flex justify-between font-bold text-lg"><span>Grand Total:</span><span>₹{totals.grandTotal.toFixed(2)}</span></div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Notes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><Label>Terms & Conditions</Label><Textarea value={newEstimate.terms_and_conditions} onChange={(e) => setNewEstimate({...newEstimate, terms_and_conditions: e.target.value})} rows={3} /></div>
                <div><Label>Notes</Label><Textarea value={newEstimate.notes} onChange={(e) => setNewEstimate({...newEstimate, notes: e.target.value})} rows={3} /></div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={resetForm}>Reset</Button>
                <Button onClick={handleCreateEstimate} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="create-estimate-submit">Create Estimate</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
          {selectedEstimate && (
            <>
              <DialogHeader className="flex-shrink-0">
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedEstimate.estimate_number}
                      <EstimateStatusBadge status={selectedEstimate.status} />
                      {selectedEstimate.is_expired && <Badge variant="destructive">Expired</Badge>}
                    </DialogTitle>
                    <DialogDescription>{selectedEstimate.customer_name}</DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4 flex-1 overflow-y-auto min-h-0">
                {/* Linked Ticket Banner - For ticket estimates */}
                {selectedEstimate.is_ticket_estimate && selectedEstimate.ticket_id && (
                  <div className="bg-[rgba(59,158,255,0.08)] border border-[rgba(59,158,255,0.25)] rounded-lg px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Ticket className="h-5 w-5 text-[#3B9EFF]" />
                      <div>
                        <p className="text-sm font-medium text-[#3B9EFF]">Linked Service Ticket</p>
                        <p className="text-xs text-[#3B9EFF]">{selectedEstimate.ticket_id}</p>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open(`/tickets?id=${selectedEstimate.ticket_id}`, '_blank')}
                      className="text-[#3B9EFF] border-[rgba(59,158,255,0.35)] hover:bg-[rgba(59,158,255,0.08)]"
                    >
                      <Wrench className="h-4 w-4 mr-1" />
                      Open Job Card
                    </Button>
                  </div>
                )}

                {/* Lock Banner */}
                {selectedEstimate.locked_at && (
                  <div className="bg-[rgba(255,140,0,0.08)] border border-[rgba(255,140,0,0.25)] rounded-lg px-4 py-3 flex items-center gap-2 text-[#FF8C00]">
                    <AlertTriangle className="h-5 w-5" />
                    <div>
                      <p className="font-medium">Estimate Locked</p>
                      <p className="text-xs">{selectedEstimate.lock_reason || 'Locked for editing'} - {selectedEstimate.locked_by_name}</p>
                    </div>
                  </div>
                )}

                {/* Info Grid */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div><p className="text-[rgba(244,246,240,0.45)]">Date</p><p className="font-medium">{selectedEstimate.date}</p></div>
                  <div><p className="text-[rgba(244,246,240,0.45)]">Expiry</p><p className="font-medium">{selectedEstimate.expiry_date || '-'}</p></div>
                  <div><p className="text-[rgba(244,246,240,0.45)]">Reference</p><p className="font-medium">{selectedEstimate.reference_number || '-'}</p></div>
                  <div><p className="text-[rgba(244,246,240,0.45)]">GSTIN</p><p className="font-medium font-mono text-xs">{selectedEstimate.customer_gstin || '-'}</p></div>
                </div>

                {/* Vehicle Info for Ticket Estimates */}
                {selectedEstimate.is_ticket_estimate && selectedEstimate.vehicle_number && (
                  <div className="grid grid-cols-3 gap-4 text-sm bg-[#111820] p-3 rounded-lg">
                    <div><p className="text-[rgba(244,246,240,0.45)]">Vehicle</p><p className="font-medium">{selectedEstimate.vehicle_number}</p></div>
                    <div><p className="text-[rgba(244,246,240,0.45)]">Model</p><p className="font-medium">{selectedEstimate.vehicle_model || '-'}</p></div>
                    <div><p className="text-[rgba(244,246,240,0.45)]">Technician</p><p className="font-medium">{selectedEstimate.assigned_technician_name || '-'}</p></div>
                  </div>
                )}

                {/* Price List Info */}
                {selectedEstimate.price_list_name && (
                  <div className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.25)] rounded-lg px-3 py-2 text-sm flex items-center gap-2">
                    <IndianRupee className="h-4 w-4 text-[#22C55E]" />
                    <span className="text-[#22C55E]">
                      Price List Applied: <strong>{selectedEstimate.price_list_name}</strong>
                    </span>
                  </div>
                )}

                <Separator />

                {/* Line Items */}
                <div>
                  <h4 className="font-medium mb-2">Line Items ({selectedEstimate.line_items?.length || 0})</h4>
                  <EstimateLineItemsTable 
                    lineItems={selectedEstimate.line_items} 
                    estimate={selectedEstimate} 
                    readOnly={true} 
                  />
                </div>

                {/* Totals */}
                <div className="flex justify-end">
                  <EstimateTotalsBlock
                    subtotal={selectedEstimate.subtotal}
                    discount={selectedEstimate.total_discount}
                    taxAmount={selectedEstimate.total_tax}
                    total={selectedEstimate.grand_total}
                    shippingCharge={selectedEstimate.shipping_charge}
                    adjustment={selectedEstimate.adjustment}
                    gstType={selectedEstimate.gst_type}
                  />
                </div>

                <Separator />

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {/* Edit - Available for all statuses except converted and void */}
                  {selectedEstimate.status !== "converted" && selectedEstimate.status !== "void" && (
                    <Button 
                      variant="outline" 
                      onClick={() => handleOpenEdit(selectedEstimate)}
                      data-testid="edit-estimate-btn"
                    >
                      <Edit className="h-4 w-4 mr-1" /> Edit
                    </Button>
                  )}
                  
                  {/* Primary Status Actions */}
                  {selectedEstimate.status === "draft" && (
                    <>
                      <Button variant="outline" onClick={() => { setSendEmail(selectedEstimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Send</Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteEstimate(selectedEstimate.estimate_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                    </>
                  )}
                  {(selectedEstimate.status === "sent" || selectedEstimate.status === "customer_viewed") && (
                    <>
                      <Button variant="outline" onClick={() => { setSendEmail(selectedEstimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Resend</Button>
                      <Button onClick={() => handleMarkAccepted(selectedEstimate.estimate_id)} className="bg-[#22C55E] hover:bg-[rgba(34,197,94,0.85)] text-[#080C0F]"><CheckCircle className="h-4 w-4 mr-1" /> Mark Accepted</Button>
                      <Button variant="outline" onClick={() => handleMarkDeclined(selectedEstimate.estimate_id)}><XCircle className="h-4 w-4 mr-1" /> Mark Declined</Button>
                    </>
                  )}
                  {selectedEstimate.status === "accepted" && (
                    <>
                      <Button onClick={() => handleConvertToInvoice(selectedEstimate.estimate_id)} className="bg-[#8B5CF6] hover:bg-purple-600 text-white"><ArrowRightLeft className="h-4 w-4 mr-1" /> Convert to Invoice</Button>
                      <Button variant="outline" onClick={() => handleConvertToSO(selectedEstimate.estimate_id)}><ArrowRightLeft className="h-4 w-4 mr-1" /> Convert to Sales Order</Button>
                    </>
                  )}
                  {(selectedEstimate.status === "declined" || selectedEstimate.status === "expired") && (
                    <Button variant="outline" onClick={() => { setSendEmail(selectedEstimate.customer_email || ""); setShowSendDialog(true); }}><Send className="h-4 w-4 mr-1" /> Resend</Button>
                  )}
                  
                  {/* Common Actions */}
                  <Separator orientation="vertical" className="h-8" />
                  <Button variant="outline" onClick={() => { setShareLink(null); setShowShareDialog(true); }} data-testid="share-btn"><Share2 className="h-4 w-4 mr-1" /> Share</Button>
                  <Button variant="outline" onClick={() => { fetchAttachments(selectedEstimate.estimate_id); setShowAttachmentDialog(true); }} data-testid="attachments-btn"><Paperclip className="h-4 w-4 mr-1" /> Attachments</Button>
                  <Button variant="outline" onClick={() => handleDownloadPDF(selectedEstimate.estimate_id)} data-testid="download-pdf-btn"><Download className="h-4 w-4 mr-1" /> PDF</Button>
                  <Button variant="outline" onClick={() => handleClone(selectedEstimate.estimate_id)}><Copy className="h-4 w-4 mr-1" /> Clone</Button>
                </div>

                {/* Customer Viewed Info */}
                {selectedEstimate.status === "customer_viewed" && selectedEstimate.first_viewed_at && (
                  <div className="bg-[rgba(26,255,228,0.08)] border border-[rgba(26,255,228,0.20)] rounded-lg p-3">
                    <p className="text-sm text-[#1AFFE4] flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      <strong>Customer viewed on:</strong> {new Date(selectedEstimate.first_viewed_at).toLocaleString('en-IN')}
                    </p>
                  </div>
                )}

                {/* Converted To */}
                {selectedEstimate.converted_to && (
                  <div className="bg-[rgba(139,92,246,0.08)] rounded-lg p-3">
                    <p className="text-sm text-[#8B5CF6]">
                      <strong>Converted to:</strong> {selectedEstimate.converted_to}
                    </p>
                  </div>
                )}

                {/* History */}
                {selectedEstimate.history?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">History</h4>
                    <div className="space-y-2 text-sm">
                      {selectedEstimate.history.slice(0, 5).map((h, idx) => (
                        <div key={idx} className="flex justify-between text-[rgba(244,246,240,0.45)]">
                          <span>{h.action}: {h.details}</span>
                          <span className="text-xs">{new Date(h.timestamp).toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Send Dialog */}
      <Dialog open={showSendDialog} onOpenChange={setShowSendDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Estimate</DialogTitle>
            <DialogDescription>Email this estimate to the customer</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Email To</Label>
              <Input value={sendEmail} onChange={(e) => setSendEmail(e.target.value)} placeholder="customer@example.com" />
            </div>
            <div>
              <Label>Message (optional)</Label>
              <Textarea value={sendMessage} onChange={(e) => setSendMessage(e.target.value)} placeholder="Add a personal message..." rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendDialog(false)}>Cancel</Button>
            <Button onClick={handleSendEstimate} className="bg-[#C8FF00] text-[#080C0F] font-bold">Send Estimate</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Share Link Dialog */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Share2 className="h-5 w-5" /> Share Estimate</DialogTitle>
            <DialogDescription>Generate a public link for customers to view, accept, or decline this estimate.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {!shareLink ? (
              <>
                <div className="space-y-3">
                  <div>
                    <Label>Link Expires In (days)</Label>
                    <Input 
                      type="number" 
                      value={shareConfig.expiry_days} 
                      onChange={(e) => setShareConfig({...shareConfig, expiry_days: parseInt(e.target.value) || 30})}
                      min={1} 
                      max={365} 
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Allow Customer to Accept</Label>
                    <input 
                      type="checkbox" 
                      checked={shareConfig.allow_accept} 
                      onChange={(e) => setShareConfig({...shareConfig, allow_accept: e.target.checked})}
                      className="h-4 w-4"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Allow Customer to Decline</Label>
                    <input 
                      type="checkbox" 
                      checked={shareConfig.allow_decline} 
                      onChange={(e) => setShareConfig({...shareConfig, allow_decline: e.target.checked})}
                      className="h-4 w-4"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Password Protected</Label>
                    <input 
                      type="checkbox" 
                      checked={shareConfig.password_protected} 
                      onChange={(e) => setShareConfig({...shareConfig, password_protected: e.target.checked})}
                      className="h-4 w-4"
                    />
                  </div>
                  {shareConfig.password_protected && (
                    <div>
                      <Label>Password</Label>
                      <Input 
                        type="password" 
                        value={shareConfig.password} 
                        onChange={(e) => setShareConfig({...shareConfig, password: e.target.value})}
                        placeholder="Enter password"
                      />
                    </div>
                  )}
                </div>
                <Button 
                  onClick={handleCreateShareLink} 
                  disabled={shareLoading}
                  className="w-full bg-[#C8FF00] text-[#080C0F] font-bold"
                  data-testid="generate-share-link-btn"
                >
                  {shareLoading ? "Generating..." : "Generate Share Link"}
                </Button>
              </>
            ) : (
              <div className="space-y-4">
                <div className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.25)] rounded-lg p-4">
                  <p className="text-sm text-[#22C55E] font-medium mb-2">Share link created successfully!</p>
                  <div className="flex items-center gap-2">
                    <Input 
                      value={shareLink.full_url} 
                      readOnly 
                      className="text-xs font-mono"
                    />
                    <Button size="sm" variant="outline" onClick={copyShareLink}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="text-xs text-[rgba(244,246,240,0.45)] space-y-1">
                  <p><strong>Expires:</strong> {new Date(shareLink.expires_at).toLocaleDateString('en-IN')}</p>
                  <p><strong>Can Accept:</strong> {shareLink.allow_accept ? 'Yes' : 'No'}</p>
                  <p><strong>Can Decline:</strong> {shareLink.allow_decline ? 'Yes' : 'No'}</p>
                  <p><strong>Password Protected:</strong> {shareLink.password_protected ? 'Yes' : 'No'}</p>
                </div>
                <Button 
                  variant="outline" 
                  onClick={() => setShareLink(null)} 
                  className="w-full"
                >
                  Create Another Link
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Attachments Dialog */}
      <Dialog open={showAttachmentDialog} onOpenChange={setShowAttachmentDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Paperclip className="h-5 w-5" /> Attachments</DialogTitle>
            <DialogDescription>Upload files to attach to this estimate (max 3 files, 10MB each)</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Upload Area */}
            <div className="border-2 border-dashed border-[rgba(255,255,255,0.13)] rounded-lg p-4 text-center">
              <input 
                type="file" 
                id="attachment-upload" 
                className="hidden" 
                onChange={handleUploadAttachment}
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt,.csv"
              />
              <label htmlFor="attachment-upload" className="cursor-pointer">
                <Upload className="h-8 w-8 mx-auto text-[rgba(244,246,240,0.25)] mb-2" />
                <p className="text-sm text-[rgba(244,246,240,0.45)]">
                  {uploading ? "Uploading..." : "Click to upload a file"}
                </p>
                <p className="text-xs text-[rgba(244,246,240,0.25)] mt-1">PDF, Images, Word, Excel (max 10MB)</p>
              </label>
            </div>

            {/* Attachments List */}
            {attachments.length > 0 ? (
              <div className="space-y-2">
                <Label>Attached Files ({attachments.length}/3)</Label>
                {attachments.map((att) => (
                  <div key={att.attachment_id} className="flex items-center justify-between bg-[#111820] rounded-lg p-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <FileText className="h-4 w-4 text-[rgba(244,246,240,0.25)] flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{att.filename}</p>
                        <p className="text-xs text-[rgba(244,246,240,0.25)]">{(att.file_size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => downloadAttachment(att.attachment_id, att.filename)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="text-red-500 hover:text-[#FF3B2F]"
                        onClick={() => handleDeleteAttachment(att.attachment_id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[rgba(244,246,240,0.45)] text-center">No attachments yet</p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Preferences Dialog */}
      <Dialog open={showPreferencesDialog} onOpenChange={setShowPreferencesDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Settings className="h-5 w-5" /> Estimate Preferences</DialogTitle>
            <DialogDescription>Configure automation and workflow settings for estimates</DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* Auto-Conversion Settings */}
            <div className="space-y-4">
              <h4 className="font-medium text-sm">Automatic Conversion</h4>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-convert accepted estimates</Label>
                  <p className="text-xs text-[rgba(244,246,240,0.45)]">Automatically create invoices when estimates are accepted</p>
                </div>
                <input 
                  type="checkbox" 
                  checked={preferences.auto_convert_on_accept} 
                  onChange={(e) => setPreferences({...preferences, auto_convert_on_accept: e.target.checked})}
                  className="h-4 w-4"
                />
              </div>
              {preferences.auto_convert_on_accept && (
                <div>
                  <Label>Convert to</Label>
                  <Select 
                    value={preferences.auto_convert_to} 
                    onValueChange={(v) => setPreferences({...preferences, auto_convert_to: v})}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft_invoice">Draft Invoice</SelectItem>
                      <SelectItem value="open_invoice">Open Invoice (ready to send)</SelectItem>
                      <SelectItem value="sales_order">Sales Order</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <Separator />

            {/* Public Link Settings */}
            <div className="space-y-4">
              <h4 className="font-medium text-sm">Public Link Settings</h4>
              <div className="flex items-center justify-between">
                <Label>Allow customers to accept via link</Label>
                <input 
                  type="checkbox" 
                  checked={preferences.allow_public_accept} 
                  onChange={(e) => setPreferences({...preferences, allow_public_accept: e.target.checked})}
                  className="h-4 w-4"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Allow customers to decline via link</Label>
                <input 
                  type="checkbox" 
                  checked={preferences.allow_public_decline} 
                  onChange={(e) => setPreferences({...preferences, allow_public_decline: e.target.checked})}
                  className="h-4 w-4"
                />
              </div>
            </div>

            <Separator />

            {/* Notification Settings */}
            <div className="space-y-4">
              <h4 className="font-medium text-sm">Notifications</h4>
              <div className="flex items-center justify-between">
                <Label>Notify when customer views estimate</Label>
                <input 
                  type="checkbox" 
                  checked={preferences.notify_on_view} 
                  onChange={(e) => setPreferences({...preferences, notify_on_view: e.target.checked})}
                  className="h-4 w-4"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Notify when customer accepts</Label>
                <input 
                  type="checkbox" 
                  checked={preferences.notify_on_accept} 
                  onChange={(e) => setPreferences({...preferences, notify_on_accept: e.target.checked})}
                  className="h-4 w-4"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Notify when customer declines</Label>
                <input 
                  type="checkbox" 
                  checked={preferences.notify_on_decline} 
                  onChange={(e) => setPreferences({...preferences, notify_on_decline: e.target.checked})}
                  className="h-4 w-4"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreferencesDialog(false)}>Cancel</Button>
            <Button onClick={handleSavePreferences} className="bg-[#C8FF00] text-[#080C0F] font-bold">Save Preferences</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><FileUp className="h-5 w-5" /> Import Estimates</DialogTitle>
            <DialogDescription>Upload a CSV file to import estimates in bulk</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="border-2 border-dashed border-[rgba(255,255,255,0.13)] rounded-lg p-6 text-center">
              <input 
                type="file" 
                id="import-file" 
                className="hidden" 
                accept=".csv"
                onChange={(e) => setImportFile(e.target.files[0])}
              />
              <label htmlFor="import-file" className="cursor-pointer">
                <Upload className="h-10 w-10 mx-auto text-[rgba(244,246,240,0.25)] mb-2" />
                <p className="text-sm text-[rgba(244,246,240,0.45)]">
                  {importFile ? importFile.name : "Click to select CSV file"}
                </p>
              </label>
            </div>
            <Button variant="outline" onClick={downloadImportTemplate} className="w-full gap-2">
              <Download className="h-4 w-4" /> Download Template
            </Button>
            <p className="text-xs text-[rgba(244,246,240,0.45)]">
              Template includes: customer_name, date, item_name, quantity, rate, tax_percentage
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowImportDialog(false); setImportFile(null); }}>Cancel</Button>
            <Button onClick={handleImport} disabled={!importFile || importing} className="bg-[#C8FF00] text-[#080C0F] font-bold">
              {importing ? "Importing..." : "Import"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Action Dialog */}
      <Dialog open={showBulkActionDialog} onOpenChange={setShowBulkActionDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><ListChecks className="h-5 w-5" /> Bulk Actions</DialogTitle>
            <DialogDescription>Apply action to {selectedIds.length} selected estimates</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Action</Label>
              <Select value={bulkAction} onValueChange={setBulkAction}>
                <SelectTrigger><SelectValue placeholder="Select action..." /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="mark_sent">Mark as Sent</SelectItem>
                  <SelectItem value="mark_expired">Mark as Expired</SelectItem>
                  <SelectItem value="void">Void Estimates</SelectItem>
                  <SelectItem value="delete">Delete (Draft only)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {bulkAction === "void" && (
              <div className="bg-[rgba(255,140,0,0.08)] p-3 rounded-lg text-sm text-[#FF8C00]">
                <AlertTriangle className="h-4 w-4 inline mr-2" />
                Voiding estimates is irreversible. Converted estimates cannot be voided.
              </div>
            )}
            {bulkAction === "delete" && (
              <div className="bg-[rgba(255,59,47,0.08)] p-3 rounded-lg text-sm text-[#FF3B2F]">
                <AlertTriangle className="h-4 w-4 inline mr-2" />
                Only draft estimates will be deleted. This action is irreversible.
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowBulkActionDialog(false); setBulkAction(""); }}>Cancel</Button>
            <Button 
              onClick={handleBulkAction} 
              disabled={!bulkAction}
              className={bulkAction === "delete" || bulkAction === "void" ? "bg-[#FF3B2F] hover:bg-[rgba(255,59,47,0.85)]" : "bg-[#C8FF00] text-[#080C0F] font-bold"}
            >
              Apply to {selectedIds.length} Estimates
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom Fields Dialog */}
      <Dialog open={showCustomFieldsDialog} onOpenChange={setShowCustomFieldsDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Edit className="h-5 w-5" /> Custom Fields</DialogTitle>
            <DialogDescription>Manage custom fields for estimates</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
            {/* Existing Fields */}
            {customFields.length > 0 ? (
              <div className="space-y-2">
                <Label>Existing Fields</Label>
                {customFields.map((field, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-[#111820] rounded-lg p-3">
                    <div>
                      <p className="font-medium text-sm">{field.field_name}</p>
                      <p className="text-xs text-[rgba(244,246,240,0.45)]">
                        {field.field_type} {field.is_required && "• Required"} 
                        {field.show_in_pdf && " • PDF"} {field.show_in_portal && " • Portal"}
                      </p>
                    </div>
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      className="text-red-500 hover:text-[#FF3B2F]"
                      onClick={() => handleDeleteCustomField(field.field_name)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[rgba(244,246,240,0.45)] text-center py-4">No custom fields defined yet</p>
            )}
            
            <Separator />
            
            {/* Add New Field */}
            <div className="space-y-3">
              <Label>Add New Field</Label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs">Field Name</Label>
                  <Input 
                    value={newCustomField.field_name}
                    onChange={(e) => setNewCustomField({...newCustomField, field_name: e.target.value})}
                    placeholder="e.g., Project Code"
                  />
                </div>
                <div>
                  <Label className="text-xs">Type</Label>
                  <Select 
                    value={newCustomField.field_type}
                    onValueChange={(v) => setNewCustomField({...newCustomField, field_type: v})}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="number">Number</SelectItem>
                      <SelectItem value="date">Date</SelectItem>
                      <SelectItem value="checkbox">Checkbox</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input 
                    type="checkbox"
                    checked={newCustomField.is_required}
                    onChange={(e) => setNewCustomField({...newCustomField, is_required: e.target.checked})}
                    className="h-4 w-4"
                  />
                  Required
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input 
                    type="checkbox"
                    checked={newCustomField.show_in_pdf}
                    onChange={(e) => setNewCustomField({...newCustomField, show_in_pdf: e.target.checked})}
                    className="h-4 w-4"
                  />
                  Show in PDF
                </label>
              </div>
              <Button onClick={handleAddCustomField} className="w-full bg-[#C8FF00] text-[#080C0F] font-bold">
                <Plus className="h-4 w-4 mr-2" /> Add Field
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* PDF Templates Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><LayoutTemplate className="h-5 w-5" /> PDF Templates</DialogTitle>
            <DialogDescription>Choose a template style for PDF generation</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            {pdfTemplates.map((template) => (
              <div 
                key={template.id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedTemplate === template.id 
                    ? 'border-[#C8FF00] bg-[rgba(34,197,94,0.08)]' 
                    : 'border-[rgba(255,255,255,0.07)] hover:border-[rgba(255,255,255,0.13)]'
                }`}
                onClick={() => setSelectedTemplate(template.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{template.name}</p>
                    <p className="text-sm text-[rgba(244,246,240,0.45)]">{template.description}</p>
                  </div>
                  <div 
                    className="w-8 h-8 rounded-full"
                    style={{ backgroundColor: template.primary_color }}
                  />
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTemplateDialog(false)}>Close</Button>
            {selectedEstimate && (
              <Button 
                onClick={() => {
                  handleDownloadWithTemplate(selectedEstimate.estimate_id, selectedTemplate);
                  setShowTemplateDialog(false);
                }}
                className="bg-[#C8FF00] text-[#080C0F] font-bold"
              >
                <Download className="h-4 w-4 mr-2" /> Download with {selectedTemplate}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Estimate Dialog */}
      <Dialog open={showEditDialog} onOpenChange={(open) => {
        if (!open && editEstimatePersistence.isDirty) {
          editEstimatePersistence.setShowCloseConfirm(true);
        } else {
          setShowEditDialog(open);
          if (!open) editEstimatePersistence.clearSavedData();
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col [&_.overflow-visible]:overflow-visible">
          <DialogHeader className="flex-shrink-0">
            <div className="flex justify-between items-start">
              <div>
                <DialogTitle className="flex items-center gap-2"><Edit className="h-5 w-5" /> Edit Estimate</DialogTitle>
                <DialogDescription>Modify estimate details (available until converted to invoice)</DialogDescription>
              </div>
              <AutoSaveIndicator 
                lastSaved={editEstimatePersistence.lastSaved} 
                isSaving={editEstimatePersistence.isSaving} 
                isDirty={editEstimatePersistence.isDirty} 
              />
            </div>
          </DialogHeader>
          
          {editEstimate && (
            <div className="space-y-4 py-4 flex-1 overflow-y-auto min-h-0">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Reference Number</Label>
                  <Input 
                    value={editEstimate.reference_number} 
                    onChange={(e) => setEditEstimate({...editEstimate, reference_number: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Estimate Date</Label>
                  <Input 
                    type="date" 
                    value={editEstimate.estimate_date} 
                    onChange={(e) => setEditEstimate({...editEstimate, estimate_date: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Expiry Date</Label>
                  <Input 
                    type="date" 
                    value={editEstimate.expiry_date} 
                    onChange={(e) => setEditEstimate({...editEstimate, expiry_date: e.target.value})}
                  />
                </div>
              </div>
              
              {/* Line Items - Enhanced with Search */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Label className="flex items-center gap-2">
                    <Package className="h-4 w-4" /> Item Table
                  </Label>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setShowAddItemDialog(true)}>
                      <Plus className="h-4 w-4 mr-1" /> New Item
                    </Button>
                    <Button size="sm" variant="outline" onClick={addEditLineItem}>
                      <Plus className="h-4 w-4 mr-1" /> Add Row
                    </Button>
                  </div>
                </div>
                <div className="border rounded-lg overflow-visible">
                  <table className="w-full text-sm">
                    <thead className="bg-[#111820] border-b">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium w-[250px]">ITEM DETAILS</th>
                        <th className="px-3 py-2 text-center font-medium w-20">QTY</th>
                        <th className="px-3 py-2 text-center font-medium w-24">
                          <div className="flex items-center justify-center gap-1">RATE <IndianRupee className="h-3 w-3" /></div>
                        </th>
                        <th className="px-3 py-2 text-center font-medium w-28">DISCOUNT</th>
                        <th className="px-3 py-2 text-center font-medium w-24">TAX</th>
                        <th className="px-3 py-2 text-right font-medium w-24">AMOUNT</th>
                        <th className="px-3 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {editEstimate.line_items.map((item, idx) => {
                        const qty = item.quantity || 1;
                        const rate = item.rate || 0;
                        const grossAmount = qty * rate;
                        let discountAmount = 0;
                        if (item.discount_type === 'amount') {
                          discountAmount = item.discount_value || 0;
                        } else {
                          discountAmount = (grossAmount * (item.discount_percent || 0)) / 100;
                        }
                        const taxableAmount = grossAmount - discountAmount;
                        const taxAmount = taxableAmount * ((item.tax_percentage || 0) / 100);
                        const total = taxableAmount + taxAmount;
                        
                        return (
                          <tr key={idx} className="border-b border-[rgba(255,255,255,0.04)] hover:bg-[#111820]">
                            <td className="px-3 py-2">
                              <div className="relative">
                                <div className="flex items-center gap-1">
                                  <Package className="h-4 w-4 text-[rgba(244,246,240,0.25)] flex-shrink-0" />
                                  <Input 
                                    value={editActiveItemIndex === idx ? editItemSearch : item.name}
                                    onChange={(e) => {
                                      const value = e.target.value;
                                      setEditActiveItemIndex(idx);
                                      setEditItemSearch(value);
                                      updateEditLineItem(idx, "name", value);
                                      updateEditLineItem(idx, "item_id", "");
                                      // Filter items
                                      if (value.length >= 1) {
                                        const filtered = items.filter(i => 
                                          i.name?.toLowerCase().includes(value.toLowerCase()) || 
                                          i.sku?.toLowerCase().includes(value.toLowerCase())
                                        );
                                        setEditSearchResults(filtered);
                                      } else {
                                        setEditSearchResults([]);
                                      }
                                    }}
                                    onFocus={() => {
                                      setEditActiveItemIndex(idx);
                                      setEditItemSearch(item.name || "");
                                    }}
                                    placeholder="Type or search item..."
                                    className="border-0 bg-transparent focus:ring-1 h-8 text-sm"
                                    data-testid={`edit-item-search-${idx}`}
                                  />
                                </div>
                                {/* Search Results Dropdown */}
                                {editActiveItemIndex === idx && editItemSearch.length >= 1 && !item.item_id && editSearchResults.length > 0 && (
                                  <div className="absolute z-50 left-0 right-0 mt-1 bg-[#111820] border border-[rgba(255,255,255,0.13)] rounded max-h-48 overflow-y-auto">
                                    {editSearchResults.slice(0, 8).map(searchItem => (
                                      <div 
                                        key={searchItem.item_id}
                                        className="px-3 py-2 hover:bg-[rgba(59,158,255,0.08)] cursor-pointer flex justify-between items-center"
                                        onClick={() => selectEditItem(searchItem, idx)}
                                      >
                                        <div>
                                          <p className="font-medium text-sm">{searchItem.name}</p>
                                          <p className="text-xs text-[rgba(244,246,240,0.45)]">SKU: {searchItem.sku || 'N/A'}</p>
                                        </div>
                                        <span className="text-sm font-mono text-[rgba(244,246,240,0.45)]">₹{(searchItem.rate || searchItem.sales_rate || 0).toLocaleString()}</span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                                {/* Show SKU if item is selected */}
                                {item.item_id && (
                                  <p className="text-xs text-[rgba(244,246,240,0.25)] mt-0.5 ml-5">SKU: {item.sku || item.item_id?.slice(0, 8)}</p>
                                )}
                              </div>
                            </td>
                            <td className="px-3 py-2">
                              <Input 
                                type="number" 
                                value={item.quantity} 
                                onChange={(e) => updateEditLineItem(idx, "quantity", parseFloat(e.target.value) || 1)}
                                className="h-8 text-center"
                                min="1"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <Input 
                                type="number" 
                                value={item.rate} 
                                onChange={(e) => updateEditLineItem(idx, "rate", parseFloat(e.target.value) || 0)}
                                className="h-8 text-center"
                                min="0"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <div className="flex items-center gap-1">
                                <Select 
                                  value={item.discount_type || "percent"} 
                                  onValueChange={(v) => updateEditLineItem(idx, "discount_type", v)}
                                >
                                  <SelectTrigger className="w-12 h-8 px-1">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="percent"><Percent className="h-3 w-3" /></SelectItem>
                                    <SelectItem value="amount"><IndianRupee className="h-3 w-3" /></SelectItem>
                                  </SelectContent>
                                </Select>
                                <Input 
                                  type="number"
                                  className="w-16 h-8 text-center"
                                  value={item.discount_type === 'amount' ? (item.discount_value || 0) : (item.discount_percent || 0)}
                                  onChange={(e) => {
                                    const val = parseFloat(e.target.value) || 0;
                                    if (item.discount_type === 'amount') {
                                      updateEditLineItem(idx, "discount_value", val);
                                    } else {
                                      updateEditLineItem(idx, "discount_percent", val);
                                    }
                                  }}
                                  min="0"
                                />
                              </div>
                            </td>
                            <td className="px-3 py-2">
                              <Select 
                                value={String(item.tax_percentage || 18)} 
                                onValueChange={(v) => updateEditLineItem(idx, "tax_percentage", parseFloat(v))}
                              >
                                <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="0">0%</SelectItem>
                                  <SelectItem value="5">5%</SelectItem>
                                  <SelectItem value="12">12%</SelectItem>
                                  <SelectItem value="18">18%</SelectItem>
                                  <SelectItem value="28">28%</SelectItem>
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="px-3 py-2 text-right font-mono font-medium">
                              ₹{total.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                            </td>
                            <td className="px-3 py-2 text-center">
                              <Button size="icon" variant="ghost" onClick={() => removeEditLineItem(idx)} className="h-7 w-7">
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                      {editEstimate.line_items.length === 0 && (
                        <tr>
                          <td colSpan={7} className="px-3 py-8 text-center text-[rgba(244,246,240,0.25)]">
                            No items added. Click "+ Add Row" to start.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Customer Notes</Label>
                  <Textarea 
                    value={editEstimate.customer_notes} 
                    onChange={(e) => setEditEstimate({...editEstimate, customer_notes: e.target.value})}
                    rows={2}
                  />
                </div>
                <div>
                  <Label>Terms & Conditions</Label>
                  <Textarea 
                    value={editEstimate.terms_conditions} 
                    onChange={(e) => setEditEstimate({...editEstimate, terms_conditions: e.target.value})}
                    rows={2}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Discount</Label>
                  <div className="flex gap-2">
                    <Select value={editEstimate.discount_type} onValueChange={(v) => setEditEstimate({...editEstimate, discount_type: v})}>
                      <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">%</SelectItem>
                        <SelectItem value="amount">₹</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input 
                      type="number" 
                      value={editEstimate.discount_value} 
                      onChange={(e) => setEditEstimate({...editEstimate, discount_value: parseFloat(e.target.value) || 0})}
                    />
                  </div>
                </div>
                <div>
                  <Label>Shipping Charge</Label>
                  <Input 
                    type="number" 
                    value={editEstimate.shipping_charge} 
                    onChange={(e) => setEditEstimate({...editEstimate, shipping_charge: parseFloat(e.target.value) || 0})}
                  />
                </div>
                <div>
                  <Label>Adjustment</Label>
                  <Input 
                    type="number" 
                    value={editEstimate.adjustment} 
                    onChange={(e) => setEditEstimate({...editEstimate, adjustment: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter className="flex-shrink-0 border-t pt-4 mt-4">
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button onClick={handleUpdateEstimate} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="save-estimate-btn">Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Quick Add Item Dialog */}
      <Dialog open={showAddItemDialog} onOpenChange={setShowAddItemDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Package className="h-5 w-5" /> Quick Add Item</DialogTitle>
            <DialogDescription>Add a new item to your inventory</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Item Name *</Label>
              <Input 
                value={quickAddItem.name}
                onChange={(e) => setQuickAddItem({...quickAddItem, name: e.target.value})}
                placeholder="Enter item name"
                autoFocus
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>SKU</Label>
                <Input 
                  value={quickAddItem.sku}
                  onChange={(e) => setQuickAddItem({...quickAddItem, sku: e.target.value})}
                  placeholder="Auto-generated if empty"
                />
              </div>
              <div>
                <Label>Type</Label>
                <Select value={quickAddItem.item_type} onValueChange={(v) => setQuickAddItem({...quickAddItem, item_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="product">Product</SelectItem>
                    <SelectItem value="service">Service</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Rate (₹)</Label>
                <Input 
                  type="number"
                  value={quickAddItem.rate}
                  onChange={(e) => setQuickAddItem({...quickAddItem, rate: parseFloat(e.target.value) || 0})}
                  placeholder="0.00"
                />
              </div>
              <div>
                <Label>Unit</Label>
                <Select value={quickAddItem.unit} onValueChange={(v) => setQuickAddItem({...quickAddItem, unit: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pcs">Pieces (pcs)</SelectItem>
                    <SelectItem value="kg">Kilogram (kg)</SelectItem>
                    <SelectItem value="ltr">Liter (ltr)</SelectItem>
                    <SelectItem value="mtr">Meter (mtr)</SelectItem>
                    <SelectItem value="box">Box</SelectItem>
                    <SelectItem value="hrs">Hours (hrs)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>GST Rate</Label>
                <Select value={String(quickAddItem.tax_percentage)} onValueChange={(v) => setQuickAddItem({...quickAddItem, tax_percentage: parseFloat(v)})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">GST 0%</SelectItem>
                    <SelectItem value="5">GST 5%</SelectItem>
                    <SelectItem value="12">GST 12%</SelectItem>
                    <SelectItem value="18">GST 18%</SelectItem>
                    <SelectItem value="28">GST 28%</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>HSN Code</Label>
                <Input 
                  value={quickAddItem.hsn_code}
                  onChange={(e) => setQuickAddItem({...quickAddItem, hsn_code: e.target.value})}
                  placeholder="Optional"
                />
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <Textarea 
                value={quickAddItem.description}
                onChange={(e) => setQuickAddItem({...quickAddItem, description: e.target.value})}
                placeholder="Item description (optional)"
                rows={2}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowAddItemDialog(false);
              setQuickAddItem({ name: newLineItem.name || "", sku: "", rate: 0, description: "", unit: "pcs", tax_percentage: 18, hsn_code: "", item_type: "product" });
            }}>Cancel</Button>
            <Button onClick={handleQuickAddItem} className="bg-[#C8FF00] text-[#080C0F] font-bold">
              <Plus className="h-4 w-4 mr-2" /> Create & Add
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Estimate Close Confirmation */}
      <FormCloseConfirmDialog
        open={editEstimatePersistence.showCloseConfirm}
        onClose={() => editEstimatePersistence.setShowCloseConfirm(false)}
        onSave={async () => {
          await handleUpdateEstimate();
        }}
        onDiscard={() => {
          editEstimatePersistence.clearSavedData();
          setShowEditDialog(false);
        }}
        isSaving={false}
        entityName="Estimate"
      />
    </div>
  );
}
