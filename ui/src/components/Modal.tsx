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
import { useQueryClient } from "@tanstack/react-query";
import { invalidateAfterWrite } from "../api/queries";

/** The generic dialog behind archive, add-contact, add-interview and pairing —
 *  the port of `modal()` (index.html:1576). Fields are described, not written:
 *  a caller says what it wants collected and what to do with the values. */

export interface ModalField {
  key: string;
  label: string;
  /** Fixed value/label pairs, e.g. an application picker. */
  choices?: { value: string; label: string }[];
  /** A controlled vocabulary; a blank first option is added, as in the vanilla page. */
  options?: string[];
  multiline?: boolean;
  type?: string;
  placeholder?: string;
  value?: string;
}

export interface ModalOptions {
  title: string;
  submit?: string;
  /** Runs with the trimmed values while the dialog is still open. Throwing
   *  keeps it open and shows the message, so nothing typed is lost. */
  onSubmit?: (values: Record<string, string>) => Promise<void> | void;
}

export type OpenModal = (
  fields: ModalField[],
  opts: ModalOptions,
) => Promise<Record<string, string> | null>;

const ModalContext = createContext<OpenModal | null>(null);

interface ModalRequest {
  fields: ModalField[];
  opts: ModalOptions;
  resolve: (values: Record<string, string> | null) => void;
}

function initialValues(fields: ModalField[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const field of fields) {
    out[field.key] =
      field.value ?? (field.choices ? (field.choices[0]?.value ?? "") : "");
  }
  return out;
}

export function ModalProvider({ children }: { children: ReactNode }) {
  const [request, setRequest] = useState<ModalRequest | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const qc = useQueryClient();

  const open = useCallback<OpenModal>(
    (fields, opts) =>
      new Promise((resolve) => {
        setValues(initialValues(fields));
        setProblem("");
        setBusy(false);
        setRequest({ fields, opts, resolve });
      }),
    [],
  );

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (request && !dialog.open) dialog.showModal();
    if (!request && dialog.open) dialog.close();
  }, [request]);

  const finish = useCallback(
    (result: Record<string, string> | null) => {
      setRequest((current) => {
        current?.resolve(result);
        return null;
      });
    },
    [],
  );

  const submit = async () => {
    if (!request) return;
    setBusy(true);
    setProblem("");
    const trimmed: Record<string, string> = {};
    for (const [key, value] of Object.entries(values)) trimmed[key] = value.trim();
    try {
      await request.opts.onSubmit?.(trimmed);
      finish(trimmed);
      // The vanilla page refreshed after every modal submit; a modal that only
      // collects values has no write to invalidate, so it skips this.
      if (request.opts.onSubmit) await invalidateAfterWrite(qc);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  const value = useMemo(() => open, [open]);

  return (
    <ModalContext.Provider value={value}>
      {children}
      <dialog
        id="modal"
        data-modal=""
        ref={dialogRef}
        onCancel={(event) => {
          event.preventDefault();
          finish(null);
        }}
      >
        <form method="dialog" id="modalForm" onSubmit={(e) => e.preventDefault()}>
          {request ? (
            <>
              <h2 style={{ marginTop: 0 }}>{request.opts.title}</h2>
              {request.fields.map((field) => {
                const id = `modal-${field.key}`;
                const onChange = (next: string) =>
                  setValues((current) => ({ ...current, [field.key]: next }));
                return (
                  <div key={field.key}>
                    <label htmlFor={id}>{field.label}</label>
                    {field.choices ? (
                      <select
                        id={id}
                        value={values[field.key] ?? ""}
                        onChange={(e) => onChange(e.target.value)}
                      >
                        {field.choices.map((choice) => (
                          <option key={choice.value} value={choice.value}>
                            {choice.label}
                          </option>
                        ))}
                      </select>
                    ) : field.options ? (
                      <select
                        id={id}
                        value={values[field.key] ?? ""}
                        onChange={(e) => onChange(e.target.value)}
                      >
                        {["", ...field.options].map((option) => (
                          <option key={option} value={option}>
                            {option || "—"}
                          </option>
                        ))}
                      </select>
                    ) : field.multiline ? (
                      <textarea
                        id={id}
                        rows={3}
                        placeholder={field.placeholder ?? ""}
                        value={values[field.key] ?? ""}
                        onChange={(e) => onChange(e.target.value)}
                      />
                    ) : (
                      <input
                        id={id}
                        type={field.type ?? "text"}
                        placeholder={field.placeholder ?? ""}
                        value={values[field.key] ?? ""}
                        onChange={(e) => onChange(e.target.value)}
                      />
                    )}
                  </div>
                );
              })}
              <div
                className="muted"
                style={{ marginTop: 10, color: problem ? "var(--bad)" : undefined }}
              >
                {problem}
              </div>
              <div
                className="row"
                style={{ marginTop: 16, justifyContent: "flex-end" }}
              >
                <button className="btn" type="button" onClick={() => finish(null)}>
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={busy}
                  onClick={() => void submit()}
                >
                  {request.opts.submit ?? "Save"}
                </button>
              </div>
            </>
          ) : null}
        </form>
      </dialog>
    </ModalContext.Provider>
  );
}

export function useModal(): OpenModal {
  const open = useContext(ModalContext);
  if (!open) throw new Error("useModal used outside ModalProvider");
  return open;
}
