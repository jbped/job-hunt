import { useIndexQuery } from "../api/queries";
import { useAddInterview } from "../lib/actions";
import InterviewCard from "./interviews/InterviewCard";

export default function InterviewsView() {
  const index = useIndexQuery().data;
  const addInterview = useAddInterview();

  const upcoming = [...(index?.interviews ?? [])]
    .filter((i) => i.upcoming)
    .sort((a, b) => (a.date || "9").localeCompare(b.date || "9"));
  const previous = [...(index?.interviews ?? [])]
    .filter((i) => !i.upcoming)
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  return (
    <section data-view="calendar" data-active="">
      <div className="actionbar">
        <button className="btn btn-primary" id="scheduleInterview" onClick={() => void addInterview(null)}>
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
