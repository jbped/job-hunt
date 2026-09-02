import { afterEach, describe, expect, it, vi } from "vitest";
import {
  requestApplication,
  subscribeApplicationRequest,
  takePendingApplication,
} from "../wikilink";

afterEach(() => {
  takePendingApplication();
});

describe("requestApplication", () => {
  it("keeps the request pending while nobody claims it", () => {
    const watcher = vi.fn();
    const unsubscribe = subscribeApplicationRequest(watcher);

    requestApplication("Applications/Acme/Engineer");

    // App's view-switching listener sees it but does not claim it.
    expect(watcher).toHaveBeenCalledWith("Applications/Acme/Engineer");
    expect(takePendingApplication()).toBe("Applications/Acme/Engineer");
    expect(takePendingApplication()).toBeNull();
    unsubscribe();
  });

  it("drops the pending copy once a listener claims the request", () => {
    const watcher = vi.fn();
    const claimer = vi.fn(() => true);
    const unsubscribeWatcher = subscribeApplicationRequest(watcher);
    const unsubscribeClaimer = subscribeApplicationRequest(claimer);

    requestApplication("Applications/Acme/Engineer/Analysis.md");

    expect(claimer).toHaveBeenCalledWith("Applications/Acme/Engineer/Analysis.md");
    // A claimed request must not linger and hijack the next mount.
    expect(takePendingApplication()).toBeNull();
    unsubscribeWatcher();
    unsubscribeClaimer();
  });
});
