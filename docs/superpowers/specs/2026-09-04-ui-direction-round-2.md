# Direction alignment: job-hunt webapp, design round two

Date: 2026-09-04. Status: approved direction for the second Claude Design pass. Supersedes the shell and navigation sections of `2026-09-03-ui-design-brief.md`; everything else in that brief still applies. The round-one prototype ("Job Hunt App") is the starting point, not the target.

## The one-line direction

The application is the hub. Everything else is either a feed into it, a record attached to it, or a setting for it. The user must always see where they are, what state everything is in, and one verb to act on.

## Keep from round one

- What's next is computed from state, not written by hand.
- Document state machine: scaffold → drafted → rendered → stale. A scaffold cannot be rendered.
- The assistant proposes; the user clicks. Actions appear as buttons under a reply; nothing changes until clicked.
- The company level: shared question bank and company voice.
- Skills are claimed per accomplishment and validated individually. The matrix is derived. An unproved skill is blocked from resumes.
- Submission checklist is advisory. Marking applied moves the status.
- The application header: status, round, one next step with its verb.
- Universal "+ Add" in the rail.

## Change

### 1. The board is the landing page

What's next, Applications, and Leads merge into one kanban board. Columns, left to right:

| Column | Status |
|---|---|
| Discovered | discovered |
| Preparing | preparing |
| Applied | applied |
| Interviewing | interviewing, card shows "round N" or "round N of M" |
| Offer | offer |
| Closed (collapsed) | rejected, withdrawn, closed |

Every card shows four things and nothing else: role and company, days in column, one signal, one verb. When several signals apply, show the first that matches:

1. Dated item overdue or today
2. Past interview undocumented
3. Rendered document stale
4. Document still a scaffold
5. Not submitted, documents ready
6. Quiet for N days

Above the columns, a **Today strip**: interviews, calls, follow-ups, anything with a date, in time order.

Above the strip on a new vault, a **first-run checklist** that clears itself: Upload a resume · Start your interviews (N roles) · Pair the extension. It stays until all three are done. It never blocks.

### 2. Leads are companies

There is no lead entity. "Check out this company, I know someone there" is a company record with a reason, a linked person, and an optional follow-up date. It appears as a company card in Discovered with the role line "no role yet" and the verb "Look into it". Adding a role turns it into an application in place. Deciding against it removes the card; the company and its people stay on file. The follow-up date puts it in the Today strip. The person page lists it under "introduced you to".

### 3. Rail

Board · Experience · People · Profile. Bottom: Assistant, Settings. Nothing else.

### 4. Experience

The section is called Experience. It holds roles; each role holds evidence. Badges use the word evidence: "3 roles without evidence". Interviews create evidence; nothing is typed in directly.

Onboarding path: upload a resume → the assistant scaffolds one role per entry with placeholder evidence → each role shows the verb "Interview". Emphasised, not enforced: the rest of the app is reachable throughout.

### 5. Application page

Header unchanged. Five tabs: Overview, Posting, Documents, Interviews, Submission.

- Overview: the brief (inline-editable), the analysis, and the company's questions and voice as a read-only supporting block, edited on the company page.
- Documents: per-document template picker; state, last render, sent version; draft editor and last render side by side.
- No Conversations tab. The assistant panel lists this application's conversations when opened here.

Rounds are derived from the count of interview notes. The brief has an optional "expected rounds" field.

### 6. Assistant

Resizable split pane, 340 to 720 px, page stays visible. Scope follows the page: application, company, role, or board (general). Conversations file to their record; general ones file to the board. The panel lists recent conversations for its current scope.

Footer: provider · model · effort, a context meter ("42k of 200k"), and a Compact button where the provider supports it.

No persona. No name.

### 7. People and privacy

One person page, merged in the UI from two notes. Identity, relationship, notes, and application links are readable by the assistant. Emails, phones, and handles are not; they live in a separate Contacts note the assistant never receives. Each contact entry carries an audience pill: self · application · public.

The assistant can therefore say "nudge Dana after the panel" and draft the message. The address is pasted by the user.

### 8. Profile

Three tabs: About (headline, summary), Contact (your own entries with audience pills; only application and public print on a resume), Education and certifications. No templates here.

### 9. Settings

Appearance · Extension · Templates · Assistant · Workflows.

- Appearance: theme, base colour.
- Extension: pairing status, pair, revoke.
- Templates: default resume and cover letter per kind, from the vault's template folder.
- Assistant: default provider, model, effort. Capture automation toggles, each off by default: analyse the posting · draft the resume · draft the cover letter. With a toggle off, the same action is a button on the application.
- Workflows: your voice (global), then one card per workflow showing the read-only default beside your instructions, with a mode switch: **Add** (append to the default) or **Replace** (substitute the workflow). Replace never touches the truth and privacy rules; say so next to the switch. Reset to default on every card.

No landing-page setting.

### 10. Colour carries meaning

The base colour is the neutral surface. On top of it, a fixed semantic set:

- Each board column has a hue.
- Signals by severity: red for overdue and undocumented, amber for stale and scaffold, blue for ready to submit, grey for quiet.
- Green for verified evidence and rendered documents.
- One accent per card. Never two.

### 11. Copy

- Every card, row, and empty state: one noun phrase, one state, one verb.
- Verbs are imperatives: Render · Draft · Document · Interview · Pair · Look into it.
- Empty states name the action, not the reason. "Upload a resume", not "Nothing here yet".
- No explanatory sentences under controls. Tooltips only where a term is unavoidable.
- No persona, no exclamation marks, no reassurance.

## Vocabulary

Application status: discovered · preparing · applied · interviewing · offer · rejected · withdrawn · closed. Researching and screening are gone.

Role: needs-interview · source-verified · documented. Evidence: draft · partial · verified. Document: scaffold · drafted · rendered · stale.

## Unchanged constraints

No login. No notifications. Nothing is ever deleted; closed and passed things are archived. The captured posting is immutable. A skill without evidence never appears on a resume. Contact details never reach the assistant. Desktop first, 1440 × 900 frames, light and dark.

## Redraw, in this order

1. Board with Today strip and first-run checklist, both the empty vault and a populated one.
2. Application page, Overview and Documents.
3. Experience, roles list and one role with evidence.
4. Assistant panel open on an application, with a reply carrying actions and the footer meter.
5. Person page, merged view with audience pills.
6. Settings, Assistant and Workflows.
7. Extension popup, unpaired and capture preview.
