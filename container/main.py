"""
Main script for scraping news articles and uploading results to cloud storage.

This script uses the `NewsScraper` class and `SiteConfig` objects to scrape
news articles from multiple websites and upload the results as a JSON file
directly to cloud object storage. Local storage of results is not performed.

Cloud storage uploads are currently implemented for Azure Blob Storage and
the infrastructure is in place to extend support to Amazon S3 and Google Cloud
Storage via the `storage.py` module.

Steps:
    1. Define configurations for websites to scrape.
    2. Use `NewsScraper.scrape_all_sites` to scrape articles
        from these websites.
    3. Upload the scraped articles as a JSON file to the configured
        cloud storage provider.

Usage:
    Run this script directly:
        python main.py

Requirements:
    - Ensure the `models.py`, `scraper.py`, and `storage.py` modules are
    present in the `container` directory.
    - Python 3.7 or higher.
    - External libraries:
        requests,
        fake_useragent,
        bs4,
        pydantic,
        dateutil,
        loguru,
        azure-storage-blob.

Cloud Storage Configuration:
    The upload destination is controlled by environment variables.
    Currently supported:
        Azure:
            Set `AZURE_BLOB_CONTAINER` and `AZURE_STORAGE_CONNECTION_STRING`
            to upload to Azure Blob Storage.
        AWS:
            (TBI) Set `AWS_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, and
            `AWS_SECRET_ACCESS_KEY` to upload to Amazon S3.
        GCP:
            (TBI) Set `GCP_BUCKET` and `GOOGLE_APPLICATION_CREDENTIALS`
            to upload to Google Cloud Storage.

Notes:
    - If no supported cloud storage configuration is provided,
        the script will log a warning and skip upload.
    - To add support for a new provider, implement the upload logic in
      `storage.py` and update the upload section in `main.py`.

"""

import json
import io
import os
from loguru import logger
from scraper import NewsScraper
from models import SiteConfig
import sys
from storage import upload_file_to_azure_blob
from dotenv import load_dotenv

if os.environ.get("USE_DOTENV", "0") == "1":
    load_dotenv("credentials/azure.env")

logger.remove()  # Remove default logger
logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")


def get_site_configs():
    """
    Define and return the site configurations for scraping.

    Returns:
        List[SiteConfig]: A list of `SiteConfig` objects
            for the websites to scrape.
    """
    logger.info("Defining site configurations...")
    BBC_URL = "https://www.bbc.com"
    APNEWS_URL = "https://apnews.com/"

    bbc_config = SiteConfig(
        base_url=BBC_URL,
        news_url=f"{BBC_URL}/news",
        section_selector='section[data-analytics-group="true"]',
        card_selector='div[data-testid="anchor-inner-wrapper"]',
        title_selector="h2",
        link_selector="a",
        keyword="article",
        summary_selector="p[data-testid='card-description']",
        date_selector="time",
        date_attribute="datetime",
    )

    apnews_config = SiteConfig(
        base_url=APNEWS_URL,
        section_selector="div.FourColumnContainer-column",
        card_selector="div.PagePromo",
        title_selector="span.PagePromoContentIcons-text",
        link_selector="a",
        keyword="article",
        date_attribute="data-posted-date-timestamp",
    )

    return [bbc_config, apnews_config]


def main():
    """
    Main function to scrape news articles and save them to a JSON file.
    """
    logger.info("Starting the scraping process...")

    # Get site configurations
    site_configs = get_site_configs()

    # Scrape articles
    try:
        articles = NewsScraper.scrape_all_sites(site_configs)
        logger.info(
            f"Scraping completed. Total articles scraped: {len(articles)}.",
        )
    except Exception as e:
        logger.critical(f"An error occurred during scraping: {e}")
        return

    # Prepare the data to upload as JSON
    result_json = json.dumps(
        [article.model_dump(mode="json") for article in articles],
        ensure_ascii=False,
        indent=4,
    )
    # Convert the JSON string to bytes and wrap in BytesIO for in-memory upload
    data = io.BytesIO(result_json.encode("utf-8"))

    try:
        upload_file_to_azure_blob(
            dest_blob_name="articles.json",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error uploading to Azure Blob: {e}")


if __name__ == "__main__":
    main()
