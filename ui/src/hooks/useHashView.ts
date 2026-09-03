import { useCallback, useState } from "react";

export const VIEWS = [
  "now",
  "leads",
  "applications",
  "board",
  "calendar",
  "people",
  "evidence",
  "agent",
  "archived",
] as const;

export type View = (typeof VIEWS)[number];

function isView(value: string): value is View {
  return (VIEWS as readonly string[]).includes(value);
}

/** Hash routing exactly as the vanilla page did it (`show()`, index.html:1725):
 *  the hash is read once on load, never listened to, and every switch uses
 *  replaceState so the view never enters the back/forward stack. */
export function useHashView(): [View, (view: View) => void] {
  const [view, setViewState] = useState<View>(() => {
    const initial = window.location.hash.replace("#", "");
    return isView(initial) ? initial : "now";
  });

  const setView = useCallback((next: View) => {
    window.history.replaceState(null, "", "#" + next);
    setViewState(next);
  }, []);

  return [view, setView];
}
