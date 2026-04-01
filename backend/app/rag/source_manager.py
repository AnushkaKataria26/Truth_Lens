import datetime
import logging

logger = logging.getLogger(__name__)

# [MOCK] from celery import Celery
# celery_app = Celery("truthlens")

def fetch_wikipedia_summaries():
    logger.info("Fetching wikipedia summaries...")
    # [MOCK] Ingest data and add to Pinecone vector DB
    return True

def fetch_politifact():
    logger.info("Fetching politifact factchecks...")
    return True

def fetch_snopes():
    logger.info("Fetching snopes factchecks...")
    return True

def fetch_isac_feed():
    logger.info("Fetching ISAC threat feed...")
    return True

def fetch_google_factcheck():
    logger.info("Fetching google factcheck API...")
    return True

# Define all knowledge sources as a typed registry
# Each source has: name, type, fetch_function, refresh_interval_hours, last_refreshed
KNOWLEDGE_SOURCES = [
    {
        "name": "wikipedia_summaries",
        "type": "bulk",
        "fetch_fn": fetch_wikipedia_summaries,
        "refresh_interval_hours": 168,  # weekly
        "last_refreshed": None
    },
    {
        "name": "politifact_factchecks",
        "type": "api",
        "fetch_fn": fetch_politifact,
        "refresh_interval_hours": 24,
        "last_refreshed": None
    },
    {
        "name": "snopes_factchecks",
        "type": "scrape",
        "fetch_fn": fetch_snopes,
        "refresh_interval_hours": 24,
        "last_refreshed": None
    },
    {
        "name": "isac_threat_feed",
        "type": "api",
        "fetch_fn": fetch_isac_feed,
        "refresh_interval_hours": 6,
        "last_refreshed": None
    },
    {
        "name": "google_factcheck_api",
        "type": "api",
        "fetch_fn": fetch_google_factcheck,
        "refresh_interval_hours": 12,
        "last_refreshed": None
    },
]

# @celery_app.task
def refresh_stale_sources():
    """
    Celery beat schedule calls this every hour.
    Checks last_refreshed timestamp per source and re-indexes only 
    sources past their refresh_interval.
    """
    now = datetime.datetime.utcnow()
    logger.info(f"Running refresh_stale_sources at {now}")
    
    for source in KNOWLEDGE_SOURCES:
        last_refreshed = source.get("last_refreshed")
        interval = source.get("refresh_interval_hours", 24)
        
        # If never refreshed or past interval, refresh it
        needs_refresh = False
        if not last_refreshed:
            needs_refresh = True
        else:
            elapsed = now - last_refreshed
            if elapsed.total_seconds() >= interval * 3600:
                needs_refresh = True
                
        if needs_refresh:
            try:
                logger.info(f"Refreshing source: {source['name']}")
                success = source["fetch_fn"]()
                if success:
                    source["last_refreshed"] = now
                    logger.info(f"Successfully refreshed {source['name']}")
            except Exception as e:
                logger.error(f"Failed to refresh source {source['name']}: {e}")
