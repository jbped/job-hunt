import { useIndexQuery, useSchemaQuery } from "../api/queries";
import { api } from "../api/client";
import { useModal } from "../components/Modal";
import { useToast } from "../components/Toast";
import type { CreatedPath } from "../api/types";
import InterviewCard from "./interviews/InterviewCard";

/** Port of `addInterview(null)` (index.html:1658) — the "Schedule interview"
 *  action on this view always asks which application, unlike the same modal
 *  reached from the Applications viewer with one already picked. */
function useScheduleInterview() {
  const modal = useModal();
  const toast = useToast();
  const index = useIndexQuery().data;
  const schema = useSchemaQuery().data;

  return async () => {
    if (!index || !schema) return;
    const applications = [...index.applications].sort((a, b) => Number(b.active) - Number(a.active));
    await modal(
      [
        {
          key: "application",
          label: "Application",
          choices: applications.map((a) => ({ value: a.path, label: `${a.company} — ${a.position}` })),
        },
        { key: "when", label: "Date and time", placeholder: "2026-09-02 14:00 MDT" },
        { key: "stage", label: "Stage", options: schema.stage },
        { key: "method", label: "Method", options: schema.method },
        { key: "point_of_contact", label: "Point of contact" },
        { key: "interviewers", label: "Interviewers" },
        { key: "location_or_link", label: "Location or link" },
      ],
      {
        title: "Schedule an interview",
        submit: "Schedule",
        onSubmit: async (values) => {
          if (!values.when) throw new Error("A date is required.");
          const { application, ...fields } = values;
          if (!application) throw new Error("Pick the application this interview belongs to.");
          const result = await api<CreatedPath>("/api/interview", {
            method: "POST",
            body: { application, ...fields },
          });
          toast(`Scheduled — preparation notes live in ${result.path}`);
        },
      },
    );
  };
}

export default function InterviewsView() {
  const index = useIndexQuery().data;
  const scheduleInterview = useScheduleInterview();

  const upcoming = [...(index?.interviews ?? [])]
    .filter((i) => i.upcoming)
    .sort((a, b) => (a.date || "9").localeCompare(b.date || "9"));
  const previous = [...(index?.interviews ?? [])]
    .filter((i) => !i.upcoming)
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  return (
    <section data-view="calendar" data-active="">
      <div className="actionbar">
        <button className="btn btn-primary" id="scheduleInterview" onClick={() => void scheduleInterview()}>
          Schedule interview
        </button>
        <span className="hint">
          Interviews belong to an application. Set the status to completed when one happens, then record
          the outcome in its note.
        </span>
      </div>
      <h2>Upcoming</h2>
      <div id="calendarUpcoming">
        {upcoming.length ? (
          upcoming.map((iv) => <InterviewCard key={iv.path} interview={iv} />)
        ) : (
          <div className="empty">Nothing scheduled. Use "Schedule interview" above when one lands.</div>
        )}
      </div>
      <h2>Previous</h2>
      <div id="calendarPrevious">
        {previous.length ? (
          previous.map((iv) => <InterviewCard key={iv.path} interview={iv} />)
        ) : (
          <div className="empty">No interviews completed or cancelled yet.</div>
        )}
      </div>
    </section>
  );
}
