# Design brief: the job-hunt webapp

Date: 2026-09-03. Status: approved input for Claude Design mocks
(Initiative 3 of the 2026-09-03 findings review). This brief is written
to be handed to a designer or design tool with **no knowledge of the
current UI, and no obligation to it**. Do not look at the existing
dashboard; design from this document alone.

## What the product is

A local, personal job-hunt application. One person uses it, on their own
machine, over their own data. It is the one place they work their search:
build a deep record of their past experience, track every application
and lead, keep the people around each one, produce tailored resumes and
cover letters, and always know what to do next. An AI companion lives in
the app and works the same records with them.

The data is a folder of markdown notes (an Obsidian vault). The user
must never need to know that. The app is a complete editor of its own
data; the notes are an implementation detail and an optional
"read it anywhere" view for people who sync the folder.

## Who it is for

One job seeker, actively searching, probably stressed, checking in
several times a day for weeks or months. Low technical expertise:
they installed the app by following a short set of instructions and
expect it to behave like a polished product, not a developer tool.
Never show them a file path, a format name, or a command.

## Purpose hierarchy (design to this order)

1. **Get the user a job.** Every screen should make the next step toward
   that obvious.
2. **The evidence interview.** The single most valuable feature. The
   companion interviews the user about past roles and produces
   *evidence journals*: rich accounts of accomplishments, decisions,
   metrics, and context that a resume cannot hold. Later documents are
   tailored from this evidence. The app must make it visible which
   parts of the user's history are still *unexamined* (imported from an
   old resume but not yet interviewed) and make starting an interview a
   one-step act.
3. **Applications, with everything around them.** For each posting:
   where it stands, what happens next, the posting itself, the analysis,
   the drafts and rendered documents with their state, the people
   involved, interviews, company-level answers to recurring questions,
   and the conversations about it. Organised so the user can digest it
   in seconds and act.

Everything else (leads, people, settings, templates) supports those.

## Core principles for the design

- **Computed, not nagged.** The app derives state and next actions from
  the data itself. It shows what is next, and highlights when something
  is inconsistent (a status that lags what has clearly happened). It
  never blocks the user on housekeeping; it makes the housekeeping
  visible and one click away.
- **The companion proposes, the user acts.** The AI companion talks,
  suggests, and offers buttons (calls to action) that run the app's
  deterministic operations. It never changes anything on its own. Every
  state change in the app passes through a click the user makes.
- **Deterministic wherever possible.** Rendering a PDF, tracking
  status, computing next steps, capturing a posting: no AI. AI is used
  for generation and conversation only: interviews, analysis, drafts.
- **State is always visible.** A document is scaffold, drafted,
  rendered, or stale. A role is unexamined, partly documented, or
  documented. An application is at one of ten stages. Show it.
- **Never a dead end.** Every empty state names the next action and
  offers it.

## Top-level structure

Navigation has these destinations. The landing destination is a user
setting, choosing between the first two.

### 1. What's next

The computed to-do view across the whole search. Grouped, scannable,
every row a direct action:

- Evidence to capture: roles and accomplishments still unexamined
  ("Interview me about Acme, 2019–2022").
- Applications needing a step: brief incomplete, analysis not written,
  resume or cover letter not drafted, rendered document stale because
  its draft changed, applied with no follow-up in N days, interview
  scheduled soon, offer awaiting response.
- Inconsistencies: stage looks wrong given what exists (e.g. a rendered,
  submitted resume but status still "preparing").
- Leads worth deciding on.

Rows carry a reason ("no activity for 14 days") and one primary action.
It should feel like a calm morning briefing, not a backlog.

### 2. Applications

**Board**: applications by stage. Stages, in order: discovered,
researching, preparing, applied, screening, interviewing, offer;
terminal: rejected, withdrawn, closed. Cards show company, role, days
in stage, a next-step hint, and small state badges (documents, people,
interviews). Moving a card changes the stage. Archived applications
are out of the way but reachable.

