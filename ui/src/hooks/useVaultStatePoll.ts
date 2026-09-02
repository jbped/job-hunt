import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { invalidateAfterWrite } from "../api/queries";
import type { StateResponse } from "../api/types";

/** True while a rerender would eat work in progress — a focused field or the
 *  open form modal (`editingNow()`, index.html:1780). The note overlay is not
 *  counted, matching the vanilla page. */
function editingNow(): boolean {
  if (document.querySelector("dialog[data-modal][open]")) return true;
  const active = document.activeElement;
  return (
    active !== null && ["INPUT", "SELECT", "TEXTAREA"].includes(active.tagName)
  );
}

/** The vault is edited outside this page — Obsidian, the agent, the scripts —
 *  so poll the stat-only digest and invalidate when it moves. A raw interval
 *  rather than `refetchInterval` because the skip-while-editing gate has to
 *  inspect focus state on every tick. */
export function useVaultStatePoll(): void {
  const qc = useQueryClient();
  const known = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function check(): Promise<void> {
      if (document.hidden || editingNow()) return;
      try {
        const { state } = await api<StateResponse>("/api/state");
        if (cancelled || known.current === state) return;
        const first = known.current === null;
        known.current = state;
        if (!first) await invalidateAfterWrite(qc);
      } catch {
        /* the server is briefly gone (a restart); the next tick recovers */
      }
    }

    const timer = window.setInterval(() => void check(), 3000);
    const onVisible = () => {
      if (!document.hidden) void check();
    };
    const onFocus = () => void check();
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onFocus);
    void check();

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onFocus);
    };
  }, [qc]);
}
