import { useEffect, useState } from "react";
import type { AgentEvent } from "../../api/types";

export interface ChatMessage {
  role: "user" | "assistant" | "error";
  text: string;
}

export interface ChatState {
  messages: ChatMessage[];
  /** Assistant text arriving token by token, before its message event lands. */
  streaming: string;
  /** A turn is open: the input stays disabled until the `done` sentinel. */
  busy: boolean;
}

const EMPTY: ChatState = { messages: [], streaming: "", busy: false };

/** What one SSE event does to the transcript.
 *
 *  Two shapes carry assistant text: `stream_event` deltas (the CLI's
 *  `--include-partial-messages` output, which arrives token by token) and the
 *  whole `assistant` message that follows them. The deltas render as they
 *  arrive; the finished message replaces them, so a browser that missed a
 *  delta still ends up with the full turn.
 */
export function reduceEvent(event: AgentEvent, state: ChatState): ChatState {
  switch (event.type) {
    case "stream_event": {
      const delta = event.event;
      if (delta?.type === "content_block_delta" && delta.delta?.type === "text_delta") {
        return { ...state, streaming: state.streaming + (delta.delta.text ?? "") };
      }
      return state;
    }
    case "assistant": {
      const text = (event.message?.content ?? [])
        .filter((part) => part.type === "text" || part.text)
        .map((part) => part.text ?? "")
        .join("")
        .trim();
      if (!text) return { ...state, streaming: "" };
      return {
        messages: [...state.messages, { role: "assistant", text }],
        streaming: "",
        busy: state.busy,
      };
    }
    case "agent_error":
      return {
        messages: [...state.messages, { role: "error", text: event.text ?? "" }],
        streaming: "",
        busy: state.busy,
      };
    case "result": {
      if (!event.is_error) return { ...state, streaming: "" };
      return {
        messages: [...state.messages, { role: "error", text: event.result ?? "The agent failed." }],
        streaming: "",
        busy: state.busy,
      };
    }
    case "done":
      return { ...state, streaming: "", busy: false };
    default:
      return state;
  }
}

/** Subscribe to one conversation's event stream.
 *
 *  The stream is a plain `EventSource`: a GET, so no token — the server treats
 *  the unguessable session id as the capability. `messages` is owned here so a
 *  user turn and the agent's answer land in the same list.
 */
export function useAgentStream(sessionId: string | null) {
  const [state, setState] = useState<ChatState>(EMPTY);

  // Deliberately no clear here: the id arrives from the server *during* a
  // turn the user has already typed into, and wiping the transcript then would
  // erase their own message. Starting or switching conversations calls
  // `reset()` instead.
  useEffect(() => {
    if (!sessionId) return;
    const source = new EventSource(
      `/api/agent/stream?session=${encodeURIComponent(sessionId)}`,
    );
    source.onmessage = (message: MessageEvent<string>) => {
      let event: AgentEvent;
      try {
        event = JSON.parse(message.data) as AgentEvent;
      } catch {
        return;
      }
      // Functional, always: a user turn posted a moment ago may not have
      // rendered yet, and reading a stale snapshot would drop it.
      setState((previous) => reduceEvent(event, previous));
    };
    return () => source.close();
  }, [sessionId]);

  function say(text: string): void {
    setState((previous) => ({
      ...previous,
      messages: [...previous.messages, { role: "user", text }],
      busy: true,
    }));
  }

  function fail(text: string): void {
    setState((previous) => ({
      messages: [...previous.messages, { role: "error", text }],
      streaming: "",
      busy: false,
    }));
  }

  function reset(): void {
    setState(EMPTY);
  }

  return { ...state, say, fail, reset };
}
