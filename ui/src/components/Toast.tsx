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

export type ToastKind = "ok" | "error";
export type ToastFn = (message: string, kind?: ToastKind) => void;

const ToastContext = createContext<ToastFn | null>(null);

interface ToastState {
  message: string;
  kind: ToastKind;
  /** Distinguishes two identical messages so the timer restarts. */
  seq: number;
}

/** Port of `toast()` (index.html:391): one node, `data-show`/`data-kind`, and
 *  an error stays up long enough to read (6s) where an ack does not (2.5s). */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);
  const seq = useRef(0);

  const show = useCallback<ToastFn>((message, kind) => {
    seq.current += 1;
    setToast({ message, kind: kind ?? "ok", seq: seq.current });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(
      () => setToast(null),
      toast.kind === "error" ? 6000 : 2500,
    );
    return () => window.clearTimeout(timer);
  }, [toast]);

  const value = useMemo(() => show, [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        id="toast"
        role="status"
        data-show={toast ? "1" : undefined}
        data-kind={toast?.kind ?? "ok"}
      >
        {toast?.message ?? ""}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastFn {
  const fn = useContext(ToastContext);
  if (!fn) throw new Error("useToast used outside ToastProvider");
  return fn;
}
