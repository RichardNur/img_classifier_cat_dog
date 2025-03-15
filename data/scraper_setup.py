from scrape_subreddit_avatars import RedditUserImageScraper


def run_scraper():
    """
    Run the Reddit User Avatar Scraper
    """
    print("Reddit User Avatar Scraper")
    print("-" * 25)


    subreddit = input("Enter subreddit name (without r/): ")
    folder_name = input("Enter folder name for saving the training images: ")


    scraper = RedditUserImageScraper(subreddit, folder_name)
    scraper.scrape()


if __name__ == "__main__":
    run_scraper()
