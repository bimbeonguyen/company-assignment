import unittest
from transformer import convert_to_markdown

class TestHTMLToMarkdownTransformer(unittest.TestCase):
    def test_basic_conversion(self):
        html = "<h1>How to Setup</h1><p>Follow these steps:</p><ul><li>Step 1</li><li>Step 2</li></ul>"
        expected = "# How to Setup\n\nFollow these steps:\n\n* Step 1\n* Step 2"
        # Since white-spaces/newlines might differ slightly depending on markdownify defaults,
        # we can strip extra whitespaces or do a smart comparison.
        result = convert_to_markdown(html)
        self.assertIn("# How to Setup", result)
        self.assertIn("Follow these steps:", result)
        self.assertIn("* Step 1", result)

    def test_relative_link_expansion(self):
        html = '<p>Check out our <a href="/hc/en-us/articles/12345">Setup Guide</a> or <a href="/hc/articles/67890">Direct Article</a>.</p>'
        result = convert_to_markdown(html)
        # Verify relative links are rewritten to absolute links
        self.assertIn("https://support.optisigns.com/hc/en-us/articles/12345", result)
        self.assertIn("https://support.optisigns.com/hc/articles/67890", result)

    def test_absolute_link_untouched(self):
        html = '<p>Go to <a href="https://google.com">Google</a>.</p>'
        result = convert_to_markdown(html)
        self.assertIn("https://google.com", result)
        self.assertNotIn("https://support.optisigns.comhttps://google.com", result)

    def test_code_block_preservation(self):
        html = '<pre><code>print("Hello World")</code></pre>'
        result = convert_to_markdown(html)
        self.assertIn("```", result)
        self.assertIn('print("Hello World")', result)

    def test_article_url_appending(self):
        html = "<p>Helpful info</p>"
        url = "https://support.optisigns.com/hc/en-us/articles/123"
        result = convert_to_markdown(html, url)
        self.assertIn("Article URL: https://support.optisigns.com/hc/en-us/articles/123", result)
