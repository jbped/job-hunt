import { useIndexQuery } from "../api/queries";
import { useFormModal } from "../components/FormModal";
import NoteViewer from "../components/NoteViewer";

/** Port of `renderEvidence()` (index.html:1477): roles then accomplishments,
 *  each a `noteViewer` whose summary also carries the company and status. The
 *  shared `NoteViewer` has no slot for that extra summary content (frozen —
 *  see the branch report for this gap); the company/status ride along in the
 *  title text instead, which is the closest approximation without editing it. */
export default function EvidenceView() {
  const index = useIndexQuery().data;
  const openForm = useFormModal();

  const roles = (index?.evidence ?? []).filter((e) => e.kind === "role");
  const accomplishments = (index?.evidence ?? []).filter((e) => e.kind === "accomplishment");
  const skills = Object.entries(index?.skills ?? {});

  function group(kind: "Roles" | "Accomplishments", items: typeof roles) {
    if (!items.length) return null;
    return (
      <div key={kind}>
        <h2>{kind}</h2>
        <div className="card stack">
          {items.map((item) => (
            <NoteViewer
              key={item.path}
              path={item.path}
              title={
                [item.title, item.company, item.status].filter(Boolean).join(" — ") || item.title
              }
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <section data-view="evidence" data-active="">
      <div className="actionbar">
        <button className="btn btn-primary" id="addRole" onClick={() => void openForm("role")}>
          Add role
        </button>
        <button className="btn" id="addAccomplishment" onClick={() => void openForm("accomplishment")}>
          Add accomplishment
        </button>
        <span className="hint">
          These create scaffolds with open questions. The facts come from evidence interviews with your
          agent, or by hand in Obsidian.
        </span>
      </div>
      <h2>Career evidence</h2>
      <div id="evidence">
        {group("Roles", roles)}
        {group("Accomplishments", accomplishments)}
        {skills.length ? (
          <div>
            <h2>Skills</h2>
            <div className="card stack">
              {skills.map(([name, entries]) => (
                <div className="row" key={name}>
                  <span className="title" style={{ minWidth: "10rem" }}>
                    {name}
                  </span>
                  <span className="muted grow">{entries.map((e) => e.title).join(" · ")}</span>
                </div>
              ))}
              <div className="muted">
                Derived from evidence frontmatter — a skill not listed here has no evidence behind it.
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
