import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useFormModal } from "../FormModal";
import { makeQueryClient, renderWithProviders, schemaFixture } from "./testUtils";

function Opener() {
  const openForm = useFormModal();
  return <button onClick={() => void openForm("lead")}>open</button>;
}

const schema = schemaFixture();

function mockFetch() {
  return vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/schema")
      return new Response(JSON.stringify(schema), { status: 200 });
    if (url === "/api/lead")
      return new Response(JSON.stringify({ path: "Leads/Acme.md" }), { status: 200 });
    return new Response(JSON.stringify({ error: "no such route" }), { status: 404 });
  });
}

describe("useFormModal", () => {
  let fetchMock: ReturnType<typeof mockFetch>;

  beforeEach(() => {
    fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("builds the dialog from the schema form spec", async () => {
    renderWithProviders(<Opener />, makeQueryClient());
    await userEvent.click(screen.getByRole("button", { name: "open" }));

    expect(await screen.findByText("Add a lead")).toBeInTheDocument();
    expect(screen.getByLabelText("Company")).toBeInTheDocument();
    const status = screen.getByLabelText("Status");
    expect(status.tagName).toBe("SELECT");
    expect(
      Array.from((status as HTMLSelectElement).options).map((o) => o.value),
    ).toEqual(["", "open", "passed"]);
  });

  it("refuses to submit while a required field is empty", async () => {
    renderWithProviders(<Opener />, makeQueryClient());
    await userEvent.click(screen.getByRole("button", { name: "open" }));
    await screen.findByText("Add a lead");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));

    expect(await screen.findByText("Company is required.")).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url) === "/api/lead"),
    ).toHaveLength(0);
  });

  it("posts the exact payload to the form's endpoint", async () => {
    renderWithProviders(<Opener />, makeQueryClient());
    await userEvent.click(screen.getByRole("button", { name: "open" }));
    await screen.findByText("Add a lead");
    await userEvent.type(screen.getByLabelText("Company"), "Acme");
    await userEvent.selectOptions(screen.getByLabelText("Status"), "open");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([url]) => String(url) === "/api/lead");
      expect(post).toBeDefined();
      const init = post?.[1];
      expect(init?.method).toBe("POST");
      expect(JSON.parse(String(init?.body))).toEqual({
        company: "Acme",
        status: "open",
      });
    });
  });
});
