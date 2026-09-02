import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { NoteContent } from "./NoteViewer";

/** A lightbox for notes that have no view of their own — people, evidence,
 *  leads (`openNoteOverlay()`, index.html:640). Rendered like any note, edit
 *  buffer included; wikilinks inside it keep navigating in place. */

export interface NoteOverlayApi {
  open: (path: string) => void;
  close: () => void;
  /** The path currently shown, or null — the wikilink router closes the
   *  overlay before switching to the Applications view. */
  path: string | null;
}

const NoteOverlayContext = createContext<NoteOverlayApi | null>(null);

export function NoteOverlayProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const open = useCallback((next: string) => setPath(next), []);
  const close = useCallback(() => setPath(null), []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (path && !dialog.open) dialog.showModal();
    if (!path && dialog.open) dialog.close();
  }, [path]);

  const value = useMemo(() => ({ open, close, path }), [open, close, path]);
  const label = path ? (path.split("/").pop() ?? path).replace(/\.md$/, "") : "";

  return (
    <NoteOverlayContext.Provider value={value}>
      {children}
      <dialog
        id="noteOverlay"
        ref={dialogRef}
        onCancel={(event) => {
          event.preventDefault();
          close();
        }}
      >
        <div id="noteOverlayBody">
          {path ? (
            <>
              <div className="row">
                <span className="title grow">{label}</span>
                <button className="btn" onClick={close}>
                  Close
                </button>
              </div>
              <div className="note-body">
                <NoteContent path={path} />
              </div>
            </>
          ) : null}
        </div>
      </dialog>
    </NoteOverlayContext.Provider>
  );
}

export function useNoteOverlay(): NoteOverlayApi {
  const api = useContext(NoteOverlayContext);
  if (!api) throw new Error("useNoteOverlay used outside NoteOverlayProvider");
  return api;
}
