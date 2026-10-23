"""Keep HTML templates and browser assets current during local development."""
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse
import unittest

from jinja2 import DictLoader

from app import ROOT, create_app


class AssetLinks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.urls = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" or tag == "link" and attributes.get("rel") == "stylesheet":
            self.urls.append(attributes.get("src") or attributes["href"])


class FrontendDeliveryTests(unittest.TestCase):
    def test_asset_urls_match_the_current_file_contents(self):
        client = create_app({"TESTING": True}).test_client()
        urls = AssetLinks(client.get("/").get_data(as_text=True)).urls
        self.assertEqual(len(urls), 4)
        for url in urls:
            with self.subTest(url=url):
                parsed = urlparse(url)
                expected = sha256((ROOT / parsed.path.lstrip("/")).read_bytes()).hexdigest()[:12]
                self.assertEqual(parse_qs(parsed.query)["v"], [expected])
                response = client.get(url)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_workspace_html_is_not_stored_in_browser_cache(self):
        response = create_app({"TESTING": True}).test_client().get("/")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_changed_templates_reload_in_a_running_app(self):
        app = create_app({"TESTING": True})
        loader = DictLoader({"index.html": "first template"})
        app.jinja_env.loader = loader
        client = app.test_client()
        self.assertEqual(client.get("/").get_data(as_text=True), "first template")
        loader.mapping["index.html"] = "updated template"
        self.assertEqual(client.get("/").get_data(as_text=True), "updated template")


if __name__ == "__main__":
    unittest.main()
