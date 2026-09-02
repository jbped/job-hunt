import "@testing-library/jest-dom/vitest";

// jsdom implements <dialog> without showModal/close, so the real components
// would throw before any assertion runs. This is the smallest stand-in that
// keeps `open` honest.
const proto = window.HTMLDialogElement?.prototype;
if (proto && !proto.showModal) {
  proto.showModal = function showModal(this: HTMLDialogElement) {
    this.open = true;
  };
  proto.show = function show(this: HTMLDialogElement) {
    this.open = true;
  };
  proto.close = function close(this: HTMLDialogElement) {
    this.open = false;
    this.dispatchEvent(new Event("close"));
  };
}
