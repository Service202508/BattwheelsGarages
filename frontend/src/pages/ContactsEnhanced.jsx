import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { 
  Plus, Users, Search, Edit, Trash2, Building2, User, Phone, Mail, Globe, 
  MapPin, Tag, Shield, FileText, RefreshCw, CheckCircle, XCircle, Eye,
  UserPlus, Home, Truck, CreditCard, MoreVertical, Send, Key, ChevronRight,
  Receipt, ShoppingCart, History, Save
} from "lucide-react";
import { StatCard, StatCardGrid, formatCurrencyCompact } from "@/components/ui/stat-card";
import { ResponsiveTable, EmptyState, TableSkeleton } from "@/components/ui/data-display";
import PageHeader from "@/components/PageHeader";
import { API } from "@/App";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

const contactTypeColors = {
  customer: "bg-[rgba(59,158,255,0.10)] text-[#3B9EFF] border border-[rgba(59,158,255,0.25)]",
  vendor: "bg-[rgba(255,140,0,0.10)] text-[#FF8C00] border border-[rgba(255,140,0,0.25)]",
  both: "bg-[rgba(139,92,246,0.10)] text-[#8B5CF6] border border-[rgba(139,92,246,0.25)]"
};

const contactTypeLabels = {
  customer: "Customer",
  vendor: "Vendor", 
  both: "Customer & Vendor"
};

