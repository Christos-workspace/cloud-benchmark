"""
Data models for news scraping.

This module defines models used for structuring scraped data and configuring
scraping settings.

Classes:
    NewsArticle: Represents a news article scraped from a website.
    SiteConfig: Represents the configuration settings required to scrape a
        specific website.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import date


class NewsArticle(BaseModel):
    """
    Represents a news article scraped from a website.

    This class is used to structure and store details of a news article,
    such as the title, publication date, and an optional summary.

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

    This class is used to define the parameters required for extracting
    news articles, such as CSS selectors for locating article details and
    optional filtering criteria.

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
