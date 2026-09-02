import type { DocSelection } from "./helpers";

/** The vanilla page held the selected application, the selected document and
 *  the picker filter as module state (`CURRENT`/`DOC`, index.html:374;
 *  `PICK_FILTER`, index.html:855), so leaving the view and coming back kept
 *  all three. The React view unmounts when another one is shown, so the same
 *  state lives beside it instead of inside it. */
interface Selection {
  app: string | null;
  doc: DocSelection | null;
  filter: string;
}

const state: Selection = { app: null, doc: null, filter: "" };

export function selection(): Readonly<Selection> {
  return state;
}

export function setSelectedApp(path: string | null): void {
  state.app = path;
}

export function setSelectedDoc(doc: DocSelection | null): void {
  state.doc = doc;
}

export function setPickFilter(filter: string): void {
  state.filter = filter;
}

/** Page-lifetime state needs clearing between tests. */
export function resetSelection(): void {
  state.app = null;
  state.doc = null;
  state.filter = "";
}
