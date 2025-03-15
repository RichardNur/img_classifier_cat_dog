import os
import requests
import time
from PIL import Image
from io import BytesIO


class RedditUserImageScraper:
    def __init__(self, subreddit, folder_name):
        """
        Initialize scraper: subreddit, folder name, and other variables
        """
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.users_processed = 0
        self.images_downloaded = 0
        self.total_users = 0

        self.subreddit = subreddit.strip()
        self.folder_name = folder_name.strip()
        self.save_dir = f"train/{self.folder_name}"
        self.posts_url = f"https://www.reddit.com/r/{self.subreddit}/new.json?limit=100"
        self.comments_url = f"https://www.reddit.com/r/{self.subreddit}/comments.json?limit=100"

        os.makedirs(self.save_dir, exist_ok=True)

    def get_users_from_posts(self):
        """Fetch users from subreddit posts"""
        response = requests.get(self.posts_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Error fetching post data: {response.status_code}")
            return []
        data = response.json()
        return [post["data"].get("author") for post in data.get("data", {}).get("children", []) if
                post["data"].get("author")]

    def get_users_from_comments(self):
        """Fetch users from subreddit comments"""
        response = requests.get(self.comments_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Error fetching comment data: {response.status_code}")
            return []
        data = response.json()
        return [comment["data"].get("author") for comment in data.get("data", {}).get("children", []) if
                comment["data"].get("author")]

    def save_image(self, url, username):
        """Save user avatar image"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))

            if img.width < 150:
                print(f"Skipped {username}'s image (too small: {img.width}px)")
                return False

            img_filename = os.path.join(self.save_dir,
                                        f"{self.subreddit}_user_{str(self.images_downloaded).zfill(5)}_{username}.jpg")
            with open(img_filename, "wb") as f:
                f.write(response.content)

            print(f"Saved: {img_filename}")
            return True
        except Exception as e:
            print(f"Error saving {username}'s image: {e}")
            return False

    def process_user(self, user):
        """Process individual user"""
        if user and user != "[deleted]":
            user_url = f"https://www.reddit.com/user/{user}/about.json"
            try:
                user_response = requests.get(user_url, headers=self.headers)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    avatar_url = user_data.get("data", {}).get("snoovatar_img") or user_data.get("data", {}).get(
                        "icon_img", "")

                    if not avatar_url:
                        print(f"No avatar found for r/{self.subreddit} user: {user}")
                        return

                    # Clean up the URL - remove query parameters
                    avatar_url = avatar_url.split('?')[0]

                    # Skip default/placeholder avatars
                    if any(skip in avatar_url.lower() for skip in ["snoo", "default", "placeholder"]):
                        print(f"Default avatar for r/{self.subreddit} user: {user} found, skipped")
                        return

                    # Try to get the highest quality image
                    if "avatars.redditmedia.com" in avatar_url:
                        avatar_url = avatar_url.replace("_bigger", "").replace("_normal", "")

                    if self.save_image(avatar_url, user):
                        self.images_downloaded += 1
                        print(f"✅ Avatar for r/{self.subreddit} user: {user} saved successfully")

            except Exception as e:
                print(f"Error processing {user}: {e}")

            time.sleep(1)  # Avoid rate limits



    def scrape(self):
        """Main scraping process"""
        print(f"\nStarting scraping for r/{self.subreddit}")
        users = list(set(self.get_users_from_posts() + self.get_users_from_comments()))
        self.total_users = len(users)

        print(f"Found {self.total_users} unique users")

        for user in users:
            self.users_processed += 1
            progress = (self.users_processed / self.total_users) * 100
            print(f"\nProgress: {progress:.1f}% ({self.users_processed}/{self.total_users} users)")
            self.process_user(user)

        print(f"\n✅ Completed! Downloaded {self.images_downloaded} images to '{self.save_dir}'")



if __name__ == "__main__":
    pass