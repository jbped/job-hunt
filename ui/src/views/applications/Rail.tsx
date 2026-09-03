import type { ReactNode } from "react";
import EditableField from "../../components/EditableField";
import { ObsidianLink } from "../../components/NoteViewer";
import type { Application, VaultIndex } from "../../api/types";
import PickList from "./PickList";
import FieldRow from "../../components/FieldRow";
import { ReferencePill } from "../../components/Pills";
import { involvementMatches, peopleFor } from "../../lib/people";
import { NOTE_ORDER, type DocSelection } from "./helpers";
import { useAddContact, useAddInterview, useLinkPerson } from "../../lib/actions";
import QuestionsPanel from "./QuestionsPanel";

/** `docButton()`, index.html:1012. The selection is marked from the path each
 *  button carries rather than its label, so duplicate names cannot confuse it
 *  (`syncDocSelection()`, index.html:1025). */
function DocButton({
  label,
  path,
  kind,
  selected,
  onSelect,
  children,
}: {
  label: string;
  path: string;
  kind: DocSelection["kind"];
  selected: boolean;
  onSelect: (doc: DocSelection) => void;
  children?: ReactNode;
}) {
  return (
    <button
      className="pick"
      data-doc={path}
      aria-current={selected ? "true" : "false"}
      onClick={() => onSelect({ label, path, kind })}
    >
      <span className={`dot ${kind === "pdf" ? "good" : ""}`} />
      <span>{label}</span>
      {children}
    </button>
  );
}

/** The company folder an application sits in. The bank is keyed by that folder
 *  name, which is the sanitised company — `app.company` is the frontmatter
 *  spelling and can differ from it. */
function companyFolder(app: Application): string {
  return app.path.split("/")[1] ?? app.company;
}

/** `buildRail()`, index.html:870 — navigation, this application's people and
 *  interviews, its documents, and every field the schema marks editable. */
