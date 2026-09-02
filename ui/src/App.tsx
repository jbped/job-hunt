import { useAuditQuery, useIndexQuery, useSchemaQuery } from "./api/queries";
import { useHashView, type View } from "./hooks/useHashView";
import { useVaultStatePoll } from "./hooks/useVaultStatePoll";
import type { AuditReport } from "./api/types";
import NowView from "./views/NowView";
import LeadsView from "./views/LeadsView";
import ApplicationsView from "./views/ApplicationsView";
import BoardView from "./views/BoardView";
import InterviewsView from "./views/InterviewsView";
import PeopleView from "./views/PeopleView";
import EvidenceView from "./views/EvidenceView";
import ArchivedView from "./views/ArchivedView";

/** Nav order and labels are the contract: the hash token for Interviews stays
 *  `calendar` so existing deep-links keep working. */
const NAV: { view: View; label: string }[] = [
  { view: "now", label: "Now" },
  { view: "leads", label: "Leads" },
  { view: "applications", label: "Applications" },
  { view: "board", label: "Board" },
  { view: "calendar", label: "Interviews" },
  { view: "people", label: "People" },
  { view: "evidence", label: "Evidence" },
  { view: "archived", label: "Archived" },
];

const SECTIONS: Record<View, () => JSX.Element> = {
  now: NowView,
  leads: LeadsView,
  applications: ApplicationsView,
  board: BoardView,
  calendar: InterviewsView,
  people: PeopleView,
  evidence: EvidenceView,
  archived: ArchivedView,
};

/** Port of `renderAudit()` (index.html:711): errors outrank warnings, and only
 *  the first of either is quoted — the banner points at the audit, it is not
 *  the audit. */
function AuditBanner({ report }: { report: AuditReport | undefined }) {
  if (report?.errors.length) {
    const extra =
      report.errors.length > 1 ? ` (+${report.errors.length - 1} more)` : "";
    return (
      <div className="banner bad">
        {`${report.errors.length} vault error(s): ${report.errors[0]}${extra}`}
      </div>
    );
  }
  if (report?.warnings.length) {
    return (
      <div className="banner warn">
        {`${report.warnings.length} thing(s) missing information — find the value ` +
          `or leave it Unknown, but don't guess. First: ${report.warnings[0]}`}
      </div>
    );
  }
  return null;
}

export default function App() {
  const [view, setView] = useHashView();
  const index = useIndexQuery();
  const schema = useSchemaQuery();
  const audit = useAuditQuery();
  useVaultStatePoll();

  const loadError = index.error ?? schema.error;
  const ActiveView = SECTIONS[view];

  return (
    <>
      <header>
        <h1>Job Hunt</h1>
        <span className="vault" id="vaultName">
          {schema.data?.vault_name ?? ""}
        </span>
        <nav>
          {NAV.map((item) => (
            <button
              key={item.view}
              data-view={item.view}
              aria-current={item.view === view ? "true" : "false"}
              onClick={() => setView(item.view)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <main>
        {loadError ? (
          <div className="banner bad">
            {"Could not load the vault: " + loadError.message}
          </div>
        ) : null}
        <div id="auditBanner">
          <AuditBanner report={audit.data} />
        </div>
        {index.data && schema.data ? <ActiveView /> : null}
      </main>
    </>
  );
}
