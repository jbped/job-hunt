import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import EditableField from "../EditableField";
import { makeQueryClient, renderWithProviders, schemaFixture } from "./testUtils";

/** The inline field editor is the one write that deliberately does NOT redraw
 *  the page: a re-render mid-edit collapses editors and steals focus while
 *  someone is moving between fields, and the vault poller redraws once they
 *  are idle (`editable()`, index.html:679). A conflict is the exception —
 *  there the page is provably stale and has to catch up. */

const PATH = "Applications/Acme/Engineer/Application Brief.md";

function mockFetch(fieldResponse: () => Response) {
  return vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/schema")
      return new Response(JSON.stringify(schemaFixture()), { status: 200 });
    if (url === "/api/field") return fieldResponse();
    return new Response(JSON.stringify({ error: "no such route" }), { status: 404 });
  });
}

describe("EditableField", () => {
  let fetchMock: ReturnType<typeof mockFetch>;

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("on a successful save", () => {
    beforeEach(() => {
      fetchMock = mockFetch(
        () =>
          new Response(JSON.stringify({ changed: true, fingerprint: "new-print" }), {
            status: 200,
          }),
      );
      vi.stubGlobal("fetch", fetchMock);
    });

    it("posts the field and toasts, without invalidating the index", async () => {
      const qc = makeQueryClient();
      const invalidate = vi.spyOn(qc, "invalidateQueries");
      renderWithProviders(
        <EditableField
          path={PATH}
          field="next_action"
          value="call them"
          fingerprint="old-print"
        />,
        qc,
      );

      const input = screen.getByRole("textbox");
      await userEvent.clear(input);
      await userEvent.type(input, "send the follow-up");
      await userEvent.tab();

      await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Saved"));
      const post = fetchMock.mock.calls.find(([url]) => String(url) === "/api/field");
      expect(JSON.parse(String(post?.[1]?.body))).toEqual({
        path: PATH,
        field: "next_action",
        value: "send the follow-up",
        fingerprint: "old-print",
      });
      // The contract: no redraw, so the field the user is in keeps its focus.
      expect(invalidate).not.toHaveBeenCalled();
    });

    it("says so when the value did not actually change", async () => {
      vi.stubGlobal(
        "fetch",
        mockFetch(
          () =>
            new Response(
              JSON.stringify({ changed: false, fingerprint: "old-print" }),
              { status: 200 },
            ),
        ),
      );
      const qc = makeQueryClient();
      const invalidate = vi.spyOn(qc, "invalidateQueries");
      renderWithProviders(
        <EditableField
          path={PATH}
          field="status"
          value="open"
          enumKey="lead_status"
        />,
        qc,
      );

      await waitFor(() => expect(screen.getByRole("combobox")).toBeInTheDocument());
      await userEvent.selectOptions(screen.getByRole("combobox"), "passed");

      await waitFor(() =>
        expect(screen.getByRole("status")).toHaveTextContent("No change"),
      );
      expect(invalidate).not.toHaveBeenCalled();
    });
  });

  describe("on a 409 conflict", () => {
    beforeEach(() => {
      fetchMock = mockFetch(
        () =>
          new Response(
            JSON.stringify({
              error: "Application Brief.md changed on disk since it was read",
            }),
            { status: 409 },
          ),
      );
      vi.stubGlobal("fetch", fetchMock);
    });

    it("toasts the conflict and re-reads the vault", async () => {
      const qc = makeQueryClient();
      const invalidate = vi.spyOn(qc, "invalidateQueries");
      renderWithProviders(
        <EditableField
          path={PATH}
          field="next_action"
          value="call them"
          fingerprint="stale-print"
        />,
        qc,
      );

      const input = screen.getByRole("textbox");
      await userEvent.clear(input);
      await userEvent.type(input, "send the follow-up");
      await userEvent.tab();

      await waitFor(() =>
        expect(screen.getByRole("status")).toHaveTextContent("changed on disk"),
      );
      expect(screen.getByRole("status")).toHaveAttribute("data-kind", "error");
      await waitFor(() =>
        expect(invalidate).toHaveBeenCalledWith({ queryKey: ["index"] }),
      );
    });
  });
});