**Detail** (the most important screen after the interview): one
application, everything about it, digestible in seconds:

- Header: company, role, stage, days in stage, primary next action.
- The brief: structured fields with vocabularies (how it was found,
  location, work model, compensation, dates). Editable in place as
  forms, never as raw text.
- The posting: verbatim, read-only, clearly marked as the captured
  original.
- The analysis: AI-written fit assessment; regenerate via the
  companion.
- Documents: resume and cover letter, each with its state (scaffold →
  drafted → rendered → stale), the chosen template, the rendered
  versions, and actions that respect state (you cannot render a
  scaffold; "draft it" is offered instead).
- People: contacts on this application with their role (recruiter,
  hiring manager, referral, reference), linked to their person record.
- Interviews: one entry per interview, scheduled/completed, with notes.
- Company answers: the bank of answers this company has asked across
  its postings, reusable, editable in place.
- Company voice: an optional per-company customization of how the AI
  writes for this company (tone, emphasis). Present it as a feature,
  not a hidden setting.
- Conversations: every companion chat scoped to this application.
- Submission: notes, date, channel; the act of marking it applied.

### 3. Evidence

Priority 2 of the product gets its own home:

- Roles: every past role with its documentation state (unexamined /
  source-verified / documented). Unexamined roles are the headline.
- Accomplishments: the evidence journals, with state (draft / partial /
  verified), skills and themes they support.
- Skill matrix: the skills the evidence actually supports. Only these
  can appear on a resume; make that rule feel like a strength.
- Interview queue and "Start interview": the one-step entry into the
  evidence interview, which opens the companion scoped to evidence.
- Sources: imported documents (old resumes, certificates) the facts
  came from, so the user sees why a role is "source-verified".

### 4. Leads

Pre-application interest: companies or roles the user is watching.
Simple list with status (new / pursuing / promoted / passed) and a
one-click "promote to application".

### 5. People

Everyone in the search, filed by warmth: network (real relationships),
recruiters, job-hunt contacts (targets, interviewers, hiring managers).
A person shows their relationship to the user, who can introduce them,
and every application they touch.

### 6. Companion (drawer, on every screen)

Not a page. A drawer (or bubble that opens into one) reachable from
anywhere. Chat bubbles, streaming replies, a visible "working"
indicator, and a first-message prompt so an empty conversation is
never silent.

Every conversation has a **scope**: general, evidence, a company, or an
application. The scope is set from wherever the drawer was opened and
can be changed. The scope seeds what the companion knows and files the
conversation, so record pages list their own chats and the drawer's
history filters to the current scope.

