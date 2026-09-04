import { Checkbox, Label } from "job-hunt-ui";

export const SubmissionChecklist = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 360 }}>
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Checkbox id="resume" defaultChecked />
      <Label htmlFor="resume">Resume rendered</Label>
    </div>
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Checkbox id="letter" defaultChecked />
      <Label htmlFor="letter">Cover letter rendered</Label>
    </div>
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Checkbox id="questions" />
      <Label htmlFor="questions">Company questions answered</Label>
    </div>
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Checkbox id="referral" disabled />
      <Label htmlFor="referral">Referral requested</Label>
    </div>
  </div>
);

export const States = () => (
  <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
    <Checkbox />
    <Checkbox defaultChecked />
    <Checkbox checked="indeterminate" />
    <Checkbox disabled />
    <Checkbox disabled defaultChecked />
  </div>
);
