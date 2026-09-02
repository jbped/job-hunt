/** Small formatting helpers the vanilla page kept at module scope
 *  (index.html:388–390). */

export const today = (): string => new Date().toISOString().slice(0, 10);

export const days = (a: string, b: string): number =>
  Math.round((+new Date(b) - +new Date(a)) / 86400000);

/** A note's display label: its file name without the extension. */
export function noteLabel(path: string): string {
  return (path.split("/").pop() ?? path).replace(/\.md$/, "");
}
