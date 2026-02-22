import { useEffect, useCallback, useRef, useState } from 'react';
import { useBlocker } from 'react-router-dom';

/**
 * useUnsavedChanges Hook
 * Tracks form dirty state and provides navigation blocking
 * 
 * @param {object} currentData - Current form data
 * @param {object} originalData - Original/initial form data
 * @param {object} options - Configuration options
 * @param {boolean} options.enabled - Enable/disable tracking (default: true)
 * @param {function} options.compareFunction - Custom comparison function
 * @param {boolean} options.blockNavigation - Block in-app navigation (default: true)
 * @param {boolean} options.blockBrowserClose - Block browser close/refresh (default: true)
 * @param {string} options.message - Warning message for browser dialog
 * 
 * @returns {object} { isDirty, setIsDirty, resetDirtyState, blocker }
 */
export function useUnsavedChanges(currentData, originalData, options = {}) {
  const {
    enabled = true,
    compareFunction = null,
    blockNavigation = true,
    blockBrowserClose = true,
    message = 'You have unsaved changes. Are you sure you want to leave?'
  } = options;

  const [isDirty, setIsDirty] = useState(false);
  const [manualDirty, setManualDirty] = useState(false);
  const originalDataRef = useRef(originalData);

  // Update original data ref when it changes
  useEffect(() => {
    originalDataRef.current = originalData;
  }, [originalData]);

  // Default comparison function (deep equality check)
  const defaultCompare = useCallback((current, original) => {
    if (!current || !original) return false;
    
    // Handle arrays
    if (Array.isArray(current) && Array.isArray(original)) {
      if (current.length !== original.length) return false;
      return current.every((item, index) => {
        return JSON.stringify(item) === JSON.stringify(original[index]);
      });
    }
    
    // Handle objects
    if (typeof current === 'object' && typeof original === 'object') {
      const currentKeys = Object.keys(current);
      const originalKeys = Object.keys(original);
      
      // Check if same number of keys
      if (currentKeys.length !== originalKeys.length) return false;
      
      // Check each key
      return currentKeys.every(key => {
        const currentVal = current[key];
        const originalVal = original[key];
        
        // Skip functions
        if (typeof currentVal === 'function') return true;
        
        // Deep compare
        return JSON.stringify(currentVal) === JSON.stringify(originalVal);
      });
    }
    
    // Primitive comparison
    return current === original;
  }, []);

  // Check if data has changed
  useEffect(() => {
    if (!enabled) {
      setIsDirty(false);
      return;
    }

    const compare = compareFunction || defaultCompare;
    const isEqual = compare(currentData, originalDataRef.current);
    setIsDirty(!isEqual || manualDirty);
  }, [currentData, enabled, compareFunction, defaultCompare, manualDirty]);

  // Browser beforeunload handler
  useEffect(() => {
    if (!enabled || !blockBrowserClose || !isDirty) return;

    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = message;
      return message;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [enabled, blockBrowserClose, isDirty, message]);

  // React Router navigation blocker
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) => {
      return enabled && blockNavigation && isDirty && currentLocation.pathname !== nextLocation.pathname;
    }
  );

  // Reset dirty state (call after successful save)
  const resetDirtyState = useCallback((newOriginalData = null) => {
    if (newOriginalData !== null) {
      originalDataRef.current = newOriginalData;
    }
    setIsDirty(false);
    setManualDirty(false);
  }, []);

  // Mark as dirty manually (for edge cases)
  const markAsDirty = useCallback(() => {
    setManualDirty(true);
  }, []);

  // Mark as clean manually
  const markAsClean = useCallback(() => {
    setManualDirty(false);
    setIsDirty(false);
  }, []);

  return {
    isDirty,
    setIsDirty,
    resetDirtyState,
    markAsDirty,
    markAsClean,
    blocker
  };
}

/**
 * useFormDirtyState Hook
 * Simplified hook for tracking form dirty state in dialogs
 * 
 * @param {boolean} isOpen - Whether dialog/form is open
 * @param {object} initialData - Initial form data when opened
 * @param {object} currentData - Current form data
 * 
 * @returns {object} { isDirty, resetOnClose }
 */
export function useFormDirtyState(isOpen, initialData, currentData) {
  const [isDirty, setIsDirty] = useState(false);
  const initialDataRef = useRef(null);

  // Capture initial data when dialog opens
  useEffect(() => {
    if (isOpen) {
      initialDataRef.current = JSON.parse(JSON.stringify(initialData || {}));
      setIsDirty(false);
    }
  }, [isOpen]);

  // Check for changes
  useEffect(() => {
    if (!isOpen || !initialDataRef.current) return;
    
    const hasChanges = JSON.stringify(currentData) !== JSON.stringify(initialDataRef.current);
    setIsDirty(hasChanges);
  }, [isOpen, currentData]);

  const resetOnClose = useCallback(() => {
    initialDataRef.current = null;
    setIsDirty(false);
  }, []);

  return { isDirty, resetOnClose, setIsDirty };
}

export default useUnsavedChanges;
