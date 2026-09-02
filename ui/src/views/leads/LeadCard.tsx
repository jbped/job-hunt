import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { invalidateAfterWrite } from "../../api/queries";
import type { CreatedPath, Lead } from "../../api/types";
import EditableField from "../../components/EditableField";
import { ObsidianLink } from "../../components/NoteViewer";
import { useToast } from "../../components/Toast";
import { requestApplication } from "../../lib/wikilink";
import FieldRow from "./FieldRow";
import { useArchiveUnit } from "./useArchiveUnit";

const today = () => new Date().toISOString().slice(0, 10);

// Wikilink values ("[[People/Network/Jo Doe]]") display as their leaf name
// (`inlineText()`, index.html:1199).
function inlineText(value: string | null): string {
  const trimmed = String(value ?? "").trim();
  const match = /^\[\[([^\]]+)\]\]$/.exec(trimmed);
  if (!match) return value ?? "";
  return match[1].split("|").pop()!.split("/").pop()!;
}

/** POST /api/application with `{lead}` (`promoteLead()`, index.html:1143):
 *  scaffolds the application, then hands the Applications view its path. */
function usePromoteLead() {
  const toast = useToast();
  const qc = useQueryClient();

  return async (lead: Lead) => {
    try {
      const result = await api<CreatedPath>("/api/application", {
        method: "POST",
        body: { lead: lead.path },
      });
      toast(`Promoted to ${result.path}`);
      await invalidateAfterWrite(qc);
      requestApplication(result.path);
    } catch (error) {
      toast(error instanceof Error ? error.message : String(error), "error");
    }
  };
}

/** `leadCard()` (index.html:1154). The editor's open/closed state is this
 *  component's own state — background refreshes cannot collapse it. */
export default function LeadCard({ lead }: { lead: Lead }) {
  const [editorOpen, setEditorOpen] = useState(false);
  const promote = usePromoteLead();
  const archive = useArchiveUnit();

  const open = lead.status === "new" || lead.status === "pursuing";
  const roleKnown = Boolean(lead.role && lead.role !== "Unknown");
  const overdue = Boolean(lead.next_follow_up && lead.next_follow_up < today());
  const kind = lead.status === "promoted" ? "good" : lead.status === "passed" ? "bad" : "";

  return (
    <div className="card">
      <div className="row">
        <span className="title grow">
          {roleKnown ? `${lead.company} — ${lead.role}` : lead.company}
        </span>
        {lead.next_follow_up ? (
          <span className={`pill ${overdue ? "bad" : "warn"}`}>
            {`follow up ${lead.next_follow_up}`}
          </span>
        ) : null}
        <span className={`pill ${kind}`}>{lead.status}</span>
        {open ? (
          <button
            className="btn"
            onClick={() => void promote(lead)}
            title={roleKnown ? "Scaffold the application" : "Record the role first"}
          >
            Promote
          </button>
        ) : null}
        <button
          className="btn"
          onClick={() => archive("lead", lead.path, lead.company ?? lead.path)}
          title="Move this lead to Archive/"
        >
          Archive…
        </button>
        <ObsidianLink path={lead.path} />
      </div>
      <div className="muted">
        {[
          inlineText(lead.source),
          lead.date_added ? `added ${lead.date_added}` : null,
          lead.status === "passed" ? lead.passed_reason : null,
        ]
          .filter(Boolean)
          .join(" · ")}
      </div>
      {lead.url ? (
        <div>
          <a href={lead.url} target="_blank" rel="noreferrer" className="muted">
            {lead.url}
          </a>
        </div>
      ) : null}
      {open ? (
        <details
          className="editor"
          open={editorOpen}
          onToggle={(event) => setEditorOpen(event.currentTarget.open)}
        >
          <summary>Edit details</summary>
          <FieldRow label="Status">
            <EditableField
              path={lead.path}
              field="status"
              value={lead.status ?? ""}
              enumKey="lead_status"
              fingerprint={lead.fingerprint}
            />
          </FieldRow>
          <FieldRow label="Role">
            <EditableField
              path={lead.path}
              field="role"
              value={lead.role ?? ""}
              placeholder="Unknown is honest"
              fingerprint={lead.fingerprint}
            />
          </FieldRow>
          <FieldRow label="URL">
            <EditableField
              path={lead.path}
              field="url"
              value={lead.url ?? ""}
              placeholder="https://…"
              fingerprint={lead.fingerprint}
            />
          </FieldRow>
          <FieldRow label="Source">
            <EditableField
              path={lead.path}
              field="source"
              value={lead.source ?? ""}
              placeholder="[[People/Network/Full Name]]"
              fingerprint={lead.fingerprint}
            />
          </FieldRow>
          <FieldRow label="Next follow-up">
            <EditableField
              path={lead.path}
              field="next_follow_up"
              value={lead.next_follow_up ?? ""}
              type="date"
              fingerprint={lead.fingerprint}
            />
          </FieldRow>
          <FieldRow label="Why passed">
            <EditableField
              path={lead.path}
              field="passed_reason"
              value={lead.passed_reason ?? ""}
              placeholder="Kept as funnel data"
              fingerprint={lead.fingerprint}
            />
          </FieldRow>
        </details>
      ) : null}
    </div>
  );
}
