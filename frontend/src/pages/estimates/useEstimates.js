import { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import { useEstimateCalculations } from "@/hooks/useEstimateCalculations";
import { useEstimateFilters } from "@/hooks/useEstimateFilters";
import { useFormPersistence } from "@/hooks/useFormPersistence";

const API = process.env.REACT_APP_BACKEND_URL + "/api/v1";

const INITIAL_ESTIMATE = {
  customer_id: "", reference_number: "", date: new Date().toISOString().split('T')[0],
  expiry_date: "", subject: "", salesperson_name: "", terms_and_conditions: "", notes: "",
  discount_type: "none", discount_value: 0, shipping_charge: 0, adjustment: 0,
  adjustment_description: "", line_items: []
};

const INITIAL_LINE_ITEM = {
  item_id: "", name: "", description: "", quantity: 1, unit: "pcs", rate: 0,
  discount_type: "percent", discount_percent: 0, discount_value: 0, tax_percentage: 18, hsn_code: ""
};

export function useEstimates() {
  const location = useLocation();

  // Core state
  const [activeTab, setActiveTab] = useState("estimates");
  const [estimates, setEstimates] = useState([]);
  const [ticketEstimates, setTicketEstimates] = useState([]);
  const [summary, setSummary] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [loading, setLoading] = useState(true);
  const { search, setSearch, statusFilter, setStatusFilter } = useEstimateFilters();

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
    expiry_days: 30, allow_accept: true, allow_decline: true,
    password_protected: false, password: ""
  });

  // Attachments state
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Preferences state
  const [preferences, setPreferences] = useState({
    auto_convert_on_accept: false, auto_convert_to: "draft_invoice",
    auto_send_converted: false, allow_public_accept: true,
    allow_public_decline: true, notify_on_view: true,
    notify_on_accept: true, notify_on_decline: true
  });

  // Custom fields state
  const [customFields, setCustomFields] = useState([]);
  const [newCustomField, setNewCustomField] = useState({
    field_name: "", field_type: "text", options: [],
    is_required: false, default_value: "", show_in_pdf: true, show_in_portal: true
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

  // Quick Add Item state
  const [quickAddItem, setQuickAddItem] = useState({
    name: "", sku: "", rate: 0, description: "", unit: "pcs",
    tax_percentage: 18, hsn_code: "", item_type: "product"
  });

  // Form states
  const [newEstimate, setNewEstimate] = useState({ ...INITIAL_ESTIMATE });
  const [newLineItem, setNewLineItem] = useState({ ...INITIAL_LINE_ITEM });
  const [sendEmail, setSendEmail] = useState("");
  const [sendMessage, setSendMessage] = useState("");

  // Edit item search state
  const [editItemSearch, setEditItemSearch] = useState("");
  const [editSearchResults, setEditSearchResults] = useState([]);
  const [editActiveItemIndex, setEditActiveItemIndex] = useState(null);

  // Auto-save for New Estimate form
  const newEstimatePersistence = useFormPersistence(
    'estimate_new', newEstimate, INITIAL_ESTIMATE,
    { enabled: activeTab === "create", isDialogOpen: activeTab === "create",
      setFormData: setNewEstimate, debounceMs: 2000, entityName: 'Estimate' }
  );

  // Auto-save for Edit Estimate dialog
  const editEstimatePersistence = useFormPersistence(
    editEstimate?.estimate_id ? `estimate_edit_${editEstimate.estimate_id}` : 'estimate_edit_temp',
    editEstimate, editEstimate,
    { enabled: showEditDialog && !!editEstimate, isDialogOpen: showEditDialog,
      setFormData: setEditEstimate, debounceMs: 2000, entityName: 'Estimate' }
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
      window.history.replaceState({}, '', '/estimates');
    }
  }, [location.search]);

  useEffect(() => { fetchData(); }, []);

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
      setEstimates(data.data || data.estimates || []);
    } catch (e) { console.error("Failed to fetch estimates:", e); }
  };

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

  const handleQuickAddItem = async () => {
    if (!quickAddItem.name) return toast.error("Item name is required");
    try {
      const res = await fetch(`${API}/items-enhanced/`, {
        method: "POST", headers,
        body: JSON.stringify({
          name: quickAddItem.name, sku: quickAddItem.sku || `SKU-${Date.now()}`,
          description: quickAddItem.description, rate: quickAddItem.rate || 0,
          unit: quickAddItem.unit || "pcs", tax_percentage: quickAddItem.tax_percentage || 18,
          hsn_code: quickAddItem.hsn_code, item_type: quickAddItem.item_type || "product", status: "active"
        })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Item "${quickAddItem.name}" created`);
        setShowAddItemDialog(false);
        setNewLineItem({
          item_id: data.item?.item_id || "", name: quickAddItem.name,
          description: quickAddItem.description || "", quantity: 1,
          unit: quickAddItem.unit || "pcs", rate: quickAddItem.rate || 0,
          discount_type: "percent", discount_percent: 0, discount_value: 0,
          tax_percentage: quickAddItem.tax_percentage || 18, hsn_code: quickAddItem.hsn_code || ""
        });
        setQuickAddItem({ name: "", sku: "", rate: 0, description: "", unit: "pcs", tax_percentage: 18, hsn_code: "", item_type: "product" });
        fetchItems();
      } else { toast.error(data.detail || "Failed to create item"); }
    } catch (e) { toast.error("Error creating item"); }
  };

  const searchContacts = async (query) => {
    if (!query || query.length < 2) { setContacts([]); return; }
    try {
      const res = await fetch(`${API}/contact-integration/contacts/search?q=${encodeURIComponent(query)}&contact_type=customer&limit=10`, { headers });
      const data = await res.json();
      setContacts(data.contacts || []);
    } catch (e) { console.error("Failed to search contacts:", e); }
  };

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

  const fetchItemPricing = async (itemId, customerId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/item-pricing/${itemId}?customer_id=${customerId || ""}`, { headers });
      const data = await res.json();
      if (data.code === 0) return data.item;
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
        newEstimatePersistence.onSuccessfulSave();
        resetForm();
        fetchData();
      } else { toast.error(data.detail || "Failed to create estimate"); }
    } catch (e) { toast.error("Error creating estimate"); }
  };

  const handleDeleteEstimate = async (estimateId) => {
    if (!confirm("Delete this estimate?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Estimate deleted"); setShowDetailDialog(false); fetchData(); }
      else { const data = await res.json(); toast.error(data.detail || "Cannot delete estimate"); }
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
        setShowSendDialog(false); setSendEmail(""); setSendMessage("");
        fetchEstimateDetail(selectedEstimate.estimate_id); fetchData();
      } else { toast.error(data.detail || "Failed to send estimate"); }
    } catch (e) { toast.error("Error sending estimate"); }
  };

  // Share Link Functions
  const handleCreateShareLink = async () => {
    if (!selectedEstimate) return;
    setShareLoading(true);
    try {
      const res = await fetch(`${API}/estimates-enhanced/${selectedEstimate.estimate_id}/share`, {
        method: "POST", headers, body: JSON.stringify(shareConfig)
      });
      const data = await res.json();
      if (res.ok) {
        const fullUrl = `${window.location.origin}${data.share_link.public_url}`;
        setShareLink({ ...data.share_link, full_url: fullUrl });
        toast.success("Share link created!");
      } else { toast.error(data.detail || "Failed to create share link"); }
    } catch (e) { toast.error("Error creating share link"); }
    finally { setShareLoading(false); }
  };

  const copyShareLink = () => {
    if (shareLink?.full_url) { navigator.clipboard.writeText(shareLink.full_url); toast.success("Link copied to clipboard!"); }
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
    if (file.size > 10 * 1024 * 1024) { toast.error("File size exceeds 10MB limit"); return; }
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("uploaded_by", localStorage.getItem("user_name") || "user");
    try {
      const res = await fetch(`${API}/estimates-enhanced/${selectedEstimate.estimate_id}/attachments`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData
      });
      const data = await res.json();
      if (res.ok) { toast.success("File uploaded successfully"); fetchAttachments(selectedEstimate.estimate_id); }
      else { toast.error(data.detail || "Failed to upload file"); }
    } catch (e) { toast.error("Error uploading file"); }
    finally { setUploading(false); }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm("Delete this attachment?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${selectedEstimate.estimate_id}/attachments/${attachmentId}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Attachment deleted"); fetchAttachments(selectedEstimate.estimate_id); }
      else { toast.error("Failed to delete attachment"); }
    } catch (e) { toast.error("Error deleting attachment"); }
  };

  const downloadAttachment = (attachmentId, filename) => {
    const url = `${API}/estimates-enhanced/${selectedEstimate.estimate_id}/attachments/${attachmentId}`;
    const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
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
        link.href = url; link.download = `Estimate_${estimateId}.pdf`; link.click();
        window.URL.revokeObjectURL(url); toast.success("PDF downloaded!");
      } else {
        const data = await res.json();
        const printWindow = window.open('', '_blank');
        printWindow.document.write(data.html); printWindow.document.close(); printWindow.print();
        toast.info("PDF preview opened in new window");
      }
    } catch (e) { console.error("PDF error:", e); toast.error("Error generating PDF"); }
  };

  // Preferences Functions
  const fetchPreferences = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/preferences`, { headers });
      const data = await res.json();
      if (data.code === 0) setPreferences(data.preferences);
    } catch (e) { console.error("Failed to fetch preferences:", e); }
  };

  const handleSavePreferences = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/preferences`, { method: "PUT", headers, body: JSON.stringify(preferences) });
      const data = await res.json();
      if (res.ok) { toast.success("Preferences saved!"); setShowPreferencesDialog(false); }
      else { toast.error(data.detail || "Failed to save preferences"); }
    } catch (e) { toast.error("Error saving preferences"); }
  };

  // Bulk Actions Functions
  const toggleSelectAll = () => {
    if (selectedIds.length === estimates.length) setSelectedIds([]);
    else setSelectedIds(estimates.map(e => e.estimate_id));
  };

  const toggleSelect = (estimateId) => {
    setSelectedIds(prev => prev.includes(estimateId) ? prev.filter(id => id !== estimateId) : [...prev, estimateId]);
  };

  const handleBulkAction = async () => {
    if (selectedIds.length === 0) { toast.error("Select at least one estimate"); return; }
    if (!bulkAction) { toast.error("Select an action"); return; }
    try {
      const res = await fetch(`${API}/estimates-enhanced/bulk/action`, {
        method: "POST", headers,
        body: JSON.stringify({ estimate_ids: selectedIds, action: bulkAction, reason: "Bulk action from UI" })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`${data.updated || data.deleted || 0} estimates updated`);
        if (data.errors?.length > 0) toast.warning(`${data.errors.length} failed: ${data.errors[0].error}`);
        setSelectedIds([]); setBulkAction(""); setShowBulkActionDialog(false); fetchData();
      } else { toast.error(data.detail || "Bulk action failed"); }
    } catch (e) { toast.error("Error performing bulk action"); }
  };

  // Edit Estimate
  const handleOpenEdit = (estimate) => {
    const normalizedLineItems = (estimate.line_items || []).map(item => ({
      ...item, quantity: item.quantity || item.qty || 1,
      rate: item.rate || item.unit_price || 0, discount_type: item.discount_type || "percent",
      discount_percent: item.discount_percent || 0, discount_value: item.discount_value || item.discount || 0,
      tax_percentage: item.tax_percentage || item.tax_rate || 18,
    }));
    const discountType = estimate.discount_type || "none";
    setEditEstimate({
      estimate_id: estimate.estimate_id,
      is_ticket_estimate: estimate.is_ticket_estimate || false,
      reference_number: estimate.reference_number || "", date: estimate.date || "",
      expiry_date: estimate.expiry_date || "", line_items: normalizedLineItems,
      discount_type: discountType === "none" ? "none" : discountType === "percent" ? "percent" : "amount",
      discount_value: estimate.discount_value || 0, shipping_charge: estimate.shipping_charge || 0,
      notes: estimate.notes || "", terms_and_conditions: estimate.terms_and_conditions || "",
      adjustment: estimate.adjustment || 0
    });
    setEditItemSearch(""); setEditSearchResults([]); setEditActiveItemIndex(null);
    if (items.length === 0) fetchItems();
    setShowEditDialog(true);
  };

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
    setTimeout(() => {
      setEditActiveItemIndex(editEstimate?.line_items?.length || 0);
      setEditItemSearch("");
    }, 100);
  };

  const selectEditItem = (item, index) => {
    setEditEstimate(prev => {
      const updated = [...prev.line_items];
      updated[index] = {
        ...updated[index], item_id: item.item_id, name: item.name,
        description: item.description || "", rate: item.rate || item.sales_rate || 0,
        unit: item.unit || "pcs", tax_percentage: item.tax_percentage || 18,
        hsn_code: item.hsn_code || ""
      };
      return { ...prev, line_items: updated };
    });
    setEditItemSearch(""); setEditSearchResults([]); setEditActiveItemIndex(null);
  };

  const removeEditLineItem = (index) => {
    setEditEstimate(prev => ({ ...prev, line_items: prev.line_items.filter((_, i) => i !== index) }));
  };

  const handleUpdateEstimate = async () => {
    if (!editEstimate) return;
    try {
      if (editEstimate.is_ticket_estimate) {
        toast.info("Ticket estimates are managed from the Job Card. Use the Ticket Estimates tab to navigate there.");
        setShowEditDialog(false); return;
      }
      const updatePayload = {
        reference_number: editEstimate.reference_number, date: editEstimate.date,
        expiry_date: editEstimate.expiry_date, discount_type: editEstimate.discount_type,
        discount_value: editEstimate.discount_value, shipping_charge: editEstimate.shipping_charge,
        notes: editEstimate.notes, terms_and_conditions: editEstimate.terms_and_conditions,
        adjustment: editEstimate.adjustment,
        line_items: editEstimate.line_items.map(item => ({
          item_id: item.item_id || null, name: item.name || "", description: item.description || "",
          hsn_code: item.hsn_code || "", quantity: item.quantity || 1, unit: item.unit || "pcs",
          rate: item.rate || 0, discount_percent: item.discount_percent || 0,
          discount_amount: item.discount_type === "amount" ? (item.discount_value || 0) : 0,
          tax_percentage: item.tax_percentage || 0,
        })),
      };
      const res = await fetch(`${API}/estimates-enhanced/${editEstimate.estimate_id}`, {
        method: "PUT", headers, body: JSON.stringify(updatePayload)
      });
      if (res.ok) {
        toast.success("Estimate updated successfully");
        editEstimatePersistence.onSuccessfulSave();
        setShowEditDialog(false); fetchEstimateDetail(editEstimate.estimate_id); fetchData();
      } else { const err = await res.json(); toast.error(err.detail || "Failed to update estimate"); }
    } catch (e) { toast.error("Error updating estimate"); }
  };

  // Custom Fields Functions
  const fetchCustomFields = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/custom-fields`, { headers });
      const data = await res.json();
      if (data.code === 0) setCustomFields(data.custom_fields || []);
    } catch (e) { console.error("Failed to fetch custom fields:", e); }
  };

  const handleAddCustomField = async () => {
    if (!newCustomField.field_name.trim()) { toast.error("Field name is required"); return; }
    try {
      const res = await fetch(`${API}/estimates-enhanced/custom-fields`, { method: "POST", headers, body: JSON.stringify(newCustomField) });
      const data = await res.json();
      if (res.ok) {
        toast.success("Custom field added!");
        setNewCustomField({ field_name: "", field_type: "text", options: [], is_required: false, default_value: "", show_in_pdf: true, show_in_portal: true });
        fetchCustomFields();
      } else { toast.error(data.detail || "Failed to add custom field"); }
    } catch (e) { toast.error("Error adding custom field"); }
  };

  const handleDeleteCustomField = async (fieldName) => {
    if (!confirm(`Delete custom field "${fieldName}"?`)) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/custom-fields/${encodeURIComponent(fieldName)}`, { method: "DELETE", headers });
      if (res.ok) { toast.success("Custom field deleted"); fetchCustomFields(); }
      else { toast.error("Failed to delete custom field"); }
    } catch (e) { toast.error("Error deleting custom field"); }
  };

  // PDF Templates Functions
  const fetchPdfTemplates = async () => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/templates`, { headers });
      const data = await res.json();
      if (data.code === 0) setPdfTemplates(data.templates || []);
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
        link.href = url; link.download = `Estimate_${estimateId}_${templateId}.pdf`; link.click();
        window.URL.revokeObjectURL(url); toast.success("PDF downloaded!");
      } else {
        const data = await res.json();
        const printWindow = window.open('', '_blank');
        printWindow.document.write(data.html); printWindow.document.close(); printWindow.print();
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
        link.href = url; link.download = `estimates_export_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click(); window.URL.revokeObjectURL(url); toast.success("Export downloaded!");
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data.estimates, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url; link.download = `estimates_export_${new Date().toISOString().slice(0, 10)}.json`;
        link.click(); window.URL.revokeObjectURL(url); toast.success(`Exported ${data.count} estimates!`);
      }
    } catch (e) { toast.error("Export failed"); }
  };

  const handleImport = async () => {
    if (!importFile) { toast.error("Please select a file"); return; }
    setImporting(true);
    const formData = new FormData();
    formData.append("file", importFile);
    try {
      const res = await fetch(`${API}/estimates-enhanced/import?skip_errors=true`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Imported ${data.imported} estimates!`);
        if (data.errors?.length > 0) toast.warning(`${data.errors.length} rows had errors`);
        setShowImportDialog(false); setImportFile(null); fetchData();
      } else { toast.error(data.detail || "Import failed"); }
    } catch (e) { toast.error("Import error"); }
    finally { setImporting(false); }
  };

  const downloadImportTemplate = () => { window.open(`${API}/estimates-enhanced/import/template`, '_blank'); };

  // Status Actions
  const handleMarkAccepted = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/mark-accepted`, { method: "POST", headers });
      if (res.ok) { toast.success("Estimate marked as accepted"); fetchEstimateDetail(estimateId); fetchData(); }
    } catch (e) { toast.error("Error updating status"); }
  };

  const handleMarkDeclined = async (estimateId) => {
    const reason = prompt("Enter decline reason (optional):");
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/mark-declined?reason=${encodeURIComponent(reason || "")}`, { method: "POST", headers });
      if (res.ok) { toast.success("Estimate marked as declined"); fetchEstimateDetail(estimateId); fetchData(); }
    } catch (e) { toast.error("Error updating status"); }
  };

  // Convert Actions
  const handleConvertToInvoice = async (estimateId) => {
    if (!confirm("Convert this estimate to an invoice?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/convert-to-invoice`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) { toast.success(`Converted to Invoice ${data.invoice_number}`); setShowDetailDialog(false); fetchData(); }
      else { toast.error(data.detail || "Failed to convert"); }
    } catch (e) { toast.error("Error converting estimate"); }
  };

  const handleConvertToSO = async (estimateId) => {
    if (!confirm("Convert this estimate to a sales order?")) return;
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/convert-to-sales-order`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) { toast.success(`Converted to Sales Order ${data.salesorder_number}`); setShowDetailDialog(false); fetchData(); }
      else { toast.error(data.detail || "Failed to convert"); }
    } catch (e) { toast.error("Error converting estimate"); }
  };

  const handleClone = async (estimateId) => {
    try {
      const res = await fetch(`${API}/estimates-enhanced/${estimateId}/clone`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) { toast.success(`Cloned as ${data.estimate_number}`); fetchData(); }
    } catch (e) { toast.error("Error cloning estimate"); }
  };

  // Line items
  const addLineItem = () => {
    if (!newLineItem.name) return toast.error("Item name is required");
    const qty = newLineItem.quantity || 1;
    const rate = newLineItem.rate || 0;
    const grossAmount = qty * rate;
    let discountAmount = 0;
    if (newLineItem.discount_type === 'amount') discountAmount = newLineItem.discount_value || 0;
    else discountAmount = (grossAmount * (newLineItem.discount_percent || 0)) / 100;
    const taxableAmount = grossAmount - discountAmount;
    const taxAmount = taxableAmount * ((newLineItem.tax_percentage || 0) / 100);
    const total = taxableAmount + taxAmount;
    const item = {
      ...newLineItem, quantity: qty, rate: rate, gross_amount: grossAmount,
      discount: discountAmount, discount_type: newLineItem.discount_type || 'percent',
      discount_percent: newLineItem.discount_percent || 0, discount_value: newLineItem.discount_value || 0,
      taxable_amount: taxableAmount, tax_amount: taxAmount, total: total
    };
    setNewEstimate(prev => ({ ...prev, line_items: [...prev.line_items, item] }));
    setNewLineItem({ ...INITIAL_LINE_ITEM });
  };

  const removeLineItem = (index) => {
    setNewEstimate(prev => ({ ...prev, line_items: prev.line_items.filter((_, i) => i !== index) }));
  };

  const selectItem = async (item) => {
    if (newEstimate.customer_id) {
      const pricedItem = await fetchItemPricing(item.item_id, newEstimate.customer_id);
      if (pricedItem) {
        setNewLineItem({
          item_id: pricedItem.item_id, name: pricedItem.name, description: pricedItem.description || "",
          quantity: 1, unit: pricedItem.unit || "pcs", rate: pricedItem.rate,
          base_rate: pricedItem.base_rate, discount_percent: 0,
          tax_percentage: pricedItem.tax_percentage || 18, hsn_code: pricedItem.hsn_code || "",
          price_list_applied: pricedItem.price_list_name,
          discount_from_pricelist: pricedItem.discount_applied || 0,
          markup_from_pricelist: pricedItem.markup_applied || 0
        });
        if (pricedItem.price_list_name) {
          if (pricedItem.discount_applied > 0) toast.success(`Price adjusted: -₹${pricedItem.discount_applied} (${pricedItem.price_list_name})`, { duration: 2000 });
          else if (pricedItem.markup_applied > 0) toast.info(`Price adjusted: +₹${pricedItem.markup_applied} (${pricedItem.price_list_name})`, { duration: 2000 });
        }
        return;
      }
    }
    setNewLineItem({
      item_id: item.item_id, name: item.name, description: item.description || "",
      quantity: 1, unit: item.unit || "pcs", rate: item.rate || item.sales_rate || 0,
      discount_percent: 0, tax_percentage: item.tax_percentage || 18, hsn_code: item.hsn_code || ""
    });
  };

  const totals = useEstimateCalculations(newEstimate);

  const resetForm = () => {
    setNewEstimate({ ...INITIAL_ESTIMATE, date: new Date().toISOString().split('T')[0] });
    setSelectedContact(null); setContactSearch(""); setCustomerPricing(null);
  };

  return {
    // Core state
    activeTab, setActiveTab, estimates, ticketEstimates, summary, funnel, loading,
    search, setSearch, statusFilter, setStatusFilter,
    // Dialogs
    showCreateDialog, setShowCreateDialog, showDetailDialog, setShowDetailDialog,
    showSendDialog, setShowSendDialog, showShareDialog, setShowShareDialog,
    showAttachmentDialog, setShowAttachmentDialog, showPreferencesDialog, setShowPreferencesDialog,
    showImportDialog, setShowImportDialog, showBulkActionDialog, setShowBulkActionDialog,
    showCustomFieldsDialog, setShowCustomFieldsDialog, showTemplateDialog, setShowTemplateDialog,
    showEditDialog, setShowEditDialog, showAddItemDialog, setShowAddItemDialog,
    selectedEstimate, setSelectedEstimate,
    // Edit
    editEstimate, setEditEstimate, editItemSearch, setEditItemSearch,
    editSearchResults, setEditSearchResults, editActiveItemIndex, setEditActiveItemIndex,
    editEstimatePersistence,
    // Bulk
    selectedIds, setSelectedIds, bulkAction, setBulkAction,
    // Share
    shareLink, setShareLink, shareLoading, shareConfig, setShareConfig,
    // Attachments
    attachments, uploading,
    // Preferences
    preferences, setPreferences,
    // Custom fields
    customFields, newCustomField, setNewCustomField,
    // Templates
    pdfTemplates, selectedTemplate, setSelectedTemplate,
    // Import
    importFile, setImportFile, importing,
    // Contacts
    contacts, setContacts, contactSearch, setContactSearch,
    selectedContact, setSelectedContact, customerPricing, setCustomerPricing,
    // Items
    items, newLineItem, setNewLineItem, quickAddItem, setQuickAddItem,
    // Send
    sendEmail, setSendEmail, sendMessage, setSendMessage,
    // Persistence
    newEstimatePersistence, newEstimate, setNewEstimate, totals,
    // Fetchers
    fetchData, fetchEstimates, fetchTicketEstimates, fetchEstimateDetail,
    fetchPreferences, fetchCustomFields, fetchPdfTemplates, fetchAttachments, fetchItems,
    // Handlers
    handleCreateEstimate, handleDeleteEstimate, handleSendEstimate,
    handleCreateShareLink, copyShareLink,
    handleUploadAttachment, handleDeleteAttachment, downloadAttachment,
    handleDownloadPDF, handleSavePreferences,
    toggleSelectAll, toggleSelect, handleBulkAction,
    handleOpenEdit, updateEditLineItem, addEditLineItem, selectEditItem, removeEditLineItem,
    handleUpdateEstimate,
    handleAddCustomField, handleDeleteCustomField,
    handleDownloadWithTemplate,
    handleExport, handleImport, downloadImportTemplate,
    handleMarkAccepted, handleMarkDeclined,
    handleConvertToInvoice, handleConvertToSO, handleClone,
    addLineItem, removeLineItem, selectItem, resetForm,
    searchContacts, fetchCustomerPricing,
  };
}
