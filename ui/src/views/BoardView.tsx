import { useState } from "react";
import { useIndexQuery, useSchemaQuery } from "../api/queries";
import type { Application } from "../api/types";
import BoardCard, { StatusPill, useMoveCard } from "./board/BoardCard";

/** One drop-target column per status. Drag-and-drop and each card's `<select>`
 *  are two paths to the same write (`renderBoard()`, index.html:1116). */
function BoardColumn({
  status,
  terminal,
  applications,
  allStatuses,
  onMove,
}: {
  status: string;
  terminal: string[];
  applications: Application[];
  allStatuses: string[];
  onMove: (app: Application, status: string) => void;
}) {
  const [dragOver, setDragOver] = useState(false);
  const group = applications.filter((app) => app.status === status);

  return (
    <div
      className={dragOver ? "col drop" : "col"}
      onDragOver={(event) => {
        event.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragOver(false);
        const path = event.dataTransfer.getData("text/app-path");
        const app = applications.find((a) => a.path === path);
        if (app) onMove(app, status);
      }}
    >
      <div className="row">
        <StatusPill status={status} terminal={terminal} />
        <span className="muted">{String(group.length)}</span>
      </div>
      {group.map((app) => (
        <BoardCard key={app.path} app={app} allStatuses={allStatuses} onMove={onMove} />
      ))}
    </div>
  );
}

export default function BoardView() {
  const [showTerminal, setShowTerminal] = useState(false);
  const index = useIndexQuery();
  const schema = useSchemaQuery();
  const onMove = useMoveCard();

  const applications = index.data?.applications ?? [];
  const allStatuses = schema.data?.status ?? [];
  const terminal = schema.data?.terminal ?? [];
  const statuses = allStatuses.filter((s) => showTerminal || !terminal.includes(s));

  return (
    <section data-view="board" data-active="">
      <div className="actionbar">
        <label
          className="hint"
          style={{ display: "flex", gap: 6, alignItems: "center", margin: 0, fontWeight: 400 }}
        >
          <input
            type="checkbox"
            style={{ width: "auto" }}
            checked={showTerminal}
            onChange={(event) => setShowTerminal(event.target.checked)}
          />{" "}
          show terminal statuses
        </label>
        <span className="hint">
          Drag a card between columns to change status; the select on each card does the same.
        </span>
      </div>
      <div id="board" className="board">
        {statuses.map((status) => (
          <BoardColumn
            key={status}
            status={status}
            terminal={terminal}
            applications={applications}
            allStatuses={allStatuses}
            onMove={onMove}
          />
        ))}
      </div>
    </section>
  );
}
