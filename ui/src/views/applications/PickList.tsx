import { useState } from "react";
import type { Application } from "../../api/types";
import { today } from "./helpers";

/** `pickButton()`, index.html:856 — the dot carries the state: brand while the
 *  application is active, bad once its next action is overdue, blank when the
 *  application is closed. */
function PickButton({
  item,
  selectedPath,
  onSelect,
}: {
  item: Application;
  selectedPath: string;
  onSelect: (app: Application) => void;
}) {
  const overdue = !!item.next_action_date && item.next_action_date < today();
  return (
    <button
      className="pick"
      data-app={item.path}
      aria-current={item.path === selectedPath ? "true" : "false"}
      onClick={() => onSelect(item)}
    >
      <span className={`dot ${item.active ? (overdue ? "bad" : "brand") : ""}`} />
      <span>{`${item.company} — ${item.position}`}</span>
      <span className="sub">{item.status}</span>
    </button>
  );
}

/** `fillPickList()`, index.html:1000 — active first, closed beneath their own
 *  label. The filter (index.html:876) survives re-renders as component state,
 *  so selecting a result does not clear it, and only appears once the list is
 *  long enough to need it. */
export default function PickList({
  applications,
  selectedPath,
  onSelect,
}: {
  applications: Application[];
  selectedPath: string;
  onSelect: (app: Application) => void;
}) {
  const [filter, setFilter] = useState("");

  const needle = filter.toLowerCase();
  const match = (a: Application) =>
    !needle ||
    `${a.company} ${a.position} ${a.status}`.toLowerCase().includes(needle);

  const active = applications.filter((a) => a.active && match(a));
  const closed = applications.filter((a) => !a.active && match(a));

  return (
    <div className="card">
      <h3>Applications</h3>
      {applications.length > 6 ? (
        <div className="pick-filter">
          <input
            type="search"
            placeholder="Filter…"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          />
        </div>
      ) : null}
      <div className="pick-list">
        {active.map((item) => (
          <PickButton
            key={item.path}
            item={item}
            selectedPath={selectedPath}
            onSelect={onSelect}
          />
        ))}
        {closed.length ? <div className="group-label">Closed</div> : null}
        {closed.map((item) => (
          <PickButton
            key={item.path}
            item={item}
            selectedPath={selectedPath}
            onSelect={onSelect}
          />
        ))}
        {!active.length && !closed.length ? (
          <div className="muted" style={{ padding: "4px 9px" }}>
            No matches.
          </div>
        ) : null}
      </div>
    </div>
  );
}
