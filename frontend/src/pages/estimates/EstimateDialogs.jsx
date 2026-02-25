/**
 * EstimateDialogs — All secondary dialogs: Send, Share, Attachments, Preferences,
 * Import, Bulk Action, Custom Fields, Templates, Edit, Quick Add Item, Close Confirm.
 * Zero logic changes — pure extraction.
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Send, Share2, Paperclip, FileText, Upload, Download, X, Copy, Settings,
  FileUp, ListChecks, AlertTriangle, Edit, Plus, LayoutTemplate, Package,
  Trash2, IndianRupee, Percent
} from "lucide-react";
import { AutoSaveIndicator, DraftRecoveryBanner, FormCloseConfirmDialog } from "@/components/UnsavedChangesDialog";

export function SendDialog({ open, onOpenChange, sendEmail, setSendEmail, sendMessage, setSendMessage, onSend }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Send className="h-5 w-5" /> Send Estimate</DialogTitle>
          <DialogDescription>Send this estimate to the customer via email</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div>
            <Label>Email To</Label>
            <Input value={sendEmail} onChange={(e) => setSendEmail(e.target.value)} placeholder="customer@example.com" type="email" data-testid="send-email-input" />
          </div>
          <div>
            <Label>Message (optional)</Label>
            <Textarea value={sendMessage} onChange={(e) => setSendMessage(e.target.value)} placeholder="Add a personal note..." rows={3} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onSend} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="send-estimate-btn"><Send className="h-4 w-4 mr-2" /> Send</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ShareDialog({ open, onOpenChange, shareLink, setShareLink, shareConfig, setShareConfig, shareLoading, onCreateShareLink, onCopyShareLink }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Share2 className="h-5 w-5" /> Share Estimate</DialogTitle>
          <DialogDescription>Create a public link for this estimate</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {!shareLink ? (
            <>
              <div className="space-y-4">
                <div>
                  <Label>Link Expiry (days)</Label>
                  <Input type="number" value={shareConfig.expiry_days} onChange={(e) => setShareConfig({...shareConfig, expiry_days: parseInt(e.target.value) || 30})} min={1} max={365} />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Allow Customer to Accept</Label>
                  <input type="checkbox" checked={shareConfig.allow_accept} onChange={(e) => setShareConfig({...shareConfig, allow_accept: e.target.checked})} className="h-4 w-4" />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Allow Customer to Decline</Label>
                  <input type="checkbox" checked={shareConfig.allow_decline} onChange={(e) => setShareConfig({...shareConfig, allow_decline: e.target.checked})} className="h-4 w-4" />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Password Protected</Label>
                  <input type="checkbox" checked={shareConfig.password_protected} onChange={(e) => setShareConfig({...shareConfig, password_protected: e.target.checked})} className="h-4 w-4" />
                </div>
                {shareConfig.password_protected && (
                  <div><Label>Password</Label><Input type="password" value={shareConfig.password} onChange={(e) => setShareConfig({...shareConfig, password: e.target.value})} placeholder="Enter password" /></div>
                )}
              </div>
              <Button onClick={onCreateShareLink} disabled={shareLoading} className="w-full bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="generate-share-link-btn">
                {shareLoading ? "Generating..." : "Generate Share Link"}
              </Button>
            </>
          ) : (
            <div className="space-y-4">
              <div className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.25)] rounded-lg p-4">
                <p className="text-sm text-[#22C55E] font-medium mb-2">Share link created successfully!</p>
                <div className="flex items-center gap-2">
                  <Input value={shareLink.full_url} readOnly className="text-xs font-mono" />
                  <Button size="sm" variant="outline" onClick={onCopyShareLink}><Copy className="h-4 w-4" /></Button>
                </div>
              </div>
              <div className="text-xs text-[rgba(244,246,240,0.45)] space-y-1">
                <p><strong>Expires:</strong> {new Date(shareLink.expires_at).toLocaleDateString('en-IN')}</p>
                <p><strong>Can Accept:</strong> {shareLink.allow_accept ? 'Yes' : 'No'}</p>
                <p><strong>Can Decline:</strong> {shareLink.allow_decline ? 'Yes' : 'No'}</p>
                <p><strong>Password Protected:</strong> {shareLink.password_protected ? 'Yes' : 'No'}</p>
              </div>
              <Button variant="outline" onClick={() => setShareLink(null)} className="w-full">Create Another Link</Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function AttachmentsDialog({ open, onOpenChange, attachments, uploading, onUpload, onDelete, onDownload }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Paperclip className="h-5 w-5" /> Attachments</DialogTitle>
          <DialogDescription>Upload files to attach to this estimate (max 3 files, 10MB each)</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="border-2 border-dashed border-[rgba(255,255,255,0.13)] rounded-lg p-4 text-center">
            <input type="file" id="attachment-upload" className="hidden" onChange={onUpload} accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt,.csv" />
            <label htmlFor="attachment-upload" className="cursor-pointer">
              <Upload className="h-8 w-8 mx-auto text-[rgba(244,246,240,0.25)] mb-2" />
              <p className="text-sm text-[rgba(244,246,240,0.45)]">{uploading ? "Uploading..." : "Click to upload a file"}</p>
              <p className="text-xs text-[rgba(244,246,240,0.25)] mt-1">PDF, Images, Word, Excel (max 10MB)</p>
            </label>
          </div>
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
                    <Button size="sm" variant="ghost" onClick={() => onDownload(att.attachment_id, att.filename)}><Download className="h-4 w-4" /></Button>
                    <Button size="sm" variant="ghost" className="text-red-500 hover:text-[#FF3B2F]" onClick={() => onDelete(att.attachment_id)}><X className="h-4 w-4" /></Button>
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
  );
}

export function PreferencesDialog({ open, onOpenChange, preferences, setPreferences, onSave }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Settings className="h-5 w-5" /> Estimate Preferences</DialogTitle>
          <DialogDescription>Configure automation and workflow settings for estimates</DialogDescription>
        </DialogHeader>
        <div className="space-y-6 py-4">
          <div className="space-y-4">
            <h4 className="font-medium text-sm">Automatic Conversion</h4>
            <div className="flex items-center justify-between">
              <div><Label>Auto-convert accepted estimates</Label><p className="text-xs text-[rgba(244,246,240,0.45)]">Automatically create invoices when estimates are accepted</p></div>
              <input type="checkbox" checked={preferences.auto_convert_on_accept} onChange={(e) => setPreferences({...preferences, auto_convert_on_accept: e.target.checked})} className="h-4 w-4" />
            </div>
            {preferences.auto_convert_on_accept && (
              <div>
                <Label>Convert to</Label>
                <Select value={preferences.auto_convert_to} onValueChange={(v) => setPreferences({...preferences, auto_convert_to: v})}>
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
          <div className="space-y-4">
            <h4 className="font-medium text-sm">Public Link Settings</h4>
            <div className="flex items-center justify-between"><Label>Allow customers to accept via link</Label><input type="checkbox" checked={preferences.allow_public_accept} onChange={(e) => setPreferences({...preferences, allow_public_accept: e.target.checked})} className="h-4 w-4" /></div>
            <div className="flex items-center justify-between"><Label>Allow customers to decline via link</Label><input type="checkbox" checked={preferences.allow_public_decline} onChange={(e) => setPreferences({...preferences, allow_public_decline: e.target.checked})} className="h-4 w-4" /></div>
          </div>
          <Separator />
          <div className="space-y-4">
            <h4 className="font-medium text-sm">Notifications</h4>
            <div className="flex items-center justify-between"><Label>Notify when customer views estimate</Label><input type="checkbox" checked={preferences.notify_on_view} onChange={(e) => setPreferences({...preferences, notify_on_view: e.target.checked})} className="h-4 w-4" /></div>
            <div className="flex items-center justify-between"><Label>Notify when customer accepts</Label><input type="checkbox" checked={preferences.notify_on_accept} onChange={(e) => setPreferences({...preferences, notify_on_accept: e.target.checked})} className="h-4 w-4" /></div>
            <div className="flex items-center justify-between"><Label>Notify when customer declines</Label><input type="checkbox" checked={preferences.notify_on_decline} onChange={(e) => setPreferences({...preferences, notify_on_decline: e.target.checked})} className="h-4 w-4" /></div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onSave} className="bg-[#C8FF00] text-[#080C0F] font-bold">Save Preferences</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ImportDialog({ open, onOpenChange, importFile, setImportFile, importing, onImport, onDownloadTemplate }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><FileUp className="h-5 w-5" /> Import Estimates</DialogTitle>
          <DialogDescription>Upload a CSV file to import estimates in bulk</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="border-2 border-dashed border-[rgba(255,255,255,0.13)] rounded-lg p-6 text-center">
            <input type="file" id="import-file" className="hidden" accept=".csv" onChange={(e) => setImportFile(e.target.files[0])} />
            <label htmlFor="import-file" className="cursor-pointer">
              <Upload className="h-10 w-10 mx-auto text-[rgba(244,246,240,0.25)] mb-2" />
              <p className="text-sm text-[rgba(244,246,240,0.45)]">{importFile ? importFile.name : "Click to select CSV file"}</p>
            </label>
          </div>
          <Button variant="outline" onClick={onDownloadTemplate} className="w-full gap-2"><Download className="h-4 w-4" /> Download Template</Button>
          <p className="text-xs text-[rgba(244,246,240,0.45)]">Template includes: customer_name, date, item_name, quantity, rate, tax_percentage</p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { onOpenChange(false); setImportFile(null); }}>Cancel</Button>
          <Button onClick={onImport} disabled={!importFile || importing} className="bg-[#C8FF00] text-[#080C0F] font-bold">{importing ? "Importing..." : "Import"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function BulkActionDialog({ open, onOpenChange, selectedIds, bulkAction, setBulkAction, onBulkAction }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
            <div className="bg-[rgba(255,140,0,0.08)] p-3 rounded-lg text-sm text-[#FF8C00]"><AlertTriangle className="h-4 w-4 inline mr-2" />Voiding estimates is irreversible. Converted estimates cannot be voided.</div>
          )}
          {bulkAction === "delete" && (
            <div className="bg-[rgba(255,59,47,0.08)] p-3 rounded-lg text-sm text-[#FF3B2F]"><AlertTriangle className="h-4 w-4 inline mr-2" />Only draft estimates will be deleted. This action is irreversible.</div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { onOpenChange(false); setBulkAction(""); }}>Cancel</Button>
          <Button onClick={onBulkAction} disabled={!bulkAction} className={bulkAction === "delete" || bulkAction === "void" ? "bg-[#FF3B2F] hover:bg-[rgba(255,59,47,0.85)]" : "bg-[#C8FF00] text-[#080C0F] font-bold"}>Apply to {selectedIds.length} Estimates</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function CustomFieldsDialog({ open, onOpenChange, customFields, newCustomField, setNewCustomField, onAdd, onDelete }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Edit className="h-5 w-5" /> Custom Fields</DialogTitle>
          <DialogDescription>Manage custom fields for estimates</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
          {customFields.length > 0 ? (
            <div className="space-y-2">
              <Label>Existing Fields</Label>
              {customFields.map((field, idx) => (
                <div key={idx} className="flex items-center justify-between bg-[#111820] rounded-lg p-3">
                  <div>
                    <p className="font-medium text-sm">{field.field_name}</p>
                    <p className="text-xs text-[rgba(244,246,240,0.45)]">{field.field_type} {field.is_required && "• Required"} {field.show_in_pdf && " • PDF"} {field.show_in_portal && " • Portal"}</p>
                  </div>
                  <Button size="sm" variant="ghost" className="text-red-500 hover:text-[#FF3B2F]" onClick={() => onDelete(field.field_name)}><Trash2 className="h-4 w-4" /></Button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[rgba(244,246,240,0.45)] text-center py-4">No custom fields defined yet</p>
          )}
          <Separator />
          <div className="space-y-3">
            <Label>Add New Field</Label>
            <div className="grid grid-cols-2 gap-3">
              <div><Label className="text-xs">Field Name</Label><Input value={newCustomField.field_name} onChange={(e) => setNewCustomField({...newCustomField, field_name: e.target.value})} placeholder="e.g., Project Code" /></div>
              <div><Label className="text-xs">Type</Label>
                <Select value={newCustomField.field_type} onValueChange={(v) => setNewCustomField({...newCustomField, field_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text">Text</SelectItem><SelectItem value="number">Number</SelectItem>
                    <SelectItem value="date">Date</SelectItem><SelectItem value="checkbox">Checkbox</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newCustomField.is_required} onChange={(e) => setNewCustomField({...newCustomField, is_required: e.target.checked})} className="h-4 w-4" />Required</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newCustomField.show_in_pdf} onChange={(e) => setNewCustomField({...newCustomField, show_in_pdf: e.target.checked})} className="h-4 w-4" />Show in PDF</label>
            </div>
            <Button onClick={onAdd} className="w-full bg-[#C8FF00] text-[#080C0F] font-bold"><Plus className="h-4 w-4 mr-2" /> Add Field</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function TemplatesDialog({ open, onOpenChange, templates, selectedTemplate, setSelectedTemplate, selectedEstimate, onDownloadWithTemplate }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><LayoutTemplate className="h-5 w-5" /> PDF Templates</DialogTitle>
          <DialogDescription>Choose a template style for PDF generation</DialogDescription>
        </DialogHeader>
        <div className="space-y-3 py-4">
          {templates.map((template) => (
            <div key={template.id} className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${selectedTemplate === template.id ? 'border-[#C8FF00] bg-[rgba(34,197,94,0.08)]' : 'border-[rgba(255,255,255,0.07)] hover:border-[rgba(255,255,255,0.13)]'}`} onClick={() => setSelectedTemplate(template.id)}>
              <div className="flex items-center justify-between">
                <div><p className="font-medium">{template.name}</p><p className="text-sm text-[rgba(244,246,240,0.45)]">{template.description}</p></div>
                <div className="w-8 h-8 rounded-full" style={{ backgroundColor: template.primary_color }} />
              </div>
            </div>
          ))}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
          {selectedEstimate && (
            <Button onClick={() => { onDownloadWithTemplate(selectedEstimate.estimate_id, selectedTemplate); onOpenChange(false); }} className="bg-[#C8FF00] text-[#080C0F] font-bold">
              <Download className="h-4 w-4 mr-2" /> Download with {selectedTemplate}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function EditEstimateDialog({ state, handlers }) {
  const {
    showEditDialog, editEstimate, setEditEstimate, editEstimatePersistence,
    editItemSearch, setEditItemSearch, editSearchResults, setEditSearchResults,
    editActiveItemIndex, setEditActiveItemIndex, items, showAddItemDialog, setShowAddItemDialog,
  } = state;
  const {
    setShowEditDialog, handleUpdateEstimate, updateEditLineItem, addEditLineItem,
    selectEditItem, removeEditLineItem,
  } = handlers;

  return (
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
            <AutoSaveIndicator lastSaved={editEstimatePersistence.lastSaved} isSaving={editEstimatePersistence.isSaving} isDirty={editEstimatePersistence.isDirty} />
          </div>
        </DialogHeader>

        {editEstimate && (
          <div className="space-y-4 py-4 flex-1 overflow-y-auto min-h-0">
            <div className="grid grid-cols-3 gap-4">
              <div><Label>Reference Number</Label><Input value={editEstimate.reference_number} onChange={(e) => setEditEstimate({...editEstimate, reference_number: e.target.value})} /></div>
              <div><Label>Estimate Date</Label><Input type="date" value={editEstimate.date} onChange={(e) => setEditEstimate({...editEstimate, date: e.target.value})} /></div>
              <div><Label>Expiry Date</Label><Input type="date" value={editEstimate.expiry_date} onChange={(e) => setEditEstimate({...editEstimate, expiry_date: e.target.value})} /></div>
            </div>

            {/* Line Items */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <Label className="flex items-center gap-2"><Package className="h-4 w-4" /> Item Table</Label>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setShowAddItemDialog(true)}><Plus className="h-4 w-4 mr-1" /> New Item</Button>
                  <Button size="sm" variant="outline" onClick={addEditLineItem}><Plus className="h-4 w-4 mr-1" /> Add Row</Button>
                </div>
              </div>
              <div className="border rounded-lg overflow-visible">
                <table className="w-full text-sm">
                  <thead className="bg-[#111820] border-b">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium w-[250px]">ITEM DETAILS</th>
                      <th className="px-3 py-2 text-center font-medium w-20">QTY</th>
                      <th className="px-3 py-2 text-center font-medium w-24"><div className="flex items-center justify-center gap-1">RATE <IndianRupee className="h-3 w-3" /></div></th>
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
                      if (item.discount_type === 'amount') discountAmount = item.discount_value || 0;
                      else discountAmount = (grossAmount * (item.discount_percent || 0)) / 100;
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
                                    setEditActiveItemIndex(idx); setEditItemSearch(value);
                                    updateEditLineItem(idx, "name", value); updateEditLineItem(idx, "item_id", "");
                                    if (value.length >= 1) {
                                      const filtered = items.filter(i => i.name?.toLowerCase().includes(value.toLowerCase()) || i.sku?.toLowerCase().includes(value.toLowerCase()));
                                      setEditSearchResults(filtered);
                                    } else { setEditSearchResults([]); }
                                  }}
                                  onFocus={() => { setEditActiveItemIndex(idx); setEditItemSearch(item.name || ""); }}
                                  placeholder="Type or search item..."
                                  className="border-0 bg-transparent focus:ring-1 h-8 text-sm"
                                  data-testid={`edit-item-search-${idx}`}
                                />
                              </div>
                              {editActiveItemIndex === idx && editItemSearch.length >= 1 && !item.item_id && editSearchResults.length > 0 && (
                                <div className="absolute z-50 left-0 right-0 mt-1 bg-[#111820] border border-[rgba(255,255,255,0.13)] rounded max-h-48 overflow-y-auto">
                                  {editSearchResults.slice(0, 8).map(searchItem => (
                                    <div key={searchItem.item_id} className="px-3 py-2 hover:bg-[rgba(59,158,255,0.08)] cursor-pointer flex justify-between items-center" onClick={() => selectEditItem(searchItem, idx)}>
                                      <div><p className="font-medium text-sm">{searchItem.name}</p><p className="text-xs text-[rgba(244,246,240,0.45)]">SKU: {searchItem.sku || 'N/A'}</p></div>
                                      <span className="text-sm font-mono text-[rgba(244,246,240,0.45)]">₹{(searchItem.rate || searchItem.sales_rate || 0).toLocaleString()}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {item.item_id && <p className="text-xs text-[rgba(244,246,240,0.25)] mt-0.5 ml-5">SKU: {item.sku || item.item_id?.slice(0, 8)}</p>}
                            </div>
                          </td>
                          <td className="px-3 py-2"><Input type="number" value={item.quantity} onChange={(e) => updateEditLineItem(idx, "quantity", parseFloat(e.target.value) || 1)} className="h-8 text-center" min="1" /></td>
                          <td className="px-3 py-2"><Input type="number" value={item.rate} onChange={(e) => updateEditLineItem(idx, "rate", parseFloat(e.target.value) || 0)} className="h-8 text-center" min="0" /></td>
                          <td className="px-3 py-2">
                            <div className="flex items-center gap-1">
                              <Select value={item.discount_type || "percent"} onValueChange={(v) => updateEditLineItem(idx, "discount_type", v)}>
                                <SelectTrigger className="w-12 h-8 px-1"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="percent"><Percent className="h-3 w-3" /></SelectItem>
                                  <SelectItem value="amount"><IndianRupee className="h-3 w-3" /></SelectItem>
                                </SelectContent>
                              </Select>
                              <Input type="number" className="w-16 h-8 text-center" value={item.discount_type === 'amount' ? (item.discount_value || 0) : (item.discount_percent || 0)} onChange={(e) => {
                                const val = parseFloat(e.target.value) || 0;
                                if (item.discount_type === 'amount') updateEditLineItem(idx, "discount_value", val);
                                else updateEditLineItem(idx, "discount_percent", val);
                              }} min="0" />
                            </div>
                          </td>
                          <td className="px-3 py-2">
                            <Select value={String(item.tax_percentage || 18)} onValueChange={(v) => updateEditLineItem(idx, "tax_percentage", parseFloat(v))}>
                              <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="0">0%</SelectItem><SelectItem value="5">5%</SelectItem>
                                <SelectItem value="12">12%</SelectItem><SelectItem value="18">18%</SelectItem><SelectItem value="28">28%</SelectItem>
                              </SelectContent>
                            </Select>
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-medium">₹{total.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                          <td className="px-3 py-2 text-center"><Button size="icon" variant="ghost" onClick={() => removeEditLineItem(idx)} className="h-7 w-7"><Trash2 className="h-4 w-4 text-red-500" /></Button></td>
                        </tr>
                      );
                    })}
                    {editEstimate.line_items.length === 0 && (
                      <tr><td colSpan={7} className="px-3 py-8 text-center text-[rgba(244,246,240,0.25)]">No items added. Click "+ Add Row" to start.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div><Label>Customer Notes</Label><Textarea value={editEstimate.notes} onChange={(e) => setEditEstimate({...editEstimate, notes: e.target.value})} rows={2} /></div>
              <div><Label>Terms & Conditions</Label><Textarea value={editEstimate.terms_and_conditions} onChange={(e) => setEditEstimate({...editEstimate, terms_and_conditions: e.target.value})} rows={2} /></div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Discount</Label>
                <div className="flex gap-2">
                  <Select value={editEstimate.discount_type} onValueChange={(v) => setEditEstimate({...editEstimate, discount_type: v})}>
                    <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="none">None</SelectItem><SelectItem value="percent">%</SelectItem><SelectItem value="amount">₹</SelectItem></SelectContent>
                  </Select>
                  <Input type="number" value={editEstimate.discount_value} onChange={(e) => setEditEstimate({...editEstimate, discount_value: parseFloat(e.target.value) || 0})} />
                </div>
              </div>
              <div><Label>Shipping Charge</Label><Input type="number" value={editEstimate.shipping_charge} onChange={(e) => setEditEstimate({...editEstimate, shipping_charge: parseFloat(e.target.value) || 0})} /></div>
              <div><Label>Adjustment</Label><Input type="number" value={editEstimate.adjustment} onChange={(e) => setEditEstimate({...editEstimate, adjustment: parseFloat(e.target.value) || 0})} /></div>
            </div>
          </div>
        )}

        <DialogFooter className="flex-shrink-0 border-t pt-4 mt-4">
          <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdateEstimate} className="bg-[#C8FF00] text-[#080C0F] font-bold" data-testid="save-estimate-btn">Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function QuickAddItemDialog({ open, onOpenChange, quickAddItem, setQuickAddItem, newLineItem, onQuickAdd }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Package className="h-5 w-5" /> Quick Add Item</DialogTitle>
          <DialogDescription>Add a new item to your inventory</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div><Label>Item Name *</Label><Input value={quickAddItem.name} onChange={(e) => setQuickAddItem({...quickAddItem, name: e.target.value})} placeholder="Enter item name" autoFocus /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>SKU</Label><Input value={quickAddItem.sku} onChange={(e) => setQuickAddItem({...quickAddItem, sku: e.target.value})} placeholder="Auto-generated if empty" /></div>
            <div><Label>Type</Label>
              <Select value={quickAddItem.item_type} onValueChange={(v) => setQuickAddItem({...quickAddItem, item_type: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="product">Product</SelectItem><SelectItem value="service">Service</SelectItem></SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Rate (₹)</Label><Input type="number" value={quickAddItem.rate} onChange={(e) => setQuickAddItem({...quickAddItem, rate: parseFloat(e.target.value) || 0})} placeholder="0.00" /></div>
            <div><Label>Unit</Label>
              <Select value={quickAddItem.unit} onValueChange={(v) => setQuickAddItem({...quickAddItem, unit: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="pcs">Pieces (pcs)</SelectItem><SelectItem value="kg">Kilogram (kg)</SelectItem>
                  <SelectItem value="ltr">Liter (ltr)</SelectItem><SelectItem value="mtr">Meter (mtr)</SelectItem>
                  <SelectItem value="box">Box</SelectItem><SelectItem value="hrs">Hours (hrs)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label>GST Rate</Label>
              <Select value={String(quickAddItem.tax_percentage)} onValueChange={(v) => setQuickAddItem({...quickAddItem, tax_percentage: parseFloat(v)})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="0">GST 0%</SelectItem><SelectItem value="5">GST 5%</SelectItem>
                  <SelectItem value="12">GST 12%</SelectItem><SelectItem value="18">GST 18%</SelectItem><SelectItem value="28">GST 28%</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>HSN Code</Label><Input value={quickAddItem.hsn_code} onChange={(e) => setQuickAddItem({...quickAddItem, hsn_code: e.target.value})} placeholder="Optional" /></div>
          </div>
          <div><Label>Description</Label><Textarea value={quickAddItem.description} onChange={(e) => setQuickAddItem({...quickAddItem, description: e.target.value})} placeholder="Item description (optional)" rows={2} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => {
            onOpenChange(false);
            setQuickAddItem({ name: newLineItem.name || "", sku: "", rate: 0, description: "", unit: "pcs", tax_percentage: 18, hsn_code: "", item_type: "product" });
          }}>Cancel</Button>
          <Button onClick={onQuickAdd} className="bg-[#C8FF00] text-[#080C0F] font-bold"><Plus className="h-4 w-4 mr-2" /> Create & Add</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function EditCloseConfirmDialog({ persistence, onSave, onDiscard }) {
  return (
    <FormCloseConfirmDialog
      open={persistence.showCloseConfirm}
      onClose={() => persistence.setShowCloseConfirm(false)}
      onSave={onSave}
      onDiscard={onDiscard}
      isSaving={false}
      entityName="Estimate"
    />
  );
}
