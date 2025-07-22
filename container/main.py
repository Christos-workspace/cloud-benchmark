from scraper import NewsScraper, SiteConfig
import json


BBC_URL = "https://www.bbc.com"
APNEWS_URL = "https://apnews.com/"
REUTERS_URL = "https://www.reuters.com/"


def main():
    bbc_config = SiteConfig(
        base_url=BBC_URL,
        news_url=f"{BBC_URL}/news",
        section_selector='section[data-analytics-group="true"]',
        card_selector='div[data-testid="anchor-inner-wrapper"]',
        title_selector="h2",
        link_selector="a",
        keyword='article',
        summary_selector="p[data-testid='card-description']",
        date_selector="time",
        date_attribute="datetime"
    )

    # apnews_config = SiteConfig(
    #     base_url=APNEWS_URL,
    #     section_selector="div.FourColumnContainer-column",
    #     card_selector="div.PagePromo-content",
    #     title_selector="span.PagePromoContentIcons-text",
    #     link_selector="a",
    #     keyword='article',
    #     date_selector="bsp-timestamp",
    #     date_atttribute="data-timestamp"
    # )
    # #
    # Create scrapers for all sites
    all_articles = NewsScraper.scrape_all_sites([
        bbc_config,
        # apnews_config,


        # Add similar configs for APNEWS and REUTERS here
    ])

    # Save results
    with open('container/articles.json', 'w') as f:
        json.dump(
            [article.model_dump(mode='json') for article in all_articles],
            f,
            ensure_ascii=False,
            indent=4)


if __name__ == "__main__":
    main()
