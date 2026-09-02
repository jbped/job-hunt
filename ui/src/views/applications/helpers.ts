/** Reading order, not alphabetical: the brief the user owns, then the posting,
 *  then everything derived from it (index.html:829). */
export const NOTE_ORDER = [
  "Job Description",
  "Analysis",
  "Contacts",
  "Resume Content",
  "Cover Letter",
  "Submission Notes",
];

/** The document the right pane shows (the vanilla page's `DOC`). */
export interface DocSelection {
  label: string;
  path: string;
  kind: "note" | "pdf";
}
