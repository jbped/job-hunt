import type { ReactNode } from "react";
import type { Person } from "../../api/types";
import { ObsidianLink } from "../../components/NoteViewer";
import EditableField from "../../components/EditableField";

/** `fieldRow()` (index.html:705). */
function FieldRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="field-row">
      <label>{label}</label>
      {children}
    </div>
  );
}

/** `referencePill()` (index.html:1319). */
function ReferencePill({ status }: { status: string | null }) {
  if (!status) return null;
  const kind = status === "confirmed" ? "good" : status === "declined" ? "bad" : "warn";
  return <span className={`pill ${kind}`}>{`reference: ${status}`}</span>;
}

/** Port of `personCard()` (index.html:1429). Open/closed accordion state lives
 *  in the parent's per-path Set (`personCard`'s `OPEN_EDITORS`), passed down so
 *  a background refresh never collapses an editor someone is working in. */
export default function PersonCard({
  person,
  open,
  onToggle,
}: {
  person: Person;
  open: boolean;
  onToggle: (nextOpen: boolean) => void;
}) {
  return (
    <div className="card">
      <div className="row">
        <span className="title grow">{person.name}</span>
        {person.professional_relationships.map((r) => (
          <span className="pill" key={r}>
            {r}
          </span>
        ))}
        {person.relationships.map((r) => (
          <span className="pill" key={r}>{`job search: ${r}`}</span>
        ))}
        <ReferencePill status={person.reference_status} />
        <ObsidianLink path={person.path} />
      </div>
      <div className="muted">
        {[person.company_context, person.email, person.phone, person.preferred_contact_method]
          .filter(Boolean)
          .join(" · ")}
      </div>
      {person.applications.map((a, i) => (
        <div className="muted" key={i}>
          {`${a.application}${a.roles.length ? " — " + a.roles.join(", ") : ""}`}
        </div>
      ))}
      <details className="editor" open={open} onToggle={(event) => onToggle(event.currentTarget.open)}>
        <summary>Edit details</summary>
        <FieldRow label="Company context">
          <EditableField
            path={person.path}
            field="company_context"
            value={person.company_context ?? ""}
            fingerprint={person.fingerprint}
            placeholder="Where you know them from"
          />
        </FieldRow>
        <FieldRow label="Via">
          <EditableField
            path={person.path}
            field="via"
            value={person.via ?? ""}
            fingerprint={person.fingerprint}
            placeholder="[[People/Network/Full Name]]"
          />
        </FieldRow>
        <FieldRow label="Email">
          <EditableField path={person.path} field="email" value={person.email ?? ""} fingerprint={person.fingerprint} />
        </FieldRow>
        <FieldRow label="Phone">
          <EditableField path={person.path} field="phone" value={person.phone ?? ""} fingerprint={person.fingerprint} />
        </FieldRow>
        <FieldRow label="Preferred contact">
          <EditableField
            path={person.path}
            field="preferred_contact_method"
            value={person.preferred_contact_method ?? ""}
            fingerprint={person.fingerprint}
          />
        </FieldRow>
        <FieldRow label="Next follow-up">
          <EditableField
            path={person.path}
            field="next_follow_up"
            value={person.next_follow_up ?? ""}
            fingerprint={person.fingerprint}
            type="date"
          />
        </FieldRow>
        <FieldRow label="Last contact">
          <EditableField
            path={person.path}
            field="last_contact"
            value={person.last_contact ?? ""}
            fingerprint={person.fingerprint}
            type="date"
          />
        </FieldRow>
        <FieldRow label="Reference status">
          <EditableField
            path={person.path}
            field="reference_status"
            value={person.reference_status ?? ""}
            fingerprint={person.fingerprint}
            enumKey="reference_permission"
          />
        </FieldRow>
        <FieldRow label="Consent confirmed">
          <EditableField
            path={person.path}
            field="permission_confirmed"
            value={person.permission_confirmed ?? ""}
            fingerprint={person.fingerprint}
            values={["true", "false"]}
          />
        </FieldRow>
        <FieldRow label="Consent date">
          <EditableField
            path={person.path}
            field="permission_confirmed_at"
            value={person.permission_confirmed_at ?? ""}
            fingerprint={person.fingerprint}
            type="date"
          />
        </FieldRow>
      </details>
    </div>
  );
}
