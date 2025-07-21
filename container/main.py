from scraper import NewsScraper, SiteConfig, BBC_URL
import json

def main():
    # Example configuration for BBC
    bbc_config = SiteConfig(
        base_url=BBC_URL,
        news_url=f"{BBC_URL}/news",
        section_selector='section[data-analytics-group="true"]',
        card_selector='div[data-testid="anchor-inner-wrapper"]',
        title_selector="h2",
        link_selector="a",
        summary_selector="p[data-testid='card-description']",
        date_selector="time",
    )

    # Create scrapers for all sites
    all_results = NewsScraper.scrape_all_sites([
        bbc_config,
        # Add similar configs for APNEWS and REUTERS here
    ])

    # Save results
    with open('articles.json', 'w') as f:
        json.dump(
            {
                site_name: [article.model_dump(mode='json')
                            for article in articles_list]
                for site_name, articles_list in all_results.items()
            },
            f,
            ensure_ascii=False,
            indent=4)

if __name__ == "__main__":
    main()
