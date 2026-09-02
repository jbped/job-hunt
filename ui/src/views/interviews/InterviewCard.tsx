import { useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { invalidateAfterWrite, useSchemaQuery } from "../../api/queries";
import type { FieldSaveResult, Interview } from "../../api/types";
import { useToast } from "../../components/Toast";
import NoteViewer from "../../components/NoteViewer";
import { requestApplication } from "../../lib/wikilink";

/** Port of `interviewCard()` (index.html:1222). The status select is not the
 *  shared `EditableField`: unlike an inline field edit, a status change here
 *  always refreshes afterward — success or failure — matching the reference's
 *  unconditional `await refresh()`. */
export default function InterviewCard({ interview }: { interview: Interview }) {
  const schema = useSchemaQuery().data;
  const toast = useToast();
  const qc = useQueryClient();

  async function onStatusChange(next: string) {
    try {
      const result = await api<FieldSaveResult>("/api/field", {
        method: "POST",
        body: { path: interview.path, field: "status", value: next, fingerprint: interview.fingerprint },
      });
      toast(
        result.changed && next === "completed"
          ? "Completed — record the outcome in the note below"
          : result.changed
            ? "Saved"
            : "No change",
      );
    } catch (error) {
      toast(error instanceof Error ? error.message : String(error), "error");
    }
    await invalidateAfterWrite(qc);
  }

  const pillKind = interview.status === "completed" ? "good" : interview.status === "cancelled" ? "bad" : "";

  return (
    <div className="card">
      <div className="row">
        <span className={`pill ${pillKind}`}>{interview.when || "date unknown"}</span>
        <span className="grow">
          <a
            href="#"
            className="title"
            title="Open the application"
            onClick={(event) => {
              event.preventDefault();
              // The vanilla page routed through openDetail(); this view has no
              // application selection concept of its own, so it defers to the
              // wikilink pub/sub the Applications view already subscribes to.
              requestApplication(interview.application);
            }}
          >
            {`${interview.company} — ${interview.position}`}
          </a>
          <div className="muted">
            {[interview.stage, interview.method, interview.interviewers, interview.location_or_link]
              .filter(Boolean)
              .join(" · ")}
          </div>
        </span>
        <select value={interview.status} onChange={(event) => void onStatusChange(event.target.value)}>
          {(schema?.interview_status ?? []).map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <NoteViewer path={interview.path} title="Preparation and outcome" />
    </div>
  );
}
