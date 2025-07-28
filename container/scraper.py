import time
import requests
from bs4 import BeautifulSoup as bs
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, List, Optional
from fake_useragent import UserAgent
from datetime import datetime as dt, timezone, date
from dateutil import parser
from playwright.sync_api import sync_playwright
from loguru import logger
from pprint import pprint
# Log to file and rotate every 10 MB
logger.add("container/scraper.log", rotation="10 MB")


class NewsArticle(BaseModel):
    site_name: str
    title: str
    url: HttpUrl
    published_date: date
    summary: Optional[str] = Field(
        default=None, description="Summary of the article")


class SiteConfig(BaseModel):
    base_url: HttpUrl
    news_url: Optional[HttpUrl] = None  # Optional URl for direct news access
    section_selector: str
    card_selector: str
    title_selector: str
    link_selector: str
    keyword: Optional[str] = None
    summary_selector: Optional[str] = None
    date_selector: Optional[str] = None
    date_attribute: Optional[str] = None


class NewsScraper:
    def __init__(self, config: SiteConfig):
        self.config = config

    @staticmethod
    def get_page_html(url: str, headless: bool = True) -> str:
        """
        Uses Playwright to fetch the rendered HTML of a webpage.
        Args:
            url (str): The URL to visit.
            headless (bool): Whether to run the browser in headless mode.
        Returns:
            str: The HTML content of the page.
        """
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=headless)
            page = browser.new_page()
            page.goto(url)
            # Optionally, wait for network to be idle or for a selector to appear:
            # page.wait_for_load_state('networkidle')
            html = page.content()
            browser.close()
        return html

    @staticmethod
    def get_soup(url: str):
        """
        Fetches the HTML content of a given URL and
        parses it into a BeautifulSoup object.

        Args:
            url (str): The URL of the webpage to scrape.

        Returns:
            BeautifulSoup: Parsed HTML content of the webpage.

        Raises:
            Exception: If the HTTP request fails (non-200 status code).
        """
        logger.info(f"Fetching URL: {url}")
        # response = requests.get(
        #     url, headers={"User-Agent": UserAgent().random})
        # time.sleep(3)
        # if response.status_code != 200:
        #     logger.error(f"Failed to fetch data from {
        #                  url} - Status code: {response.status_code}")
        #     raise Exception(f"Failed to fetch data from {url}")
        # soup = bs(response.content, 'lxml')
        html = NewsScraper.get_page_html(url)
        soup = bs(html, 'lxml')
        logger.debug(f"Fetched and parsed HTML from {url}")
        return soup

    @staticmethod
    def parse_date(date_str: str) -> date:
        """
        Parse a date string into a date object.
        """
        try:
            if date_str.isdigit():
                return dt.fromtimestamp(int(date_str)/1000, tz=timezone.utc).date()
            else:
                return parser.parse(date_str).date()

        except ValueError:
            logger.error(f"Error parsing date string {
                         date_str}, applying default date")
            return date.today()

    def scrape_site(self) -> List[NewsArticle]:
        """Scrape articles from the configured news site"""
        logger.info(f"Starting scraping for site: {self.config.base_url}")
        if not self.config.news_url:
            logger.warning("No newa URL provided, using base URL instead.")
            self.config.news_url = self.config.base_url
        soup = self.get_soup(str(self.config.news_url))
        site_name = self.config.base_url.host
        sections = soup.select(self.config.section_selector)
        logger.debug(f"Found {len(sections)} sections in the page")

        articles = []
        unique_links = set()

        for section in sections:
            cards = section.select(self.config.card_selector)
            logger.debug(f"Found {len(cards)} cards in section")
            for card in cards:
                print("---------------------------------")
                pprint(card)
                print("---------------------------------")
                link_elem = card.select_one(self.config.link_selector)
                summary_selector = self.config.summary_selector
                date_selector = self.config.date_selector
                date_attribute = self.config.date_attribute
                logger.debug(f"summary selector is: {summary_selector}")
                logger.debug(f"date selector is: {date_selector}")
                logger.debug(f"date attribute is: {date_attribute}")

                if not link_elem:
                    logger.warning(
                        "No link element found in card, skipping...")
                    continue

                link = link_elem.get('href')
                if not link:
                    logger.warning(
                        "Link element present but no href found, skipping...")
                    continue

                # Handle relative links
                if not link.startswith("http"):
                    link = f"{self.config.base_url}{link}"

                logger.debug(f"Processing link: {link}")

                if link in unique_links:
                    logger.debug(f"Duplicate link found: {link}, skipping...")
                    continue

                if 'article' not in link:
                    logger.debug(f"Link does not contain article: {
                                 link}, skipping...")
                    continue

                unique_links.add(link)

                # Extract article details
                title_elem = card.select_one(self.config.title_selector)
                if not title_elem:
                    logger.warning(
                        "No title found for article card, skipping...")
                    continue
                title = title_elem.get_text().strip()
                logger.debug(f"Article title: {title}")

                if summary_selector:

                    summary_elem = card.select_one(
                        summary_selector)
                    summary = summary_elem.get_text().strip() if summary_elem else ""
                else:
                    summary = ""

                if date_selector:
                    logger.debug(f"using date selector: {date_selector}")

                    date_elem = card.select_one(date_selector)
                    if not date_elem:
                        logger.warning(f"No date found for article card: {
                                       title}, trying to fetch from link...")
                        time_soup = self.get_soup(link)
                        date_elem = time_soup.select_one(date_selector)

                    date_str = date_elem.get(
                        date_attribute)
                    logger.debug(f"Date string found for {
                                 date_attribute}: {date_str}")
                else:
                    logger.debug(
                        "No date selector provided, using date attribute")
                    logger.debug(f"date attribute is: {
                                 date_attribute}")
                    date_str = card.get(date_attribute)
                    logger.debug(f"date string found: {date_str}")

                pub_date = self.parse_date(date_str)

                articles.append(NewsArticle(
                    site_name=site_name,
                    title=title,
                    url=link,
                    published_date=pub_date,
                    summary=summary
                ))
                logger.success(f"Added article: {title} ({link})")

        logger.info(f"Scraping complete for {self.config.base_url}. {
                    len(articles)} articles found.")

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
                logger.critical(f"Scraping failed for {
                                config.base_url.host}: {e}")
                articles = []
        logger.info(
            f"All sites scraped. Total articles found: {len(all_articles)}"
        )
        return all_articles
