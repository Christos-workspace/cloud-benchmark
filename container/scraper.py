import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime as dt, timezone, date
from dateutil import parser
import sys
from loguru import logger

logger.remove()  # Remove default logger
logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")


class NewsArticle(BaseModel):
    """
    Represents a news article scraped from a website.

    Attributes:
        site_name (str): The name of the website the article was scraped from.
        title (str): The title of the news article.
        url (HttpUrl): The URL of the news article.
        published_date (date): The publication date of the article.
        summary (Optional[str]): A brief summary or description of the article.
            Defaults to None if no summary is available.
    """

    site_name: str
    title: str
    url: HttpUrl
    published_date: date
    summary: Optional[str] = Field(
        default=None,
        description="Summary of the article",
    )


class SiteConfig(BaseModel):
    """
    Represents the configuration settings for scraping a news website.

    Attributes:
        base_url (HttpUrl): The base URL of the website.
        news_url (Optional[HttpUrl]): An optional URL that directly points
        to the news section of the website.
        section_selector (str): The CSS selector used to identify sections
        on the webpage.
        card_selector (str): The CSS selector used to identify individual
        news article cards within a section.
        title_selector (str): The CSS selector used to extract the title of
        a news article from a card.
        link_selector (str): The CSS selector used to extract the hyperlink
        to the article from a card.
        keyword (Optional[str]): A keyword to filter articles.
        Only articles containing this keyword will be scraped.
        summary_selector (Optional[str]): The CSS selector used to extract
        a summary or description of the article, if available.
        date_selector (Optional[str]): The CSS selector used to locate
        the element containing the publication date of the article.
        date_attribute (str): The attribute of the date element that
        contains the publication date (e.g., "datetime").
    """

    base_url: HttpUrl
    news_url: Optional[HttpUrl] = None
    section_selector: str
    card_selector: str
    title_selector: str
    link_selector: str
    keyword: Optional[str] = None
    summary_selector: Optional[str] = None
    date_selector: Optional[str] = None
    date_attribute: str


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
        including CSS selectors and other parameters
        for extracting article details.

    Methods:
        get_page_html(url: str) -> str:
            Fetches the HTML content of a given URL using the requests library.
        get_soup(url: str) -> BeautifulSoup:
            Parses the HTML content of a URL into a BeautifulSoup object.
        parse_date(date_str: str) -> date:
            Converts a date string into a Python date object.
            Supports various formats.
        scrape_site() -> List[NewsArticle]:
            Scrapes the configured website and returns
            a list of NewsArticle objects.
        scrape_all_sites(configs: List[SiteConfig]) -> List[NewsArticle]:
            Scrapes multiple websites based on a list of SiteConfig objects and
            aggregates all found articles into a single list.
    """

    def __init__(self, config: SiteConfig):
        self.config = config

    @staticmethod
    def get_page_html(url: str) -> str:
        """
        Fetch the HTML content of a given URL.

        This method sends an HTTP GET request to the specified URL and
        retrieves the HTML content of the webpage.
        It uses a random user agent to avoid being blocked
        by websites that restrict automated requests.

        Args:
            url (str): The URL of the webpage to fetch.

        Returns:
            str: The HTML content of the webpage as a string. If the request
            fails, the function logs an error message
            and returns an empty string.

        Raises:
            requests.RequestException: If there is an issue with
            the HTTP request.
        """
        response = requests.get(
            url,
            headers={"User-Agent": UserAgent().random},
        )
        if response.status_code != 200:
            logger.error(
                f"Failed to fetch {url}, status code: {response.status_code}",
            )
        html = response.content
        return html

    @staticmethod
    def get_soup(url: str):
        """
        Fetch the HTML content of a given URL and parse it
        into a BeautifulSoup object.

        This method logs the URL being fetched and
        uses the `get_page_html` method
        to retrieve the raw HTML content. The HTML is then parsed into
        a BeautifulSoup object using the `html.parser` parser.

        Args:
            url (str): The URL of the webpage to scrape.

        Returns:
            BeautifulSoup: A BeautifulSoup object containing the HTML content.

        Raises:
            ValueError: If the retrieved HTML content is empty or malformed.
        """
        logger.info(f"Fetching URL: {url}")
        html = NewsScraper.get_page_html(url)
        soup = bs(html, "html.parser")
        logger.debug(f"Fetched and parsed HTML from {url}")
        return soup

    @staticmethod
    def parse_date(date_str: str) -> date:
        """
        Parse a date string into a date object.
        """
        try:
            if date_str.isdigit():
                return dt.fromtimestamp(int(date_str) / 1000, tz=timezone.utc).date()
            else:
                return parser.parse(date_str).date()

        except ValueError:
            logger.error(f"Error parsing date string {date_str}, applying default date")
            return date.today()

    def scrape_site(self) -> List[NewsArticle]:
        """Scrape articles from the configured news site"""

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
                    logger.warning("No link element found in card, skipping...")
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
                    logger.debug(f"Link does not contain article: {link}, skipping...")
                    continue

                unique_links.add(link)

                # Extract article details
                title_elem = card.select_one(title_selector)
                if not title_elem:
                    logger.warning("No title found for article card, skipping...")
                    continue
                title = title_elem.get_text().strip()

                if summary_selector:
                    summary_elem = card.select_one(summary_selector)
                    summary = summary_elem.get_text().strip() if summary_elem else ""
                else:
                    summary = ""

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
                    logger.debug("No date selector provided, using date attribute")
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
            f"Scraping complete for {base_url}. {len(articles)} articles found."
        )

        return articles

    @staticmethod
    def scrape_all_sites(configs: List[SiteConfig]) -> List[NewsArticle]:
        """Scrape multiple sites and return results grouped by site"""
        all_articles = []
        for config in configs:
            logger.info(f"Scraping site: {config.base_url}")
            scraper = NewsScraper(config)
            try:
                articles = scraper.scrape_site()
                all_articles.extend(articles)
            except Exception as e:
                logger.critical(f"Scraping failed for {config.base_url.host}: {e}")
                articles = []
        logger.info(f"All sites scraped. Total articles found: {len(all_articles)}")
        return all_articles
