import { openDB, type DBSchema, type IDBPDatabase } from 'idb';

export interface PlaygroundEntry {
  id?: number;
  runtime: 'python' | 'sql' | 'js';
  code: string;
  output: string;
  error: string | null;
  timestamp: string;
}

interface PlaygroundDB extends DBSchema {
  history: {
    key: number;
    value: PlaygroundEntry;
    indexes: { 'by-runtime': string; 'by-timestamp': string };
  };
}

let dbPromise: Promise<IDBPDatabase<PlaygroundDB>> | null = null;

function getPlaygroundDB() {
  if (!dbPromise) {
    dbPromise = openDB<PlaygroundDB>('whetzy-playground', 1, {
      upgrade(db) {
        const store = db.createObjectStore('history', {
          keyPath: 'id',
          autoIncrement: true,
        });
        store.createIndex('by-runtime', 'runtime');
        store.createIndex('by-timestamp', 'timestamp');
      },
    });
  }
  return dbPromise;
}

export async function savePlaygroundEntry(entry: Omit<PlaygroundEntry, 'id'>): Promise<number> {
  const db = await getPlaygroundDB();
  return db.add('history', entry as PlaygroundEntry);
}

export async function getPlaygroundHistory(
  runtime?: 'python' | 'sql' | 'js',
  limit = 50,
): Promise<PlaygroundEntry[]> {
  const db = await getPlaygroundDB();
  let all: PlaygroundEntry[];
  if (runtime) {
    all = await db.getAllFromIndex('history', 'by-runtime', runtime);
  } else {
    all = await db.getAll('history');
  }
  all.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  return all.slice(0, limit);
}

export async function clearPlaygroundHistory(): Promise<void> {
  const db = await getPlaygroundDB();
  await db.clear('history');
}
