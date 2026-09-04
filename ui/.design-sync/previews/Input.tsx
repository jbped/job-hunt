import { Field, FieldDescription, FieldLabel, Input } from "job-hunt-ui";

export const BriefFields = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 360 }}>
    <Field>
      <FieldLabel htmlFor="company">Company</FieldLabel>
      <Input id="company" defaultValue="Globex" />
    </Field>
    <Field>
      <FieldLabel htmlFor="req">Requisition ID</FieldLabel>
      <Input id="req" placeholder="e.g. R-10428" />
      <FieldDescription>Optional — copied from the posting.</FieldDescription>
    </Field>
  </div>
);

export const States = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 360 }}>
    <Input defaultValue="Senior Frontend Engineer" />
    <Input placeholder="Search applications" />
    <Input defaultValue="Not editable" disabled />
    <Input defaultValue="missing-value" aria-invalid />
  </div>
);
