import { useIndexQuery, useSchemaQuery } from "../api/queries";
import { ObsidianLink } from "../components/NoteViewer";
import RestoreButton from "./archived/RestoreButton";

/** `statusPill()` (index.html:429), local since Board's copy lives in a
 *  sibling subdir that Archived has no reason to import. */
function StatusPill({ status, terminal }: { status: string; terminal: string[] }) {
  const bad = terminal.includes(status);
  const good = status === "offer";
  return <span className={`pill ${bad ? "bad" : good ? "good" : ""}`}>{status}</span>;
}

/** `renderArchived()` (index.html:1551). There is no delete: every entry here
 *  came from `/api/archive` and can go back with one click. */
export default function ArchivedView() {
  const index = useIndexQuery();
  const schema = useSchemaQuery();
  const entries = index.data?.archived ?? [];
  const terminal = schema.data?.terminal ?? [];

  return (
    <section data-view="archived" data-active="">
      <h2>Archived</h2>
      <p className="hint">
        Moved to the vault's Archive/ folder, whole and untouched. There is no delete — restoring
        puts a unit back exactly where it came from.
      </p>
      <div id="archived">
        {entries.length === 0 ? (
          <div className="empty">
            Nothing archived. Applications and leads archive from their own views.
          </div>
        ) : (
          entries.map((entry) => {
            const name = [entry.company, entry.position].filter(Boolean).join(" — ");
            return (
              <div className="card" key={entry.path}>
                <div className="row">
                  <span className="title grow">{name || entry.path}</span>
                  <span className="pill">{entry.kind}</span>
                  {entry.status ? <StatusPill status={entry.status} terminal={terminal} /> : null}
                  <RestoreButton entry={entry} />
                  <ObsidianLink path={entry.brief} />
                </div>
                <div className="muted">
                  {[
                    entry.archived ? `archived ${entry.archived}` : null,
                    entry.archive_reason,
                    entry.archived_from,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
