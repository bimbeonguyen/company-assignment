import unittest
from unittest.mock import patch, MagicMock
from scraper import ZendeskScraper

class TestZendeskScraper(unittest.TestCase):
    @patch('requests.get')
    def test_fetch_articles_single_page(self, mock_get):
        # Setup mock response for a single page of results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {"id": 1, "title": "Article 1", "body": "<p>Content 1</p>", "html_url": "url1", "updated_at": "2026-06-08T12:00:00Z"},
                {"id": 2, "title": "Article 2", "body": "<p>Content 2</p>", "html_url": "url2", "updated_at": "2026-06-08T13:00:00Z"}
            ],
            "count": 2,
            "next_page": None
        }
        mock_get.return_value = mock_response

        scraper = ZendeskScraper()
        articles = scraper.fetch_articles()

        # Check mock calls
        mock_get.assert_called_once_with(
            "https://support.optisigns.com/api/v2/help_center/en-us/articles.json",
            params={"sort_by": "updated_at", "sort_order": "asc"}
        )
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["id"], 1)
        self.assertEqual(articles[1]["id"], 2)

    @patch('requests.get')
    def test_fetch_articles_multiple_pages(self, mock_get):
        # Setup mock responses for paginated results
        mock_response_page1 = MagicMock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "articles": [{"id": 1, "title": "Article 1", "body": "...", "html_url": "url1", "updated_at": "2026-06-08T12:00:00Z"}],
            "count": 2,
            "next_page": "https://support.optisigns.com/api/v2/help_center/en-us/articles.json?page=2&sort_by=updated_at&sort_order=asc"
        }

        mock_response_page2 = MagicMock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            "articles": [{"id": 2, "title": "Article 2", "body": "...", "html_url": "url2", "updated_at": "2026-06-08T13:00:00Z"}],
            "count": 2,
            "next_page": None
        }

        # Mock requests.get side effect to handle paginated requests
        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        scraper = ZendeskScraper()
        articles = scraper.fetch_articles()

        self.assertEqual(mock_get.call_count, 2)
        # First call uses initial base URL and query params
        mock_get.assert_any_call(
            "https://support.optisigns.com/api/v2/help_center/en-us/articles.json",
            params={"sort_by": "updated_at", "sort_order": "asc"}
        )
        # Second call follows next_page link directly without appending initial params
        mock_get.assert_any_call(
            "https://support.optisigns.com/api/v2/help_center/en-us/articles.json?page=2&sort_by=updated_at&sort_order=asc"
        )
        
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["id"], 1)
        self.assertEqual(articles[1]["id"], 2)
