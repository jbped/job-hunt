import { useEffect } from "react";
import { api, withParam } from "../api/client";
import type { Application, ResolveResponse } from "../api/types";
import { useIndexQuery } from "../api/queries";
import { useNoteOverlay } from "../components/NoteOverlay";
import { useToast, type ToastFn } from "../components/Toast";

/** The wikilink translation layer: resolve the target server-side the way
 *  Obsidian would, then route inside the app — files open directly,
 *  application documents open in the split view, everything else opens in the
 *  note overlay (`openWikilink()`, index.html:613). */

export interface WikilinkHelpers {
  /** Needed to decide whether the resolved note belongs to an application. */
  applications: Application[];
  showApplication: (app: Application, path: string) => void;
  openOverlay: (path: string) => void;
  toast: ToastFn;
}

/** Both the wikilink router and the "New application" button need to put the
 *  split view on a particular document without owning it. They publish a
 *  request; App switches the view and the Applications view selects the target.
 *  The path may be an application folder or any note inside one. */
type ApplicationListener = (path: string) => boolean | void;

const listeners = new Set<ApplicationListener>();
let pending: string | null = null;

/** A listener that took the request says so by returning true; App's
 *  view-switching listener does not, because switching the view is not
 *  selecting the document. Only an unclaimed request is left pending, so a
 *  handled one can never hijack the next Applications mount. */
export function requestApplication(path: string): void {
  let handled = false;
  for (const listener of listeners) if (listener(path) === true) handled = true;
  pending = handled ? null : path;
}

export function subscribeApplicationRequest(
  listener: ApplicationListener,
): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** A request published before the Applications view mounted, consumed once. */
export function takePendingApplication(): string | null {
  const path = pending;
  pending = null;
  return path;
}

export async function openWikilink(
  link: string,
  helpers: WikilinkHelpers,
): Promise<void> {
  let resolved: ResolveResponse;
  try {
    resolved = await api<ResolveResponse>(withParam("/api/resolve", "link", link));
  } catch (error) {
    helpers.toast(error instanceof Error ? error.message : String(error), "error");
    return;
  }
  const path = resolved.path;
  if (/\.(png|jpe?g|pdf)$/i.test(path)) {
    window.open(`/file/${encodeURI(path)}`, "_blank");
    return;
  }
  const app = helpers.applications.find((a) => path.startsWith(a.path + "/"));
  if (app) {
    helpers.showApplication(app, path);
    return;
  }
  helpers.openOverlay(path);
}

/** One delegated listener for every `a[data-wikilink]` on the page, exactly as
 *  the vanilla page did it (index.html:663) — so a note rendered anywhere,
 *  overlay included, routes without wiring. */
export function useWikilinkDelegation(): void {
  const index = useIndexQuery();
  const overlay = useNoteOverlay();
  const toast = useToast();
  const applications = index.data?.applications ?? [];

  useEffect(() => {
    function onClick(event: MouseEvent) {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const link = target.closest("a[data-wikilink]");
      if (!(link instanceof HTMLElement)) return;
      event.preventDefault();
      const value = link.dataset.wikilink;
      if (!value) return;
      void openWikilink(value, {
        applications,
        showApplication: (_app, path) => {
          overlay.close();
          requestApplication(path);
        },
        openOverlay: overlay.open,
        toast,
      });
    }
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [applications, overlay, toast]);
}
