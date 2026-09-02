import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { VaultIndex } from "../../api/types";
import ArchivedView from "../ArchivedView";
import LeadsView from "../LeadsView";
import {
  makeQueryClient,
  renderWithProviders,
  schemaFixture,
} from "../../components/__tests__/testUtils";

/** Archiving from Leads and restoring from Archived are the two halves of the
 *  API's only removal flow (`archiveUnit()`/`restoreUnit()`, index.html:1527/1540) —
 *  both must invalidate the index projection so every view sees the move. */

const LEAD_INDEX: VaultIndex = {
  vault: "/vault",
  vault_name: "Career",
  generated_note: "",
  applications: [],
  leads: [
    {
      company: "Acme",
      role: "Engineer",
      url: null,
      source: null,
      date_added: "2026-08-01",
      status: "new",
      next_follow_up: null,
      passed_reason: null,
      application: null,
      path: "Leads/Acme.md",
      fingerprint: "lead-fp",
    },
  ],
  archived: [],
  contacts: [],
  interviews: [],
  people: [],
  evidence: [],
  skills: {},
};

const ARCHIVED_INDEX: VaultIndex = {
  ...LEAD_INDEX,
  leads: [],
  archived: [
    {
      kind: "lead",
      company: "Acme",
      position: null,
      status: null,
      archived: "2026-09-01",
      archive_reason: "Went quiet",
      archived_from: "Leads/Acme.md",
      path: "Archive/Leads/Acme.md",
      brief: "Archive/Leads/Acme.md",
      fingerprint: "arch-fp",
    },
  ],
};

function mockFetch(index: VaultIndex) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/index") return new Response(JSON.stringify(index), { status: 200 });
    if (url === "/api/schema")
      return new Response(JSON.stringify(schemaFixture()), { status: 200 });
    if (url === "/api/archive")
      return new Response(
        JSON.stringify({ changed: true, archived: "Archive/Leads/Acme.md", from: "Leads/Acme.md" }),
        { status: 200 },
      );
    if (url === "/api/unarchive")
      return new Response(
        JSON.stringify({ changed: true, restored: "Leads/Acme.md" }),
        { status: 200 },
      );
    return new Response(
      JSON.stringify({ error: `no such route: ${url} ${init?.method ?? "GET"}` }),
      { status: 404 },
    );
  });
}

describe("archive / restore", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("archiving a lead POSTs /api/archive and invalidates the index", async () => {
    const fetchMock = mockFetch(LEAD_INDEX);
    vi.stubGlobal("fetch", fetchMock);
    const qc = makeQueryClient();
    const invalidate = vi.spyOn(qc, "invalidateQueries");
    renderWithProviders(<LeadsView />, qc);

    await userEvent.click(await screen.findByRole("button", { name: "Archive…" }));
    await screen.findByText("Archive Acme?");
    await userEvent.click(screen.getByRole("button", { name: "Archive" }));

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([url]) => String(url) === "/api/archive");
      expect(post).toBeDefined();
      const init = post?.[1];
      expect(init?.method).toBe("POST");
      expect(JSON.parse(String(init?.body))).toEqual({
        kind: "lead",
        path: "Leads/Acme.md",
        reason: "",
      });
    });
    await waitFor(() => {
      expect(invalidate).toHaveBeenCalledWith({ queryKey: ["index"] });
    });
  });

  it("restoring an archived unit POSTs /api/unarchive and invalidates the index", async () => {
    const fetchMock = mockFetch(ARCHIVED_INDEX);
    vi.stubGlobal("fetch", fetchMock);
    const qc = makeQueryClient();
    const invalidate = vi.spyOn(qc, "invalidateQueries");
    renderWithProviders(<ArchivedView />, qc);

    await userEvent.click(await screen.findByRole("button", { name: "Restore" }));

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([url]) => String(url) === "/api/unarchive");
      expect(post).toBeDefined();
      const init = post?.[1];
      expect(init?.method).toBe("POST");
      expect(JSON.parse(String(init?.body))).toEqual({ path: "Archive/Leads/Acme.md" });
    });
    await waitFor(() => {
      expect(invalidate).toHaveBeenCalledWith({ queryKey: ["index"] });
    });
  });
});
