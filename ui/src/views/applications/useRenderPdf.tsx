import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { invalidateAfterWrite } from "../../api/queries";
import type { Application, JobStatus, RenderResult } from "../../api/types";
import type { DocSelection } from "./helpers";

/** `renderPdf()`, index.html:1687 — POST the render, then poll the job every
 *  700ms until it stops running. The finished artifact is shown where the other
 *  documents are shown rather than squeezed into the rail, so the hook hands
 *  the selection back to the view. */
export interface RenderPdf {
  /** What the rail's `#renderOut` box currently says. */
  message: ReactNode;
  start: (app: Application, kind: "resume" | "cover-letter") => Promise<void>;
}

export function useRenderPdf(onArtifact: (doc: DocSelection) => void): RenderPdf {
  const [message, setMessage] = useState<ReactNode>(null);
  const timer = useRef<number | null>(null);
  const qc = useQueryClient();

  const stop = () => {
    if (timer.current !== null) {
      window.clearInterval(timer.current);
      timer.current = null;
    }
  };

  useEffect(() => stop, []);

  const start = useCallback<RenderPdf["start"]>(
    async (app, kind) => {
      stop();
      setMessage(
        <div className="muted">{`Generating ${kind.replace("-", " ")}…`}</div>,
      );
      let job: string;
      try {
        ({ job } = await api<RenderResult>("/api/render", {
          method: "POST",
          body: { path: app.path, kind },
        }));
      } catch (error) {
        setMessage(
          <div className="banner bad">
            {error instanceof Error ? error.message : String(error)}
          </div>,
        );
        return;
      }

      timer.current = window.setInterval(() => {
        void (async () => {
          let state: JobStatus;
          try {
            state = await api<JobStatus>(`/api/job/${job}`);
          } catch (error) {
            stop();
            setMessage(
              <div className="banner bad">
                {error instanceof Error ? error.message : String(error)}
              </div>,
            );
            return;
          }
          if (state.state === "running") return;
          stop();

          if (state.state === "failed") {
            setMessage(<div className="banner bad">{state.error}</div>);
            return;
          }
          onArtifact({
            label: (state.pdf.split("/").pop() ?? state.pdf).replace(/\.pdf$/, ""),
            path: state.pdf,
            kind: "pdf",
          });
          setMessage(
            state.problems?.length ? (
              <div className="banner bad">
                {"Do not submit yet — " + state.problems.join("; ")}
              </div>
            ) : (
              <div className="muted">
                <span className="pill good">validated</span>
                {" " + state.notes.join(" · ")}
              </div>
            ),
          );
          await invalidateAfterWrite(qc);
        })();
      }, 700);
    },
    [onArtifact, qc],
  );

  return { message, start };
}
