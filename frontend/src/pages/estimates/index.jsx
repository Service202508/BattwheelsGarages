/**
 * Estimates — Thin orchestrator that wires the useEstimates hook to all sub-components.
 * Manages the top-level Tabs wrapper so all TabsContent children share context.
 * Zero logic changes — all state and handlers live in useEstimates.js.
 */
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Ticket } from "lucide-react";
import { useEstimates } from "./useEstimates";
import { EstimatesSummary, EstimatesTabContent, TicketEstimatesTabContent } from "./EstimatesTable";
import { EstimateDetail } from "./EstimateDetail";
import { EstimateModal } from "./EstimateModal";
import {
  SendDialog, ShareDialog, AttachmentsDialog, PreferencesDialog,
  ImportDialog, BulkActionDialog, CustomFieldsDialog, TemplatesDialog,
  EditEstimateDialog, QuickAddItemDialog, EditCloseConfirmDialog,
} from "./EstimateDialogs";

export default function Estimates() {
  const hook = useEstimates();

  const summaryHandlers = {
    setStatusFilter: hook.setStatusFilter, fetchEstimates: hook.fetchEstimates,
    handleExport: hook.handleExport, setShowImportDialog: hook.setShowImportDialog,
    setShowBulkActionDialog: hook.setShowBulkActionDialog,
    setShowCustomFieldsDialog: hook.setShowCustomFieldsDialog,
    setShowTemplateDialog: hook.setShowTemplateDialog,
    setShowPreferencesDialog: hook.setShowPreferencesDialog,
    fetchCustomFields: hook.fetchCustomFields, fetchPdfTemplates: hook.fetchPdfTemplates,
    fetchPreferences: hook.fetchPreferences,
  };

  const tableHandlers = {
    setStatusFilter: hook.setStatusFilter, fetchEstimates: hook.fetchEstimates,
    fetchEstimateDetail: hook.fetchEstimateDetail, handleClone: hook.handleClone,
    toggleSelectAll: hook.toggleSelectAll, toggleSelect: hook.toggleSelect,
    setActiveTab: hook.setActiveTab,
  };

  const ticketHandlers = {
    fetchEstimateDetail: hook.fetchEstimateDetail, handleOpenEdit: hook.handleOpenEdit,
  };

  const detailHandlers = {
    handleOpenEdit: hook.handleOpenEdit, handleDeleteEstimate: hook.handleDeleteEstimate,
    handleConvertToInvoice: hook.handleConvertToInvoice, handleConvertToSO: hook.handleConvertToSO,
    handleMarkAccepted: hook.handleMarkAccepted, handleMarkDeclined: hook.handleMarkDeclined,
    handleClone: hook.handleClone, handleDownloadPDF: hook.handleDownloadPDF,
    setSendEmail: hook.setSendEmail, setShowSendDialog: hook.setShowSendDialog,
    setShareLink: hook.setShareLink, setShowShareDialog: hook.setShowShareDialog,
    fetchAttachments: hook.fetchAttachments, setShowAttachmentDialog: hook.setShowAttachmentDialog,
  };

  const createHandlers = {
    handleCreateEstimate: hook.handleCreateEstimate, addLineItem: hook.addLineItem,
    removeLineItem: hook.removeLineItem, selectItem: hook.selectItem,
    searchContacts: hook.searchContacts, fetchCustomerPricing: hook.fetchCustomerPricing,
    setSelectedContact: hook.setSelectedContact, setShowAddItemDialog: hook.setShowAddItemDialog,
    setShowBulkActionDialog: hook.setShowBulkActionDialog, resetForm: hook.resetForm,
  };

  const editState = {
    showEditDialog: hook.showEditDialog, editEstimate: hook.editEstimate,
    setEditEstimate: hook.setEditEstimate, editEstimatePersistence: hook.editEstimatePersistence,
    editItemSearch: hook.editItemSearch, setEditItemSearch: hook.setEditItemSearch,
    editSearchResults: hook.editSearchResults, setEditSearchResults: hook.setEditSearchResults,
    editActiveItemIndex: hook.editActiveItemIndex, setEditActiveItemIndex: hook.setEditActiveItemIndex,
    items: hook.items, showAddItemDialog: hook.showAddItemDialog, setShowAddItemDialog: hook.setShowAddItemDialog,
  };

  const editHandlers = {
    setShowEditDialog: hook.setShowEditDialog, handleUpdateEstimate: hook.handleUpdateEstimate,
    updateEditLineItem: hook.updateEditLineItem, addEditLineItem: hook.addEditLineItem,
    selectEditItem: hook.selectEditItem, removeEditLineItem: hook.removeEditLineItem,
  };

  return (
    <div className="space-y-6 p-6" data-testid="estimates-page">
      {/* Summary + Quick Actions (above Tabs) */}
      <EstimatesSummary state={hook} handlers={summaryHandlers} />

      {/* Single Tabs wrapper — all TabsContent must be children of this */}
      <Tabs value={hook.activeTab} onValueChange={hook.setActiveTab}>
        <TabsList className="bg-[#111820] border border-[rgba(255,255,255,0.07)] p-1">
          <TabsTrigger value="estimates" className="data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">Estimates</TabsTrigger>
          <TabsTrigger value="ticket-estimates" className="flex items-center gap-1 data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">
            <Ticket className="h-4 w-4" /> Ticket Estimates ({hook.ticketEstimates.length})
          </TabsTrigger>
          <TabsTrigger value="create" className="data-[state=active]:bg-[rgba(200,255,0,0.10)] data-[state=active]:text-[#C8FF00] data-[state=active]:border-b-2 data-[state=active]:border-b-[#C8FF00] text-[rgba(244,246,240,0.45)]">Create New</TabsTrigger>
        </TabsList>

        <EstimatesTabContent state={hook} handlers={tableHandlers} />
        <TicketEstimatesTabContent state={hook} handlers={ticketHandlers} />
        <EstimateModal state={hook} handlers={createHandlers} />
      </Tabs>

      {/* Detail Dialog */}
      <EstimateDetail
        open={hook.showDetailDialog}
        onOpenChange={hook.setShowDetailDialog}
        estimate={hook.selectedEstimate}
        handlers={detailHandlers}
      />

      {/* Secondary Dialogs */}
      <SendDialog open={hook.showSendDialog} onOpenChange={hook.setShowSendDialog} sendEmail={hook.sendEmail} setSendEmail={hook.setSendEmail} sendMessage={hook.sendMessage} setSendMessage={hook.setSendMessage} onSend={hook.handleSendEstimate} />
      <ShareDialog open={hook.showShareDialog} onOpenChange={hook.setShowShareDialog} shareLink={hook.shareLink} setShareLink={hook.setShareLink} shareConfig={hook.shareConfig} setShareConfig={hook.setShareConfig} shareLoading={hook.shareLoading} onCreateShareLink={hook.handleCreateShareLink} onCopyShareLink={hook.copyShareLink} />
      <AttachmentsDialog open={hook.showAttachmentDialog} onOpenChange={hook.setShowAttachmentDialog} attachments={hook.attachments} uploading={hook.uploading} onUpload={hook.handleUploadAttachment} onDelete={hook.handleDeleteAttachment} onDownload={hook.downloadAttachment} />
      <PreferencesDialog open={hook.showPreferencesDialog} onOpenChange={hook.setShowPreferencesDialog} preferences={hook.preferences} setPreferences={hook.setPreferences} onSave={hook.handleSavePreferences} />
      <ImportDialog open={hook.showImportDialog} onOpenChange={hook.setShowImportDialog} importFile={hook.importFile} setImportFile={hook.setImportFile} importing={hook.importing} onImport={hook.handleImport} onDownloadTemplate={hook.downloadImportTemplate} />
      <BulkActionDialog open={hook.showBulkActionDialog} onOpenChange={hook.setShowBulkActionDialog} selectedIds={hook.selectedIds} bulkAction={hook.bulkAction} setBulkAction={hook.setBulkAction} onBulkAction={hook.handleBulkAction} />
      <CustomFieldsDialog open={hook.showCustomFieldsDialog} onOpenChange={hook.setShowCustomFieldsDialog} customFields={hook.customFields} newCustomField={hook.newCustomField} setNewCustomField={hook.setNewCustomField} onAdd={hook.handleAddCustomField} onDelete={hook.handleDeleteCustomField} />
      <TemplatesDialog open={hook.showTemplateDialog} onOpenChange={hook.setShowTemplateDialog} templates={hook.pdfTemplates} selectedTemplate={hook.selectedTemplate} setSelectedTemplate={hook.setSelectedTemplate} selectedEstimate={hook.selectedEstimate} onDownloadWithTemplate={hook.handleDownloadWithTemplate} />
      <EditEstimateDialog state={editState} handlers={editHandlers} />
      <QuickAddItemDialog open={hook.showAddItemDialog} onOpenChange={hook.setShowAddItemDialog} quickAddItem={hook.quickAddItem} setQuickAddItem={hook.setQuickAddItem} newLineItem={hook.newLineItem} onQuickAdd={hook.handleQuickAddItem} />
      <EditCloseConfirmDialog
        persistence={hook.editEstimatePersistence}
        onSave={async () => { await hook.handleUpdateEstimate(); }}
        onDiscard={() => { hook.editEstimatePersistence.clearSavedData(); hook.setShowEditDialog(false); }}
      />
    </div>
  );
}
