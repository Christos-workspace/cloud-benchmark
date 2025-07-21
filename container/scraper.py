
import requests
from bs4 import BeautifulSoup as bs
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from typing import Dict, List, Optional, Union
from fake_useragent import UserAgent
from datetime import datetime as dt, date
from pprint import pprint
import json


BBC_URL = "https://www.bbc.com"
APNEWS_URL = "https://apnews.com/"
REUTERS_URL = "https://www.reuters.com/"


class NewsArticle(BaseModel):
    title: str
    url: HttpUrl
    published_date: date
    summary: str = ""


class SiteConfig(BaseModel):
    base_url: HttpUrl
    section_selector: str
    card_selector: str
    title_selector: str
    link_selector: str
    summary_selector: str
    date_selector: str
    date_parser: callable  # Function to handle site-specific date formatting

class NewsScraper:
    def __init__(self, config: SiteConfig):
        self.config = config
    
    @staticmethod
    def get_soup(url: str):
    """
    Fetches the HTML content of a given URL and parses it into a BeautifulSoup object.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        BeautifulSoup: Parsed HTML content of the webpage.

    Raises:
        Exception: If the HTTP request fails (non-200 status code).
    """
    response = requests.get(url, headers={"User-Agent": UserAgent().random})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from {url}")
    def scrape_site(self) -> List[NewsArticle]:
        """Scrape articles from the configured news site"""
        soup = self.get_soup(str(self.config.base_url))
        sections = soup.select(self.config.section_selector)
        
        articles = []
        unique_links = set()
        
        for section in sections:
            cards = section.select(self.config.card_selector)
            for card in cards:
                link_elem = card.select_one(self.config.link_selector)
                if not link_elem:
                    continue
                    
                link = link_elem.get('href')
                if not link:
                    continue
                
                # Handle relative links
                if not link.startswith("http"):
                    link = f"{self.config.base_url}{link}"
                
                if link in unique_links:
                    continue
                unique_links.add(link)
                
                # Extract article details
                title = card.select_one(self.config.title_selector).get_text().strip()
                summary_elem = card.select_one(self.config.summary_selector)
                summary = summary_elem.get_text().strip() if summary_elem else ""
                
                # Get publication date
                date_elem = card.select_one(self.config.date_selector)
                date_str = date_elem.get('datetime') if date_elem else ""
                pub_date = self.config.date_parser(date_str) if date_str else date.today()
                
                try:
                    article = NewsArticle(
                        title=title,
                        url=link,
                        published_date=pub_date,
                        summary=summary
                    )
                    articles.append(article)
                except ValidationError as e:
                    print(f"Skipping invalid article data: {e}")
        
        return articles

    @staticmethod
    def scrape_all_sites(configs: List[SiteConfig]) -> Dict[str, List[NewsArticle]]:
        """Scrape multiple sites and return results grouped by site"""
        results = {}
        for config in configs:
            scraper = NewsScraper(config)
            site_name = config.base_url.host  # type: ignore
            results[site_name] = scraper.scrape_site()
        return results

if __name__ == "__main__":
    # Example configuration for BBC
    bbc_config = SiteConfig(
        base_url=BBC_URL,
        section_selector='section[data-analytics-group="true"]',
        card_selector='div[data-testid="anchor-inner-wrapper"]',
        title_selector="h2",
        link_selector="a",
        summary_selector="p[data-testid='card-description']",
        date_selector="time",
        date_parser=lambda d: dt.fromisoformat(d.replace('Z', '+00:00')).date()
    )
    
    # Create scrapers for all sites
    all_results = NewsScraper.scrape_all_sites([
        bbc_config,
        # Add similar configs for APNEWS and REUTERS here
    ])
    
    # Save results
    with open('container/articles.json', 'w') as f:
        json.dump({k: [a.dict() for a in v] for k, v in all_results.items()}, f, indent=4)
