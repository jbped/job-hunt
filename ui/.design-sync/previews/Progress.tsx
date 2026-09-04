import { Progress } from "job-hunt-ui";

export const EvidenceCoverage = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 360 }}>
    <div>
      <div style={{ fontSize: 13, marginBottom: 6 }}>Roles documented — 2 of 5</div>
      <Progress value={40} />
    </div>
    <div>
      <div style={{ fontSize: 13, marginBottom: 6 }}>Skill matrix backed by evidence</div>
      <Progress value={72} />
    </div>
    <div>
      <div style={{ fontSize: 13, marginBottom: 6 }}>Application brief complete</div>
      <Progress value={100} />
    </div>
  </div>
);

export const Steps = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 360 }}>
    <Progress value={0} />
    <Progress value={25} />
    <Progress value={50} />
    <Progress value={75} />
    <Progress value={100} />
  </div>
);
