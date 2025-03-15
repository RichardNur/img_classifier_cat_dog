import requests
import stem
import stem.control
from stem import Signal
from requests.exceptions import RequestException
import time
import os

class RedditUserImageScraper:
    def __init__(self, subreddit, folder_name):
        # Basic settings
        self.subreddit = subreddit.strip()
        self.folder_name = folder_name.strip()
        self.save_dir = f"data/train/{self.folder_name}"

        # API endpoints
        self.posts_url = f"https://www.reddit.com/r/{self.subreddit}/new.json?limit=100"
        self.comments_url = f"https://www.reddit.com/r/{self.subreddit}/comments.json?limit=100"

        # Request settings
        self.headers = {"User-Agent": "Mozilla/5.0"}

        # Pagination
        self.after_post = None
        self.after_comment = None
        self.max_pages = 10

        # Counters
        self.users_processed = 0
        self.images_downloaded = 0
        self.total_users = 0

        # Create directory
        os.makedirs(self.save_dir, exist_ok=True)

        self.session = requests.Session()
        # Tor SOCKS proxy config
        self.session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }

    def new_tor_ip(self):
        try:
            with stem.control.Controller.from_port(port=9051) as controller:
                controller.authenticate(password="cats_and_dogs")  # Use the plain password here, not the hash
                controller.signal(Signal.NEWNYM)
                time.sleep(5)  # Wait for new IP
        except Exception as e:
            print(f"Tor IP-Change failed: {e}")

    def make_request(self, url, max_retries=3):
        for i in range(max_retries):
            try:
                response = self.session.get(url, headers=self.headers)
                if response.status_code == 429:  # Rate limit
                    print("Rate limit, change Tor IP...")
                    self.new_tor_ip()
                    continue
                return response
            except RequestException as e:
                print(f"Request failed: {e}")
                self.new_tor_ip()
                if i == max_retries - 1:
                    raise
            time.sleep(2)

    def get_users_from_comments(self):
        all_users = []
        page = 0

        while page < self.max_pages:
            url = self.comments_url
            if self.after_comment:
                url += f"&after={self.after_comment}"

            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                break

            data = response.json()
            comments = data.get("data", {}).get("children", [])
            if not comments:
                break

            users = [comment["data"].get("author") for comment in comments if comment["data"].get("author")]
            all_users.extend(users)

            self.after_comment = data["data"].get("after")
            if not self.after_comment:
                break

            page += 1
            time.sleep(2)

        return all_users

    def save_image(self, url, username):
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                img_filename = os.path.join(self.save_dir,
                    f"{self.subreddit}_user_{str(self.images_downloaded).zfill(5)}_{username}.jpg")

                with open(img_filename, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"Error saving image for {username}: {e}")
            return False

    def scrape(self):
        print(f"\nStarting scraping for r/{self.subreddit}")
        print("Fetching users from multiple pages...")
        print("Please be patient.")

        # Change Tor IP at the start
        self.new_tor_ip()

        users = list(set(self.get_users_from_posts() + self.get_users_from_comments()))
        self.total_users = len(users)

        print(f"Found {self.total_users} unique users")

        for user in users:
            self.users_processed += 1
            progress = (self.users_processed / self.total_users) * 100
            print(f"\nProgress: {progress:.1f}% ({self.users_processed}/{self.total_users} users)")
            self.process_user(user)

        print(f"\n✅ Completed! Downloaded {self.images_downloaded} images to '{self.save_dir}'")

    def get_users_from_posts(self):
        all_users = []
        page = 0

        while page < self.max_pages:
            url = self.posts_url
            if self.after_post:
                url += f"&after={self.after_post}"

            response = self.make_request(url)  # Using Tor session
            if response.status_code != 200:
                break

            data = response.json()
            posts = data.get("data", {}).get("children", [])
            if not posts:
                break

            users = [post["data"].get("author") for post in posts if post["data"].get("author")]
            all_users.extend(users)

            self.after_post = data["data"].get("after")
            if not self.after_post:
                break

            page += 1
            time.sleep(2)

        return all_users

    def process_user(self, user):
        if user and user != "[deleted]":
            user_url = f"https://www.reddit.com/user/{user}/about.json"
            max_retries = 3
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    user_response = self.make_request(user_url)  # Using Tor session
                    user_data = user_response.json()
                    avatar_url = user_data.get("data", {}).get("snoovatar_img") or user_data.get("data", {}).get("icon_img", "")

                    if not avatar_url:
                        print(f"No avatar found for r/{self.subreddit} user: {user}")
                        break

                    avatar_url = avatar_url.split('?')[0]

                    if any(skip in avatar_url.lower() for skip in ["snoo", "default", "placeholder"]):
                        print(f"Default avatar for r/{self.subreddit} user: {user}, skipped")
                        break

                    if "avatars.redditmedia.com" in avatar_url:
                        avatar_url = avatar_url.replace("_bigger", "").replace("_normal", "")

                    response = self.make_request(avatar_url)  # Using Tor session
                    if response.status_code == 200:
                        img_filename = os.path.join(self.save_dir,
                            f"{self.subreddit}_user_{str(self.images_downloaded).zfill(5)}_{user}.jpg")

                        with open(img_filename, 'wb') as f:
                            f.write(response.content)
                        self.images_downloaded += 1
                        print(f"✅ Avatar for r/{self.subreddit} user: {user} saved successfully")
                    break

                except Exception as e:
                    print(f"Error processing {user}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2

                time.sleep(1)