export default function Rail({
  app,
  doc,
  index,
  onSelectApp,
  onSelectDoc,
  renderMessage,
  onRenderPdf,
}: {
  app: Application;
  doc: DocSelection;
  index: VaultIndex;
  onSelectApp: (app: Application) => void;
  onSelectDoc: (doc: DocSelection) => void;
  renderMessage: ReactNode;
  onRenderPdf: (app: Application, kind: "resume" | "cover-letter") => void;
}) {
  const addContact = useAddContact();
  const addInterview = useAddInterview();
  const linkPerson = useLinkPerson();

  const interviews = index.interviews
    .filter((i) => i.application === app.path)
    .sort((a, b) => (a.date || "9").localeCompare(b.date || "9"));

  const involved = peopleFor(index.people, app);
  const contacts = index.contacts.filter((c) => c.application === app.path);
  const seen = new Set(involved.map((p) => p.name.toLowerCase()));

  const noteEntries = Object.entries(app.notes || {}).sort(
    (a, b) =>
      ((NOTE_ORDER.indexOf(a[0]) + 1) || 99) - ((NOTE_ORDER.indexOf(b[0]) + 1) || 99),
  );
  const pdfs = (app.artifacts || []).filter((a) => a.name.endsWith(".pdf"));
  // The bank belongs to the company, not the application — which is the point:
  // a second application here inherits every answer already given.
  const questions = index.company_questions.filter((q) => q.company === companyFolder(app));

  return (
    <>
      <PickList
        applications={index.applications}
        selectedPath={app.path}
        onSelect={onSelectApp}
      />

      {/* Actions — what can be done to this application, in one place at the
          top. Generating artifacts lives with the artifacts, further down. */}
      <div className="card">
        <h3>Actions</h3>
        <div className="rail-actions">
          <button className="btn" onClick={() => void addContact(app)}>
            Add contact
          </button>
        </div>
      </div>

      {/* Interviews — this application's, soonest first. Each opens its note in
          the viewer; the status pill mirrors the Interviews tab. */}
      <div className="card">
        <h3>Interviews</h3>
        {interviews.map((iv) => (
          <DocButton
            key={iv.path}
            label={`${iv.when || "date unknown"}${iv.stage ? " · " + iv.stage : ""}`}
            path={iv.path}
            kind="note"
            selected={doc.path === iv.path}
            onSelect={onSelectDoc}
          >
            <span
              className={`pill ${
                iv.status === "completed"
                  ? "good"
                  : iv.status === "cancelled"
                    ? "bad"
                    : ""
              }`}
            >
              {iv.status}
            </span>
          </DocButton>
        ))}
        {!interviews.length ? (
          <div className="muted" style={{ padding: "2px 0 6px" }}>
            None scheduled yet.
          </div>
        ) : null}
        <div className="rail-actions">
          <button className="btn" onClick={() => void addInterview(app)}>
            Schedule interview
          </button>
        </div>
      </div>

      {/* People — who is attached to this application: referrals, references,
          contacts. Sourced from People notes plus this application's Contacts
          entries. */}
      <div className="card">
        <h3>People</h3>
        {involved.map((person) => {
          const roles = (person.applications || [])
            .filter((a) => involvementMatches(a, app))
            .flatMap((a) => a.roles);
          return (
            <div className="row" style={{ padding: "3px 0" }} key={person.path}>
              <span className="grow">{person.name}</span>
              {[...new Set(roles)].map((role) => (
                <span className="pill" key={role}>
                  {role}
                </span>
              ))}
              <ReferencePill status={person.reference_status} />
              <ObsidianLink path={person.path} />
            </div>
          );
        })}
        {contacts
          .filter((c) => !seen.has(c.name.toLowerCase()))
          .map((c) => (
            <div className="row" style={{ padding: "3px 0" }} key={`${c.note}:${c.name}`}>
              <span className="grow">{c.name}</span>
              {c.application_role ? (
                <span className="pill">{c.application_role}</span>
              ) : null}
              <span className="muted" style={{ fontSize: 11 }}>
                contacts only
              </span>
            </div>
          ))}
        {!involved.length && !contacts.length ? (
          <div className="muted" style={{ padding: "2px 0 6px" }}>
            No one attached yet.
          </div>
        ) : null}
        <div className="rail-actions">
          <button className="btn" onClick={() => void linkPerson(app)}>
            Link person
          </button>
        </div>
      </div>

      {/* Documents */}
      <div className="card">
        <h3>Documents</h3>
        <DocButton
          label="Application Brief"
          path={app.brief}
          kind="note"
          selected={doc.path === app.brief}
          onSelect={onSelectDoc}
        />
        {noteEntries.map(([name, path]) => (
          <DocButton
            key={path}
            label={name}
            path={path}
            kind="note"
            selected={doc.path === path}
            onSelect={onSelectDoc}
          />
        ))}
        <div className="group-label">Rendered artifacts</div>
        {pdfs.map((pdf) => (
          <DocButton
            key={pdf.path}
            label={pdf.name.replace(/\.pdf$/, "")}
            path={pdf.path}
            kind="pdf"
            selected={doc.path === pdf.path}
            onSelect={onSelectDoc}
          />
        ))}
        <div className="rail-actions" style={{ marginTop: 8 }}>
          <button
            className="btn btn-primary"
            onClick={() => onRenderPdf(app, "resume")}
          >
            Generate resume
          </button>
          <button className="btn" onClick={() => onRenderPdf(app, "cover-letter")}>
            Generate cover letter
          </button>
        </div>
        <div id="renderOut">{renderMessage}</div>
      </div>

      {/* Details — every field the schema marks editable, plus the read-only dates. */}
      <div className="card">
        <h3>Details</h3>
        <FieldRow label="Status">
          <EditableField
            path={app.brief}
            field="status"
            value={app.status}
            enumKey="status"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Next action">
          <EditableField
            path={app.brief}
            field="next_action"
            value={app.next_action ?? ""}
            placeholder="What happens next"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Due">
          <EditableField
            path={app.brief}
            field="next_action_date"
            value={app.next_action_date ?? ""}
            type="date"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Applied">
          <EditableField
            path={app.brief}
            field="date_applied"
            value={app.date_applied ?? ""}
            type="date"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        {app.date_found ? (
          <FieldRow label="Found">
            <span className="muted">{app.date_found}</span>
          </FieldRow>
        ) : null}
        <FieldRow label="Job URL">
          <EditableField
            path={app.brief}
            field="job_url"
            value={app.job_url ?? ""}
            placeholder="https://…"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Source">
          <EditableField
            path={app.brief}
            field="posting_source"
            value={app.posting_source ?? ""}
            placeholder="Where the posting lives"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Found via">
          <EditableField
            path={app.brief}
            field="discovery_method"
            value={app.discovery_method ?? ""}
            enumKey="discovery_method"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Detail">
          <EditableField
            path={app.brief}
            field="discovery_detail"
            value={app.discovery_detail ?? ""}
            placeholder="Referrer, board, site"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Location">
          <EditableField
            path={app.brief}
            field="location"
            value={app.location ?? ""}
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Work model">
          <EditableField
            path={app.brief}
            field="work_model"
            value={app.work_model ?? ""}
            enumKey="work_model"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Comp status">
          <EditableField
            path={app.brief}
            field="compensation_status"
            value={app.compensation_status ?? ""}
            enumKey="compensation_status"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Currency">
          <EditableField
            path={app.brief}
            field="compensation_currency"
            value={app.compensation_currency ?? ""}
            placeholder="USD"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Comp min">
          <EditableField
            path={app.brief}
            field="compensation_min"
            value={app.compensation_min ?? ""}
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Comp max">
          <EditableField
            path={app.brief}
            field="compensation_max"
            value={app.compensation_max ?? ""}
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Comp period">
          <EditableField
            path={app.brief}
            field="compensation_period"
            value={app.compensation_period ?? ""}
            enumKey="compensation_period"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Comp requested">
          <EditableField
            path={app.brief}
            field="compensation_requested"
            value={app.compensation_requested ?? ""}
            placeholder="What you asked for, when, and where"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Level stated">
          <EditableField
            path={app.brief}
            field="experience_level_stated"
            value={app.experience_level_stated ?? ""}
            placeholder="As the posting states it"
            fingerprint={app.fingerprint}
          />
        </FieldRow>
      </div>

      <QuestionsPanel
        company={companyFolder(app)}
        appPath={app.path}
        questions={questions}
      />
    </>
  );
}
