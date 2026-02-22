import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * useAutoSave Hook
 * Automatically saves form data to localStorage and optionally syncs with backend
 * 
 * @param {string} storageKey - Unique key for localStorage (e.g., 'estimate_draft_new')
 * @param {object} formData - Current form data to save
 * @param {object} options - Configuration options
 * @param {number} options.debounceMs - Debounce delay in ms (default: 2000)
 * @param {boolean} options.enabled - Enable/disable auto-save (default: true)
 * @param {function} options.onSave - Callback when data is saved
 * @param {function} options.onRestore - Callback when data is restored
 * @param {boolean} options.saveToBackend - Whether to sync with backend API
 * @param {string} options.backendEndpoint - API endpoint for backend sync
 * 
 * @returns {object} { lastSaved, isSaving, clearSavedData, restoreSavedData, hasSavedData }
 */
export function useAutoSave(storageKey, formData, options = {}) {
  const {
    debounceMs = 2000,
    enabled = true,
    onSave,
    onRestore,
    saveToBackend = false,
    backendEndpoint = null,
  } = options;

  const [lastSaved, setLastSaved] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [hasSavedData, setHasSavedData] = useState(false);
  const timeoutRef = useRef(null);
  const initialLoadRef = useRef(true);

  // Generate full storage key with user context
  const getFullKey = useCallback(() => {
    const orgId = localStorage.getItem('organization_id') || 'default';
    const userId = localStorage.getItem('user_id') || 'anonymous';
    return `autosave_${orgId}_${userId}_${storageKey}`;
  }, [storageKey]);

  // Check if there's saved data on mount
  useEffect(() => {
    const fullKey = getFullKey();
    const saved = localStorage.getItem(fullKey);
    setHasSavedData(!!saved);
  }, [getFullKey]);

  // Auto-save effect with debounce
  useEffect(() => {
    if (!enabled || initialLoadRef.current) {
      initialLoadRef.current = false;
      return;
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout for debounced save
    timeoutRef.current = setTimeout(() => {
      saveData();
    }, debounceMs);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [formData, enabled, debounceMs]);

  // Save data to localStorage
  const saveData = useCallback(async () => {
    if (!enabled || !formData) return;

    setIsSaving(true);
    const fullKey = getFullKey();
    
    try {
      const savePayload = {
        data: formData,
        timestamp: new Date().toISOString(),
        version: 1
      };

      localStorage.setItem(fullKey, JSON.stringify(savePayload));
      setLastSaved(new Date());
      setHasSavedData(true);

      // Optional backend sync
      if (saveToBackend && backendEndpoint) {
        const token = localStorage.getItem('token');
        await fetch(backendEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ draft_key: storageKey, data: formData })
        });
      }

      onSave?.({ data: formData, timestamp: savePayload.timestamp });
    } catch (error) {
      console.error('Auto-save error:', error);
    } finally {
      setIsSaving(false);
    }
  }, [enabled, formData, getFullKey, saveToBackend, backendEndpoint, storageKey, onSave]);

  // Restore saved data
  const restoreSavedData = useCallback(() => {
    const fullKey = getFullKey();
    const saved = localStorage.getItem(fullKey);
    
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        onRestore?.(parsed.data);
        return parsed.data;
      } catch (error) {
        console.error('Error restoring saved data:', error);
        return null;
      }
    }
    return null;
  }, [getFullKey, onRestore]);

  // Clear saved data
  const clearSavedData = useCallback(() => {
    const fullKey = getFullKey();
    localStorage.removeItem(fullKey);
    setHasSavedData(false);
    setLastSaved(null);
  }, [getFullKey]);

  // Force save (bypass debounce)
  const forceSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    saveData();
  }, [saveData]);

  // Get saved data info without restoring
  const getSavedDataInfo = useCallback(() => {
    const fullKey = getFullKey();
    const saved = localStorage.getItem(fullKey);
    
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return {
          exists: true,
          timestamp: new Date(parsed.timestamp),
          data: parsed.data
        };
      } catch {
        return { exists: false };
      }
    }
    return { exists: false };
  }, [getFullKey]);

  return {
    lastSaved,
    isSaving,
    hasSavedData,
    clearSavedData,
    restoreSavedData,
    forceSave,
    getSavedDataInfo
  };
}

/**
 * Format last saved time for display
 */
export function formatLastSaved(date) {
  if (!date) return null;
  
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) {
    return 'Just now';
  } else if (diff < 3600000) {
    const mins = Math.floor(diff / 60000);
    return `${mins} min${mins > 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}

export default useAutoSave;
