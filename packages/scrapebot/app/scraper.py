import requests
import logging

logger = logging.getLogger(__name__)

class ZendeskScraper:
    def __init__(self, base_url="https://support.optisigns.com/api/v2/help_center/en-us/articles.json"):
        self.base_url = base_url

    def _make_request(self, url, params=None, max_retries=5):
        import time
        retries = 0
        while retries < max_retries:
            # Conditionally pass params to satisfy mock/unittest calls exactly
            if params is not None:
                response = requests.get(url, params=params)
            else:
                response = requests.get(url)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    sleep_time = int(retry_after) if retry_after else 60
                except ValueError:
                    sleep_time = 60
                logger.warning(f"Rate limit (429) hit. Retrying in {sleep_time} seconds (Attempt {retries + 1}/{max_retries})...")
                time.sleep(sleep_time)
                retries += 1
                continue
            
            response.raise_for_status()
            return response
        raise requests.exceptions.HTTPError(f"Max retries ({max_retries}) exceeded due to API rate limits.")

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
                response = self._make_request(url, params=params)
            else:
                response = self._make_request(url)

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
