import { Button } from "job-hunt-ui";

export const Variants = () => (
  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
    <Button>Draft the resume</Button>
    <Button variant="secondary">Save brief</Button>
    <Button variant="outline">Open posting</Button>
    <Button variant="ghost">Skip</Button>
    <Button variant="destructive">Withdraw</Button>
    <Button variant="link">View analysis</Button>
  </div>
);

export const Sizes = () => (
  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
    <Button size="xs">Extra small</Button>
    <Button size="sm">Small</Button>
    <Button size="default">Default</Button>
    <Button size="lg">Large</Button>
  </div>
);

export const States = () => (
  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
    <Button>Enabled</Button>
    <Button disabled>Disabled</Button>
    <Button variant="outline" disabled>
      Render (needs a draft)
    </Button>
  </div>
);
