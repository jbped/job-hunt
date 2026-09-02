# Phase B reports — Phase C integration ledger

Branch tips to merge into `react-frontend-0.6`, in order: `0.6-views-apps`
(dd4cd0e), `0.6-views-board-leads` (c1a706b), `0.6-views-rest` (ad6dd85).
All three: typecheck, vitest, and `server/test_safety.py` green at their
tips; no builds run, nothing pushed.

Phase C owns these integration items beyond the plan's C1–C3 (all reported
by B workers who correctly refused to edit frozen shared code):

1. **Fix `lib/wikilink.ts` pending-request bug (B1 #5):** `requestApplication`
   leaves the pending path set even when a mounted listener handled it, so a
   stale path can hijack the next ApplicationsView mount. B1 defends by
   calling `takePendingApplication()` in its subscriber; fix properly in the
   lib and drop the defensive call if it becomes redundant.
2. **Lift duplicated helpers into `ui/src/lib/`:** `statusPill()` (B1
   `applications/helpers.tsx`, B2 `board/BoardCard.tsx` + `ArchivedView.tsx`),
   `referencePill()`, `fieldRow()`, `today()`, `peopleFor()`/
   `involvementMatches()` (B1). Replace the local copies.
3. **Dedupe `addContact` / `addInterview` / `linkPerson`:** B1 implemented
   application-scoped copies in `views/applications/actions.ts`; B3 has its
   own in Interviews/People. One shared implementation, two call sites.
4. **`NoteViewer` summary slot (B3):** the reference `renderEvidence()`
   appends company + status-pill badges inside the note `<summary>`; the
   shared `NoteViewer` only takes a string title, and B3 folded the badges
   into the title text. Add a `summary?: ReactNode` prop and restore real
   badges in Evidence.
5. **No ActionBar in Applications (B1 #1):** the plan named one; the
   reference has none in the Applications section. Correct as built —
   don't "fix" it back.
6. **Render invalidation (B1 #2):** `renderPdf()` in the reference ends with
   `refresh()`; B1 invalidates after the job settles. The plan's "no
   invalidation for render" was wrong — keep B1's behavior.
7. **B2 could not click through live** (no browser automation); the parity
   walk in C2 is the first full manual pass over Board/Leads/Archived —
   walk those views extra carefully.
8. Check for stray dev servers on ports 8765/8766 before C2's smoke
   (B2 smoke-tested with live servers; kill leftovers).
