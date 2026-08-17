#!/usr/bin/env python3
"""Tests for the safety boundaries the scripts promise.

Each test pins a rule that protects personal data or evidence integrity:
audience filtering on the letterhead, the vault write boundary, which notes
the dashboard may append to, the concurrency guard, and CSRF protection on
the local server. Run with:

    python test_safety.py
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import tempfile
import threading
import unittest
import urllib.request

import init_vault
import new_application
import render_pdf
import serve
import vaultlib as v


CONTACT = """---
type: contact-profile
full_name: Test Person
preferred_name: Test
contacts:
  location: {value: "Testville", audience: application}
  phone: {value: "555-0100", audience: recruiter}
  email: {value: "test@example.com", audience: public}
  linkedin: {value: "linkedin.com/in/test", audience: self}
---

# Contact

## Header

- Current resume title: Tester
"""


class SafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.vault = Path(cls._tmp.name) / "vault"
        init_vault.create(cls.vault)
        (cls.vault / "Personal Information" / "Contact.md").write_text(
            CONTACT, encoding="utf-8")
        cls.app = new_application.create(cls.vault, "Testco", "Tester")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_letterhead_prints_only_application_and_public(self):
        contact = render_pdf.letterhead(self.vault)["contact"]
        self.assertEqual(contact, ["Testville", "test@example.com"])

    def test_resolve_rejects_paths_outside_the_vault(self):
        with self.assertRaises(serve.RequestError):
            serve.resolve(self.vault, "../outside.md")

    def test_render_rejects_paths_outside_the_vault(self):
        outside = Path(self._tmp.name) / "elsewhere"
        outside.mkdir(exist_ok=True)
        with self.assertRaises(serve.RequestError):
            serve.start_render(self.vault, {"path": "../elsewhere", "kind": "resume"})

    def test_append_entry_only_touches_entry_notes(self):
        brief = str((self.app / "Application Brief.md").relative_to(self.vault))
        with self.assertRaises(serve.RequestError):
            serve.append_entry(self.vault, {"path": brief, "title": "Sneaky",
                                            "fields": {"note": "x"}})
        contacts = str((self.app / "Contacts.md").relative_to(self.vault))
        result = serve.append_entry(self.vault, {"path": contacts, "title": "Jo Doe",
                                                 "fields": {"role": "recruiter"}})
        self.assertTrue(result["changed"])

    def test_interview_completion_only_touches_interviews(self):
        brief = str((self.app / "Application Brief.md").relative_to(self.vault))
        with self.assertRaises(serve.RequestError):
            serve.complete_interview(self.vault, {"path": brief, "title": "x"})

    def test_stale_fingerprint_is_refused(self):
        contacts = self.app / "Contacts.md"
        rel = str(contacts.relative_to(self.vault))
        stale = v.fingerprint(contacts)
        contacts.write_text(contacts.read_text(encoding="utf-8") + "\n<!-- obsidian -->\n",
                            encoding="utf-8")
        with self.assertRaises(serve.RequestError):
            serve.append_entry(self.vault, {"path": rel, "title": "Raced Entry",
                                            "fields": {"role": "other"},
                                            "fingerprint": stale})

    def test_empty_sanitized_names_are_rejected(self):
        with self.assertRaises(SystemExit):
            new_application.create(self.vault, ".", "Role")

    def test_posts_require_session_token(self):
        serve.Handler.vault = self.vault
        serve.Handler.token = "test-token-value"
        server = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def post(headers):
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/field",
                    data=json.dumps({"path": "x"}).encode(),
                    headers=headers, method="POST")
                try:
                    return urllib.request.urlopen(request).status
                except urllib.error.HTTPError as error:
                    return error.code

            json_type = {"Content-Type": "application/json"}
            self.assertEqual(post(json_type), 403)
            self.assertEqual(post({**json_type, "X-Session-Token": "wrong"}), 403)
            self.assertEqual(post({"X-Session-Token": "test-token-value"}), 403)
            self.assertEqual(post({**json_type, "Origin": "http://evil.example",
                                   "X-Session-Token": "test-token-value"}), 403)
            self.assertEqual(post({**json_type, "X-Session-Token": "test-token-value"}),
                             404)  # authenticated; fails on the bogus path, not on auth
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
