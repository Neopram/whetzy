/**
 * IndexedDB queue for quiz answers submitted while offline.
 * Falls back silently if IDB is unavailable (private browsing, etc.).
 */

const DB_NAME = 'whetzy_offline';
const DB_VERSION = 1;
const STORE = 'pending_answers';

export interface PendingAnswer {
  id: string;
  sessionId: string;
  questionId: string;
  selectedIndex: number | null;
  responseTimeMs: number;
  timestamp: number;
  /** Lo que corrige el servidor en ejecutables y `fill_blank` (2026-10-01). */
  execOutput?: string;
  answerText?: string;
  /** `interactive` (40.1). */
  widgetState?: unknown;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/** Id del evento offline, que viaja como `event_id` (columna de 64). Antes era
 *  `${sessionId}_${questionId}_${Date.now()}`: 65 caracteres con ids de pregunta
 *  de 14, y esas respuestas se perdían al reenviarse. */
export function offlineEventId(): string {
  return crypto.randomUUID();
}

export async function enqueue(answer: PendingAnswer): Promise<void> {
  try {
    const db = await openDB();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(answer);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // IDB unavailable — answer is lost for sync, but UI already handled it
  }
}

export async function dequeueAll(): Promise<PendingAnswer[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      const getAll = store.getAll();
      getAll.onsuccess = () => {
        const items = (getAll.result as PendingAnswer[]).sort(
          (a, b) => a.timestamp - b.timestamp,
        );
        // Clear the store
        store.clear();
        tx.oncomplete = () => resolve(items);
        tx.onerror = () => reject(tx.error);
      };
      getAll.onerror = () => reject(getAll.error);
    });
  } catch {
    return [];
  }
}

export async function pendingCount(): Promise<number> {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE, 'readonly');
      const req = tx.objectStore(STORE).count();
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(0);
    });
  } catch {
    return 0;
  }
}