Replies can carry **calls to action**: buttons the user clicks to run
an app operation ("Draft the resume for Globex", "Render the cover
letter", "Archive this lead", "Start the interview about Acme"). Design
the CTA as a first-class element of a reply, not a link buried in text.

Workflows the companion launches (as scoped conversations): the
evidence interview, application analysis, resume draft, cover letter
draft.

Provider, model, and effort can be changed per conversation from a
compact control in the drawer; defaults live in settings.

### 7. Settings

- Landing page (what's next / applications).
- Appearance: light, dark, or follow the system, plus a choice of base
  colour. The app ships seven palettes and defaults to a cool grey; the
  choice is the user's and applies everywhere. Present it as a normal
  preference, not a developer setting.
- Browser extension pairing (status, pair action).
- Templates: default template per document kind; the place to add a
  template (for now an explained drop location, later an upload flow).
- AI providers: which providers are available (Claude, Codex, Gemini),
  default provider, model, and effort; clear statement when a provider
  is unavailable in the current mode and why.
- AI workflows: for each workflow (interview, analysis, resume draft,
  cover letter draft) the default behaviour shown read-only, the user's
  customization editable, a reset, and a preview of the composed
  instructions. A global "voice" customization applies to all.

## Cross-cutting behaviours

- **Live freshness.** The data can change outside the app (a synced
  note edited elsewhere, the companion writing a journal). Views update
  live. If the exact field the user is editing changes underneath them,
  show a small "changed on disk" notice with reload / keep; never lose
  their typing silently.
- **Editing.** Structured fields are forms with dropdowns for
  controlled vocabularies. Prose (notes, journals, answers) uses a
  simple editor with live preview. No raw-markup exposure.
- **Errors and stale sessions.** If the app's backend restarted, tell
  the user before they type, not after they submit.
- **Rendered documents** are PDFs; show them inline with version
  history; "download" and "open" are obvious.

## Browser extension (companion surface, design alongside)

A popup that, on open, shows whether it can reach the app and is paired
(with a pair action if not), then a preview of the captured posting's
extracted fields (title, company, location, work model, posted date,
salary range, requisition id, URL) editable before submit, plus the two
things only the user knows, required, as dropdowns: how they found it
and the detail (who referred, which board). Submitting creates a
complete application; the user should never land on an application that
immediately flags missing required fields.

## Tone and visual direction

Calm, focused, and encouraging. The user is under pressure; the app
should reduce it. Dense enough for a power user checking in several
times a day, but with a clear hierarchy so the next step is obvious
without reading. Avoid dashboard clichés (gauges, vanity metrics).
Light and dark themes. Desktop-first, usable on a laptop screen without
horizontal scrolling; the extension popup is small.

## Constraints on the design (not on the visuals)

- No login, single user, local only.
- No notifications outside the app.
- No delete anywhere: things are archived, never destroyed.
- The captured posting is never editable.
- The skill matrix gates what may appear on a resume.

## What we want back

Mocks for, in priority order: the evidence view with an interview
launch; the application detail; what's next; the applications board;
the companion drawer with a CTA-bearing reply and scope control; the
settings page (AI workflows section in particular); the extension
popup in its unpaired and preview states. A navigation shell that
holds them together. Explore two directions for the shell and the
application detail before converging.

---

## Appendix: notes for whoever drives the design tool

Not part of the brief. The brief above is deliberately free of
implementation, and a designer working from it should ignore this section.
These are constraints and gaps discovered while syncing the component library
to Claude Design on 2026-09-03. They affect how the mocks get made, not what
the product should be.

- **Utility classes are not open-ended.** Designs render with the design
  system's compiled stylesheet and no Tailwind compiler, so only the utility
  families the library ships resolve — anything outside them silently does
  nothing. The available families are enumerated in
  `ui/.design-sync/conventions.md`, which the design agent receives. If a
  mock needs a class outside that list, widen the safelist in
  `ui/src/design-system.lib.css` and re-sync rather than working around it.
- **Reply calls-to-action have no component behind them yet.** The library
  covers the companion drawer well — `Bubble`, `Message`, `MessageScroller`
  and `MessageAvatar` are all synced — but nothing expresses a CTA-bearing
  reply, so it has to be composed from a button inside the message content.
  If the mocks settle on one shape for it, that is the first composite worth
  promoting into a real component and re-syncing. (shadcn also publishes
  `Attachment` and `Questionnaire`, which may suit the interview and
  document-upload flows; neither is installed here yet.)
- **There is no prose editor in the component library.** The brief asks for
  notes, journals and company answers to be edited with live preview and no
  raw-markup exposure; shadcn ships nothing for this — its registry has no
  editor, rich-text or markdown entry at all. An engine has to be chosen: a
  textarea with a preview pane is free but still shows markup; Tiptap with
  hand-styled shadcn chrome is the usual answer; Plate (`platejs`) ships its
  own shadcn-compatible registry and installs through the same CLI. The
  deciding constraint is not the toolbar but the serializer — markdown notes
  are the only source of truth and must stay readable in Obsidian, so
  anything the editor cannot round-trip losslessly is destroyed on save. The
  mocks do not need this settled: the editing surface can be drawn from
  `Card`, `Button`, `Separator` and `Textarea`, and the engine chosen to fit
  it. A formatting toolbar wants shadcn's `toggle-group`, which is published
  but not installed here — add it and re-sync when the editor is built.
