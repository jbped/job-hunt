import type { ReactNode } from "react";
import type { Application, Person, PersonInvolvement } from "../../api/types";

/** Reading order, not alphabetical: the brief the user owns, then the posting,
 *  then everything derived from it (index.html:829). */
export const NOTE_ORDER = [
  "Job Description",
  "Analysis",
  "Contacts",
  "Resume Content",
  "Cover Letter",
  "Submission Notes",
];

export const today = (): string => new Date().toISOString().slice(0, 10);

/** The document the right pane shows (the vanilla page's `DOC`). */
export interface DocSelection {
  label: string;
  path: string;
  kind: "note" | "pdf";
}

export function noteLabel(path: string): string {
  return (path.split("/").pop() ?? path).replace(/\.md$/, "");
}

const normName = (s: string | null | undefined): string =>
  String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

export function involvementMatches(
  involvement: PersonInvolvement,
  app: Application,
): boolean {
  const title = normName(involvement.application);
  return title.includes(normName(app.company)) && title.includes(normName(app.position));
}

export function peopleFor(people: Person[], app: Application): Person[] {
  return people.filter((p) =>
    (p.applications || []).some((a) => involvementMatches(a, app)),
  );
}

/** `statusPill()`, index.html:429. */
export function StatusPill({
  status,
  terminal,
}: {
  status: string;
  terminal: string[];
}) {
  const bad = terminal.includes(status);
  const good = status === "offer";
  return <span className={`pill ${bad ? "bad" : good ? "good" : ""}`}>{status}</span>;
}

/** `referencePill()`, index.html:1322. */
export function ReferencePill({ status }: { status: string | null }) {
  if (!status) return null;
  const kind = status === "confirmed" ? "good" : status === "declined" ? "bad" : "warn";
  return <span className={`pill ${kind}`}>{`reference: ${status}`}</span>;
}

/** `fieldRow()`, index.html:705. */
export function FieldRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="field-row">
      <label>{label}</label>
      {children}
    </div>
  );
}
