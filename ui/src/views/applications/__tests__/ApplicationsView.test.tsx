import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ApplicationsView from "../../ApplicationsView";
import { resetSelection } from "../selection";
import { requestApplication, takePendingApplication } from "../../../lib/wikilink";
import type { Application, VaultIndex } from "../../../api/types";
import {
  makeQueryClient,
  renderWithProviders,
  schemaFixture,
} from "../../../components/__tests__/testUtils";

function application(over: Partial<Application> & { company: string }): Application {
  const path = over.path ?? `Applications/${over.company}`;
  return {
    position: "Engineer",
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
    archived: null,
    archive_reason: null,
    archived_from: null,
    ...over,
  };
}

const ACME = application({
  company: "Acme",
  notes: { Analysis: "Applications/Acme/Analysis.md" },
});
const OLDCO = application({ company: "Oldco", status: "rejected", active: false });

const INDEX: VaultIndex = {
  vault: "/vault",
  vault_name: "Career",
  generated_note: "",
  applications: [ACME, OLDCO],
  leads: [],
  archived: [],
  contacts: [],
  interviews: [],
  people: [],
  evidence: [],
  skills: {},
};

function noteFor(path: string) {
  return {
    path,
    name: path.split("/").pop(),
    text: `# ${path.split("/").pop()}\n\nBody of ${path}.`,
    fingerprint: "note-fp",
    readonly: false,
  };
}

describe("ApplicationsView", () => {
  let fetchMock: ReturnType<typeof vi.fn>;
  let posts: { url: string; body: unknown }[];
  let job: string;

  beforeEach(() => {
    resetSelection();
    takePendingApplication();
    posts = [];
    job = "running";
    fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const ok = (payload: unknown) =>
        new Response(JSON.stringify(payload), { status: 200 });
      if (init?.method === "POST")
        posts.push({ url, body: JSON.parse(String(init.body)) });

      if (url === "/api/index") return ok(INDEX);
      if (url === "/api/schema")
        return ok(schemaFixture({ status: ["applied", "rejected"], terminal: ["rejected"] }));
      if (url === "/api/audit") return ok({ errors: [], warnings: [] });
      if (url.startsWith("/api/note?"))
        return ok(noteFor(decodeURIComponent(url.split("path=")[1] ?? "")));
      if (url === "/api/render") return ok({ job: "abc123456789" });
      if (url.startsWith("/api/job/"))
        return ok(
          job === "running"
            ? { state: "running", kind: "resume" }
            : {
                state: "done",
                kind: "resume",
                pdf: "Applications/Acme/Acme Resume.pdf",
                preview: null,
                pages: 1,
                notes: ["1 page"],
                problems: [],
              },
        );
      if (url === "/api/archive")
        return ok({ changed: true, archived: "Archive/Acme", from: ACME.path });
      return new Response(JSON.stringify({ error: "no such route" }), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => vi.unstubAllGlobals());

  it("lists active applications above closed ones and opens the brief first", async () => {
    renderWithProviders(<ApplicationsView />);

    const acme = await screen.findByRole("button", { name: /Acme — Engineer/ });
    expect(acme).toHaveAttribute("aria-current", "true");
    expect(screen.getByText("Closed")).toBeInTheDocument();

    // The right pane defaults to the note the user owns.
    expect(await screen.findByText("Body of Applications/Acme/Application Brief.md.")).toBeInTheDocument();
    const brief = screen.getByRole("button", { name: "Application Brief" });
    expect(brief).toHaveAttribute("aria-current", "true");
  });

  it("switches applications and documents from the rail", async () => {
    renderWithProviders(<ApplicationsView />);

    await userEvent.click(await screen.findByRole("button", { name: "Analysis" }));
    expect(await screen.findByText("Body of Applications/Acme/Analysis.md.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analysis" })).toHaveAttribute(
      "aria-current",
      "true",
    );

    // Picking another application drops the previous document selection.
    await userEvent.click(screen.getByRole("button", { name: /Oldco — Engineer/ }));
    expect(
      await screen.findByText("Body of Applications/Oldco/Application Brief.md."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Analysis" })).not.toBeInTheDocument();
  });

  it("keeps the selection when the view is left and re-entered", async () => {
    const first = renderWithProviders(<ApplicationsView />);
    await userEvent.click(await screen.findByRole("button", { name: "Analysis" }));
    await screen.findByText("Body of Applications/Acme/Analysis.md.");
    first.unmount();

    renderWithProviders(<ApplicationsView />);
    expect(
      await screen.findByText("Body of Applications/Acme/Analysis.md."),
    ).toBeInTheDocument();
  });

  it("shows the application a wikilink asks for", async () => {
    requestApplication("Applications/Oldco/Application Brief.md");
    renderWithProviders(<ApplicationsView />);

    expect(
      await screen.findByText("Body of Applications/Oldco/Application Brief.md."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Oldco — Engineer/ })).toHaveAttribute(
      "aria-current",
      "true",
    );
  });

  it("renders a PDF, polls the job, and shows the artifact in the viewer", async () => {
    renderWithProviders(<ApplicationsView />);

    await userEvent.click(await screen.findByRole("button", { name: "Generate resume" }));
    expect(posts).toContainEqual({
      url: "/api/render",
      body: { path: ACME.path, kind: "resume" },
    });
    expect(screen.getByText("Generating resume…")).toBeInTheDocument();

    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([u]) => String(u).startsWith("/api/job/"))).toBe(
        true,
      ),
    );
    job = "done";

    expect(await screen.findByText("validated", {}, { timeout: 3000 })).toBeInTheDocument();
    const head = document.querySelector(".viewer-head");
    expect(head).not.toBeNull();
    expect(within(head as HTMLElement).getByText("Acme Resume")).toBeInTheDocument();
    expect(document.querySelector('object[type="application/pdf"]')).not.toBeNull();
  });

  it("archives the whole application through the shared modal", async () => {
    const qc = makeQueryClient();
    const invalidate = vi.spyOn(qc, "invalidateQueries");
    renderWithProviders(<ApplicationsView />, qc);

    await userEvent.click(await screen.findByRole("button", { name: "Archive…" }));
    await userEvent.type(await screen.findByLabelText(/Why/), "Position closed");
    await userEvent.click(screen.getByRole("button", { name: "Archive" }));

    await waitFor(() =>
      expect(posts).toContainEqual({
        url: "/api/archive",
        body: { kind: "application", path: ACME.path, reason: "Position closed" },
      }),
    );
    await waitFor(() =>
      expect(invalidate).toHaveBeenCalledWith({ queryKey: ["index"] }),
    );
  });
});
