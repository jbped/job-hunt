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
