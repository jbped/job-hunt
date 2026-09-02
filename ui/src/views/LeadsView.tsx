import { useIndexQuery } from "../api/queries";
import type { Lead } from "../api/types";
import { useFormModal } from "../components/FormModal";
import LeadCard from "./leads/LeadCard";

const byDate = (a: Lead, b: Lead) =>
  String(a.date_added ?? "9").localeCompare(String(b.date_added ?? "9"));

/** `renderLeads()` (index.html:1204): pre-application interest, grouped into
 *  three buckets by status. */
export default function LeadsView() {
  const index = useIndexQuery();
  const openForm = useFormModal();
  const leads = index.data?.leads ?? [];

  const open = leads.filter((l) => l.status === "new" || l.status === "pursuing").sort(byDate);
  const promoted = leads.filter((l) => l.status === "promoted").sort(byDate);
  const passed = leads.filter((l) => l.status === "passed").sort(byDate);

  return (
    <section data-view="leads" data-active="">
      <div className="actionbar">
        <button className="btn btn-primary" onClick={() => void openForm("lead")}>
          Add lead
        </button>
        <span className="hint">
          Interest before commitment — a company is enough. Promoting a lead scaffolds the
          application and links back.
        </span>
      </div>
      <h2>Open</h2>
      <div id="leadsOpen">
        {open.length === 0 ? (
          <div className="empty">
            No open leads. “Add lead” records a company worth looking into.
          </div>
        ) : (
          open.map((lead) => <LeadCard key={lead.path} lead={lead} />)
        )}
      </div>
      <h2>Promoted</h2>
      <div id="leadsPromoted">
        {promoted.length === 0 ? (
          <div className="empty">Nothing promoted yet.</div>
        ) : (
          promoted.map((lead) => <LeadCard key={lead.path} lead={lead} />)
        )}
      </div>
      <h2>Passed</h2>
      <div id="leadsPassed">
        {passed.length === 0 ? (
          <div className="empty">Nothing passed on yet.</div>
        ) : (
          passed.map((lead) => <LeadCard key={lead.path} lead={lead} />)
        )}
      </div>
    </section>
  );
}
