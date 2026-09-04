import { Badge } from "job-hunt-ui";

export const Stages = () => (
  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
    <Badge>Applied</Badge>
    <Badge variant="secondary">Screening</Badge>
    <Badge variant="outline">Researching</Badge>
    <Badge variant="destructive">Rejected</Badge>
    <Badge variant="ghost">Withdrawn</Badge>
  </div>
);

export const DocumentState = () => (
  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
    <Badge variant="outline">Scaffold</Badge>
    <Badge variant="secondary">Drafted</Badge>
    <Badge>Rendered</Badge>
    <Badge variant="destructive">Stale</Badge>
  </div>
);
