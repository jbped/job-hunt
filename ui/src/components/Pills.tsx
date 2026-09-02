/** Port of `statusPill()` (index.html:429): "bad" for a terminal status, "good"
 *  for an offer, plain otherwise. */
export function StatusPill({
  status,
  terminal,
}: {
  status: string;
  terminal: string[];
}) {
  const bad = terminal.includes(status);
  const good = status === "offer";
  return <span className={`pill ${bad ? "bad" : good ? "good" : ""}`}>{status}</span>;
}

/** Port of `referencePill()` (index.html:1319). Reference consent is the one
 *  fact a resume cannot guess at, so it is always shown when recorded. */
export function ReferencePill({ status }: { status: string | null }) {
  if (!status) return null;
  const kind = status === "confirmed" ? "good" : status === "declined" ? "bad" : "warn";
  return <span className={`pill ${kind}`}>{`reference: ${status}`}</span>;
}
