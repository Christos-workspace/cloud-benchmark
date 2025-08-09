"""
News scraping logic.

This module defines the `NewsScraper` class and its associated methods for
fetching, parsing, and processing web pages.

Classes:
    NewsScraper: A web scraper for extracting news articles based on a given
        `SiteConfig` object.

Methods:
    get_page_html(url: str) -> str: Fetches the HTML content of a given URL.
    get_soup(url: str) -> BeautifulSoup: Parses the HTML content into a
        BeautifulSoup object.
    parse_date(date_str: str) -> date: Converts a date string into a Python
        date object.
    scrape_site() -> List[NewsArticle]: Scrapes a single website and returns
        a list of structured news articles.
    scrape_all_sites(configs: List[SiteConfig]) -> List[NewsArticle]: Scrapes
        multiple websites using a list of `SiteConfig` objects.
"""

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from typing import List
from datetime import datetime as dt, timezone, date
from dateutil import parser
from models import NewsArticle, SiteConfig
from loguru import logger


class NewsScraper:
    """
    A web scraper for extracting news articles from websites
    based on a given configuration.

    The NewsScraper class uses a SiteConfig object to define
    how to locate and extract news articles from a website.
    It provides methods for retrieving, parsing, and processing web pages,
    as well as extracting relevant information into structured
    NewsArticle objects.

    Attributes:
        config (SiteConfig): The configuration settings for the scraper,
        including CSS selectors and other parameters for
        extracting article details.

    """

    def __init__(self, config: SiteConfig):
        self.config = config

    @staticmethod
    def get_page_html(url: str) -> str:
        """
        Fetch the HTML content of a given URL.

        Args:
            url (str): The URL of the webpage to fetch.

        Returns:
                str: The HTML content of the webpage as a string.
        """
        response = requests.get(
            url,
            headers={"User-Agent": UserAgent().random},
        )
        if response.status_code != 200:
            logger.error(
                f"Failed to fetch {url}, status code: {response.status_code}",
            )
        return response.content

    @staticmethod
    def get_soup(url: str):
        """
        Parse the HTML content of a given URL into a BeautifulSoup object.

        Args:
            url (str): The URL of the webpage to scrape.

        Returns:
            BeautifulSoup: Parsed HTML content.
        """
        html = NewsScraper.get_page_html(url)
        return bs(html, "html.parser")

    @staticmethod
    def parse_date(date_str: str) -> date:
        """
        Convert a date string into a Python date object.

        Args:
            date_str (str): The date string to parse.

        Returns:
            date: A Python `date` object.

        """
        try:
            if date_str.isdigit():
                return dt.fromtimestamp(
                    int(date_str) / 1000,
                    tz=timezone.utc,
                ).date()
            return parser.parse(date_str).date()

        except ValueError:
            logger.error(
                f"Error parsing date string {date_str}, applying default date",
            )
            return date.today()

    def scrape_site(self) -> List[NewsArticle]:
        """
        Scrape news articles from the configured website.

        Returns:
            List[NewsArticle]: A list of `NewsArticle` objects containing the
                scraped data from the website.
        """

        base_url = self.config.base_url
        news_url = self.config.news_url
        section_selector = self.config.section_selector
        card_selector = self.config.card_selector
        title_selector = self.config.title_selector
        link_selector = self.config.link_selector
        keyword = self.config.keyword
        summary_selector = self.config.summary_selector
        date_selector = self.config.date_selector
        date_attribute = self.config.date_attribute

        logger.info(f"Starting scraping for site: {base_url}")
        if not news_url:
            logger.warning("No news URL provided, using base URL instead.")
            news_url = base_url
        soup = self.get_soup(str(news_url))
        site_name = base_url.host
        sections = soup.select(section_selector)
        logger.debug(f"Found {len(sections)} sections in the page")

        articles = []
        unique_links = set()

        for section in sections:
            cards = section.select(card_selector)
            logger.debug(f"Found {len(cards)} cards in section")

            for card in cards:
                link_elem = card.select_one(link_selector)
                if not link_elem:
                    logger.warning(
                        "No link element found in card, skipping...",
                    )
                    continue

                link = link_elem.get("href")
                if not link:
                    logger.warning(
                        "Link element present but no href found, skipping..."
                    )
                    continue

                if not link.startswith("http"):
                    link = f"{base_url}{link}"

                logger.debug(f"Processing link: {link}")

                if link in unique_links:
                    logger.debug(f"Duplicate link found: {link}, skipping...")
                    continue

                if keyword not in link:
                    logger.debug(
                        f"Link does not contain article: {link}, skipping...",
                    )
                    continue

                unique_links.add(link)

                # Extract article details
                title_elem = card.select_one(title_selector)
                if not title_elem:
                    logger.warning(
                        "No title found for article card, skipping...",
                    )
                    continue
                title = title_elem.get_text().strip()

                summary = (
                    card.select_one(summary_selector).get_text().strip()
                    if summary_selector and (card.select_one(summary_selector))
                    else ""
                )

                if date_selector:
                    date_elem = card.select_one(date_selector)
                    if not date_elem:
                        logger.warning(
                            f"No date found for article card: {
                                title
                            }, trying to fetch from link..."
                        )
                        time_soup = self.get_soup(link)
                        date_elem = time_soup.select_one(date_selector)

                    date_str = date_elem.get(date_attribute)
                else:
                    logger.debug(
                        "No date selector provided, using date attribute",
                    )
                    date_str = card.get(date_attribute)

                pub_date = self.parse_date(date_str)

                articles.append(
                    NewsArticle(
                        site_name=site_name,
                        title=title,
                        url=link,
                        published_date=pub_date,
                        summary=summary,
                    )
                )
                logger.success(f"Added article: {title} ({link})")

        logger.info(
            f"Scraping complete for {base_url},{len(articles)} articles found",
        )

        return articles

    @staticmethod
    def scrape_all_sites(configs: List[SiteConfig]) -> List[NewsArticle]:
        """
        Scrape multiple websites and aggregate results.

        Args:
            configs (List[SiteConfig]): List of site configurations.

        Returns:
            List[NewsArticle]: Aggregated news articles across all sites.
        """
        all_articles = []
        for config in configs:
            logger.info(f"Scraping site: {config.base_url}")
            scraper = NewsScraper(config)
            try:
                articles = scraper.scrape_site()
                all_articles.extend(articles)
            except Exception as e:
                logger.critical(
                    f"Scraping failed for {config.base_url.host}: {e}",
                )
                articles = []
        logger.info(
            f"All sites scraped. Total articles found: {len(all_articles)}",
        )
        return all_articles
