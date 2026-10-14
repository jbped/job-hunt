# User testing findings — 2026-09-03

Status: **collecting**. These are Jacob's raw findings from the epic test
pass. Nothing here is started, prioritized, or specced — the list gets
reviewed together first, then items graduate to specs/plans.

## 1. Extension: captured metadata is drastically limited

Chrome capture works end to end, but the metadata that comes out is thin.
Explore whether the extension can prompt/extract more from the page at
capture time (fields worth considering at review: title, location, comp
range, work model, posted date, req id, source URL context — TBD with
Jacob). Constraint to respect: `Job Description.md` stays verbatim
checksummed evidence; richer metadata belongs in the Analysis/Brief
fields, not in the capture body.

## 2. Extension: no pairing check on open

Reproduced UX failure: submitting a capture while unpaired redirects and
only then reports "not paired". The extension popup should verify on open
that it can reach a job-hunt instance and that it is paired, and show
state + a pair action up front — before any capture is attempted.

## 3. Webapp: settings menu

Add a settings surface to the UI. "Pair extension" should live there,
not as its own header button. (Other future settings candidates land
here as they appear.)

## 4. Webapp: UI iteration

Jacob's impression: the React port reads as the old page with new things
bolted on, not a rethought UI. Context for the review discussion: 0.6
was scoped parity-first by the spec ("feature parity with the current
page, same visual design"), with redesign deferred to feature work — so
the sameness is by design, and the two new panels + chat view were added
in the old visual language. The deferred redesign is now due: plan a
deliberate UI iteration pass (information architecture, header/nav
cleanup, visual design), reviewed as its own initiative.

## 5. Firefox extension is missing

There is no Firefox build of the extension. Needs to exist (packaging
and any API differences from the Chrome build to be scoped at review).

## 6. Obsidian ↔ webapp piping works; in-app editing is clunky

Positive: edits made in Obsidian show up immediately in the webapp, and
webapp edits land in the vault — the fingerprint/poll buffer system is
doing its job. Negative: editing inside the webapp is clunky as a user.
Enhancement idea: a WYSIWYG-to-markdown editing experience (must keep
markdown as the stored truth and the fingerprint contract intact).

## 7. Company questions: no editing after entry in the UI

The panel supports entry at submission time, but answers/questions can't
be edited afterwards within the UI — editing works via Obsidian (and
reflects immediately). Review: whether the intended "Edit in note"
affordance is missing, hidden, or insufficient, and what in-panel editing
should look like.

## 8. Fundamental flow gap: no "what next / where am I working" layer

The biggest finding. The UI presents applications and notes well, but has
no top-level action flow: this is an application, this is where it
stands, this is the next action — the kanban-board-style stance and a
"what do we do next" entry point are absent as a first-class experience.
This is a data/flow-structure question, not a styling one, and needs
ideation with Jacob before any UI iteration (finding 4) is designed —
the UI iteration should be built around whatever this produces.

## Status

- Chrome extension: works (findings 1 & 2).
- Firefox extension: missing (finding 5).
- Obsidian ↔ webapp round-trip: works (finding 6).
- Company questions: entry works, post-entry edit gap (finding 7).
- AI sandbox, zip, PDFs, live vault: not yet reported.

## 9. AI Interview: "New interview" gives no feedback

Clicking "New interview" produces no interaction and no indicator. By
design a session is inert until the first message is sent, but nothing
tells the user that — no prompt, no state, no streaming/thinking
indicator once a turn starts. Needs a first-run affordance and a live
"agent is working" indicator.

## 10. SEVERITY HIGH — the sandbox only exists in Docker; host mode runs the agent against the repo checkout

Observed (host mode, `serve.py` on the host, no container running):
- Tool confinement held: exactly Read/Write/Edit/Glob/Grep, no shell.
- `--restricted` held: the agent was hard-blocked from the live vault.
- BUT the allowed root was the repo checkout (cwd, chosen so the agent
  can read the skill reference). Inside it the agent could read and
  write `server/`, `.agents/skills/`, `demo/`, and read `.env`. In Docker
  `/app` is a read-only rootfs, so the container is tight; on the host
  it is not.
- The webapp offers "AI Interview" identically in both modes, so a
  normal non-Docker user gets an un-containerized agent with write
  access to the application's own source and skills — a prompt-injection
  surface the spec explicitly set out to prevent ("Claude Code running
  inside the app's Docker container").

Process note: the implementer recorded this as a host-mode limitation
and the orchestrator relayed it as such instead of treating it as a
spec violation. That was the wrong call.

Fix directions for review (not started):
a. Gate the agent routes and the UI entry to container mode only
   (server detects it is in the image, e.g. an env flag set by the
   Dockerfile), with a clear "AI Interview needs the Docker app" message
   on the host; and/or
b. Make host mode vault-confined: cwd = the vault (or a scratch dir),
   `--add-dir` = the vault only, and the interview reference injected at
   spawn from its single source file (read by the server and passed as
   system-prompt content — not a copied fork) so the repo is never a
   working directory.
Either way, add a safety test asserting the agent's allowed roots never
include the repo checkout.

## 11. Agent silently works against whichever vault it is given

The agent noticed `.env` names the live vault while its allowed root
held only `demo/vault` (the server had been started with the demo
vault) and fell back to demo data without saying so. Two sub-issues:
the agent should be told explicitly which vault it is operating on in
the seeded prompt and say so in its first message; and it should never
be able to read `.env` at all (covered by finding 10).

## Status (updated)

- AI sandbox host mode: functional but NOT sandboxed as specced
  (finding 10 — highest priority item on this list). Docker mode: not
  yet exercised by the user.
- Nothing was written to the live vault during this test (blocked by
  `--restricted`); a full vault backup from 08:50 today exists.

## 12. Templates: no discoverable default or ingress

It is unclear in the UI where to set a default template for generated
documents, or where to provide a new one. Today: per-application pickers
only (no vault-wide default), and new templates are added by dropping
`.ps` files into `Resources/Templates/` — nothing in the webapp says so
or offers an ingress. Review: a vault-level default (settings surface,
finding 3), and an in-app "add template" path — which is where 2b's
upload→clone flow lands, but even before 2b the *location* needs to be
visible.

## 13. "AI Interview" is the wrong frame — this should be an AI companion

The evidence interview is one workflow, not the product's AI experience.
The intended shape is a companion that lives as its own widget on the
page and can talk about anything in the webapp: leads, applications,
what's next, what to plan, who to follow up with — and can trigger the
app's automations from the context of the conversation. The evidence
interview stays a phenomenal feature to *surface* from it: e.g. the app
flags experience the user is claiming (from a resume/LinkedIn-style
import — an implied feature, not built) that has not yet been interviewed
into evidence journals, and the companion offers to run that interview.

Standing principle preserved: minimize token usage by automating
everything deterministic; the companion channels, directs, and answers,
and triggers automations rather than doing deterministic work itself.

This reframes 0.7's UI and seeding (currently a single "AI Interview"
view with an interview-only system prompt) and connects directly to
finding 8 (the "what next / where am I working" layer) and finding 4
(UI iteration): the companion may well be the primary answer to
finding 8. Needs ideation — vision-level, not a patch.

Implied new concept to review alongside: "claims" — imported/asserted
experience not yet backed by evidence, so the app can show what remains
to be interviewed.

## 14. Rendering an unbuilt draft is a silent waste

Resume generation works, but the app never tells the user that
`Draft - Resume.md` / `Draft - Cover Letter.md` are still the untouched
scaffold template — "Generate resume" happily renders the placeholder
and burns the render (and, with a companion in the loop, tokens) for
nothing. Needs: a clear draft state per document (template / drafted /
rendered), surfaced in the viewer and rail, a "draft not written yet"
warning that gates or at least labels the generate action, and ideally
the deterministic check reused by the audit and the companion (finding
13) so the same signal drives "what's next" (finding 8): drafting is the
next step, not rendering.

Deterministic detection is cheap: the scaffold's placeholder markers
(the same `^(YYYY|<|\{\{)`-style placeholders the index already skips)
still present in the draft ⇒ not drafted.

## 15. Stale session token is only discovered on the first write

After the server restarts (or a different server takes the port), an
already-open tab holds a dead token and the user learns only when a
write fails ("missing or invalid session token; reload the page") —
e.g. after typing a chat message. The state poll already runs on every
focus/visibility change and could detect the 403 (or a token-epoch
mismatch in `/api/state`) and prompt a reload before any input is lost.
Same class as finding 9 (no feedback).

## 16. AI provider, model, and effort selection

The sandbox hardcodes Claude Code. Requirement: the user can choose the
AI type — Claude, Codex, Gemini — and, within each, the model and the
effort/reasoning level, from the app (settings surface, finding 3, with
a per-conversation override in the companion, finding 13).

Review notes:
- 0.7 was deliberately scoped to Claude Code only, so the spawn layer,
  stream relay, and tool confinement are Claude-specific. Multi-provider
  means a small provider adapter per CLI: argv shape, streaming/JSON
  mode, session-resume mechanism, and — critically — the equivalent of
  `--restricted --tools ... --strict-mcp-config` for each (Codex:
  `--sandbox` modes + approval policy; Gemini: to be investigated). The
  investigation doc recorded that Codex/Gemini flags were never verified
  against installed binaries.
- Auth per provider is its own mount/seed path (investigation §1).
- The confinement guarantee (finding 10) must hold identically for every
  provider before it is offered; a provider without an enforceable
  files-in-vault-only mode does not ship.
- Effort/model vocab differs per provider and per CLI version — the
  registry of options should come from the server (queried from each
  installed CLI where possible), not be hardcoded in the UI.

## Status (Docker mode verified, 09:40)

User-driven probe from inside the containerized AI Interview confirmed
the specced boundary: exactly Read/Write/Edit/Glob/Grep, no shell or
network tool exposed at all; `/app` readable (skills + server source,
needed for the workflow) but write refused with EROFS (read-only
rootfs); `/vault` the designated write target. Finding 10 therefore
stands as a **host-mode-only** defect; Docker mode is the sandbox as
specced. (`.env` is not in the image — `.dockerignore` admits only
`server/`, `.agents/skills/`, `docker/`.)

## Status (10:00)

Passed by the user: Company Questions reuse across applications (the
feature's core moment); cover-letter PDF generation; container → vault →
Obsidian sync (immediate). Resume PDF passed earlier (finding 14 aside).
Remaining untested: release zip (run + docker build from the unzipped
root), a render with a `vault:` template selected, live vault.

## Status (10:10) — vault template selection verified

Measured from the rendered PDFs (`pdftotext -bbox-layout`): both resumes
rendered with `vault:Wide Margins` selected sit at left 54pt / right
558pt — the template's declared `ce-param` values — versus the engine
defaults of 38 / 570. The registry → brief field → engine path works.
The two cover letters rendered at the default 38pt: the demo ships no
cover-letter vault template (`Wide Margins.ps` is `ce-kind: resume`) and
no `cover_letter_template` was set, so the "alternative template" cover
letter was in fact the built-in — which is finding 12 again from the
other side: nothing told the user the picker had nothing alternative to
offer for that kind.

## 17. Obsidian → UI desync; expect hot-reload-grade freshness

The user observed the webapp falling out of sync with Obsidian edits in
at least one case (specific case to be captured at review), and expects
React-era freshness: vault changes should show up live without the user
noticing a refresh cycle. Today's mechanism is the 3-second `/api/state`
fingerprint poll (skipped while an input has focus or a dialog is open)
plus focus/visibility triggers. Review: which case desynced (an edit
while a field had focus? a rename/move the mtime hash misses? a view
that doesn't re-derive from the index?), and whether the poll should
become server-pushed (the SSE plumbing from 0.7 could carry vault-change
events) rather than polled.

## Decision (user, 2026-09-03): real vault stays untouched

The real Obsidian vault will not be pointed at the epic until the
findings above are worked through — too many changes pending. Everything
in this epic stays on the demo vault. (Backup of the real vault from
08:50 today exists regardless.) The release-zip check is the only
remaining item from the original test list; everything else is either
passed or captured as a finding.

## Review outcome (2026-09-03, Jacob + orchestrator)

Status: **reviewed and decomposed**. The findings above graduate into
the initiatives below; each initiative gets its own brainstorm → spec →
plan cycle before any code. Decisions recorded here are binding on
those specs.

### Purpose hierarchy (governing statement)

The product exists to get the user a job. Beneath that outcome, in
priority order:

1. **The evidence interview** — an AI conversation over the user's past
   experience that produces evidence journals (roles, accomplishments)
   holding depth a resume cannot, from which resumes and cover letters
   are later tailored.
2. **Applications and everything around them** — open applications,
   relationships, generated documents, the posting, and all supporting
   detail, organised so the user can digest, act, apply, and interview
   fast. A one-stop shop.

Target user: low technical expertise, "click install, follow minimal
instructions". They may never open Obsidian; the webapp must be a
complete editor of its own vault. Obsidian remains the optional
anywhere-view over a synced vault.

### Architecture decisions

- **Computed-first "what next".** The schema already carries the state
  (application `status` + `next_action*`, lead status, role
  `needs-interview | source-verified | documented`, accomplishment
  status, `Interview Queue.md`). Finding 8 is a derivation/UI gap, not a
  schema gap. A **signals engine** in the server computes next actions,
  incongruencies (e.g. brief still `preparing` after a render and
  submission notes exist), and document states (scaffold / drafted /
  rendered / stale) deterministically on index; nothing derived is
  persisted as truth. `next_action` stays as a manual override. The app
  **highlights** incongruencies rather than silently correcting them.
  "Claims" (finding 13) = roles at `source-verified`/`needs-interview`;
  no new concept needed, only a first-class surface.
- **Companion proposes, user executes (option A).** The companion emits
  structured CTAs from conversation context; each maps to an existing
  token-gated server route; the UI renders buttons; the user clicks.
  The CTA vocabulary is a closed list the server validates. The agent
  never executes anything itself. A narrow first-party MCP tool is the
  recorded upgrade path if this proves too clicky.
- **Deployment doctrine.** Docker is preferred and is the hardened path
  (outer wall regardless of CLI). Host mode is the expected common case
  and therefore the *primary* confinement boundary; it must be
  vault-confined and verified from inside per provider, as Docker mode
  was. A provider without a verified files-in-vault-only mode on the
  host is not offered on the host, and the UI says so. Install
  automation (launcher: find Python, find/create vault, detect CLIs,
  open browser) is a **later initiative**.
- **Providers are a launch requirement**: Claude, Codex, Gemini, each a
  parallel worker task behind its own verification gate (flags checked
  against the installed binary; confinement probed from inside).
  "Provider" = harness + model source; model and effort options come
  from the server, queried from each CLI where possible. **Ollama /
  local models deferred**: later spike on whether Codex's local-model
  mode carries it (harness + sandbox intact); in-house loop only if not.
- **Freshness.** Server-side vault change watcher pushing events over
  the 0.7 SSE plumbing. All non-edited views update live. A field being
  edited gets a "changed on disk" banner with reload/keep. The
  skip-poll-while-focused rule is removed (it is the likely desync case
  in finding 17).
- **Editing.** Forms for every vocabulary/frontmatter field; a light
  markdown editor (textarea + live preview) for prose, chosen so a
  richer editor can replace it without touching the data path. No
  WYSIWYG-to-markdown now. The UI never makes the user think in
  markdown.
- **Document flow per application**, each step with visible state:
  captured → brief filled → analysis (AI, companion workflow) → resume
  and cover letter drafted (AI, companion workflows; the existing draft
  skills are the workflow text) → rendered (deterministic; template from
  brief field or vault default) → submitted. Render is **blocked** while
  a draft is still scaffold (placeholder markers present). Templates:
  vault-wide default per kind in settings; "add template" ingress shows
  and explains `Resources/Templates/` now, becomes 2b's clone flow later.
- **Skill customization = overlays.** Defaults stay read-only in the
  repo; the user's customization is appended guidance composed at spawn.
  Levels: global voice, per workflow (analysis, resume draft, cover
  letter draft, interview), and **per company** ("company voice", filed
  beside Company Questions, highlighted in the UI). Style-by-example via
  references to `Resources/` files. Settings shows default (read-only),
  overlay (editable), reset, and a composed-prompt preview. Open for
  the spec: whether the agent may write overlays at all (leaning
  read-only) and how the audit detects overlay tampering.
- **Companion placement.** One drawer, on every page, never its own
  page. Every conversation carries a scope (general / evidence / company
  / application) set from where it was opened and changeable; scope
  seeds context and files the conversation, so record pages list their
  own chats and the drawer history filters by current scope.
- **Landing page is a setting**: what's next or applications.
- **Extension capture arrives complete.** Inferable fields populated
  (date found = today, URL, posting source from domain, schema.org
  JobPosting JSON-LD where present); user-only fields (discovery method
  and detail) required in the popup as vocabulary dropdowns served from
  the schema route; everything else optional. Editable preview before
  submit. Pairing/reachability checked on popup open. Firefox is the
  same extension packaged for it.

### Initiatives, in build order

**Now — bounded fixes, before anything else**
- Finding 10: host-mode vault confinement (cwd in vault, `--add-dir`
  vault only, interview reference injected from the skill file at
  spawn), safety test that allowed roots never include the checkout.
- Finding 15: state poll detects a stale token and prompts reload
  before input is lost.
- Finding 9: "agent is working" indicator and a first-message prompt.

**Initiative 1 — Signals engine** (findings 8, 14). Server-side
deterministic checks → next actions, incongruencies, document states;
served on the index; consumed by audit, rail, what's next, companion.

**Initiative 2 — Companion** (findings 13, 16, 11, skill overlays).
Harness seam with Claude/Codex/Gemini adapters behind verification
gates; CTA protocol; conversation scopes; four workflows (interview,
analysis, resume draft, cover letter draft); overlays at global /
workflow / company level; the agent is told its vault and states it.

**Initiative 3 — UI redesign** (findings 4, 3, 6, 7, 12, 17). Design
brief → Claude Design mocks → React. Structure: what's next, evidence,
applications (board + detail), leads, people, companion drawer,
settings (landing page, templates default + ingress, providers/model/
effort, AI workflows, pairing). Forms + light editor; live freshness;
company questions editable in place.

**Initiative 4 — Extension** (findings 1, 2, 5). Pairing check on open,
structured extraction, complete-on-arrival form, Firefox build.
Independent; runs in parallel from day one.

**Later**: install automation; Ollama harness spike; 2b template
cloning through the companion; richer editor.

Dependencies: 1 before 3's what-next view; 2's CTA contract before 3's
drawer; the design brief and mocks start immediately
(`docs/superpowers/specs/2026-09-03-ui-design-brief.md`).

## Design round one review (2026-09-04, Jacob + orchestrator)

Reviewed the Claude Design prototype ("Job Hunt App", saved under `docs/superpowers/specs/mocks/2026-09-04-claude-design/`, not committed). Verdict: strong mechanics (computed What's next, document state machine, propose-and-click assistant, company level, per-accomplishment skill validation), weak hierarchy (data without verbs, no empty-vault state, vocabulary drift, no privacy controls, settings incomplete). Decisions, all approved:

1. The board is the landing page; What's next, Applications, and Leads merge into it.
2. Today strip on the board: interviews, calls, follow-ups, anything dated.
3. Leads become company records; a company card sits in Discovered until a role is added.
4. First-run checklist on the board, computed from vault state: resume, interviews, pairing.
5. Rail: Board, Experience, People, Profile, plus assistant and settings.
6. Interview round derived from interview note count; optional expected-rounds field on the brief.
7. Capture automation: per-workflow toggles in settings, off by default.
8. Copy: state and verb only; no persona.
9. Statuses: discovered, preparing, applied, interviewing, offer, rejected, withdrawn, closed. Researching and screening removed (schema change, migration needed).
10. Conversations file to their record; general chats file to the board.
11. Assistant is a resizable split pane.
12. People split into People and Contacts notes; the agent never receives Contacts; merged into one page in the UI. Audit flags contact patterns outside Contacts.
13. Profile: About, Contact (own entries with audience pills), Education. Templates live in settings.
14. Interview Queue note retired; "roles at needs-interview" is computed.
15. Application page: Overview, Posting, Documents, Interviews, Submission. Company questions and voice read-only on Overview. Conversations tab dropped.
16. Settings: Appearance, Extension, Templates, Assistant, Workflows. No landing setting.
17. Semantic colour: column hues, signal severity colours, green for verified and rendered, one accent per card.
18. Workflow instructions have an Add or Replace mode; Replace never touches truth and privacy rules.
19. Assistant panel shows a context meter; Compact button behind a per-provider capability flag; spike to verify with the Claude CLI.
20. Signal precedence on a card: dated overdue/today, undocumented interview, stale render, scaffold, ready to submit, quiet.

Round-two direction for Claude Design: `docs/superpowers/specs/2026-09-04-ui-direction-round-2.md`. Schema consequences (9, 12, 14, expected-rounds, company records without a role) feed Initiative 1 and need their own spec before implementation.
