import type { ReactNode } from "react";

/** `fieldRow()` (index.html:705): a label and its control on one grid row. */
export default function FieldRow({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="field-row">
      <label>{label}</label>
      {children}
    </div>
  );
}
