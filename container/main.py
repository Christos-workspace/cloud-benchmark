"""
Main script for scraping news articles and saving them to a file.

This script uses the `NewsScraper` class and `SiteConfig` objects to scrape
news articles from multiple websites and saves the results as a JSON file.
Configurations for the websites are defined in `get_site_configs()`.

Steps:
    1. Define configurations for websites to scrape.
    2. Use `NewsScraper.scrape_all_sites` to scrape
        articles from these websites.
    3. Save the scraped articles to `container/articles.json`.

Usage:
    Run this script directly:
        python main.py

Requirements:
    - Ensure the `models.py` and `scraper.py` modules are
        present in the `container` directory.
    - Python 3.7 or higher.
    - External libraries: requests, fake_useragent,
        bs4, pydantic, dateutil, loguru.
"""

import json
from loguru import logger
from scraper import NewsScraper
from models import SiteConfig
import sys

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


def save_to_file(data, filename="container/articles.json"):
    """
    Save data to a JSON file.

    Args:
        data (List[dict]): The list of articles to save.
        filename (str): The output file path
            (default: "container/articles.json").
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Data successfully saved to {filename}.")
    except Exception as e:
        logger.error(f"Failed to save data to {filename}: {e}")


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

    # Save articles to a file
    save_to_file([article.model_dump(mode="json") for article in articles])


if __name__ == "__main__":
    main()
