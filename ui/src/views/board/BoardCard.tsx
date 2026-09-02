import { useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { invalidateAfterWrite } from "../../api/queries";
import type { Application, FieldSaveResult } from "../../api/types";
import { useToast } from "../../components/Toast";
import { requestApplication } from "../../lib/wikilink";
import { days, today } from "../../lib/format";

/** One card per application. Its `<select>` and drag handle both write through
 *  `moveCard()` (index.html:1083/1095) — the same `/api/field` path as any
 *  other status edit, refreshed unconditionally afterward. */
export default function BoardCard({
  app,
  allStatuses,
  onMove,
}: {
  app: Application;
  /** The select always offers every status, unfiltered by the terminal
   *  toggle — only the columns respect it (`SCHEMA.status`, index.html:1098). */
  allStatuses: string[];
  onMove: (app: Application, status: string) => void;
}) {
  const applied = app.date_applied ? days(app.date_applied, today()) : null;
  const overdue = Boolean(app.next_action_date && app.next_action_date < today());

  return (
    <div
      className="bcard"
      draggable
      onDragStart={(event) => event.dataTransfer.setData("text/app-path", app.path)}
    >
      <div>
        <a
          href="#"
          className="title"
          onClick={(event) => {
            event.preventDefault();
            requestApplication(app.path);
          }}
        >
          {`${app.company} — ${app.position}`}
        </a>
      </div>
      <div className="muted">
        {[applied != null ? `${applied}d since applied` : null, app.next_action]
          .filter(Boolean)
          .join(" · ")}
      </div>
      {overdue ? (
        <div>
          <span className="pill bad">{`overdue ${app.next_action_date}`}</span>
        </div>
      ) : null}
      <select value={app.status} onChange={(event) => onMove(app, event.target.value)}>
        {allStatuses.map((status) => (
          <option key={status} value={status}>
            {status}
          </option>
        ))}
      </select>
    </div>
  );
}

/** `moveCard()` (index.html:1083): writes through `/api/field`, then
 *  refreshes unconditionally — success or failure both redraw the board. */
export function useMoveCard() {
  const toast = useToast();
  const qc = useQueryClient();

  return async (app: Application, status: string) => {
    if (!app || app.status === status) return;
    try {
      await api<FieldSaveResult>("/api/field", {
        method: "POST",
        body: { path: app.brief, field: "status", value: status, fingerprint: app.fingerprint },
      });
      toast("Saved");
    } catch (error) {
      toast(error instanceof Error ? error.message : String(error), "error");
    }
    await invalidateAfterWrite(qc);
  };
}
