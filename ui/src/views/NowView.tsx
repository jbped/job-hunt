import type { ReactNode } from "react";
import { useIndexQuery, useSchemaQuery } from "../api/queries";
import { useHashView } from "../hooks/useHashView";
import { requestApplication } from "../lib/wikilink";
import { ObsidianLink } from "../components/NoteViewer";
import type { Application } from "../api/types";

const today = () => new Date().toISOString().slice(0, 10);
const days = (a: string, b: string) => Math.round((+new Date(b) - +new Date(a)) / 86400000);

/** Port of `statusPill()` (index.html:429): "bad" for terminal statuses, "good"
 *  for an offer, plain otherwise. */
function StatusPill({ status, terminal }: { status: string; terminal: string[] }) {
  const bad = terminal.includes(status);
  const good = status === "offer";
  return <span className={`pill ${bad ? "bad" : good ? "good" : ""}`}>{status}</span>;
}

interface QueueItem {
  date: string;
  title: string;
  detail: string;
  open?: () => void;
  link?: string;
}

/** `renderNow()`'s upcoming panel (index.html:725): interviews first, then one
 *  aggregated queue across applications, people, contacts, and leads —
 *  soonest first, overdue flagged. */
function UpcomingPanel() {
  const index = useIndexQuery().data;
  const [, setView] = useHashView();
  if (!index) return null;

  const active = index.applications.filter((a) => a.active);
  const upcoming = [...index.interviews]
    .filter((i) => i.upcoming)
    .sort((a, b) => (a.date || "9").localeCompare(b.date || "9"));

  const queue: QueueItem[] = [];
  for (const app of active) {
    if (app.next_action && app.next_action_date)
      queue.push({
        date: app.next_action_date,
        title: `${app.company} — ${app.position}`,
        detail: app.next_action,
        open: () => requestApplication(app.path),
      });
  }
  for (const p of index.people) {
    if (p.next_follow_up)
      queue.push({
        date: p.next_follow_up,
        title: `Follow up with ${p.name}`,
        detail: p.company_context || "",
        link: p.path,
      });
  }
  for (const c of index.contacts) {
    if (c.next_follow_up)
      queue.push({
        date: c.next_follow_up,
        title: `Follow up with ${c.name}`,
        detail: `${c.company} — ${c.position}`,
        link: c.note,
      });
  }
  for (const lead of index.leads) {
    if (lead.next_follow_up && lead.status && ["new", "pursuing"].includes(lead.status))
      queue.push({
        date: lead.next_follow_up,
        title: `Lead: ${lead.company}`,
        detail: lead.role && lead.role !== "Unknown" ? lead.role : "",
        open: () => setView("leads"),
      });
  }
  queue.sort((a, b) => a.date.localeCompare(b.date) || a.title.localeCompare(b.title));

  if (!upcoming.length && !queue.length) return <div className="empty">Nothing scheduled.</div>;

  return (
    <>
      {upcoming.map((iv) => (
        <div className="card row" key={iv.path}>
          <span className="pill">{iv.when || "date unknown"}</span>
          <span className="grow">
            <a
              href="#"
              className="title"
              title="Open the application"
              onClick={(event) => {
                event.preventDefault();
                requestApplication(iv.application);
              }}
            >
              {`${iv.company} — ${iv.stage || "interview"}`}
            </a>
            <div className="muted">{iv.method ?? ""}</div>
          </span>
          <ObsidianLink path={iv.path} />
        </div>
      ))}
      {queue.map((item, i) => {
        const overdue = item.date < today();
        return (
          <div className="card row" key={i}>
            <span className={`pill ${overdue ? "bad" : ""}`}>
              {overdue ? `overdue ${item.date}` : item.date}
            </span>
            <span className="grow">
              <span className="title">{item.title}</span>
              <div className="muted">{item.detail}</div>
            </span>
            {item.open ? (
              <button className="btn" onClick={item.open}>
                Open
              </button>
            ) : (
              <ObsidianLink path={item.link!} />
            )}
          </div>
        );
      })}
    </>
  );
}

interface TodoItem {
  title: string;
  detail: string;
  app: Application | null;
}

/** `renderNow()`'s todo panel: applications missing a next action or date, gone
 *  stale, plus unconfirmed references. */
function TodoPanel() {
  const index = useIndexQuery().data;
  if (!index) return null;

  const active = index.applications.filter((a) => a.active);
  const items: TodoItem[] = [];
  for (const app of active) {
    if (!app.next_action)
      items.push({ title: `${app.company} — ${app.position}`, detail: "No next action recorded", app });
    else if (!app.next_action_date)
      items.push({
        title: `${app.company} — ${app.position}`,
        detail: `"${app.next_action}" has no due date`,
        app,
      });
    if (
      app.date_applied &&
      ["applied", "screening"].includes(app.status) &&
      days(app.date_applied, today()) > 14
    )
      items.push({
        title: `${app.company} — ${app.position}`,
        detail: `${days(app.date_applied, today())} days since applying, no status change`,
        app,
      });
  }
  const unconfirmed = index.people.filter(
    (p) => p.reference_status && p.reference_status !== "confirmed",
  ).length;
  if (unconfirmed) items.push({ title: "References", detail: `${unconfirmed} not yet confirmed`, app: null });

  if (!items.length) return <div className="empty">Nothing outstanding.</div>;

  return (
    <>
      {items.map((item, i) => (
        <div className="card row" key={i}>
          <span className="grow">
            <span className="title">{item.title}</span>
            <div className="muted">{item.detail}</div>
          </span>
          {item.app ? (
            <button className="btn" onClick={() => requestApplication(item.app!.path)}>
              Open
            </button>
          ) : null}
        </div>
      ))}
    </>
  );
}

/** `renderNow()`'s pipeline panel: one card per status in schema order. */
function PipelinePanel(): ReactNode {
  const index = useIndexQuery().data;
  const schema = useSchemaQuery().data;
  if (!index || !schema) return null;

  return (
    <>
      {schema.status.map((status) => {
        const group = index.applications.filter((a) => a.status === status);
        if (!group.length) return null;
        return (
          <div className="card" key={status}>
            <div className="row">
              <StatusPill status={status} terminal={schema.terminal} />
              <span className="muted">{group.length}</span>
            </div>
            <div className="stack" style={{ marginTop: 8 }}>
              {group.map((app) => (
                <div key={app.path}>
                  <a
                    href="#"
                    onClick={(event) => {
                      event.preventDefault();
                      requestApplication(app.path);
                    }}
                  >
                    {`${app.company} — ${app.position}`}
                  </a>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </>
  );
}

export default function NowView() {
  return (
    <section data-view="now" data-active="">
      <h2>What's coming up</h2>
      <div id="upcoming">
        <UpcomingPanel />
      </div>
      <h2>What I need to do</h2>
      <div id="todo">
        <TodoPanel />
      </div>
      <h2>Where I am</h2>
      <div id="pipeline" className="grid">
        <PipelinePanel />
      </div>
    </section>
  );
}
