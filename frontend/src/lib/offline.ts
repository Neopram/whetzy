let offlineMode = false;

export function isOffline(): boolean {
  return offlineMode || !navigator.onLine;
}

export function setOfflineMode(offline: boolean): void {
  offlineMode = offline;
}

export async function saveForOffline(key: string, data: any): Promise<void> {
  try {
    const store = await openIndexedDB();
    return new Promise((resolve, reject) => {
      const tx = store.transaction(['offline'], 'readwrite');
      const objectStore = tx.objectStore('offline');
      objectStore.put({ key, data, timestamp: Date.now() });
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    localStorage.setItem(`offline_${key}`, JSON.stringify(data));
  }
}

export async function getOfflineData(key: string): Promise<any> {
  try {
    const store = await openIndexedDB();
    return new Promise((resolve, reject) => {
      const tx = store.transaction(['offline'], 'readonly');
      const objectStore = tx.objectStore('offline');
      const request = objectStore.get(key);
      request.onsuccess = () => resolve(request.result?.data);
      request.onerror = () => reject(tx.error);
    });
  } catch {
    const cached = localStorage.getItem(`offline_${key}`);
    return cached ? JSON.parse(cached) : null;
  }
}

function openIndexedDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('WhetzyDB', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains('offline')) {
        db.createObjectStore('offline', { keyPath: 'key' });
      }
    };
  });
}

if ('serviceWorker' in navigator) {
  window.addEventListener('online', () => setOfflineMode(false));
  window.addEventListener('offline', () => setOfflineMode(true));
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}
