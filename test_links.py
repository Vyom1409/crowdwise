"""
Automated checks for CrowdWise external documentation links ("Quick Start" and "Startup").
Verifies central config constants, FastAPI static serving, README anchors,
and checks that index.html renders real anchor links cleanly without hardcoded URLs.
"""

import os
import re
import unittest
from fastapi.testclient import TestClient

import app as crowdwise_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestExternalLinksConfig(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(crowdwise_app.app)
        self.links_path = os.path.join(BASE_DIR, "src", "config", "links.js")
        self.index_path = os.path.join(BASE_DIR, "index.html")
        self.readme_path = os.path.join(BASE_DIR, "README.md")

    def test_links_config_exists_and_exports_constants(self):
        self.assertTrue(os.path.isfile(self.links_path), "src/config/links.js must exist")
        with open(self.links_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("export const QUICK_START_URL", content)
        self.assertIn("export const STARTUP_URL", content)
        self.assertIn("export const EXTERNAL_LINKS", content)
        self.assertIn("export function openExternal", content)
        self.assertIn("https://github.com/Vyom1409/crowdwise#quick-start", content)
        self.assertIn("https://github.com/Vyom1409/crowdwise#startup", content)
        self.assertIn('window.open(url, "_blank", "noopener,noreferrer")', content)

    def test_fastapi_serves_links_config(self):
        resp = self.client.get("/src/config/links.js")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("EXTERNAL_LINKS", resp.text)

    def test_index_html_imports_config_without_hardcoding_urls(self):
        with open(self.index_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Verify module import from central config
        self.assertIn("from '/src/config/links.js'", html)
        # Ensure GitHub quick-start / startup URLs are not hardcoded in index.html
        self.assertNotIn("github.com/Vyom1409/crowdwise#quick-start", html)
        self.assertNotIn("github.com/Vyom1409/crowdwise#startup", html)

        # Ensure real anchor attributes and accessibility hooks are constructed
        self.assertIn("a.target = '_blank'", html)
        self.assertIn("a.rel = 'noopener noreferrer'", html)
        self.assertIn('id="header-ext-links"', html)
        self.assertIn('id="mobile-nav-drawer"', html)
        self.assertIn('id="footer-help-links"', html)
        self.assertIn('<h3 id="footer-help-heading">Help</h3>', html)

    def test_readme_has_matching_section_headings(self):
        with open(self.readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        self.assertIsNotNone(re.search(r"^##\s+Quick Start\s*$", readme, re.MULTILINE))
        self.assertIsNotNone(re.search(r"^###\s+Startup\s*$", readme, re.MULTILINE))


if __name__ == "__main__":
    unittest.main()
