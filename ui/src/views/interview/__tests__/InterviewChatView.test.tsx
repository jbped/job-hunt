import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InterviewChatView from "../../InterviewChatView";
import { renderWithProviders } from "../../../components/__tests__/testUtils";
import type { AgentSession } from "../../../api/types";

const SESSIONS: AgentSession[] = [
  {
    id: "11111111-1111-4111-8111-111111111111",
    title: "The billing migration",
    application: "",
    created: "2026-09-01T10:00:00",
    updated: "2026-09-01T10:04:00",
  },
  {
    id: "22222222-2222-4222-8222-222222222222",
    title: "Onboarding funnel work",
    application: "Applications/Globex/Engineer",
    created: "2026-08-30T09:00:00",
    updated: "2026-08-30T09:20:00",
  },
];

/** The smallest EventSource jsdom will accept: the test drives it by hand. */
class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  closed = false;

  url: string;

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  emit(payload: unknown): void {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(payload) }));
  }

  close(): void {
    this.closed = true;
  }
}

function assistant(text: string) {
  return { type: "assistant", message: { content: [{ type: "text", text }] } };
}

describe("the interview chat", () => {
  let posts: { url: string; body: Record<string, unknown> }[];

  beforeEach(() => {
    posts = [];
    FakeEventSource.instances = [];
    vi.stubGlobal("EventSource", FakeEventSource);
    vi.stubGlobal("fetch", async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") {
        posts.push({ url, body: JSON.parse(String(init.body)) as Record<string, unknown> });
        return new Response(
          JSON.stringify({ session_id: "33333333-3333-4333-8333-333333333333" }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.startsWith("/api/agent/sessions")) {
        return new Response(JSON.stringify({ sessions: SESSIONS }), { status: 200 });
      }
      return new Response("{}", { status: 200 });
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it("lists every previous conversation, newest first as the server sent them", async () => {
    renderWithProviders(<InterviewChatView />);
    await screen.findByText("The billing migration");
    const picks = Array.from(document.querySelectorAll("#interviewSessions .pick"));
    expect(picks.map((pick) => pick.textContent)).toEqual([
      expect.stringContaining("The billing migration"),
      expect.stringContaining("Onboarding funnel work"),
    ]);
  });

  it("posts a turn, streams the answer, and re-enables the input on the sentinel", async () => {
    const user = userEvent.setup();
    renderWithProviders(<InterviewChatView />);
    await screen.findByText("The billing migration");

    await user.type(screen.getByLabelText("Message"), "I led the billing migration");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0].url).toBe("/api/agent/interview");
    // No session id on the first turn: the server mints one.
    expect(posts[0].body).toEqual({ message: "I led the billing migration" });
    expect(screen.getByText("I led the billing migration")).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toBeDisabled();

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    const stream = FakeEventSource.instances[0];
    expect(stream.url).toContain("session=33333333-3333-4333-8333-333333333333");

    stream.emit({
      type: "stream_event",
      event: { type: "content_block_delta", delta: { type: "text_delta", text: "What was " } },
    });
    await screen.findByText(/What was/);
    stream.emit(assistant("What was the **denominator**?"));
    await screen.findByText("denominator");

    expect(screen.getByLabelText("Message")).toBeDisabled();
    stream.emit({ type: "result", is_error: false });
    stream.emit({ type: "done" });
    await waitFor(() => expect(screen.getByLabelText("Message")).not.toBeDisabled());
  });

  it("carries the session id when a listed conversation is reopened", async () => {
    const user = userEvent.setup();
    renderWithProviders(<InterviewChatView />);
    await user.click(await screen.findByText("Onboarding funnel work"));

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    expect(FakeEventSource.instances[0].url).toContain(SESSIONS[1].id);

    await user.type(screen.getByLabelText("Message"), "Carrying on");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0].body).toEqual({ message: "Carrying on", session_id: SESSIONS[1].id });
  });

  it("shows an agent failure instead of hanging with the input disabled", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", async (_input: RequestInfo, init?: RequestInit) => {
      if (init?.method === "POST") {
        return new Response(JSON.stringify({ error: "The AI agent could not start." }), {
          status: 502,
        });
      }
      return new Response(JSON.stringify({ sessions: [] }), { status: 200 });
    });
    renderWithProviders(<InterviewChatView />);
    await user.type(await screen.findByLabelText("Message"), "hello");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("The AI agent could not start.");
    expect(screen.getByLabelText("Message")).not.toBeDisabled();
  });
});
