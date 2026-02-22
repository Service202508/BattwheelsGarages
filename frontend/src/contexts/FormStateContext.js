import React, { createContext, useContext, useState, useCallback } from 'react';
import { UnsavedChangesDialog } from '@/components/UnsavedChangesDialog';

/**
 * FormStateContext
 * Global context for managing form states and unsaved changes across the application
 */
const FormStateContext = createContext(null);

/**
 * FormStateProvider Component
 * Wrap your app with this to enable global form state management
 */
export function FormStateProvider({ children }) {
  const [activeForm, setActiveForm] = useState(null);
  const [pendingNavigation, setPendingNavigation] = useState(null);
  const [showDialog, setShowDialog] = useState(false);

  // Register a form as active (being edited)
  const registerForm = useCallback((formId, formState) => {
    setActiveForm({
      id: formId,
      ...formState
    });
  }, []);

  // Unregister form (form closed/submitted)
  const unregisterForm = useCallback((formId) => {
    if (activeForm?.id === formId) {
      setActiveForm(null);
    }
  }, [activeForm]);

  // Update form dirty state
  const updateFormDirtyState = useCallback((formId, isDirty) => {
    if (activeForm?.id === formId) {
      setActiveForm(prev => ({ ...prev, isDirty }));
    }
  }, [activeForm]);

  // Check if navigation should be blocked
  const shouldBlockNavigation = useCallback(() => {
    return activeForm?.isDirty === true;
  }, [activeForm]);

  // Request navigation (will show dialog if form is dirty)
  const requestNavigation = useCallback((destination, onProceed) => {
    if (shouldBlockNavigation()) {
      setPendingNavigation({ destination, onProceed });
      setShowDialog(true);
      return false;
    }
    return true;
  }, [shouldBlockNavigation]);

  // Handle dialog actions
  const handleSave = useCallback(async () => {
    if (activeForm?.onSave) {
      const success = await activeForm.onSave();
      if (success !== false) {
        setShowDialog(false);
        pendingNavigation?.onProceed?.();
        setPendingNavigation(null);
        setActiveForm(null);
      }
    }
  }, [activeForm, pendingNavigation]);

  const handleDiscard = useCallback(() => {
    setShowDialog(false);
    pendingNavigation?.onProceed?.();
    setPendingNavigation(null);
    setActiveForm(null);
  }, [pendingNavigation]);

  const handleCancel = useCallback(() => {
    setShowDialog(false);
    setPendingNavigation(null);
  }, []);

  const value = {
    activeForm,
    registerForm,
    unregisterForm,
    updateFormDirtyState,
    shouldBlockNavigation,
    requestNavigation
  };

  return (
    <FormStateContext.Provider value={value}>
      {children}
      <UnsavedChangesDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        onSave={handleSave}
        onDiscard={handleDiscard}
        onCancel={handleCancel}
        entityName={activeForm?.entityName || 'changes'}
      />
    </FormStateContext.Provider>
  );
}

/**
 * useFormState Hook
 * Access form state context
 */
export function useFormState() {
  const context = useContext(FormStateContext);
  if (!context) {
    throw new Error('useFormState must be used within a FormStateProvider');
  }
  return context;
}

/**
 * useRegisterForm Hook
 * Register a form component for unsaved changes tracking
 * 
 * @param {string} formId - Unique form identifier
 * @param {object} options - Form options
 */
export function useRegisterForm(formId, options = {}) {
  const { registerForm, unregisterForm, updateFormDirtyState } = useFormState();
  const { entityName = 'form', onSave } = options;

  // Register on mount
  React.useEffect(() => {
    registerForm(formId, { entityName, onSave, isDirty: false });
    return () => unregisterForm(formId);
  }, [formId, entityName]);

  // Update dirty state
  const setDirty = useCallback((isDirty) => {
    updateFormDirtyState(formId, isDirty);
  }, [formId, updateFormDirtyState]);

  return { setDirty };
}

export default FormStateContext;
