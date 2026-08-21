// The capture path is deliberately dumb: no site detection, no extraction
// intelligence. What the page shows is what gets stored, verbatim, and the
// dashboard checksums it on arrival. Selecting text first narrows the capture
// to the selection; otherwise the whole page's visible text is sent.

const api = typeof browser !== "undefined" ? browser : chrome;

const $ = (sel) => document.querySelector(sel);
const status = (message, kind) => {
  $("#status").textContent = message;
  $("#status").className = kind || "";
};

async function settings() {
  const stored = await api.storage.local.get({ port: 8765, token: "" });
  return { port: stored.port, token: stored.token };
}

function collectPageText() {
  const selection = window.getSelection().toString();
  return {
    text: selection.trim() ? selection : document.body.innerText,
    fromSelection: Boolean(selection.trim()),
  };
}

async function activeTab() {
  const [tab] = await api.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function capture() {
  const { port, token } = await settings();
  if (!token) {
    status("Not paired yet. Open the extension options and paste the token from the dashboard's Pair extension button.", "bad");
    api.runtime.openOptionsPage();
    return;
  }
  const company = $("#company").value.trim();
  const position = $("#position").value.trim();
  const mode = document.querySelector("input[name=mode]:checked").value;
  if (!company) { status("A company is required.", "bad"); return; }
  if (mode === "application" && !position) {
    status("A position is required for an application (or file it as a lead).", "bad");
    return;
  }

  const button = $("#capture");
  button.disabled = true;
  status("Capturing…");
  try {
    const tab = await activeTab();
    let text = "", fromSelection = false;
    if (mode === "application") {
      const [result] = await api.scripting.executeScript({
        target: { tabId: tab.id }, func: collectPageText,
      });
      ({ text, fromSelection } = result.result);
      $("#meta").textContent = fromSelection
        ? "Capturing the selected text." : "Capturing the whole page's text.";
    }
    const response = await fetch(`http://127.0.0.1:${port}/api/capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-Token": token },
      body: JSON.stringify({ mode, company, position, url: tab.url, title: tab.title, text }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
    status(`Captured: ${body.path}`, "ok");
  } catch (problem) {
    const hint = problem instanceof TypeError
      ? " Is the dashboard running? Start it with serve.py." : "";
    status(`${problem.message}${hint}`, "bad");
  } finally {
    button.disabled = false;
  }
}

async function prefill() {
  // The tab title is usually "Role - Company - Board"; offer it as a starting
  // point in the position field without pretending to parse it.
  const tab = await activeTab().catch(() => null);
  if (tab && tab.title) $("#position").placeholder = tab.title.slice(0, 60);
}

$("#capture").addEventListener("click", capture);
prefill();
