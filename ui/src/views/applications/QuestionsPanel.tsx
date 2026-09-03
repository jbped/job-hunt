import { useCallback } from "react";
import { api } from "../../api/client";
import { invalidateAfterWrite } from "../../api/queries";
import { useQueryClient } from "@tanstack/react-query";
import { useNoteOverlay } from "../../components/NoteOverlay";
import { useToast } from "../../components/Toast";
import { useAddQuestion } from "../../lib/actions";
import type { CompanyQuestion } from "../../api/types";

/** Every application folder a question has been asked on, from its `Asked on`
 *  bullet. The bullet is markdown the user may also have hand-edited, so the
 *  links are pulled out rather than assumed. */
function askedOn(question: CompanyQuestion): string[] {
  const raw = question.fields.asked_on ?? "";
  return [...raw.matchAll(/\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]/g)].map((m) =>
    m[1].trim(),
  );
}

/** The bank of short-form questions this company asks, with the answers that
 *  were submitted. It exists for the reuse moment: a second application to the
 *  same company shows the answers already given, ready to paste back.
 *
 *  Answers are the user's writing. Nothing here composes one — the add form
 *  sends what was typed, and editing happens in the note itself, behind the
 *  same fingerprint guard as every other note. */
export default function QuestionsPanel({
  company,
  appPath,
  questions,
}: {
  company: string;
  appPath: string;
  questions: CompanyQuestion[];
}) {
  const addQuestion = useAddQuestion();
  const overlay = useNoteOverlay();
  const toast = useToast();
  const qc = useQueryClient();

  const copy = useCallback(
    async (answer: string) => {
      try {
        await navigator.clipboard.writeText(answer);
        toast("Answer copied");
      } catch {
        toast("Could not reach the clipboard");
      }
    },
    [toast],
  );

  // Recording that a banked question came up here too: the answer is left
  // empty on purpose, so the server keeps the one already written.
  const markAsked = useCallback(
    async (question: CompanyQuestion) => {
      await api("/api/question", {
        method: "POST",
        body: { company, question: question.question, answer: "", asked_on: appPath },
      });
      toast("Marked as asked here");
      await invalidateAfterWrite(qc);
    },
    [appPath, company, qc, toast],
  );

  const notePath = questions[0]?.path ?? "";

  return (
    <div className="card">
      <h3>Company questions</h3>
      <div className="stack">
        {questions.map((question) => {
          const links = askedOn(question);
          const limit = question.fields.char_limit;
          return (
            <div key={question.question}>
              <div className="row">
                <span className="title grow">{question.question}</span>
                {limit ? <span className="pill">{limit} chars</span> : null}
              </div>
              {question.answer ? (
                <div className="muted" style={{ whiteSpace: "pre-wrap" }}>
                  {question.answer}
                </div>
              ) : (
                <div className="muted">No answer written yet.</div>
              )}
              <div className="row" style={{ gap: 6, marginTop: 4 }}>
                {links.map((link) => (
                  <span className="pill" key={link}>
                    {link.split("/").slice(-2).join(" · ")}
                  </span>
                ))}
                <span className="grow" />
                {question.answer ? (
                  <button className="btn" onClick={() => void copy(question.answer)}>
                    Copy answer
                  </button>
                ) : null}
                {links.includes(appPath) ? null : (
                  <button className="btn" onClick={() => void markAsked(question)}>
                    Mark asked here
                  </button>
                )}
              </div>
            </div>
          );
        })}
        {!questions.length ? (
          <div className="muted">
            Nothing banked for {company} yet. Add the questions this application
            asks and the answers you gave, and the next application here will
            have them.
          </div>
        ) : null}
      </div>
      <div className="rail-actions" style={{ marginTop: 8 }}>
        <button className="btn" onClick={() => void addQuestion(company, appPath)}>
          Add question
        </button>
        {notePath ? (
          <button className="btn" onClick={() => overlay.open(notePath)}>
            Edit in note
          </button>
        ) : null}
      </div>
    </div>
  );
}
