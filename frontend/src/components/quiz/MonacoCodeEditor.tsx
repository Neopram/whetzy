// Monaco-based code editor for fix_bug and fill_blank_exec question types.
// Lazy-loadable: import this component via React.lazy so the ~2 MB Monaco
// bundle is only fetched when an exec question is first displayed.
//
// The monacoSetup import is side-effecting: it configures loader + worker
// URLs (self-hosted, no CDN) before Monaco initialises.
import '../../lib/monacoSetup';

import Editor from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { useRef } from 'react';
import styles from './MonacoCodeEditor.module.css';

interface Props {
  value: string;
  onChange?: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  /** Approximate line count — used to size the editor height. */
  minLines?: number;
  disabled?: boolean;
}

export function MonacoCodeEditor({
  value,
  onChange,
  language = 'python',
  readOnly = false,
  minLines = 4,
  disabled = false,
}: Props) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  // Height: 22 px per line, min 4 lines, max 20 lines.
  const lineCount = Math.max(minLines, Math.min(20, (value.match(/\n/g) ?? []).length + 1));
  const height = lineCount * 22 + 12; // +12 px padding

  function handleMount(ed: editor.IStandaloneCodeEditor) {
    editorRef.current = ed;
    // Remove the "Peek references" and other context menu items that leak
    // implementation details to learners.
    ed.addAction({
      id: 'noop',
      label: '',
      run: () => undefined,
    });
  }

  return (
    <div
      className={styles.wrapper}
      style={{ height }}
      data-disabled={disabled || readOnly ? 'true' : undefined}
    >
      <Editor
        value={value}
        language={language}
        theme="vs-dark"
        onMount={handleMount}
        onChange={(v) => onChange?.(v ?? '')}
        options={{
          readOnly: readOnly || disabled,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          fontSize: 14,
          tabSize: 4,
          wordWrap: 'on',
          automaticLayout: true,
          overviewRulerLanes: 0,
          hideCursorInOverviewRuler: true,
          renderLineHighlight: 'none',
          contextmenu: false,
          folding: false,
          glyphMargin: false,
          lineDecorationsWidth: 4,
          lineNumbersMinChars: 3,
        }}
      />
    </div>
  );
}
