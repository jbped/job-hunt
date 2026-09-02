import { useCallback, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError, api, withParam } from "../api/client";
import { invalidateAfterWrite, useSchemaQuery } from "../api/queries";
import type { NotePayload, NoteSaveResult } from "../api/types";
import { renderMarkdown } from "../lib/markdown";
import { useToast } from "./Toast";

/** An `obsidian://` deep link for the note (`obsidian()`, index.html:670). */
export function ObsidianLink({ path }: { path: string }) {
  const schema = useSchemaQuery();
  const vault = schema.data?.vault_name ?? "";
  const url =
    `obsidian://open?vault=${encodeURIComponent(vault)}` +
    `&file=${encodeURIComponent(path.replace(/\.md$/, ""))}`;
  return (
    <a href={url} className="muted">
      open in Obsidian
    </a>
  );
}

/** Swap a rendered note for a full-text edit buffer. The save is atomic against
 *  the fingerprint the note loaded with: a 409 means Obsidian or another tab
 *  wrote first, and the buffer stays open so nothing is lost
 *  (`noteEditor()`, index.html:559). */
function NoteEditor({
  path,
  note,
  onDone,
}: {
  path: string;
  note: NotePayload;
  onDone: () => void;
}) {
  const [text, setText] = useState(note.text);
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const qc = useQueryClient();

  async function save() {
    setBusy(true);
    setProblem("");
    try {
      const result = await api<NoteSaveResult>("/api/note/save", {
        method: "POST",
        body: { path, text, fingerprint: note.fingerprint },
      });
      const warnings = result.warnings ?? [];
      for (const warning of warnings) toast(warning, "error");
      if (!warnings.length) toast("Saved");
      onDone();
      await invalidateAfterWrite(qc);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setProblem(message);
      toast(message, "error");
      if (message.includes("changed on disk")) await invalidateAfterWrite(qc);
      setBusy(false);
    }
  }

  return (
    <div className="note-edit">
      <textarea
        spellCheck={false}
        autoFocus
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <div className="row">
        <button
          className="btn btn-primary"
          disabled={busy}
          onClick={() => void save()}
        >
          Save
        </button>
        <button className="btn" onClick={onDone}>
          Cancel
        </button>
        <span className="muted grow" style={{ color: problem ? "var(--bad)" : undefined }}>
          {problem}
        </span>
      </div>
    </div>
  );
}

/** The rendered note plus its foot line. Callers wrap it in `.note-body`. */
export function NoteContent({ path }: { path: string }) {
  const [note, setNote] = useState<NotePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const toast = useToast();

  const load = useCallback(async () => {
    setError(null);
    try {
      setNote(await api<NotePayload>(withParam("/api/note", "path", path)));
    } catch (problem) {
      setNote(null);
      setError(problem instanceof Error ? problem.message : String(problem));
    }
  }, [path]);

  useEffect(() => {
    setEditing(false);
    void load();
  }, [load]);

  if (error) return <div className="banner bad">{error}</div>;
  if (!note) return <p className="muted">Loading…</p>;

  if (editing)
    return (
      <NoteEditor
        path={path}
        note={note}
        onDone={() => {
          setEditing(false);
          void load();
        }}
      />
    );

  return (
    <>
      {renderMarkdown(note.text)}
      <div className="note-foot">
        {note.readonly ? (
          <span className="muted">
            Evidence — read-only everywhere in this dashboard
          </span>
        ) : (
          <>
            <a
              href="#"
              className="muted"
              onClick={(event) => {
                event.preventDefault();
                // Refetch so the buffer opens on the freshest text and fingerprint.
                void (async () => {
                  try {
                    setNote(
                      await api<NotePayload>(withParam("/api/note", "path", path)),
                    );
                    setEditing(true);
                  } catch (problem) {
                    toast(
                      problem instanceof ApiError ? problem.message : String(problem),
                      "error",
                    );
                  }
                })();
              }}
            >
              edit here
            </a>
            <span className="muted"> · </span>
          </>
        )}
        <ObsidianLink path={path} />
      </div>
    </>
  );
}

/** A collapsible read-only view of a note. Content is fetched on first open so
 *  a detail page with eight notes costs one request, not eight
 *  (`noteViewer()`, index.html:529). */
export default function NoteViewer({
  path,
  title,
}: {
  path: string;
  title?: string;
}) {
  const [loaded, setLoaded] = useState(false);
  const label = title ?? (path.split("/").pop() ?? path).replace(/\.md$/, "");

  return (
    <details
      className="note"
      onToggle={(event) => {
        if (event.currentTarget.open) setLoaded(true);
      }}
    >
      <summary>
        <span className="title">{label}</span>
        <span className="muted note-path">{path}</span>
      </summary>
      <div className="note-body">{loaded ? <NoteContent path={path} /> : null}</div>
    </details>
  );
}
