import requests
from bs4 import BeautifulSoup as bs
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, List, Optional, Union
from fake_useragent import UserAgent
from datetime import datetime as dt, date

BBC_URL = "https://www.bbc.com/news"
APNEWS_URL = "https://apnews.com/"
REUTERS_URL = "https://www.reuters.com/"

class NewsArticle(BaseModel):
    title: str 
    url: HttpUrl 
    published_date: date


class NewsScraper: