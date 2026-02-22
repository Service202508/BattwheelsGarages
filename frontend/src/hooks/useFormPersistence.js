import { useState, useEffect, useCallback, useRef } from 'react';
import { useAutoSave, formatLastSaved } from './useAutoSave';
import { useFormDirtyState } from './useUnsavedChanges';

/**
 * useFormPersistence Hook
 * Combined hook for form auto-save and unsaved changes tracking
 * Easy to integrate with existing forms
 * 
 * @param {string} formKey - Unique key for this form (e.g., 'estimate_new', 'contact_edit_123')
 * @param {object} formData - Current form state
 * @param {object} initialData - Initial form data (for dirty checking)
 * @param {object} options - Configuration
 * @param {boolean} options.enabled - Enable persistence (default: true)
 * @param {boolean} options.isDialogOpen - Whether form dialog is open
 * @param {function} options.onRestore - Callback when draft is restored
 * @param {function} options.setFormData - State setter for form data
 * @param {number} options.debounceMs - Auto-save debounce (default: 2000)
 * @param {string} options.entityName - Entity name for dialogs (default: 'form')
 * 
 * @returns {object} Form persistence state and handlers
 */
export function useFormPersistence(formKey, formData, initialData, options = {}) {
  const {
    enabled = true,
    isDialogOpen = true,
    onRestore,
    setFormData,
    debounceMs = 2000,
    entityName = 'form'
  } = options;

  const [showRecoveryBanner, setShowRecoveryBanner] = useState(false);
  const [savedDraftInfo, setSavedDraftInfo] = useState(null);
  const [showCloseConfirm, setShowCloseConfirm] = useState(false);
  const isRestoringRef = useRef(false);

  // Auto-save hook
  const {
    lastSaved,
    isSaving,
    hasSavedData,
    clearSavedData,
    restoreSavedData,
    forceSave,
    getSavedDataInfo
  } = useAutoSave(formKey, formData, {
    enabled: enabled && isDialogOpen,
    debounceMs,
    onSave: ({ timestamp }) => {
      console.log(`[AutoSave] ${formKey} saved at ${timestamp}`);
    }
  });

  // Dirty state tracking
  const { isDirty, resetOnClose, setIsDirty } = useFormDirtyState(
    isDialogOpen,
    initialData,
    formData
  );

  // Check for saved draft on mount/dialog open
  useEffect(() => {
    if (isDialogOpen && enabled && !isRestoringRef.current) {
      const info = getSavedDataInfo();
      if (info.exists) {
        setSavedDraftInfo(info);
        setShowRecoveryBanner(true);
      }
    }
  }, [isDialogOpen, enabled, formKey]);

  // Handle draft restoration
  const handleRestoreDraft = useCallback(() => {
    isRestoringRef.current = true;
    const data = restoreSavedData();
    if (data && setFormData) {
      setFormData(data);
      onRestore?.(data);
    }
    setShowRecoveryBanner(false);
    isRestoringRef.current = false;
  }, [restoreSavedData, setFormData, onRestore]);

  // Handle draft discard
  const handleDiscardDraft = useCallback(() => {
    clearSavedData();
    setShowRecoveryBanner(false);
    setSavedDraftInfo(null);
  }, [clearSavedData]);

  // Handle form close attempt
  const handleCloseAttempt = useCallback((onClose) => {
    if (isDirty) {
      setShowCloseConfirm(true);
      return false; // Prevent immediate close
    }
    clearSavedData();
    resetOnClose();
    onClose?.();
    return true;
  }, [isDirty, clearSavedData, resetOnClose]);

  // Handle save and close
  const handleSaveAndClose = useCallback(async (saveFunction, onClose) => {
    if (saveFunction) {
      const success = await saveFunction();
      if (success !== false) {
        clearSavedData();
        resetOnClose();
        setShowCloseConfirm(false);
        onClose?.();
      }
    }
  }, [clearSavedData, resetOnClose]);

  // Handle discard and close
  const handleDiscardAndClose = useCallback((onClose) => {
    clearSavedData();
    resetOnClose();
    setShowCloseConfirm(false);
    onClose?.();
  }, [clearSavedData, resetOnClose]);

  // Clear data on successful save
  const onSuccessfulSave = useCallback(() => {
    clearSavedData();
    resetOnClose();
    setIsDirty(false);
  }, [clearSavedData, resetOnClose, setIsDirty]);

  // Mark form as clean (after successful save)
  const markAsClean = useCallback(() => {
    setIsDirty(false);
  }, [setIsDirty]);

  return {
    // Auto-save state
    lastSaved,
    isSaving,
    hasSavedData,
    formattedLastSaved: formatLastSaved(lastSaved),
    
    // Dirty state
    isDirty,
    setIsDirty,
    
    // Draft recovery
    showRecoveryBanner,
    savedDraftInfo,
    handleRestoreDraft,
    handleDiscardDraft,
    
    // Close handling
    showCloseConfirm,
    setShowCloseConfirm,
    handleCloseAttempt,
    handleSaveAndClose,
    handleDiscardAndClose,
    
    // Utilities
    forceSave,
    clearSavedData,
    onSuccessfulSave,
    markAsClean,
    
    // Entity name for dialogs
    entityName
  };
}

/**
 * Quick integration helper - returns props for common components
 */
export function getFormPersistenceProps(persistence) {
  return {
    // For AutoSaveIndicator
    autoSaveIndicatorProps: {
      lastSaved: persistence.lastSaved,
      isSaving: persistence.isSaving,
      isDirty: persistence.isDirty
    },
    
    // For DraftRecoveryBanner
    draftRecoveryProps: {
      show: persistence.showRecoveryBanner,
      savedAt: persistence.savedDraftInfo?.timestamp,
      onRestore: persistence.handleRestoreDraft,
      onDiscard: persistence.handleDiscardDraft
    },
    
    // For FormCloseConfirmDialog
    closeConfirmProps: {
      open: persistence.showCloseConfirm,
      onClose: () => persistence.setShowCloseConfirm(false),
      entityName: persistence.entityName
    }
  };
}

export default useFormPersistence;
