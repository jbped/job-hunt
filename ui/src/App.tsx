import { useEffect } from "react";
import { useAuditQuery, useIndexQuery, useSchemaQuery } from "./api/queries";
import { useHashView, type View } from "./hooks/useHashView";
import { useVaultStatePoll } from "./hooks/useVaultStatePoll";
import type { AuditReport } from "./api/types";
import { useFormModal } from "./components/FormModal";
import { useModal } from "./components/Modal";
import { useToast } from "./components/Toast";
import { sessionToken } from "./api/client";
import {
  requestApplication,
  subscribeApplicationRequest,
  useWikilinkDelegation,
} from "./lib/wikilink";
import NowView from "./views/NowView";
import LeadsView from "./views/LeadsView";
import ApplicationsView from "./views/ApplicationsView";
import BoardView from "./views/BoardView";
import InterviewsView from "./views/InterviewsView";
import PeopleView from "./views/PeopleView";
import EvidenceView from "./views/EvidenceView";
import ArchivedView from "./views/ArchivedView";
import InterviewChatView from "./views/InterviewChatView";

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
  { view: "agent", label: "AI Interview" },
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
  agent: InterviewChatView,
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
  const openForm = useFormModal();
  const modal = useModal();
  const toast = useToast();
  useVaultStatePoll();
  useWikilinkDelegation();

  // A request to show one application arrives from a wikilink or from creating
  // one; the view switch is App's to make, the selection the view's.
  useEffect(() => subscribeApplicationRequest(() => setView("applications")), [setView]);

  async function newApplication() {
    const created = await openForm("application");
    if (created) requestApplication(created.path);
  }

  /** The token is per-vault and survives restarts; pairing is a one-time act
   *  unless the token is deliberately re-rolled (--new-token). */
  async function pairExtension() {
    await modal(
      [
        {
          key: "token",
          label:
            "Write token — paste it into the extension's settings. " +
            "It survives restarts; re-roll it with serve.py --new-token.",
          value: sessionToken(),
        },
      ],
      {
        title: "Pair the browser extension",
        submit: "Copy",
        onSubmit: async () => {
          try {
            await navigator.clipboard.writeText(sessionToken());
            toast("Token copied");
          } catch {
            toast("Copy it from the field above", "error");
          }
        },
      },
    );
  }

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
          <button
            id="pairExtension"
            title="Show the session token the browser extension needs"
            onClick={() => void pairExtension()}
          >
            Pair extension
          </button>
          <button className="btn-primary" id="newApp" onClick={() => void newApplication()}>
            New application
          </button>
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
