// Configure Monaco Editor to use self-hosted workers (no CDN — red line 5).
// Must be imported before any monaco-editor code runs. The MonacoCodeEditor
// component imports this file at module level, so it runs on first mount.
//
// We serve a minimal stub worker from our own origin. Monaco uses it for
// background tokenization bookkeeping; we do not need language service
// workers (TypeScript checking, JSON schema) since exec questions only need
// Python and SQL syntax highlighting, which Monaco's main-thread tokenizers
// already provide.

import { loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

// Point @monaco-editor/react at the locally bundled monaco (not CDN).
loader.config({ monaco });

// Override worker resolution so every worker request goes to our own origin.
(globalThis as typeof globalThis & {
  MonacoEnvironment?: { getWorkerUrl: (id: string, label: string) => string };
}).MonacoEnvironment = {
  getWorkerUrl(_id: string, _label: string): string {
    return '/monaco-editor-worker.js';
  },
};
