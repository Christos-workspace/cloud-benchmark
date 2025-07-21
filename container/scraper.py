
import requests
from bs4 import BeautifulSoup as bs
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, List, Optional
from fake_useragent import UserAgent
from datetime import datetime as dt, date
from loguru import logger

# Log to file and rotate every 10 MB
logger.add("container/scraper.log", rotation="10 MB")


class NewsArticle(BaseModel):
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
    summary_selector: str
    date_selector: str


class NewsScraper:
    def __init__(self, config: SiteConfig):
        self.config = config

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
        response = requests.get(
            url, headers={"User-Agent": UserAgent().random})
        if response.status_code != 200:
            logger.error(f"Failed to fetch data from {
                         url} - Status code: {response.status_code}")
            raise Exception(f"Failed to fetch data from {url}")
        soup = bs(response.content, 'html.parser')
        logger.debug(f"Fetched and parsed HTML from {url}")
        return soup

    @staticmethod
    def parse_date(date_str: str) -> date:
        """
        Parese a date string into a date object.
        """
        try:
            return dt.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except ValueError:
            return date.today()

    def scrape_site(self) -> List[NewsArticle]:
        """Scrape articles from the configured news site"""
        logger.info(f"Starting scraping for site: {self.config.base_url}")
        soup = self.get_soup(str(self.config.news_url))
        sections = soup.select(self.config.section_selector)

        articles = []
        unique_links = set()

        for section in sections:
            cards = section.select(self.config.card_selector)
            logger.debug(f"Found {len(cards)} cards in section")
            for card in cards:
                link_elem = card.select_one(self.config.link_selector)
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

                if link in unique_links:
                    logger.debug(f"Duplicate link found: {link}, skipping...")
                    continue

                if 'articles' not in link:
                    logger.debug(f"Link does not contain 'articles': {
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

                summary_elem = card.select_one(self.config.summary_selector)
                summary = summary_elem.get_text().strip() if summary_elem else ""

                # Get publication date
                date_elem = card.select_one(self.config.date_selector)
                date_str = date_elem.get('datetime') if date_elem else ""
                pub_date = self.parse_date(date_str)

                articles.append(NewsArticle(
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
    def scrape_all_sites(configs: List[SiteConfig]) -> Dict[str, List[NewsArticle]]:
        """Scrape multiple sites and return results grouped by site"""
        results = {}
        for config in configs:
            logger.info(f"Scraping site: {config.base_url}")
            scraper = NewsScraper(config)
            site_name = config.base_url.host  # type: ignore
            try:
                results[site_name] = scraper.scrape_site()
            except Exception as e:
                logger.critical(f"Scraping failed for {site_name}: {e}")
                results[site_name] = []
        results_summary = {
            site: len(articles) for site, articles in results.items()
        }
        logger.info(
            f"All sites scraped. "
            f"Results: {results_summary}"
        )
        return results
