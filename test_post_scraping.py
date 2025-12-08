"""
Test scraping a single post to debug why posts aren't being scraped
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler.scraper import TuoiTreScraper, get_category_post_urls, scrape_post_details

def test_single_post_scraping():
    """Test scraping a single post"""
    scraper = TuoiTreScraper()

    try:
        # First, get some post URLs
        print("=" * 60)
        print("Step 1: Getting post URLs from category")
        print("=" * 60)
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=3)

        print(f"\nFound {len(post_urls)} post URLs:")
        for i, url in enumerate(post_urls, 1):
            print(f"  {i}. {url}")

        if not post_urls:
            print("\n⚠ ERROR: No post URLs found!")
            return

        # Try to scrape the first post
        print("\n" + "=" * 60)
        print("Step 2: Scraping first post")
        print("=" * 60)
        test_url = post_urls[0]
        print(f"\nScraping: {test_url}\n")

        try:
            post_data = scrape_post_details(scraper, test_url)

            if post_data:
                print("✓ Successfully scraped post!")
                print("\nPost Data:")
                print(f"  postId: {post_data.get('postId', 'MISSING')}")
                print(f"  title: {post_data.get('title', 'MISSING')[:100]}...")
                print(f"  author: {post_data.get('author', 'MISSING')}")
                print(f"  date: {post_data.get('date', 'MISSING')}")
                print(f"  category: {post_data.get('category', 'MISSING')}")
                print(f"  content_length: {len(post_data.get('content', ''))}")
                print(f"  comments: {len(post_data.get('comments', []))}")
                print(f"  vote_react_list: {post_data.get('vote_react_list', {})}")
            else:
                print("✗ scrape_post_details returned None!")
                print("\nPossible reasons:")
                print("  - HTML selectors don't match actual page structure")
                print("  - Required fields are missing")
                print("  - Exception occurred and was caught silently")

        except Exception as e:
            print(f"✗ Exception occurred while scraping:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # Try scraping all 3 posts
        print("\n" + "=" * 60)
        print("Step 3: Scraping all test posts")
        print("=" * 60)

        successful = 0
        failed = 0

        for i, url in enumerate(post_urls, 1):
            print(f"\n[{i}/{len(post_urls)}] {url}")
            try:
                post_data = scrape_post_details(scraper, url)
                if post_data:
                    print(f"  ✓ Success - {post_data.get('title', 'No title')[:60]}")
                    successful += 1
                else:
                    print(f"  ✗ Failed - returned None")
                    failed += 1
            except Exception as e:
                print(f"  ✗ Exception: {e}")
                failed += 1

        print("\n" + "=" * 60)
        print(f"Results: {successful} successful, {failed} failed")
        print("=" * 60)

    finally:
        scraper.close()

if __name__ == '__main__':
    test_single_post_scraping()
