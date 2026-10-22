/**
 * Tracks online/offline state and flushes the IndexedDB pending-answer queue
 * when the connection is restored.
 */

import { useEffect, useRef, useState } from 'react';
import { discard, peekAll, pendingCount, remove } from '../services/offlineQueue';
import { ApiError, quiz as quizApi } from '../services/api';

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

  // Cada respuesta sale de la cola solo cuando el servidor la confirma (42.11):
  // antes se vaciaba entera antes de enviar y un `catch {}` tragaba la caída de
  // la red, así que lo que no llegaba se perdía.
  const flush = async () => {
    if (syncingRef.current) return;
    const items = await peekAll();
    if (items.length === 0) {
      await refreshCount();
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
          item.declaredUnknown ?? false,
          item.id,
          { execOutput: item.execOutput, answerText: item.answerText, widgetState: item.widgetState },
        );
        await remove(item.id);
      } catch (e) {
        // 409: ese `event_id` ya está registrado, así que no hay nada que reenviar.
        if (e instanceof ApiError && e.status === 409) {
          await remove(item.id);
          continue;
        }
        // Sin red, 5xx, 401 (sesión por renovar) o 429: se conserva esta y el
        // resto, en orden, para el próximo `online`.
        if (!(e instanceof ApiError) || e.esTransitorio || e.status === 401 || e.status === 429) break;
        // Cualquier otro 4xx no se arregla reintentando: a descartes.
        await discard(item, e.status);
      }
    }
    syncingRef.current = false;
    setIsSyncing(false);
    await refreshCount();
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
