import { NoteContent, ObsidianLink } from "../../components/NoteViewer";
import type { Application } from "../../api/types";
import { StatusPill } from "../../components/Pills";
import type { DocSelection } from "./helpers";

/** `renderViewer()`, index.html:1030 — the right pane shows exactly one
 *  document: a note rendered with its edit flow, or a rendered PDF inline. */
export default function Viewer({
  app,
  doc,
  terminal,
  onArchive,
}: {
  app: Application;
  doc: DocSelection;
  terminal: string[];
  onArchive: (app: Application) => void;
}) {
  const url = `/file/${encodeURI(doc.path)}`;

  return (
    <div className="viewer-doc">
      <div className="viewer-head">
        <span className="title grow">{doc.label}</span>
        <StatusPill status={app.status} terminal={terminal} />
        <button
          className="btn"
          title="Move the whole application folder to Archive/"
          onClick={() => onArchive(app)}
        >
          Archive…
        </button>
        {doc.kind === "pdf" ? (
          <a href={url} target="_blank" rel="noreferrer" className="muted">
            open in a tab
          </a>
        ) : (
          <ObsidianLink path={doc.path} />
        )}
      </div>
      {doc.kind === "pdf" ? (
        <div>
          <object data={url} type="application/pdf">
            <div className="empty">
              This browser will not preview PDFs inline.{" "}
              <a href={url} target="_blank" rel="noreferrer">
                Open it in a new tab.
              </a>
            </div>
          </object>
        </div>
      ) : (
        <div className="note-body">
          {/* Keyed by path so switching documents remounts rather than showing
              the previous note while the next one loads. */}
          <NoteContent key={doc.path} path={doc.path} />
        </div>
      )}
    </div>
  );
}
