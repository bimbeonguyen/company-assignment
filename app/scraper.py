import requests
import logging

logger = logging.getLogger(__name__)

class ZendeskScraper:
    def __init__(self, base_url="https://support.optisigns.com/api/v2/help_center/en-us/articles.json"):
        self.base_url = base_url

    def fetch_articles(self, limit_pages=None):
        """
        Fetches public help center articles from Zendesk API.
        Handles pagination automatically and returns a list of article dicts.
        """
        articles = []
        url = self.base_url
        params = {"sort_by": "updated_at", "sort_order": "asc"}
        pages_fetched = 0

        while url:
            logger.info(f"Fetching articles from: {url}")
            # For the first request, we pass query params. 
            # For subsequent requests, the next_page URL already contains the page and query params, 
            # so we request it directly without overriding them.
            if url == self.base_url:
                response = requests.get(url, params=params)
            else:
                response = requests.get(url)

            response.raise_for_status()
            data = response.json()
            
            page_articles = data.get("articles", [])
            articles.extend(page_articles)
            
            pages_fetched += 1
            if limit_pages and pages_fetched >= limit_pages:
                logger.info(f"Reached page limit of {limit_pages}. Stopping scraper.")
                break
                
            url = data.get("next_page")
            
        logger.info(f"Successfully fetched {len(articles)} articles.")
        return articles
