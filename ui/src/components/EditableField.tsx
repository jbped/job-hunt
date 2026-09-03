import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { invalidateAfterWrite, useSchemaQuery } from "../api/queries";
import type { FieldSaveResult, VocabularyKey } from "../api/types";
import { useToast } from "./Toast";

/** A frontmatter field the schema allows editing. Saves on change, not on
 *  keypress, so a half-typed value is never written (`editable()`,
 *  index.html:679). */
export interface EditableFieldProps {
  /** The note written to — an application's brief, or the note's own path. */
  path: string;
  field: string;
  value: string;
  /** Names a vocabulary in /api/schema; renders a select instead of an input. */
  enumKey?: VocabularyKey;
  /** An explicit option list, when the vocabulary is not one of the schema's. */
  values?: string[];
  /** What the empty option reads as in a select. Defaults to an em dash. */
  emptyLabel?: string;
  /** An accessible name, for controls whose FieldRow label is not associated. */
  ariaLabel?: string;
  fingerprint?: string;
  type?: string;
  placeholder?: string;
}

export default function EditableField({
  path,
  field,
  value,
  enumKey,
  values,
  emptyLabel,
  ariaLabel,
  fingerprint,
  type,
  placeholder,
}: EditableFieldProps) {
  const [current, setCurrent] = useState(value);
  const [stamp, setStamp] = useState(fingerprint);
  const schema = useSchemaQuery();
  const toast = useToast();
  const qc = useQueryClient();

  // The poll redraws with fresh data once the user is idle; adopt it.
  useEffect(() => setCurrent(value), [value]);
  useEffect(() => setStamp(fingerprint), [fingerprint]);

  const allowed = enumKey ? schema.data?.[enumKey] : values;

  async function commit(next: string) {
    setCurrent(next);
    try {
      const result = await api<FieldSaveResult>("/api/field", {
        method: "POST",
        body: { path, field, value: next, fingerprint: stamp },
      });
      setStamp(result.fingerprint);
      toast(result.changed ? "Saved" : "No change");
      // No invalidation here: it would collapse editors and steal focus while
      // the user moves between fields. The vault poller redraws once they're idle.
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      toast(message, "error");
      if (message.includes("changed on disk")) await invalidateAfterWrite(qc);
    }
  }

  if (allowed)
    return (
      <select
        aria-label={ariaLabel}
        value={current}
        onChange={(event) => void commit(event.target.value)}
      >
        {["", ...allowed].map((option) => (
          <option key={option} value={option}>
            {option || emptyLabel || "—"}
          </option>
        ))}
      </select>
    );

  // The vanilla page listened for the DOM's own `change` event: it fires on
  // blur and on Enter, never per keystroke.
  return (
    <input
      aria-label={ariaLabel}
      type={type ?? "text"}
      placeholder={placeholder ?? ""}
      value={current}
      onChange={(event) => setCurrent(event.target.value)}
      onBlur={(event) => {
        if (event.target.value !== value) void commit(event.target.value);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") event.currentTarget.blur();
      }}
    />
  );
}
