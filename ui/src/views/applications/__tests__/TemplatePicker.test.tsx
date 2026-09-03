import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ApplicationsView from "../../ApplicationsView";
import { resetSelection } from "../selection";
import { takePendingApplication } from "../../../lib/wikilink";
import type { Application, Schema, VaultIndex } from "../../../api/types";
import {
  renderWithProviders,
  schemaFixture,
} from "../../../components/__tests__/testUtils";

const APP: Application = {
  company: "Globex Corporation",
  position: "Software Engineer II",
  status: "applied",
  active: true,
  path: "Applications/Globex Corporation/Software Engineer II",
  brief: "Applications/Globex Corporation/Software Engineer II/Application Brief.md",
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

const INDEX: VaultIndex = {
  vault: "/vault",
  vault_name: "Career",
  generated_note: "",
  applications: [APP],
  leads: [],
  archived: [],
  company_questions: [],
  contacts: [],
  interviews: [],
  people: [],
  evidence: [],
  skills: {},
};

const REGISTRY = {
  resume: ["built-in:Resume - Figma Inspired", "vault:Sample"],
  "cover-letter": ["built-in:Cover Letter - Figma Inspired"],
};

describe("template pickers", () => {
  let posts: { url: string; body: unknown }[];
  let schema: Schema;

  beforeEach(() => {
    resetSelection();
    takePendingApplication();
    posts = [];
    schema = schemaFixture({ status: ["applied"], templates: REGISTRY });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const ok = (payload: unknown) =>
          new Response(JSON.stringify(payload), { status: 200 });
        if (init?.method === "POST")
          posts.push({ url, body: JSON.parse(String(init.body)) });

        if (url === "/api/index") return ok(INDEX);
        if (url === "/api/schema") return ok(schema);
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
        if (url === "/api/field") return ok({ changed: true, fingerprint: "fp-2" });
        return new Response(JSON.stringify({ error: "no such route" }), {
          status: 404,
        });
      }),
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it("offers every registered template, plus the default", async () => {
    renderWithProviders(<ApplicationsView />);

    const picker = await screen.findByLabelText("Resume template");
    expect(
      Array.from(picker.querySelectorAll("option"), (o) => o.textContent),
    ).toEqual(["Default", "built-in:Resume - Figma Inspired", "vault:Sample"]);

    // The cover letter picker lists its own kind and not the resume's.
    const letters = await screen.findByLabelText("Letter template");
    expect(
      Array.from(letters.querySelectorAll("option"), (o) => o.textContent),
    ).toEqual(["Default", "built-in:Cover Letter - Figma Inspired"]);
  });

  it("writes the choice to the brief through the field flow", async () => {
    renderWithProviders(<ApplicationsView />);

    await userEvent.selectOptions(
      await screen.findByLabelText("Resume template"),
      "vault:Sample",
    );

    await waitFor(() =>
      expect(posts).toContainEqual({
        url: "/api/field",
        body: {
          path: APP.brief,
          field: "resume_template",
          value: "vault:Sample",
          fingerprint: "fp-1",
        },
      }),
    );
  });

  it("is simply absent against a server that has no registry", async () => {
    schema = schemaFixture({ status: ["applied"] });
    renderWithProviders(<ApplicationsView />);

    expect(
      await screen.findByRole("button", { name: "Generate resume" }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Resume template")).toBeNull();
    expect(screen.queryByLabelText("Letter template")).toBeNull();
  });
});
