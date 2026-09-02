import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useHashView } from "../useHashView";

function Probe() {
  const [view, setView] = useHashView();
  return (
    <div>
      <span data-testid="view">{view}</span>
      <button onClick={() => setView("leads")}>go</button>
    </div>
  );
}

describe("useHashView", () => {
  let replaceState: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    replaceState = vi.spyOn(window.history, "replaceState");
  });

  afterEach(() => {
    replaceState.mockRestore();
    window.location.hash = "";
  });

  it("reads a known view out of the hash on mount", () => {
    window.location.hash = "#board";
    render(<Probe />);
    expect(screen.getByTestId("view")).toHaveTextContent("board");
  });

  it("falls back to now for an unknown hash", () => {
    window.location.hash = "#nonsense";
    render(<Probe />);
    expect(screen.getByTestId("view")).toHaveTextContent("now");
  });

  it("switches views through replaceState, never pushState", async () => {
    const pushState = vi.spyOn(window.history, "pushState");
    window.location.hash = "#board";
    render(<Probe />);
    await act(() => userEvent.click(screen.getByRole("button", { name: "go" })));
    expect(screen.getByTestId("view")).toHaveTextContent("leads");
    expect(replaceState).toHaveBeenCalledWith(null, "", "#leads");
    expect(pushState).not.toHaveBeenCalled();
    pushState.mockRestore();
  });
});
