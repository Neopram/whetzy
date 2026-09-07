import { openDB, type DBSchema, type IDBPDatabase } from 'idb';

interface LearningEngineDB extends DBSchema {
  questions: {
    key: string;
    value: {
      id: string;
      track_id: string;
      module_id: string;
      skill_id: string;
      type: 'mcq' | 'true_false' | 'code_output' | 'fill_blank';
      difficulty_tier: 'easy' | 'medium' | 'hard' | 'expert';
      text_es: string;
      text_en: string;
      code?: string;
      options_es: string[] | null;
      options_en: string[] | null;
      correct_index: number | null;
      correct_answer_es?: string;
      correct_answer_en?: string;
      explanation_es: string;
      explanation_en: string;
      elo_rating: number;
    };
    indexes: {
      'by-module': string;
      'by-skill': string;
      'by-difficulty': string;
    };
  };
  responses: {
    key: number;
    value: {
      question_id: string;
      correct: boolean;
      response_time_ms: number;
      timestamp: string;
      xp_earned: number;
      combo_at_time: number;
    };
  };
  skill_states: {
    key: string;
    value: {
      skill_id: string;
      p_known: number;
      elo_rating: number;
      stability: number;
      difficulty: number;
      due_date: string;
      attempts: number;
      correct: number;
      last_review: string;
    };
  };
  sync_queue: {
    key: number;
    value: {
      action: string;
      payload: unknown;
      timestamp: string;
      synced: boolean;
    };
  };
}

let dbPromise: Promise<IDBPDatabase<LearningEngineDB>> | null = null;

function getDB() {
  if (!dbPromise) {
    dbPromise = openDB<LearningEngineDB>('learning-engine', 1, {
      upgrade(db) {
        const questionStore = db.createObjectStore('questions', { keyPath: 'id' });
        questionStore.createIndex('by-module', 'module_id');
        questionStore.createIndex('by-skill', 'skill_id');
        questionStore.createIndex('by-difficulty', 'difficulty_tier');

        db.createObjectStore('responses', { keyPath: undefined, autoIncrement: true });
        db.createObjectStore('skill_states', { keyPath: 'skill_id' });
        db.createObjectStore('sync_queue', { keyPath: undefined, autoIncrement: true });
      },
    });
  }
  return dbPromise;
}

export async function saveQuestions(questions: LearningEngineDB['questions']['value'][]) {
  const db = await getDB();
  const tx = db.transaction('questions', 'readwrite');
  await Promise.all(questions.map((q) => tx.store.put(q)));
  await tx.done;
}

export async function getQuestionsByModule(moduleId: string) {
  const db = await getDB();
  return db.getAllFromIndex('questions', 'by-module', moduleId);
}

export async function getQuestionsBySkill(skillId: string) {
  const db = await getDB();
  return db.getAllFromIndex('questions', 'by-skill', skillId);
}

export async function saveResponse(response: LearningEngineDB['responses']['value']) {
  const db = await getDB();
  await db.add('responses', response);
  await db.add('sync_queue', {
    action: 'submit_response',
    payload: response,
    timestamp: new Date().toISOString(),
    synced: false,
  });
}

export async function getSkillState(skillId: string) {
  const db = await getDB();
  return db.get('skill_states', skillId);
}

export async function saveSkillState(state: LearningEngineDB['skill_states']['value']) {
  const db = await getDB();
  await db.put('skill_states', state);
}

export async function getPendingSyncs() {
  const db = await getDB();
  const all = await db.getAll('sync_queue');
  return all.filter((item) => !item.synced);
}

export async function markSynced(key: number) {
  const db = await getDB();
  const item = await db.get('sync_queue', key);
  if (item) {
    item.synced = true;
    await db.put('sync_queue', item, key);
  }
}
