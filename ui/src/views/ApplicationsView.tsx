import { useCallback, useEffect, useState } from "react";
import { useIndexQuery, useSchemaQuery } from "../api/queries";
import {
  subscribeApplicationRequest,
  takePendingApplication,
} from "../lib/wikilink";
import type { Application } from "../api/types";
import Rail from "./applications/Rail";
import Viewer from "./applications/Viewer";
import { useArchiveApplication } from "./applications/actions";
import { useRenderPdf } from "./applications/useRenderPdf";
import { noteLabel, type DocSelection } from "./applications/helpers";

/** Applications: the split view (`renderApplications()`, index.html:832). Left
 *  rail carries navigation, editable metadata, and the document list; the right
 *  pane shows exactly one document. Which application and which document are
 *  selected is component state, not the hash — as in the vanilla page. */
export default function ApplicationsView() {
  const index = useIndexQuery();
  const schema = useSchemaQuery();
  const [selected, setSelected] = useState<string | null>(null);
  const [doc, setDoc] = useState<DocSelection | null>(null);
  const [request, setRequest] = useState<string | null>(null);
  const archive = useArchiveApplication();

  const onArtifact = useCallback((next: DocSelection) => setDoc(next), []);
  const render = useRenderPdf(onArtifact);

  const applications = index.data?.applications ?? [];

  // A wikilink, or a freshly created application, asks for one to be shown.
  // App switches the view; picking the target is this view's job.
  useEffect(() => {
    const unsubscribe = subscribeApplicationRequest(setRequest);
    const pending = takePendingApplication();
    if (pending) setRequest(pending);
    return unsubscribe;
  }, []);

  // Resolved once the index carries the application — a just-created one only
  // appears after the write's refetch lands.
  useEffect(() => {
    if (!request) return;
    const app = applications.find(
      (a) => request === a.path || request.startsWith(a.path + "/"),
    );
    if (!app) return;
    setSelected(app.path);
    setDoc(
      request === app.path
        ? null
        : { label: noteLabel(request), path: request, kind: "note" },
    );
    setRequest(null);
  }, [request, applications]);

  if (!index.data || !schema.data) return <section data-view="applications" data-active="" />;

  // Keep the selection across refreshes; fall back to the first application.
  const current = applications.find((a) => a.path === selected) ?? applications[0];

  // Drop a selection left over from another application, then fall back to the
  // note the user owns — it summarises the application better than anything else.
  let active = doc;
  if (current && active && !active.path.startsWith(current.path) && active.path !== current.brief)
    active = null;
  if (current && !active)
    active = { label: "Application Brief", path: current.brief, kind: "note" };

  return (
    <section data-view="applications" data-active="">
      <div className="split">
        <aside className="rail" id="rail">
          {current && active ? (
            <Rail
              app={current}
              doc={active}
              index={index.data}
              onSelectApp={(app) => {
                setSelected(app.path);
                setDoc(null);
              }}
              onSelectDoc={setDoc}
              renderMessage={render.message}
              onRenderPdf={(app, kind) => void render.start(app, kind)}
            />
          ) : (
            <div className="empty">No applications yet.</div>
          )}
        </aside>
        <div className="viewer" id="viewer">
          {current && active ? (
            <Viewer
              app={current}
              doc={active}
              terminal={schema.data.terminal ?? []}
              onArchive={(app: Application) => {
                void (async () => {
                  if (await archive(app)) {
                    setSelected(null);
                    setDoc(null);
                  }
                })();
              }}
            />
          ) : (
            <div className="empty">
              Use “New application” above to create the first one.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
