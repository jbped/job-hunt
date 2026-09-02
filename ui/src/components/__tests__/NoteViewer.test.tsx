import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NoteViewer from "../NoteViewer";
import { makeQueryClient, renderWithProviders, schemaFixture } from "./testUtils";

const NOTE = {
  path: "Applications/Acme/Engineer/Analysis.md",
  name: "Analysis",
  text: "# Analysis\n\nSomething true.",
  fingerprint: "abc123",
  readonly: false,
};

describe("NoteViewer", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("/api/note?"))
        return new Response(JSON.stringify(NOTE), { status: 200 });
      if (url === "/api/note/save")
        return new Response(JSON.stringify({ error: "note changed on disk" }), {
          status: 409,
        });
      if (url === "/api/schema")
        return new Response(JSON.stringify(schemaFixture()), { status: 200 });
      return new Response(JSON.stringify({ error: "no such route" }), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches the note only when it is first opened", async () => {
    renderWithProviders(<NoteViewer path={NOTE.path} />);
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).startsWith("/api/note?")),
    ).toHaveLength(0);

    await userEvent.click(screen.getByText("Analysis"));
    expect(await screen.findByText("Something true.")).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).startsWith("/api/note?")),
    ).toHaveLength(1);
  });

  it("toasts a fingerprint conflict and re-reads the vault", async () => {
    const qc = makeQueryClient();
    const invalidate = vi.spyOn(qc, "invalidateQueries");
    renderWithProviders(<NoteViewer path={NOTE.path} />, qc);

    await userEvent.click(screen.getByText("Analysis"));
    await screen.findByText("Something true.");
    await userEvent.click(screen.getByText("edit here"));
    const area = await screen.findByRole("textbox");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    // Shown inline beside Save and raised as a toast.
    expect(await screen.findAllByText("note changed on disk")).toHaveLength(2);
    expect(screen.getByRole("status")).toHaveTextContent("note changed on disk");
    // The buffer stays open so nothing typed is lost.
    expect(area).toBeInTheDocument();
    await waitFor(() => {
      expect(invalidate).toHaveBeenCalledWith({ queryKey: ["index"] });
    });
  });
});
