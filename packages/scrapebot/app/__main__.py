import os
import sys
import logging
from dotenv import load_dotenv
from openai import OpenAI
from scraper import ZendeskScraper
from sync import sync_vector_store, get_vector_stores_client

# Set up logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("optibot-sync")

def main():
    # Load .env file if it exists
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Error: OPENAI_API_KEY is not set in environment or .env file.")
        sys.exit(1)

    # Instantiate OpenAI client
    client = OpenAI(api_key=api_key)

    vs_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    if not vs_id:
        logger.info("OPENAI_VECTOR_STORE_ID not found in environment. Auto-provisioning a new Vector Store...")
        try:
            vs_client = get_vector_stores_client(client)
            vector_store = vs_client.create(name="OptiBot Support Vector Store")
            vs_id = vector_store.id
            logger.info("==================================================================")
            logger.info(f"SUCCESSFULLY CREATED VECTOR STORE: {vs_id}")
            logger.info("Please copy this ID and add it to your .env file:")
            logger.info(f"OPENAI_VECTOR_STORE_ID={vs_id}")
            logger.info("==================================================================")
        except Exception as e:
            logger.error(f"Failed to auto-create Vector Store: {e}")
            sys.exit(1)

    logger.info("Starting Zendesk scraping...")
    scraper = ZendeskScraper()

    try:
        active_articles = scraper.fetch_articles()
    except Exception as e:
        logger.error(f"Failed to fetch articles from Zendesk: {e}")
        sys.exit(1)

    if not active_articles:
        logger.warning("No articles fetched from Zendesk. Sync aborted.")
        sys.exit(0)

    logger.info(f"Fetched {len(active_articles)} articles from Zendesk Help Center.")

    # Run sync process
    temp_dir = "./articles"
    logger.info(f"Starting Vector Store sync (ID: {vs_id})...")
    try:
        stats = sync_vector_store(client, vs_id, active_articles, temp_dir)
        logger.info("=================== SYNC COMPLETED ===================")
        logger.info(f"Articles Found in Zendesk:  {stats['total_active']}")
        logger.info(f"Files Added to Store:       {stats['added']}")
        logger.info(f"Files Updated (Replaced):   {stats['updated']}")
        logger.info(f"Files Deleted (Stale):      {stats['deleted']}")
        logger.info(f"Files Skipped (No Change):  {stats['skipped']}")
        logger.info(f"Successfully Synced:        {stats['uploaded_successfully']} / {stats['added'] + stats['updated']} files")
        logger.info("======================================================")
        return {
            "body": {
                "message": "Sync completed successfully",
                "stats": stats
            },
            "statusCode": 200
        }
    except Exception as e:
        logger.error(f"Sync process failed: {e}")
        sys.exit(1)

    return {
        "body": {
            "message": "Sync failed",
        },
        "statusCode": 400
    }

if __name__ == "__main__":
    main()
