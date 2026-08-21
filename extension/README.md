# Job Hunt Capture extension

One click on a job posting sends the page's URL, title, and visible text to
the local dashboard, which scaffolds the application and stores the
checksummed verbatim capture — the same files the CLI scripts would create.
Select part of the page first to capture just the selection. "Lead only"
files a lightweight lead instead and stores no posting text.

Deliberately dumb by design: no site detection, no extraction cleanup. The
capture is verbatim-what-the-page-showed, with the method recorded
(`source_kind: extension`). The vault scripts' stdlib-only rule does not
apply here — the extension is its own build surface — but it is plain
no-build JavaScript anyway.

## Install (unpacked, for now)

Chrome: `chrome://extensions` → enable Developer mode → **Load unpacked** →
pick this `extension/` directory.

Firefox: `about:debugging#/runtime/this-firefox` → **Load Temporary
Add-on…** → pick `manifest.json`. Temporary add-ons unload when Firefox
closes. If captures fail with a network error, also grant the site
permission for `127.0.0.1` under the extension's Permissions tab.

## Pair with the dashboard

1. Start the dashboard: `python serve.py` (from the skill's `scripts/`).
2. Click **Pair extension** in the dashboard's top bar and copy the token.
3. Open the extension's options and paste it (the popup opens options for
   you when unpaired). The token is per-session: restart the dashboard,
   pair again.

The dashboard only ever listens on `127.0.0.1`; the token is what stops
other pages and extensions from writing to your vault.
