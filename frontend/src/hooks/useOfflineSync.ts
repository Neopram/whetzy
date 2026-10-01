/**
 * Tracks online/offline state and flushes the IndexedDB pending-answer queue
 * when the connection is restored.
 */

import { useEffect, useRef, useState } from 'react';
import { dequeueAll, pendingCount } from '../services/offlineQueue';
import { quiz as quizApi } from '../services/api';

export interface OfflineSyncState {
  isOnline: boolean;
  isSyncing: boolean;
  pendingAnswers: number;
}

export function useOfflineSync(): OfflineSyncState {
  const [isOnline, setIsOnline] = useState(() => navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pending, setPending] = useState(0);
  const syncingRef = useRef(false);

  // Refresh pending count
  const refreshCount = async () => {
    const c = await pendingCount();
    setPending(c);
  };

  const flush = async () => {
    if (syncingRef.current) return;
    const items = await dequeueAll();
    if (items.length === 0) {
      setPending(0);
      return;
    }
    syncingRef.current = true;
    setIsSyncing(true);
    for (const item of items) {
      try {
        await quizApi.answer(
          item.sessionId,
          item.questionId,
          item.selectedIndex,
          item.responseTimeMs,
          false,
          item.id,
          { execOutput: item.execOutput, answerText: item.answerText },
        );
      } catch {
        // Best-effort: if the session expired, we can't recover. Skip it.
      }
    }
    syncingRef.current = false;
    setIsSyncing(false);
    setPending(0);
  };

  useEffect(() => {
    refreshCount();

    const onOnline = () => {
      setIsOnline(true);
      void flush();
    };
    const onOffline = () => {
      setIsOnline(false);
      refreshCount();
    };

    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { isOnline, isSyncing, pendingAnswers: pending };
}
