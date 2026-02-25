/**
 * Estimates — Thin orchestrator that wires the useEstimates hook to all sub-components.
 * This is a pure extraction refactor of EstimatesEnhanced.jsx (2966 lines → ~60 lines).
 * Zero logic changes — all state and handlers live in useEstimates.js.
 */
import { useEstimates } from "./useEstimates";
import { EstimatesTable } from "./EstimatesTable";
import { EstimateDetail } from "./EstimateDetail";
import { EstimateModal } from "./EstimateModal";
import {
  SendDialog, ShareDialog, AttachmentsDialog, PreferencesDialog,
  ImportDialog, BulkActionDialog, CustomFieldsDialog, TemplatesDialog,
  EditEstimateDialog, QuickAddItemDialog, EditCloseConfirmDialog,
} from "./EstimateDialogs";

export default function Estimates() {
  const hook = useEstimates();

  // Build handler bundles for each sub-component
  const tableHandlers = {
    fetchEstimates: hook.fetchEstimates, fetchEstimateDetail: hook.fetchEstimateDetail,
    handleClone: hook.handleClone, handleExport: hook.handleExport,
    setShowImportDialog: hook.setShowImportDialog, setShowBulkActionDialog: hook.setShowBulkActionDialog,
    setShowCustomFieldsDialog: hook.setShowCustomFieldsDialog, setShowTemplateDialog: hook.setShowTemplateDialog,
    setShowPreferencesDialog: hook.setShowPreferencesDialog, fetchCustomFields: hook.fetchCustomFields,
    fetchPdfTemplates: hook.fetchPdfTemplates, fetchPreferences: hook.fetchPreferences,
    toggleSelectAll: hook.toggleSelectAll, toggleSelect: hook.toggleSelect,
    handleOpenEdit: hook.handleOpenEdit, setShowEditDialog: hook.setShowEditDialog,
    setActiveTab: hook.setActiveTab, setStatusFilter: hook.setStatusFilter,
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
      <EstimatesTable state={hook} handlers={tableHandlers} />

      <EstimateModal state={hook} handlers={createHandlers} />

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
