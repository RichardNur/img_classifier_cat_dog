from scrape_subreddit_avatars import RedditUserImageScraper


def run_scraper():
    print("Reddit User Avatar Scraper")
    print("-" * 25)

    # Get user input
    subreddit = input("Enter subreddit name (without r/): ")
    folder_name = input("Enter folder name for saving the train images: ")

    # Create and run scraper
    scraper = RedditUserImageScraper(subreddit, folder_name)
    scraper.scrape()


if __name__ == "__main__":
    run_scraper()