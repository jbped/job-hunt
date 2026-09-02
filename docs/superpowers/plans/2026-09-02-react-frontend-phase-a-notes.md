# Phase A implementation notes — read before starting B1/B2/B3 or C

Recorded from the Phase A implementer's report (branch tip `fa3d592`).
Where these contradict the 0.6 plan, these win (they follow the reference
`server/assets/ui/index.html`, which outranks the plan).

1. Stack pins: Vite 6, React 18.3, @vitejs/plugin-react 4, vitest 3
   (vitest 2 breaks `defineConfig` typing against Vite 6), TypeScript 5.8.
   The tsconfig sets `"strict": true` explicitly (the template's doesn't).
2. Note-save 409: the reference shows the message inline in the editor and
   does not refresh; the implementation keeps both the inline message
   (buffer stays open) and the toast + conditional invalidate. Both carry
   the error text.
3. Note-save success DOES invalidate queries (reference calls `refresh()`,
   index.html:583) — the plan only mentioned invalidating on conflict.
4. `EditableField` has no `.saved` feedback: the reference `editable()`
   toasts "Saved"/"No change" instead. The `.saved` CSS rule is ported but
   unused, as in the original.
5. `useModal` accepts an optional `onSubmit`; throwing inside it keeps the
   dialog open showing the message (matches `modal()`'s inline error
   handling). `useFormModal` resolves to the created path (or null), not
   void — `newApplication()` needs it.
6. The header's "Pair extension" and "New application" buttons live in
   `App.tsx` (Phase A), not in any B view. The reference's
   `toast(..., "bad")` typo became `"error"`.
7. `openWikilink` helpers carry `applications: Application[]` — needed to
   decide "application-owned".
8. The "show this application" entry is a module-level pub/sub in
   `wikilink.ts`: `requestApplication` / `subscribeApplicationRequest` /
   `takePendingApplication`. B1 must subscribe and call
   `takePendingApplication()` on mount; App already handles the view
   switch.
9. The poll's `editingNow()` checks `dialog[data-modal][open]`; `Modal.tsx`
   stamps `data-modal`. The note overlay deliberately does not block the
   poll (matches the original).
10. jsdom lacks `HTMLDialogElement.showModal`; `ui/src/test-setup.ts`
    carries a three-line polyfill — dialog tests depend on it.
