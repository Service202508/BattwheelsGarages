import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Save, Trash2, X, AlertTriangle } from "lucide-react";

/**
 * UnsavedChangesDialog Component
 * Modal dialog for handling unsaved changes when user tries to navigate away
 * 
 * @param {boolean} open - Whether dialog is open
 * @param {function} onOpenChange - Callback when open state changes
 * @param {function} onSave - Callback when user chooses to save
 * @param {function} onDiscard - Callback when user chooses to discard
 * @param {function} onCancel - Callback when user chooses to stay
 * @param {boolean} isSaving - Whether save operation is in progress
 * @param {string} title - Custom dialog title
 * @param {string} description - Custom dialog description
 * @param {string} entityName - Name of the entity being edited (e.g., "estimate", "contact")
 */
export function UnsavedChangesDialog({
  open,
  onOpenChange,
  onSave,
  onDiscard,
  onCancel,
  isSaving = false,
  title = "Unsaved Changes",
  description = "You have unsaved changes that will be lost if you leave this page.",
  entityName = "document"
}) {
  const handleSave = async () => {
    if (onSave) {
      await onSave();
    }
  };

  const handleDiscard = () => {
    if (onDiscard) {
      onDiscard();
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      onOpenChange?.(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
            </div>
            <AlertDialogTitle className="text-lg font-semibold">
              {title}
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription className="text-[rgba(244,246,240,0.35)] mt-2">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        
        <AlertDialogFooter className="flex-col sm:flex-row gap-2 mt-4">
          <Button
            variant="outline"
            onClick={handleCancel}
            className="w-full sm:w-auto"
            data-testid="unsaved-cancel-btn"
          >
            <X className="h-4 w-4 mr-2" />
            Stay on Page
          </Button>
          
          <Button
            variant="destructive"
            onClick={handleDiscard}
            className="w-full sm:w-auto"
            data-testid="unsaved-discard-btn"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Discard Changes
          </Button>
          
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="w-full sm:w-auto bg-[#C8FF00] hover:bg-[#d4ff1a] text-[#080C0F] font-bold"
            data-testid="unsaved-save-btn"
          >
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? 'Saving...' : `Save ${entityName}`}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

/**
 * NavigationBlockerDialog Component
 * Used with React Router's useBlocker hook
 * 
 * @param {object} blocker - The blocker object from useBlocker hook
 * @param {function} onSave - Callback to save before navigation
 * @param {boolean} isSaving - Whether save is in progress
 * @param {string} entityName - Name of entity being edited
 */
export function NavigationBlockerDialog({ 
  blocker, 
  onSave, 
  isSaving = false,
  entityName = "changes"
}) {
  if (blocker.state !== 'blocked') return null;

  const handleSaveAndProceed = async () => {
    if (onSave) {
      const success = await onSave();
      if (success !== false) {
        blocker.proceed();
      }
    } else {
      blocker.proceed();
    }
  };

  return (
    <UnsavedChangesDialog
      open={blocker.state === 'blocked'}
      onOpenChange={() => {}}
      onSave={handleSaveAndProceed}
      onDiscard={() => blocker.proceed()}
      onCancel={() => blocker.reset()}
      isSaving={isSaving}
      entityName={entityName}
      title="Leave Page?"
      description={`You have unsaved ${entityName}. Would you like to save before leaving?`}
    />
  );
}

/**
 * FormCloseConfirmDialog Component  
 * Used when closing a form dialog with unsaved changes
 * 
 * @param {boolean} open - Whether dialog is open
 * @param {function} onClose - Callback when dialog should close
 * @param {function} onSave - Callback to save changes
 * @param {function} onDiscard - Callback to discard and close
 * @param {boolean} isSaving - Whether save is in progress
 * @param {string} entityName - Name of entity being edited
 */
export function FormCloseConfirmDialog({
  open,
  onClose,
  onSave,
  onDiscard,
  isSaving = false,
  entityName = "form"
}) {
  return (
    <UnsavedChangesDialog
      open={open}
      onOpenChange={onClose}
      onSave={async () => {
        await onSave?.();
        onClose?.();
      }}
      onDiscard={() => {
        onDiscard?.();
        onClose?.();
      }}
      onCancel={onClose}
      isSaving={isSaving}
      entityName={entityName}
      title={`Close ${entityName}?`}
      description={`You have unsaved changes in this ${entityName}. What would you like to do?`}
    />
  );
}

/**
 * AutoSaveIndicator Component
 * Shows auto-save status in form headers
 * 
 * @param {Date} lastSaved - Last saved timestamp
 * @param {boolean} isSaving - Whether currently saving
 * @param {boolean} isDirty - Whether there are unsaved changes
 */
export function AutoSaveIndicator({ lastSaved, isSaving, isDirty }) {
  const formatTime = (date) => {
    if (!date) return '';
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) {
      const mins = Math.floor(diff / 60000);
      return `${mins}m ago`;
    }
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (isSaving) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-[rgba(244,246,240,0.45)]">
        <div className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
        <span>Saving...</span>
      </div>
    );
  }

  if (isDirty && !lastSaved) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-amber-600">
        <div className="h-2 w-2 rounded-full bg-amber-400" />
        <span>Unsaved changes</span>
      </div>
    );
  }

  if (lastSaved) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-[rgba(244,246,240,0.45)]">
        <div className="h-2 w-2 rounded-full bg-[#C8FF00]" />
        <span>Saved {formatTime(lastSaved)}</span>
      </div>
    );
  }

  return null;
}

/**
 * DraftRecoveryBanner Component
 * Shows when there's a saved draft that can be restored
 * 
 * @param {boolean} show - Whether to show the banner
 * @param {Date} savedAt - When the draft was saved
 * @param {function} onRestore - Callback to restore draft
 * @param {function} onDiscard - Callback to discard draft
 */
export function DraftRecoveryBanner({ show, savedAt, onRestore, onDiscard }) {
  if (!show) return null;

  const formatDate = (date) => {
    if (!date) return '';
    return new Date(date).toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-600" />
        <span className="text-sm text-amber-800">
          You have an unsaved draft from {formatDate(savedAt)}
        </span>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="ghost"
          onClick={onDiscard}
          className="text-amber-700 hover:text-amber-800 hover:bg-amber-100"
        >
          Discard
        </Button>
        <Button
          size="sm"
          onClick={onRestore}
          className="bg-amber-600 hover:bg-amber-700 text-white"
        >
          Restore Draft
        </Button>
      </div>
    </div>
  );
}

export default UnsavedChangesDialog;
