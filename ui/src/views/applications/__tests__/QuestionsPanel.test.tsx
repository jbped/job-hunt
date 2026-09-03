import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ApplicationsView from "../../ApplicationsView";
import { resetSelection } from "../selection";
import { takePendingApplication } from "../../../lib/wikilink";
import type { Application, CompanyQuestion, VaultIndex } from "../../../api/types";
import {
  renderWithProviders,
  schemaFixture,
} from "../../../components/__tests__/testUtils";

function application(company: string, position: string): Application {
  const path = `Applications/${company}/${position}`;
  return {
    company,
    position,
    status: "applied",
    active: true,
    path,
    brief: `${path}/Application Brief.md`,
    fingerprint: "fp-1",
    artifacts: [],
    notes: {},
    tags: [],
    job_url: null,
    posting_source: null,
    discovery_method: null,
    discovery_detail: null,
    date_found: null,
    date_applied: null,
    location: null,
    work_model: null,
    compensation_status: null,
    compensation_currency: null,
    compensation_min: null,
    compensation_max: null,
    compensation_period: null,
    compensation_requested: null,
    experience_level_stated: null,
    next_action: null,
    next_action_date: null,
    resume_template: null,
    cover_letter_template: null,
    archived: null,
    archive_reason: null,
    archived_from: null,
  };
}

const GLOBEX_ONE = application("Globex Corporation", "Software Engineer II");
const GLOBEX_TWO = application("Globex Corporation", "Platform Engineer");
const HOOLI = application("Hooli Systems", "Frontend Engineer");

const BANK = "Applications/Globex Corporation/Company Questions.md";

function question(over: Partial<CompanyQuestion>): CompanyQuestion {
  return {
    company: "Globex Corporation",
    path: BANK,
    question: "Why do you want to work here?",
    fields: { asked_on: `[[${GLOBEX_ONE.path}]]`, date: "2026-09-02" },
    answer: "Because the work is real.",
    ...over,
  };
}

const QUESTIONS: CompanyQuestion[] = [
  question({}),
  question({
    question: "Describe a time you disagreed with a decision.",
    fields: {
      asked_on: `[[${GLOBEX_ONE.path}]]`,
      date: "2026-09-02",
      char_limit: "300",
    },
    answer: "I said so early, in writing, and then backed the call.",
  }),
];

const INDEX: VaultIndex = {
  vault: "/vault",
  vault_name: "Career",
  generated_note: "",
  applications: [GLOBEX_ONE, GLOBEX_TWO, HOOLI],
  leads: [],
  archived: [],
  company_questions: QUESTIONS,
  contacts: [],
  interviews: [],
  people: [],
  evidence: [],
  skills: {},
};

describe("QuestionsPanel", () => {
  let posts: { url: string; body: unknown }[];
  let index: VaultIndex;
  let writes: string[];

  beforeEach(() => {
    resetSelection();
    takePendingApplication();
    posts = [];
    writes = [];
    index = INDEX;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const ok = (payload: unknown) =>
          new Response(JSON.stringify(payload), { status: 200 });
        if (init?.method === "POST")
          posts.push({ url, body: JSON.parse(String(init.body)) });

        if (url === "/api/index") return ok(index);
        if (url === "/api/schema") return ok(schemaFixture({ status: ["applied"] }));
        if (url === "/api/audit") return ok({ errors: [], warnings: [] });
        if (url.startsWith("/api/note?")) {
          const path = decodeURIComponent(url.split("path=")[1] ?? "");
          return ok({
            path,
            name: path.split("/").pop(),
            text: `Body of ${path}.`,
            fingerprint: "note-fp",
            readonly: false,
          });
        }
        if (url === "/api/question")
          return ok({ changed: true, path: BANK, fingerprint: "new-fp" });
        return new Response(JSON.stringify({ error: "no such route" }), {
          status: 404,
        });
      }),
    );
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: {
        writeText: async (text: string) => {
          writes.push(text);
        },
      },
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it("shows the company's bank with its answers, ready to copy", async () => {
    renderWithProviders(<ApplicationsView />);

    expect(
      await screen.findByText("Why do you want to work here?"),
    ).toBeInTheDocument();
    expect(screen.getByText("Because the work is real.")).toBeInTheDocument();
    expect(
      screen.getByText("Describe a time you disagreed with a decision."),
    ).toBeInTheDocument();
    expect(screen.getByText("300 chars")).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: "Copy answer" })[0]);
    expect(writes).toEqual(["Because the work is real."]);
  });

  it("banks a new question with the answer exactly as typed", async () => {
    renderWithProviders(<ApplicationsView />);

    await userEvent.click(await screen.findByRole("button", { name: "Add question" }));
    await userEvent.type(screen.getByLabelText("Question"), "Why this team?");
    await userEvent.type(
      screen.getByLabelText("Your answer, as submitted"),
      "Because of the people.",
    );
    await userEvent.type(screen.getByLabelText("Character limit (optional)"), "500");
    await userEvent.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() =>
      expect(posts).toContainEqual({
        url: "/api/question",
        body: {
          company: "Globex Corporation",
          question: "Why this team?",
          answer: "Because of the people.",
          asked_on: GLOBEX_ONE.path,
          char_limit: "500",
        },
      }),
    );
    // A write refetches the projection rather than patching it locally.
    await waitFor(() =>
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.filter(
          ([u]) => String(u) === "/api/index",
        ).length,
      ).toBeGreaterThan(1),
    );
  });

  it("marks a banked question as asked on this application too", async () => {
    renderWithProviders(<ApplicationsView />);

    // The second Globex application inherits the bank without having been
    // asked any of it yet — the reuse moment this panel exists for.
    await userEvent.click(
      await screen.findByRole("button", { name: /Globex Corporation — Platform Engineer/ }),
    );
    expect(
      await screen.findByText("Because the work is real."),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getAllByRole("button", { name: "Mark asked here" })[0],
    );
    await waitFor(() =>
      expect(posts).toContainEqual({
        url: "/api/question",
        body: {
          company: "Globex Corporation",
          question: "Why do you want to work here?",
          answer: "",
          asked_on: GLOBEX_TWO.path,
        },
      }),
    );
  });

  it("offers the empty state, and no note to edit, for a company with no bank", async () => {
    renderWithProviders(<ApplicationsView />);

    await userEvent.click(
      await screen.findByRole("button", { name: /Hooli Systems — Frontend Engineer/ }),
    );
    expect(
      await screen.findByText(/Nothing banked for Hooli Systems yet/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add question" })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Edit in note" }),
    ).not.toBeInTheDocument();
  });

  it("opens the bank note for fingerprint-guarded editing", async () => {
    renderWithProviders(<ApplicationsView />);

    await userEvent.click(await screen.findByRole("button", { name: "Edit in note" }));
    expect(await screen.findByText(`Body of ${BANK}.`)).toBeInTheDocument();
  });
});
