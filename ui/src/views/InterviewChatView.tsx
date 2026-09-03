import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAgentSessionsQuery } from "../api/queries";
import { renderMarkdown } from "../lib/markdown";
import { useToast } from "../components/Toast";
import type { InterviewTurnResult } from "../api/types";
import { useAgentStream } from "./interview/useAgentStream";

/** The evidence interview, run by the AI CLI the server spawns.
 *
 *  Two columns, both borrowed wholesale from the other views: the rail lists
 *  every past conversation, the main column is the conversation itself. The
 *  agent writes vault notes through its own file tools under `--restricted`;
 *  nothing typed here reaches a command line.
 */
export default function InterviewChatView() {
  const sessions = useAgentSessionsQuery();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const { messages, streaming, busy, say, fail, reset } = useAgentStream(sessionId);
  const log = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = log.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messages, streaming]);

  async function send(): Promise<void> {
    const message = draft.trim();
    if (!message || busy) return;
    setDraft("");
    say(message);
    try {
      const result = await api<InterviewTurnResult>("/api/agent/interview", {
        method: "POST",
        body: sessionId ? { message, session_id: sessionId } : { message },
      });
      if (result.session_id !== sessionId) setSessionId(result.session_id);
      await queryClient.invalidateQueries({ queryKey: ["agent-sessions"] });
    } catch (error) {
      fail(error instanceof Error ? error.message : String(error));
    }
  }

  async function closeConversation(): Promise<void> {
    if (!sessionId) return;
    try {
      await api<InterviewTurnResult>("/api/agent/interview", {
        method: "POST",
        body: { session_id: sessionId, close: true },
      });
      toast("Interview closed. Reopen it from the list to carry on.");
    } catch (error) {
      toast(error instanceof Error ? error.message : String(error), "error");
    }
    reset();
    setSessionId(null);
  }

  const listed = sessions.data?.sessions ?? [];

  return (
    <section data-view="agent" data-active="">
      <div className="actionbar">
        <button
          className="btn btn-primary"
          id="newInterview"
          onClick={() => {
            reset();
            setSessionId(null);
          }}
        >
          New interview
        </button>
        {sessionId ? (
          <button className="btn" id="closeInterview" onClick={() => void closeConversation()}>
            Close interview
          </button>
        ) : null}
        <span className="hint">
          The agent reads and writes this vault's markdown and nothing else — no shell, no web
          access. Check what it wrote in Evidence, and the audit banner above.
        </span>
      </div>

      <div className="split">
        <aside className="rail">
          <div className="card">
            <h3>Conversations</h3>
            <div className="pick-list" id="interviewSessions">
              {listed.length ? (
                listed.map((entry) => (
                  <button
                    key={entry.id}
                    className="pick"
                    aria-current={entry.id === sessionId ? "true" : "false"}
                    onClick={() => {
                      if (entry.id !== sessionId) reset();
                      setSessionId(entry.id);
                    }}
                  >
                    <span className="grow">{entry.title}</span>
                    <span className="sub">{(entry.updated || "").slice(0, 10)}</span>
                  </button>
                ))
              ) : (
                <div className="empty">No interviews yet. Ask the first question.</div>
              )}
            </div>
            <div className="muted" style={{ marginTop: "8px" }}>
              Nothing here runs until you send a message — opening a conversation costs nothing.
              Transcripts are supporting material, not vault truth; the notes the agent writes
              are.
            </div>
          </div>
        </aside>

        <div>
          <div className="card chat-log" id="chatLog" ref={log}>
            {messages.length === 0 && !streaming ? (
              <div className="empty">
                {sessionId
                  ? "This conversation is not running. Sending a message resumes it — the agent picks its history back up from where you left off."
                  : "Tell the agent which role or accomplishment you want to work through."}
              </div>
            ) : null}
            {messages.map((message, position) => (
              <div key={position} className={`bubble ${message.role}`}>
                {message.role === "assistant" ? (
                  renderMarkdown(message.text)
                ) : (
                  <p>{message.text}</p>
                )}
                {message.role === "error" ? (
                  <p className="muted">
                    If the agent is not signed in, or cannot start at all, docs/setup.md has
                    the two ways to give the container credentials.
                  </p>
                ) : null}
              </div>
            ))}
            {streaming ? (
              <div className="bubble assistant" data-streaming="">
                {renderMarkdown(streaming)}
              </div>
            ) : null}
          </div>

          <form
            className="card chat-input"
            onSubmit={(event) => {
              event.preventDefault();
              void send();
            }}
          >
            <textarea
              id="interviewMessage"
              aria-label="Message"
              rows={3}
              value={draft}
              disabled={busy}
              placeholder={busy ? "The agent is answering…" : "Type your answer"}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                  event.preventDefault();
                  void send();
                }
              }}
            />
            <div className="row">
              <span className="muted grow">
                {busy ? "Working…" : "Ctrl+Enter sends."}
              </span>
              <button className="btn btn-primary" type="submit" disabled={busy || !draft.trim()}>
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
