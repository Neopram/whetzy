// Minimal stub web worker for Monaco Editor.
// We use Monaco for syntax highlighting and basic editing only — no TypeScript
// type checking or JSON schema validation. Those features need language service
// workers; syntax tokenisation runs in the main thread and works fine without them.
// This stub satisfies Monaco's worker request so it does not 404.
self.onmessage = function () {};
