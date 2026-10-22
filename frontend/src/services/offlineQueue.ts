/**
 * IndexedDB queue for quiz answers submitted while offline.
 * Falls back silently if IDB is unavailable (private browsing, etc.).
 */

const DB_NAME = 'whetzy_offline';
// v2 (42.11): almacén de descartes para lo que el servidor rechaza para siempre.
const DB_VERSION = 2;
const STORE = 'pending_answers';
const DISCARDED = 'discarded_answers';

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
  /** «No lo sé» (42.11): antes se reenviaba siempre como `false`. */
  declaredUnknown?: boolean;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(DISCARDED)) {
        db.createObjectStore(DISCARDED, { keyPath: 'id' });
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

/** Lee la cola sin borrarla, de la más antigua a la más nueva. Antes se leía y
 *  se vaciaba en la misma transacción (`dequeueAll`), y si la red caía durante
 *  el envío esas respuestas se perdían (42.11): ahora cada una sale con
 *  `remove` cuando el servidor la confirma. */
export async function peekAll(): Promise<PendingAnswer[]> {
  try {
    const db = await openDB();
    return await new Promise((resolve, reject) => {
      const req = db.transaction(STORE, 'readonly').objectStore(STORE).getAll();
      req.onsuccess = () =>
        resolve((req.result as PendingAnswer[]).sort((a, b) => a.timestamp - b.timestamp));
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function remove(id: string): Promise<void> {
  try {
    const db = await openDB();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // IDB unavailable — se reintentará en el próximo flush
  }
}

/** Saca de la cola una respuesta que el servidor rechaza para siempre (4xx que
 *  no sea 409) y la guarda en descartes con su `status`, en una transacción:
 *  ni se reintenta sin fin ni desaparece sin rastro. */
export async function discard(answer: PendingAnswer, status: number | null): Promise<void> {
  try {
    const db = await openDB();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction([STORE, DISCARDED], 'readwrite');
      tx.objectStore(DISCARDED).put({ ...answer, status, discardedAt: Date.now() });
      tx.objectStore(STORE).delete(answer.id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // IDB unavailable — se reintentará en el próximo flush
  }
}

async function countIn(store: string): Promise<number> {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(store, 'readonly');
      const req = tx.objectStore(store).count();
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(0);
    });
  } catch {
    return 0;
  }
}

export async function discardedCount(): Promise<number> {
  return countIn(DISCARDED);
}

export async function pendingCount(): Promise<number> {
  return countIn(STORE);
}