export default function ContactsEnhanced() {
  const [activeTab, setActiveTab] = useState("contacts");
  const [contacts, setContacts] = useState([]);
  const [tags, setTags] = useState([]);
  const [summary, setSummary] = useState(null);
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [activeFilter, setActiveFilter] = useState("all");

  // Dialogs
  const [showContactDialog, setShowContactDialog] = useState(false);
  const [showTagDialog, setShowTagDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPersonDialog, setShowPersonDialog] = useState(false);
  const [showAddressDialog, setShowAddressDialog] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [contactTransactions, setContactTransactions] = useState([]);
  const [transactionSummary, setTransactionSummary] = useState(null);

  // Form states
  const navigate = useNavigate();
  const [newContact, setNewContact] = useState({
    name: "", company_name: "", contact_type: "customer", email: "", phone: "", mobile: "",
    website: "", currency_code: "INR", payment_terms: 30, credit_limit: 0,
    gstin: "", pan: "", place_of_supply: "", tax_treatment: "business_gst",
    gst_treatment: "registered", opening_balance: 0, opening_balance_type: "credit",
    tags: [], notes: "", custom_fields: {}
  });
  const [newTag, setNewTag] = useState({ name: "", description: "", color: "#3B82F6" });
  const [newPerson, setNewPerson] = useState({ first_name: "", last_name: "", email: "", phone: "", designation: "", department: "", is_primary: false });
  const [newAddress, setNewAddress] = useState({ address_type: "billing", attention: "", street: "", street2: "", city: "", state: "", state_code: "", zip_code: "", country: "India", phone: "", is_default: false });
  const [editMode, setEditMode] = useState(false);

  // Initial form data for comparison
  const initialContactData = {
    name: "", company_name: "", contact_type: "customer", email: "", phone: "", mobile: "",
    website: "", currency_code: "INR", payment_terms: 30, credit_limit: 0,
    gstin: "", pan: "", place_of_supply: "", tax_treatment: "business_gst",
    gst_treatment: "registered", opening_balance: 0, opening_balance_type: "credit",
    tags: [], notes: "", custom_fields: {}
  };

  // Auto-save for Contact form
  const contactPersistence = useFormPersistence(
    editMode && selectedContact ? `contact_edit_${selectedContact.contact_id}` : 'contact_new',
    newContact,
    initialContactData,
    {
      enabled: showContactDialog,
      isDialogOpen: showContactDialog,
      setFormData: setNewContact,
      debounceMs: 2000,
      entityName: 'Contact'
    }
  );

  const token = localStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchContacts(), fetchTags(), fetchSummary(), fetchStates()]);
    setLoading(false);
  }, []);

  const fetchContacts = async () => {
    try {
      let url = `${API}/contacts-enhanced/?per_page=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (typeFilter !== "all") url += `&contact_type=${typeFilter}`;
      if (activeFilter !== "all") url += `&is_active=${activeFilter === "active"}`;
      
      const res = await fetch(url, { headers });
      const data = await res.json();
      setContacts(data.contacts || []);
    } catch (e) { console.error("Failed to fetch contacts:", e); }
  };

  const fetchTags = async () => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/tags`, { headers });
      const data = await res.json();
      setTags(data.tags || []);
    } catch (e) { console.error("Failed to fetch tags:", e); }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/summary`, { headers });
      const data = await res.json();
      setSummary(data.summary || null);
    } catch (e) { console.error("Failed to fetch summary:", e); }
  };

  const fetchStates = async () => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/states`, { headers });
      const data = await res.json();
      setStates(data.states || []);
    } catch (e) { console.error("Failed to fetch states:", e); }
  };

  const fetchContactDetail = async (contactId) => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/${contactId}`, { headers });
      const data = await res.json();
      setSelectedContact(data.contact);
      setShowDetailDialog(true);
      
      // Fetch transaction history
      fetchContactTransactions(contactId);
    } catch (e) { toast.error("Failed to fetch contact details"); }
  };

  const fetchContactTransactions = async (contactId) => {
    try {
      const res = await fetch(`${API}/contact-integration/contacts/${contactId}/transactions?per_page=10`, { headers });
      const data = await res.json();
      setContactTransactions(data.transactions || []);
      setTransactionSummary(data.summary || null);
    } catch (e) { 
      console.error("Failed to fetch transactions:", e);
      setContactTransactions([]);
      setTransactionSummary(null);
    }
  };

  // Contact CRUD
  const handleCreateContact = async () => {
    if (!newContact.name) return toast.error("Contact name is required");
    try {
      const res = await fetch(`${API}/contacts-enhanced/`, { method: "POST", headers, body: JSON.stringify(newContact) });
      if (res.ok) {
        toast.success("Contact created");
        contactPersistence.onSuccessfulSave(); // Clear auto-saved draft
        setShowContactDialog(false);
        resetContactForm();
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to create contact");
      }
    } catch (e) { toast.error("Error creating contact"); }
  };

  const handleUpdateContact = async () => {
    if (!selectedContact) return;
    try {
      const res = await fetch(`${API}/contacts-enhanced/${selectedContact.contact_id}`, { method: "PUT", headers, body: JSON.stringify(newContact) });
      if (res.ok) {
        toast.success("Contact updated");
        contactPersistence.onSuccessfulSave(); // Clear auto-saved draft
        setEditMode(false);
        fetchContactDetail(selectedContact.contact_id);
        fetchData();
      }
    } catch (e) { toast.error("Error updating contact"); }
  };

  const handleDeleteContact = async (contactId, force = false) => {
    if (!confirm(force ? "This will deactivate the contact. Continue?" : "Delete this contact?")) return;
    try {
      const res = await fetch(`${API}/contacts-enhanced/${contactId}?force=${force}`, { method: "DELETE", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.deactivated ? "Contact deactivated" : "Contact deleted");
        setShowDetailDialog(false);
        fetchData();
      } else {
        if (data.detail?.includes("transactions")) {
          if (confirm("Contact has transactions. Deactivate instead?")) {
            handleDeleteContact(contactId, true);
          }
        } else {
          toast.error(data.detail || "Failed to delete contact");
        }
      }
    } catch (e) { toast.error("Error deleting contact"); }
  };

  const handleToggleActive = async (contactId, activate) => {
    try {
      const endpoint = activate ? "activate" : "deactivate";
      const res = await fetch(`${API}/contacts-enhanced/${contactId}/${endpoint}`, { method: "PUT", headers });
      if (res.ok) {
        toast.success(`Contact ${activate ? "activated" : "deactivated"}`);
        fetchData();
        if (selectedContact?.contact_id === contactId) {
          fetchContactDetail(contactId);
        }
      }
    } catch (e) { toast.error("Error updating contact status"); }
  };

  // Portal & Statements
  const handleEnablePortal = async (contactId) => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/${contactId}/enable-portal`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success("Portal access enabled, invite sent!");
        fetchContactDetail(contactId);
      } else {
        toast.error(data.detail || "Failed to enable portal");
      }
    } catch (e) { toast.error("Error enabling portal"); }
  };

  const handleDisablePortal = async (contactId) => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/${contactId}/disable-portal`, { method: "POST", headers });
      if (res.ok) {
        toast.success("Portal access disabled");
        fetchContactDetail(contactId);
      }
    } catch (e) { toast.error("Error disabling portal"); }
  };

  const handleEmailStatement = async (contactId) => {
    try {
      const res = await fetch(`${API}/contacts-enhanced/${contactId}/email-statement`, { method: "POST", headers });
      const data = await res.json();
      if (res.ok) {
        toast.success("Statement emailed!");
      } else {
        toast.error(data.detail || "Failed to email statement");
      }
    } catch (e) { toast.error("Error sending statement"); }
  };

  // Tags CRUD
  const handleCreateTag = async () => {
    if (!newTag.name) return toast.error("Tag name is required");
    try {
      const res = await fetch(`${API}/contacts-enhanced/tags`, { method: "POST", headers, body: JSON.stringify(newTag) });
      if (res.ok) {
        toast.success("Tag created");
        setShowTagDialog(false);
        setNewTag({ name: "", description: "", color: "#3B82F6" });
        fetchTags();
      }
    } catch (e) { toast.error("Error creating tag"); }
  };

  const handleDeleteTag = async (tagId) => {
    if (!confirm("Delete this tag?")) return;
    try {
      const res = await fetch(`${API}/contacts-enhanced/tags/${tagId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Tag deleted");
        fetchTags();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Cannot delete tag");
      }
    } catch (e) { toast.error("Error deleting tag"); }
  };

  // Persons CRUD
  const handleAddPerson = async () => {
    if (!newPerson.first_name) return toast.error("First name is required");
    try {
      const res = await fetch(`${API}/contacts-enhanced/${selectedContact.contact_id}/persons`, { method: "POST", headers, body: JSON.stringify(newPerson) });
      if (res.ok) {
        toast.success("Person added");
        setShowPersonDialog(false);
        setNewPerson({ first_name: "", last_name: "", email: "", phone: "", designation: "", department: "", is_primary: false });
        fetchContactDetail(selectedContact.contact_id);
      }
    } catch (e) { toast.error("Error adding person"); }
  };

  const handleDeletePerson = async (personId) => {
    if (!confirm("Remove this person?")) return;
    try {
      const res = await fetch(`${API}/contacts-enhanced/${selectedContact.contact_id}/persons/${personId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Person removed");
        fetchContactDetail(selectedContact.contact_id);
      }
    } catch (e) { toast.error("Error removing person"); }
  };

  // Addresses CRUD
  const handleAddAddress = async () => {
    if (!newAddress.city && !newAddress.street) return toast.error("Address details required");
    try {
      const res = await fetch(`${API}/contacts-enhanced/${selectedContact.contact_id}/addresses`, { method: "POST", headers, body: JSON.stringify(newAddress) });
      if (res.ok) {
        toast.success("Address added");
        setShowAddressDialog(false);
        setNewAddress({ address_type: "billing", attention: "", street: "", street2: "", city: "", state: "", state_code: "", zip_code: "", country: "India", phone: "", is_default: false });
        fetchContactDetail(selectedContact.contact_id);
      }
    } catch (e) { toast.error("Error adding address"); }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!confirm("Remove this address?")) return;
    try {
      const res = await fetch(`${API}/contacts-enhanced/${selectedContact.contact_id}/addresses/${addressId}`, { method: "DELETE", headers });
      if (res.ok) {
        toast.success("Address removed");
        fetchContactDetail(selectedContact.contact_id);
      }
    } catch (e) { toast.error("Error removing address"); }
  };

  // GSTIN Validation
  const validateGSTIN = async (gstin) => {
    if (!gstin || gstin.length < 15) return;
    try {
      const res = await fetch(`${API}/contacts-enhanced/validate-gstin/${gstin}`, { headers });
      const data = await res.json();
      if (data.valid) {
        setNewContact(prev => ({
          ...prev,
          place_of_supply: data.details.state_code,
          pan: data.details.pan
        }));
        toast.success(`Valid GSTIN - ${data.details.state_name}`);
      } else {
        toast.error("Invalid GSTIN format");
      }
    } catch (e) { console.error("GSTIN validation failed"); }
  };

  const resetContactForm = () => {
    setNewContact({
      name: "", company_name: "", contact_type: "customer", email: "", phone: "", mobile: "",
      website: "", currency_code: "INR", payment_terms: 30, credit_limit: 0,
      gstin: "", pan: "", place_of_supply: "", tax_treatment: "business_gst",
      gst_treatment: "registered", opening_balance: 0, opening_balance_type: "credit",
      tags: [], notes: "", custom_fields: {}
    });
    setEditMode(false);
  };

  const openEditMode = () => {
    setNewContact({
      name: selectedContact.name,
      company_name: selectedContact.company_name || "",
      contact_type: selectedContact.contact_type,
      email: selectedContact.email || "",
      phone: selectedContact.phone || "",
      mobile: selectedContact.mobile || "",
      website: selectedContact.website || "",
      currency_code: selectedContact.currency_code || "INR",
      payment_terms: selectedContact.payment_terms || 30,
      credit_limit: selectedContact.credit_limit || 0,
      gstin: selectedContact.gstin || "",
      pan: selectedContact.pan || "",
      place_of_supply: selectedContact.place_of_supply || "",
      tax_treatment: selectedContact.tax_treatment || "business_gst",
      gst_treatment: selectedContact.gst_treatment || "registered",
      notes: selectedContact.notes || "",
      tags: selectedContact.tags || [],
      custom_fields: selectedContact.custom_fields || {}
    });
    setEditMode(true);
  };

  return (
    <div className="space-y-6" data-testid="contacts-enhanced-page">
      {/* Header */}
      <PageHeader
        title="Contact Management"
        description="Customers, Vendors, Persons & Addresses"
        icon={Users}
        actions={
          <Button onClick={fetchData} variant="outline" className="gap-2 bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]" data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      {summary && (
        <StatCardGrid columns={6}>
          <StatCard
            title="Total Contacts"
            value={summary.total_contacts}
            icon={Users}
            variant="info"
          />
          <StatCard
            title="Customers"
            value={summary.customers}
            icon={User}
            variant="success"
          />
          <StatCard
            title="Vendors"
            value={summary.vendors}
            icon={Building2}
            variant="warning"
          />
          <StatCard
            title="With GSTIN"
            value={summary.with_gstin}
            icon={Shield}
            variant="purple"
          />
          <StatCard
            title="Receivable"
            value={formatCurrencyCompact(summary.total_receivable || 0)}
            icon={CreditCard}
            variant="success"
          />
          <StatCard
            title="Payable"
            value={formatCurrencyCompact(summary.total_payable || 0)}
            icon={CreditCard}
            variant="danger"
          />
        </StatCardGrid>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="tags">Tags</TabsTrigger>
        </TabsList>

        {/* Contacts Tab */}
        <TabsContent value="contacts" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <div className="flex flex-1 gap-2 max-w-2xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgba(244,246,240,0.25)]" />
                <Input value={search} onChange={(e) => setSearch(e.target.value)} onKeyUp={(e) => e.key === 'Enter' && fetchContacts()} placeholder="Search contacts..." className="pl-10 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.25)] focus:border-[#C8FF00] focus:ring-[rgba(200,255,0,0.08)]" data-testid="search-contacts" />
              </div>
              <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v); setTimeout(fetchContacts, 100); }}>
                <SelectTrigger className="w-40 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0]"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#111820] border-[rgba(255,255,255,0.1)]">
                  <SelectItem value="all" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">All Types</SelectItem>
                  <SelectItem value="customer" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Customers</SelectItem>
                  <SelectItem value="vendor" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Vendors</SelectItem>
                  <SelectItem value="both" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Both</SelectItem>
                </SelectContent>
              </Select>
              <Select value={activeFilter} onValueChange={(v) => { setActiveFilter(v); setTimeout(fetchContacts, 100); }}>
                <SelectTrigger className="w-32 bg-[#111820] border-[rgba(255,255,255,0.07)] text-[#F4F6F0]"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#111820] border-[rgba(255,255,255,0.1)]">
                  <SelectItem value="all" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">All Status</SelectItem>
                  <SelectItem value="active" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Active</SelectItem>
                  <SelectItem value="inactive" className="text-[#F4F6F0] focus:bg-[rgba(200,255,0,0.1)] focus:text-[#C8FF00]">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Dialog open={showContactDialog} onOpenChange={(open) => {
              if (!open && contactPersistence.isDirty) {
                contactPersistence.setShowCloseConfirm(true);
              } else {
                setShowContactDialog(open);
                if (!open) {
                  contactPersistence.clearSavedData();
                  resetContactForm();
                }
              }
            }}>
              <DialogTrigger asChild>
                <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold rounded-[3px] gap-2 hover:shadow-[0_0_20px_rgba(200,255,0,0.3)]" data-testid="new-contact-btn">
                  <Plus className="h-4 w-4" /> New Contact
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-[#111820] border-[rgba(255,255,255,0.13)]">
                <DialogHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <DialogTitle className="text-[#F4F6F0] font-bold">Create Contact</DialogTitle>
                      <DialogDescription className="text-[rgba(244,246,240,0.45)]">Add a new customer, vendor, or both</DialogDescription>
                    </div>
                    <AutoSaveIndicator 
                      lastSaved={contactPersistence.lastSaved} 
                      isSaving={contactPersistence.isSaving} 
                      isDirty={contactPersistence.isDirty} 
                    />
                  </div>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  {/* Draft Recovery Banner */}
                  <DraftRecoveryBanner
                    show={contactPersistence.showRecoveryBanner}
                    savedAt={contactPersistence.savedDraftInfo?.timestamp}
                    onRestore={contactPersistence.handleRestoreDraft}
                    onDiscard={contactPersistence.handleDiscardDraft}
                  />
                  
                  {/* Basic Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Contact Type *</Label>
                      <Select value={newContact.contact_type} onValueChange={(v) => setNewContact({ ...newContact, contact_type: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="customer">Customer</SelectItem>
                          <SelectItem value="vendor">Vendor</SelectItem>
                          <SelectItem value="both">Customer & Vendor</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Name *</Label>
                      <Input value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} placeholder="Contact name" data-testid="contact-name-input" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Company Name</Label>
                      <Input value={newContact.company_name} onChange={(e) => setNewContact({ ...newContact, company_name: e.target.value })} placeholder="Company name" />
                    </div>
                    <div>
                      <Label>Email</Label>
                      <Input type="email" value={newContact.email} onChange={(e) => setNewContact({ ...newContact, email: e.target.value })} placeholder="email@example.com" />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div><Label>Phone</Label><Input value={newContact.phone} onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })} placeholder="Phone number" /></div>
                    <div><Label>Mobile</Label><Input value={newContact.mobile} onChange={(e) => setNewContact({ ...newContact, mobile: e.target.value })} placeholder="Mobile number" /></div>
                    <div><Label>Website</Label><Input value={newContact.website} onChange={(e) => setNewContact({ ...newContact, website: e.target.value })} placeholder="https://" /></div>
                  </div>
                  
                  <Separator />
                  
                  {/* GST Info */}
                  <h4 className="font-medium">Tax Information</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>GSTIN</Label>
                      <Input value={newContact.gstin} onChange={(e) => setNewContact({ ...newContact, gstin: e.target.value.toUpperCase() })} onBlur={(e) => validateGSTIN(e.target.value)} placeholder="22AAAAA0000A1Z5" maxLength={15} />
                    </div>
                    <div>
                      <Label>PAN</Label>
                      <Input value={newContact.pan} onChange={(e) => setNewContact({ ...newContact, pan: e.target.value.toUpperCase() })} placeholder="AAAAA0000A" maxLength={10} />
                    </div>
                    <div>
                      <Label>Place of Supply</Label>
                      <Select value={newContact.place_of_supply || "none"} onValueChange={(v) => setNewContact({ ...newContact, place_of_supply: v === "none" ? "" : v })}>
                        <SelectTrigger><SelectValue placeholder="Select state" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Select State</SelectItem>
                          {states.map(s => <SelectItem key={s.code} value={s.code}>{s.name}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>GST Treatment</Label>
                      <Select value={newContact.gst_treatment} onValueChange={(v) => setNewContact({ ...newContact, gst_treatment: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="registered">Registered Business</SelectItem>
                          <SelectItem value="unregistered">Unregistered Business</SelectItem>
                          <SelectItem value="consumer">Consumer</SelectItem>
                          <SelectItem value="overseas">Overseas</SelectItem>
                          <SelectItem value="sez">SEZ</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Tax Treatment</Label>
                      <Select value={newContact.tax_treatment} onValueChange={(v) => setNewContact({ ...newContact, tax_treatment: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="business_gst">Business (GST Registered)</SelectItem>
                          <SelectItem value="business_none">Business (Not Registered)</SelectItem>
                          <SelectItem value="consumer">Consumer</SelectItem>
                          <SelectItem value="overseas">Overseas</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <Separator />

                  {/* Financial */}
                  <h4 className="font-medium">Payment Terms</h4>
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <Label>Payment Terms (days)</Label>
                      <Input type="number" value={newContact.payment_terms} onChange={(e) => setNewContact({ ...newContact, payment_terms: parseInt(e.target.value) || 0 })} />
                    </div>
                    <div>
                      <Label>Credit Limit</Label>
                      <Input type="number" value={newContact.credit_limit} onChange={(e) => setNewContact({ ...newContact, credit_limit: parseFloat(e.target.value) || 0 })} />
                    </div>
                    <div>
                      <Label>Opening Balance</Label>
                      <Input type="number" value={newContact.opening_balance} onChange={(e) => setNewContact({ ...newContact, opening_balance: parseFloat(e.target.value) || 0 })} />
                    </div>
                    <div>
                      <Label>Balance Type</Label>
                      <Select value={newContact.opening_balance_type} onValueChange={(v) => setNewContact({ ...newContact, opening_balance_type: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="credit">Credit (They owe you)</SelectItem>
                          <SelectItem value="debit">Debit (You owe them)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Tags */}
                  {tags.length > 0 && (
                    <>
                      <Separator />
                      <h4 className="font-medium">Tags</h4>
                      <div className="flex flex-wrap gap-2">
                        {tags.map(tag => (
                          <Badge 
                            key={tag.tag_id}
                            variant={newContact.tags.includes(tag.tag_id) ? "default" : "outline"}
                            className="cursor-pointer"
                            style={newContact.tags.includes(tag.tag_id) ? { backgroundColor: tag.color } : {}}
                            onClick={() => {
                              const newTags = newContact.tags.includes(tag.tag_id)
                                ? newContact.tags.filter(t => t !== tag.tag_id)
                                : [...newContact.tags, tag.tag_id];
                              setNewContact({ ...newContact, tags: newTags });
                            }}
                          >
                            {tag.name}
                          </Badge>
                        ))}
                      </div>
                    </>
                  )}

                  {/* Notes */}
                  <div>
                    <Label>Notes</Label>
                    <Textarea value={newContact.notes} onChange={(e) => setNewContact({ ...newContact, notes: e.target.value })} placeholder="Internal notes about this contact" rows={2} />
                  </div>
                </div>
                <DialogFooter className="border-t border-[rgba(255,255,255,0.07)] pt-4">
                  <Button variant="outline" onClick={() => setShowContactDialog(false)} className="bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]">Cancel</Button>
                  <Button onClick={handleCreateContact} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-contact-submit">Create Contact</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <TableSkeleton columns={7} rows={6} />
          ) : contacts.length === 0 ? (
            <Card className="bg-[#111820] border-[rgba(255,255,255,0.07)]">
              <EmptyState 
                icon={Users}
                title="No contacts found"
                description="Add customers and vendors to manage your business relationships."
                actionLabel="Add Contact"
                onAction={() => setShowContactDialog(true)}
                actionIcon={Plus}
              />
            </Card>
          ) : (
            <div className="bg-[#0D1317] border border-[rgba(255,255,255,0.07)] rounded">
              <ResponsiveTable>
                <thead className="bg-[#111820] border-b border-[rgba(255,255,255,0.07)]">
                  <tr>
                    <th className="px-4 py-3 text-left font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Contact</th>
                    <th className="px-4 py-3 text-left font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Type</th>
                    <th className="px-4 py-3 text-left font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Email / Phone</th>
                    <th className="px-4 py-3 text-left font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">GSTIN</th>
                    <th className="px-4 py-3 text-right font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Balance</th>
                    <th className="px-4 py-3 text-center font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Status</th>
                    <th className="px-4 py-3 text-right font-mono font-medium text-[10px] uppercase tracking-[0.12em] text-[rgba(244,246,240,0.25)]">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts.map(contact => (
                    <tr key={contact.contact_id} className="border-b border-[rgba(255,255,255,0.04)] hover:bg-[rgba(200,255,0,0.03)] cursor-pointer transition-colors duration-150" onClick={() => fetchContactDetail(contact.contact_id)} data-testid={`contact-row-${contact.contact_id}`}>
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-semibold text-[#F4F6F0]">{contact.name}</p>
                          {contact.company_name && <p className="text-[11px] text-[rgba(244,246,240,0.35)]">{contact.company_name}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={contactTypeColors[contact.contact_type]}>{contactTypeLabels[contact.contact_type]}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-[rgba(244,246,240,0.45)]">
                          {contact.email && <p className="text-xs">{contact.email}</p>}
                          {contact.phone && <p className="text-xs">{contact.phone}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[#C8FF00] font-mono text-xs tracking-[0.04em]">{contact.gstin || <span className="text-[rgba(244,246,240,0.20)]">-</span>}</td>
                      <td className="px-4 py-3 text-right">
                        {contact.balance?.receivable > 0 && <p className="text-[#22C55E] text-xs font-semibold">+₹{contact.balance.receivable.toLocaleString('en-IN')}</p>}
                        {contact.balance?.payable > 0 && <p className="text-[#FF3B2F] text-xs font-semibold">-₹{contact.balance.payable.toLocaleString('en-IN')}</p>}
                        {!contact.balance?.receivable && !contact.balance?.payable && <span className="text-[rgba(244,246,240,0.20)]">-</span>}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {contact.is_active ? <CheckCircle className="h-4 w-4 text-[#22C55E] inline" /> : <XCircle className="h-4 w-4 text-[#FF3B2F] inline" />}
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button size="icon" variant="ghost" onClick={() => fetchContactDetail(contact.contact_id)} className="text-[rgba(244,246,240,0.45)] hover:text-[#F4F6F0] hover:bg-[rgba(200,255,0,0.06)]"><Eye className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </ResponsiveTable>
            </div>
          )}
        </TabsContent>

        {/* Tags Tab */}
        <TabsContent value="tags" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showTagDialog} onOpenChange={setShowTagDialog}>
              <DialogTrigger asChild>
                <Button className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold rounded-[3px] gap-2 hover:shadow-[0_0_20px_rgba(200,255,0,0.3)]" data-testid="new-tag-btn">
                  <Plus className="h-4 w-4" /> New Tag
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#111820] border-[rgba(255,255,255,0.13)]">
                <DialogHeader><DialogTitle className="text-[#F4F6F0] font-bold">Create Tag</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div><Label className="font-mono text-[10px] font-medium tracking-[0.16em] uppercase text-[rgba(244,246,240,0.45)]">Name *</Label><Input value={newTag.name} onChange={(e) => setNewTag({ ...newTag, name: e.target.value })} placeholder="Tag name" className="bg-[#111820] border-[rgba(255,255,255,0.13)] text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.20)] focus:border-[#C8FF00]" data-testid="tag-name-input" /></div>
                  <div><Label className="font-mono text-[10px] font-medium tracking-[0.16em] uppercase text-[rgba(244,246,240,0.45)]">Description</Label><Textarea value={newTag.description} onChange={(e) => setNewTag({ ...newTag, description: e.target.value })} placeholder="Description" className="bg-[#111820] border-[rgba(255,255,255,0.13)] text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.20)] focus:border-[#C8FF00]" /></div>
                  <div>
                    <Label className="font-mono text-[10px] font-medium tracking-[0.16em] uppercase text-[rgba(244,246,240,0.45)]">Color</Label>
                    <div className="flex items-center gap-2">
                      <Input type="color" value={newTag.color} onChange={(e) => setNewTag({ ...newTag, color: e.target.value })} className="w-16 h-10 p-1 bg-[#111820] border-[rgba(255,255,255,0.13)]" />
                      <Input value={newTag.color} onChange={(e) => setNewTag({ ...newTag, color: e.target.value })} placeholder="#3B82F6" className="flex-1 bg-[#111820] border-[rgba(255,255,255,0.13)] text-[#F4F6F0] font-mono" />
                    </div>
                  </div>
                </div>
                <DialogFooter className="border-t border-[rgba(255,255,255,0.07)] pt-4">
                  <Button variant="outline" onClick={() => setShowTagDialog(false)} className="bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]">Cancel</Button>
                  <Button onClick={handleCreateTag} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold" data-testid="create-tag-submit">Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {tags.length === 0 ? (
            <Card className="bg-[#111820] border-[rgba(255,255,255,0.07)]"><CardContent className="py-12 text-center"><Tag className="h-12 w-12 mx-auto mb-4 text-[rgba(200,255,0,0.50)]" /><p className="text-[rgba(244,246,240,0.45)]">No tags yet</p></CardContent></Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tags.map(tag => (
                <Card key={tag.tag_id} className="group relative overflow-hidden bg-[#111820] border border-[rgba(255,255,255,0.07)] hover:border-[rgba(200,255,0,0.20)] hover:bg-[#141E27] transition-[background,border-color] duration-200" data-testid={`tag-card-${tag.tag_id}`}>
                  <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#C8FF00] to-[#1AFFE4] scale-x-0 origin-left transition-transform duration-[400ms] ease-[cubic-bezier(0.4,0,0.2,1)] group-hover:scale-x-100" />
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded" style={{ backgroundColor: tag.color }}></div>
                        <CardTitle className="text-lg text-[#F4F6F0]">{tag.name}</CardTitle>
                      </div>
                      <Button size="icon" variant="ghost" onClick={() => handleDeleteTag(tag.tag_id)} className="text-[#FF3B2F] hover:bg-[rgba(255,59,47,0.1)]"><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-[rgba(244,246,240,0.45)] mb-2">{tag.description || "No description"}</p>
                    <Badge className="bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)] border border-[rgba(255,255,255,0.08)]">{tag.contact_count || 0} contacts</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Contact Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={(open) => { setShowDetailDialog(open); if (!open) { setSelectedContact(null); setEditMode(false); } }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-[#111820] border-[rgba(255,255,255,0.13)]">
          {selectedContact && (
            <>
              <DialogHeader className="border-b border-[rgba(255,255,255,0.07)] pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2 text-[#F4F6F0] font-bold">
                      {selectedContact.name}
                      <Badge className={contactTypeColors[selectedContact.contact_type]}>{contactTypeLabels[selectedContact.contact_type]}</Badge>
                      {!selectedContact.is_active && <Badge className="bg-[rgba(255,59,47,0.10)] text-[#FF3B2F] border border-[rgba(255,59,47,0.25)]">Inactive</Badge>}
                    </DialogTitle>
                    {selectedContact.company_name && <DialogDescription className="text-[rgba(244,246,240,0.45)]">{selectedContact.company_name}</DialogDescription>}
                  </div>
                  <div className="flex gap-2">
                    {!editMode ? (
                      <Button size="sm" variant="outline" onClick={openEditMode} className="bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"><Edit className="h-4 w-4 mr-1" /> Edit</Button>
                    ) : (
                      <>
                        <Button size="sm" variant="outline" onClick={() => setEditMode(false)} className="bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]">Cancel</Button>
                        <Button size="sm" onClick={handleUpdateContact} className="bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold">Save</Button>
                      </>
                    )}
                  </div>
                </div>
              </DialogHeader>

              {editMode ? (
                /* Edit Form - Simplified version */
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div><Label>Name *</Label><Input value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} /></div>
                    <div><Label>Company</Label><Input value={newContact.company_name} onChange={(e) => setNewContact({ ...newContact, company_name: e.target.value })} /></div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div><Label>Email</Label><Input value={newContact.email} onChange={(e) => setNewContact({ ...newContact, email: e.target.value })} /></div>
                    <div><Label>Phone</Label><Input value={newContact.phone} onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })} /></div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div><Label>GSTIN</Label><Input value={newContact.gstin} onChange={(e) => setNewContact({ ...newContact, gstin: e.target.value.toUpperCase() })} maxLength={15} /></div>
                    <div><Label>Payment Terms (days)</Label><Input type="number" value={newContact.payment_terms} onChange={(e) => setNewContact({ ...newContact, payment_terms: parseInt(e.target.value) || 0 })} /></div>
                  </div>
                  <div><Label>Notes</Label><Textarea value={newContact.notes} onChange={(e) => setNewContact({ ...newContact, notes: e.target.value })} rows={2} /></div>
                </div>
              ) : (
                /* View Mode */
                <div className="space-y-6 py-4">
                  {/* Contact Info */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {selectedContact.email && <div className="flex items-center gap-2"><Mail className="h-4 w-4 text-[rgba(244,246,240,0.35)]" /><span className="text-sm text-[#F4F6F0]">{selectedContact.email}</span></div>}
                    {selectedContact.phone && <div className="flex items-center gap-2"><Phone className="h-4 w-4 text-[rgba(244,246,240,0.35)]" /><span className="text-sm text-[#F4F6F0]">{selectedContact.phone}</span></div>}
                    {selectedContact.website && <div className="flex items-center gap-2"><Globe className="h-4 w-4 text-[rgba(244,246,240,0.35)]" /><span className="text-sm text-[#F4F6F0] truncate">{selectedContact.website}</span></div>}
                    {selectedContact.gstin && <div className="flex items-center gap-2"><Shield className="h-4 w-4 text-[rgba(244,246,240,0.35)]" /><span className="text-sm font-mono text-[#C8FF00]">{selectedContact.gstin}</span></div>}
                  </div>

                  {/* Balance */}
                  {selectedContact.balance && (
                    <div className="grid grid-cols-3 gap-4">
                      <Card className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.20)]"><CardContent className="pt-4"><p className="font-mono text-[10px] tracking-[0.12em] uppercase text-[rgba(244,246,240,0.45)]">Receivable</p><p className="text-lg font-bold text-[#22C55E]">₹{selectedContact.balance.receivable.toLocaleString('en-IN')}</p></CardContent></Card>
                      <Card className="bg-[rgba(255,59,47,0.08)] border border-[rgba(255,59,47,0.20)]"><CardContent className="pt-4"><p className="font-mono text-[10px] tracking-[0.12em] uppercase text-[rgba(244,246,240,0.45)]">Payable</p><p className="text-lg font-bold text-[#FF3B2F]">₹{selectedContact.balance.payable.toLocaleString('en-IN')}</p></CardContent></Card>
                      <Card className="bg-[#141E27] border border-[rgba(255,255,255,0.07)]"><CardContent className="pt-4"><p className="font-mono text-[10px] tracking-[0.12em] uppercase text-[rgba(244,246,240,0.45)]">Net Balance</p><p className={`text-lg font-bold ${selectedContact.balance.net >= 0 ? 'text-[#22C55E]' : 'text-[#FF3B2F]'}`}>₹{selectedContact.balance.net.toLocaleString('en-IN')}</p></CardContent></Card>
                    </div>
                  )}

                  <Separator className="bg-[rgba(255,255,255,0.07)]" />

                  {/* Contact Persons */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-semibold flex items-center gap-2 text-[#F4F6F0]"><User className="h-4 w-4 text-[rgba(244,246,240,0.45)]" /> Contact Persons ({selectedContact.persons?.length || 0})</h4>
                      <Button size="sm" variant="outline" onClick={() => setShowPersonDialog(true)} className="bg-transparent border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.70)] hover:border-[rgba(200,255,0,0.30)] hover:text-[#F4F6F0]"><UserPlus className="h-4 w-4 mr-1" /> Add</Button>
                    </div>
                    {selectedContact.persons?.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedContact.persons.map(person => (
                          <Card key={person.person_id} className={`bg-[#141E27] border ${person.is_primary ? "border-[rgba(59,158,255,0.30)]" : "border-[rgba(255,255,255,0.07)]"}`}>
                            <CardContent className="pt-4">
                              <div className="flex justify-between">
                                <div>
                                  <p className="font-semibold text-[#F4F6F0]">{person.first_name} {person.last_name} {person.is_primary && <Badge className="ml-2 text-xs bg-[rgba(59,158,255,0.10)] text-[#3B9EFF] border border-[rgba(59,158,255,0.25)]">Primary</Badge>}</p>
                                  {person.designation && <p className="text-xs text-[rgba(244,246,240,0.35)]">{person.designation}</p>}
                                  {person.email && <p className="text-xs text-[rgba(244,246,240,0.45)]">{person.email}</p>}
                                  {person.phone && <p className="text-xs text-[rgba(244,246,240,0.45)]">{person.phone}</p>}
                                </div>
                                <Button size="icon" variant="ghost" onClick={() => handleDeletePerson(person.person_id)} className="text-[#FF3B2F] hover:bg-[rgba(255,59,47,0.1)]"><Trash2 className="h-4 w-4" /></Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    ) : <p className="text-sm text-[rgba(244,246,240,0.35)]">No contact persons added</p>}
                  </div>

                  <Separator className="bg-[rgba(255,255,255,0.07)]" />

                  {/* Addresses */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-medium flex items-center gap-2"><MapPin className="h-4 w-4" /> Addresses ({selectedContact.addresses?.length || 0})</h4>
                      <Button size="sm" variant="outline" onClick={() => setShowAddressDialog(true)}><Home className="h-4 w-4 mr-1" /> Add</Button>
                    </div>
                    {selectedContact.addresses?.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedContact.addresses.map(addr => (
                          <Card key={addr.address_id} className={addr.is_default ? "border-green-300 bg-green-50" : ""}>
                            <CardContent className="pt-4">
                              <div className="flex justify-between">
                                <div>
                                  <p className="font-medium flex items-center gap-2">
                                    {addr.address_type === "billing" ? <Home className="h-4 w-4" /> : <Truck className="h-4 w-4" />}
                                    {addr.address_type === "billing" ? "Billing" : "Shipping"}
                                    {addr.is_default && <Badge className="ml-2 text-xs bg-green-100 text-green-700">Default</Badge>}
                                  </p>
                                  {addr.attention && <p className="text-sm">{addr.attention}</p>}
                                  <p className="text-sm text-gray-600">{[addr.street, addr.street2].filter(Boolean).join(", ")}</p>
                                  <p className="text-sm text-gray-600">{[addr.city, addr.state, addr.zip_code].filter(Boolean).join(", ")}</p>
                                  <p className="text-sm text-gray-500">{addr.country}</p>
                                </div>
                                <Button size="icon" variant="ghost" onClick={() => handleDeleteAddress(addr.address_id)}><Trash2 className="h-4 w-4 text-red-400" /></Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    ) : <p className="text-sm text-gray-500">No addresses added</p>}
                  </div>

                  <Separator />

                  {/* Actions */}
                  <div className="flex flex-wrap gap-2">
                    {selectedContact.is_active ? (
                      <Button variant="outline" size="sm" onClick={() => handleToggleActive(selectedContact.contact_id, false)}><XCircle className="h-4 w-4 mr-1" /> Deactivate</Button>
                    ) : (
                      <Button variant="outline" size="sm" onClick={() => handleToggleActive(selectedContact.contact_id, true)}><CheckCircle className="h-4 w-4 mr-1" /> Activate</Button>
                    )}
                    {selectedContact.email && (
                      <>
                        {selectedContact.portal_enabled ? (
                          <Button variant="outline" size="sm" onClick={() => handleDisablePortal(selectedContact.contact_id)}><Key className="h-4 w-4 mr-1" /> Disable Portal</Button>
                        ) : (
                          <Button variant="outline" size="sm" onClick={() => handleEnablePortal(selectedContact.contact_id)}><Key className="h-4 w-4 mr-1" /> Enable Portal</Button>
                        )}
                        <Button variant="outline" size="sm" onClick={() => handleEmailStatement(selectedContact.contact_id)}><Send className="h-4 w-4 mr-1" /> Email Statement</Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => {
                            setShowDetailDialog(false);
                            navigate(`/estimates?customer_id=${selectedContact.contact_id}&customer_name=${encodeURIComponent(selectedContact.name)}`);
                          }}
                          className="bg-blue-50 hover:bg-blue-100 border-blue-200"
                          data-testid="quick-quote-btn"
                        >
                          <FileText className="h-4 w-4 mr-1" /> Quick Quote
                        </Button>
                      </>
                    )}
                    <Button variant="destructive" size="sm" onClick={() => handleDeleteContact(selectedContact.contact_id)}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                  </div>

                  {/* Transaction History */}
                  {(contactTransactions.length > 0 || transactionSummary) && (
                    <>
                      <Separator />
                      <div>
                        <h4 className="font-medium flex items-center gap-2 mb-3"><History className="h-4 w-4" /> Transaction History</h4>
                        
                        {transactionSummary && (
                          <div className="grid grid-cols-4 gap-3 mb-4">
                            <div className="bg-blue-50 rounded-lg p-2 text-center">
                              <p className="text-xs text-gray-500">Total Invoiced</p>
                              <p className="font-bold text-blue-700">₹{transactionSummary.total_invoiced?.toLocaleString('en-IN') || 0}</p>
                            </div>
                            <div className="bg-orange-50 rounded-lg p-2 text-center">
                              <p className="text-xs text-gray-500">Total Billed</p>
                              <p className="font-bold text-orange-700">₹{transactionSummary.total_billed?.toLocaleString('en-IN') || 0}</p>
                            </div>
                            <div className="bg-red-50 rounded-lg p-2 text-center">
                              <p className="text-xs text-gray-500">Outstanding</p>
                              <p className="font-bold text-red-700">₹{transactionSummary.total_outstanding?.toLocaleString('en-IN') || 0}</p>
                            </div>
                            <div className="bg-gray-100 rounded-lg p-2 text-center">
                              <p className="text-xs text-gray-500">Transactions</p>
                              <p className="font-bold">{transactionSummary.transaction_count || 0}</p>
                            </div>
                          </div>
                        )}

                        {contactTransactions.length > 0 && (
                          <div className="border rounded-lg overflow-hidden">
                            <table className="w-full text-xs">
                              <thead className="bg-gray-50">
                                <tr>
                                  <th className="px-3 py-2 text-left">Type</th>
                                  <th className="px-3 py-2 text-left">Number</th>
                                  <th className="px-3 py-2 text-left">Date</th>
                                  <th className="px-3 py-2 text-right">Amount</th>
                                  <th className="px-3 py-2 text-center">Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {contactTransactions.slice(0, 5).map((txn, idx) => (
                                  <tr key={idx} className="border-t">
                                    <td className="px-3 py-2">
                                      <Badge variant="outline" className="text-xs capitalize">
                                        {txn.type?.replace('_', ' ')}
                                      </Badge>
                                    </td>
                                    <td className="px-3 py-2 font-mono">{txn.transaction_number || '-'}</td>
                                    <td className="px-3 py-2">{txn.date ? new Date(txn.date).toLocaleDateString('en-IN') : '-'}</td>
                                    <td className="px-3 py-2 text-right font-medium">₹{(txn.total || 0).toLocaleString('en-IN')}</td>
                                    <td className="px-3 py-2 text-center">
                                      <Badge className={`text-xs ${txn.status === 'paid' ? 'bg-green-100 text-green-700' : txn.status === 'overdue' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                                        {txn.status || 'N/A'}
                                      </Badge>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {contactTransactions.length > 5 && (
                              <p className="text-xs text-gray-500 text-center py-2">+ {contactTransactions.length - 5} more transactions</p>
                            )}
                          </div>
                        )}
                      </div>
                    </>
                  )}

                  {/* Usage Stats (Legacy) */}
                  {selectedContact.usage && selectedContact.usage.is_used && !contactTransactions.length && (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-2">Transaction Summary</p>
                      <div className="flex gap-4 text-xs">
                        {selectedContact.usage.invoices > 0 && <span>Invoices: {selectedContact.usage.invoices}</span>}
                        {selectedContact.usage.bills > 0 && <span>Bills: {selectedContact.usage.bills}</span>}
                        {selectedContact.usage.estimates > 0 && <span>Estimates: {selectedContact.usage.estimates}</span>}
                        {selectedContact.usage.purchase_orders > 0 && <span>POs: {selectedContact.usage.purchase_orders}</span>}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Person Dialog */}
      <Dialog open={showPersonDialog} onOpenChange={setShowPersonDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Contact Person</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>First Name *</Label><Input value={newPerson.first_name} onChange={(e) => setNewPerson({ ...newPerson, first_name: e.target.value })} /></div>
              <div><Label>Last Name</Label><Input value={newPerson.last_name} onChange={(e) => setNewPerson({ ...newPerson, last_name: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Email</Label><Input value={newPerson.email} onChange={(e) => setNewPerson({ ...newPerson, email: e.target.value })} /></div>
              <div><Label>Phone</Label><Input value={newPerson.phone} onChange={(e) => setNewPerson({ ...newPerson, phone: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Designation</Label><Input value={newPerson.designation} onChange={(e) => setNewPerson({ ...newPerson, designation: e.target.value })} placeholder="e.g. Manager" /></div>
              <div><Label>Department</Label><Input value={newPerson.department} onChange={(e) => setNewPerson({ ...newPerson, department: e.target.value })} placeholder="e.g. Sales" /></div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={newPerson.is_primary} onCheckedChange={(checked) => setNewPerson({ ...newPerson, is_primary: checked })} />
              <Label>Primary Contact</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPersonDialog(false)}>Cancel</Button>
            <Button onClick={handleAddPerson} className="bg-[#22EDA9] text-black">Add Person</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Address Dialog */}
      <Dialog open={showAddressDialog} onOpenChange={setShowAddressDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add Address</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Address Type *</Label>
                <Select value={newAddress.address_type} onValueChange={(v) => setNewAddress({ ...newAddress, address_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="billing">Billing</SelectItem>
                    <SelectItem value="shipping">Shipping</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Attention</Label><Input value={newAddress.attention} onChange={(e) => setNewAddress({ ...newAddress, attention: e.target.value })} placeholder="Attn: Name" /></div>
            </div>
            <div><Label>Street Address</Label><Input value={newAddress.street} onChange={(e) => setNewAddress({ ...newAddress, street: e.target.value })} placeholder="Street line 1" /></div>
            <div><Label>Street Address 2</Label><Input value={newAddress.street2} onChange={(e) => setNewAddress({ ...newAddress, street2: e.target.value })} placeholder="Street line 2 (optional)" /></div>
            <div className="grid grid-cols-3 gap-4">
              <div><Label>City</Label><Input value={newAddress.city} onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })} /></div>
              <div>
                <Label>State</Label>
                <Select value={newAddress.state_code || "none"} onValueChange={(v) => {
                  const stateName = states.find(s => s.code === v)?.name || "";
                  setNewAddress({ ...newAddress, state_code: v === "none" ? "" : v, state: stateName });
                }}>
                  <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Select State</SelectItem>
                    {states.map(s => <SelectItem key={s.code} value={s.code}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div><Label>ZIP Code</Label><Input value={newAddress.zip_code} onChange={(e) => setNewAddress({ ...newAddress, zip_code: e.target.value })} /></div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={newAddress.is_default} onCheckedChange={(checked) => setNewAddress({ ...newAddress, is_default: checked })} />
              <Label>Set as default {newAddress.address_type} address</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddressDialog(false)}>Cancel</Button>
            <Button onClick={handleAddAddress} className="bg-[#22EDA9] text-black">Add Address</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Contact Close Confirmation */}
      <FormCloseConfirmDialog
        open={contactPersistence.showCloseConfirm}
        onClose={() => contactPersistence.setShowCloseConfirm(false)}
        onSave={async () => {
          if (editMode && selectedContact) {
            await handleUpdateContact();
          } else {
            await handleCreateContact();
          }
        }}
        onDiscard={() => {
          contactPersistence.clearSavedData();
          setShowContactDialog(false);
          resetContactForm();
        }}
        isSaving={false}
        entityName="Contact"
      />
    </div>
  );
}
