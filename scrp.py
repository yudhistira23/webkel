import instaloader
import time
import random
import csv
import configparser
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm

# Configuration
CONFIG_FILE = 'config.ini'
CSV_OUTPUT = 'kominfoplk_posts.csv'
LOG_FILE = 'scraper.log'
TARGET_PROFILE = 'yoremahm'
START_DATE = datetime(2025, 7, 1) #yyyy, mm, dd
END_DATE = datetime.now()  # Automatically set to today
POST_LIMIT = 1000

# Safety settings
MIN_DELAY = 10  # seconds between requests
MAX_DELAY = 20
MAX_RETRIES = 3

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def load_credentials():
    """Secure credential loading"""
    config = configparser.ConfigParser()
    if not Path(CONFIG_FILE).exists():
        log_message("❌ Error: config.ini not found")
        raise FileNotFoundError(f"Create {CONFIG_FILE} with [instagram] username and password")
    
    config.read(CONFIG_FILE)
    try:
        return config['instagram']['username'], config['instagram']['password']
    except KeyError:
        log_message("❌ Error: config.ini missing [instagram] section or credentials")
        raise

def scrape_post_comments(post):
    """Scrape comments and replies for a post"""
    comments = []
    if post.comments > 0:
        try:
            for comment in post.get_comments():
                comments.append({
                    'comment_username': comment.owner.username if comment.owner else '[deleted]',
                    'comment_text': comment.text.replace('\n', ' ').strip(),
                    'comment_likes': comment.likes_count,
                    'comment_timestamp': comment.created_at_utc.isoformat(),
                    'is_reply': False
                })
                
                if comment.answers:
                    for reply in comment.answers:
                        comments.append({
                            'comment_username': reply.owner.username if reply.owner else '[deleted]',
                            'comment_text': reply.text.replace('\n', ' ').strip(),
                            'comment_likes': reply.likes_count,
                            'comment_timestamp': reply.created_at_utc.isoformat(),
                            'is_reply': True,
                            'reply_to': comment.owner.username if comment.owner else '[deleted]'
                        })
                
                time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            log_message(f"⚠️ Failed to scrape comments for post {post.shortcode}: {str(e)}")
    
    return comments

def format_timedelta(td):
    """Convert timedelta to human-readable format"""
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def main():
    log_message("\n" + "="*50)
    log_message(f"Starting scrape of @{TARGET_PROFILE} from {START_DATE.date()} to {END_DATE.date()}")
    log_message("="*50)
    
    # Initialize loader
    L = instaloader.Instaloader(
        # Ganti user agent sesuai dengan device yang pernah digunakan
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        sleep=True,
        request_timeout=120
    )

    # Auth flow
    try:
        username, password = load_credentials()
        try:
            L.load_session_from_file(username)
            log_message("✅ Loaded existing session")
        except FileNotFoundError:
            log_message("⚠️ No session found - logging in...")
            L.login(username, password)
            L.save_session_to_file()
            log_message("✅ Login successful")
    except Exception as e:
        log_message(f"❌ Authentication failed: {str(e)}")
        return

    # Get profile
    try:
        profile = instaloader.Profile.from_username(L.context, TARGET_PROFILE)
        log_message(f"📊 Found profile @{profile.username} with {profile.mediacount} posts")
    except Exception as e:
        log_message(f"❌ Failed to load profile: {str(e)}")
        return

    # Prepare CSV
    try:
        csv_file = open(CSV_OUTPUT, 'w', newline='', encoding='utf-8')
        writer = csv.writer(csv_file)
        writer.writerow([
            'post_url', 'date', 'caption', 'likes', 'comments_count',
            'comment_username', 'comment_text', 'comment_likes', 
            'comment_timestamp', 'is_reply', 'reply_to'
        ])
    except Exception as e:
        log_message(f"❌ Failed to create CSV file: {str(e)}")
        return

    # Scrape posts
    post_count = 0
    scraped_posts = 0
    start_time = datetime.now()
    
    try:
        with tqdm(desc="Scraping posts", unit="post", total=POST_LIMIT) as progress_bar:
            for post in profile.get_posts():
                post_count += 1
                progress_bar.update(1)
                
                # Stop conditions
                if post.date_utc < START_DATE:
                    log_message(f"ℹ️ Reached start date {START_DATE.date()}")
                    break
                    
                if post.date_utc > END_DATE:
                    continue
                    
                if post_count >= POST_LIMIT:
                    log_message(f"ℹ️ Reached post limit {POST_LIMIT}")
                    break
                
                # Only process posts with comments
                if post.comments == 0:
                    continue
                    
                try:
                    # Post data
                    post_data = [
                        f"https://instagram.com/p/{post.shortcode}",
                        post.date_utc.isoformat(),
                        post.caption.replace('\n', ' ').strip() if post.caption else '',
                        post.likes,
                        post.comments
                    ]
                    
                    # Get comments
                    comments = scrape_post_comments(post)
                    
                    if not comments:
                        continue
                    
                    # Write to CSV
                    for comment in comments:
                        writer.writerow(post_data + [
                            comment['comment_username'],
                            comment['comment_text'],
                            comment['comment_likes'],
                            comment['comment_timestamp'],
                            comment['is_reply'],
                            comment.get('reply_to', '')
                        ])
                    
                    scraped_posts += 1
                    progress_bar.set_postfix_str(f"Found: {scraped_posts} | Last: {post.date_utc.date()}")
                    
                    # Calculate ETA
                    elapsed = datetime.now() - start_time
                    posts_remaining = min(POST_LIMIT - post_count, 
                                        (post.date_utc - START_DATE).days * 3)  # Estimate 3 posts/day
                    if posts_remaining > 0:
                        avg_time_per_post = elapsed.total_seconds() / post_count
                        eta = timedelta(seconds=int(avg_time_per_post * posts_remaining))
                        progress_bar.set_description(f"Scraping (ETA: {format_timedelta(eta)})")
                    
                    # Random delay
                    delay = random.uniform(MIN_DELAY, MAX_DELAY)
                    time.sleep(delay)
                    
                except Exception as e:
                    log_message(f"⚠️ Failed to scrape post {post.shortcode}: {str(e)}")
                    time.sleep(random.uniform(30, 60))
    
    finally:
        csv_file.close()
        elapsed = datetime.now() - start_time
        log_message(f"\n🎉 Finished in {format_timedelta(elapsed)}")
        log_message(f"• Processed {post_count} posts")
        log_message(f"• Found {scraped_posts} posts with comments")
        log_message(f"• Data saved to {CSV_OUTPUT}")

if __name__ == "__main__":
    main()