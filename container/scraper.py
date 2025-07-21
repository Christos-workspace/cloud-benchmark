
import requests
from bs4 import BeautifulSoup as bs
from pydantic import BaseModel, Field, HttpUrl
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


class NewsScraper:
    pass


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
    response = requests.get(url, headers={"User-Agent": UserAgent().random})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from {url}")
    soup = bs(response.content, "html.parser")
    return soup


soup = get_soup(f"{BBC_URL}/news")
sections = soup.select('section[data-analytics-group="true"]')
print(len(sections))


articles = []
unique_links = set()
for section in sections:
    cards = section.select('div[data-testid="anchor-inner-wrapper"]')
    for card in cards:
        article = {}
        link = card.select_one("a").get('href')
        if 'articles' in link and link not in unique_links:
            unique_links.add(link)
            article['title'] = card.select_one("h2").get_text()
            if not link.startswith("http"):
                article['link'] = f"{BBC_URL}{link}"
            else:
                article['link'] = f"{link}"
            summary = card.select_one("p[data-testid='card-description']")
            if summary:
                article['summary'] = summary.get_text()
            else:
                article['summary'] = ""
            url_soup = get_soup(article['link'])
            date_str = url_soup.select_one('time').get('datetime')
            article['date'] = dt.fromisoformat(
                date_str.replace('Z', '+00:00')).strftime('%d-%m-%Y')
            articles.append(article)

print(len(articles))
with open('container/articles.json', 'w') as f:
    json.dump(articles, f, indent=4)
