import os
from dotenv import load_dotenv
import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

load_dotenv()

# ================== CONFIG ==================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

if not GEMINI_API_KEY or not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
    print("❌ ERROR: Missing API keys or LinkedIn tokens in .env file!")
    exit()

genai.configure(api_key=GEMINI_API_KEY)
# Using gemini-1.5-flash as it is the current supported free tier model
model = genai.GenerativeModel('gemini-1.5-flash')

RSS_FEEDS = [
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://openai.com/index/feed/",
    "https://huggingface.co/blog/feed.xml",
    "https://blog.google/products/ai/feed/",
    "https://venturebeat.com/category/ai/feed/"
]

# ============================================

def get_top_news(limit=3):
    all_news = []
    for url in RSS_FEEDS:
        try:
            response = requests.get(url, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:3]:
                title = getattr(entry, 'title', '')
                summary = getattr(entry, 'summary', getattr(entry, 'description', ''))[:400]
                
                soup = BeautifulSoup(summary, 'html.parser')
                clean_summary = soup.get_text()
                
                if title:
                    all_news.append({'title': title, 'summary': clean_summary})
        except Exception as e:
            continue
            
    unique_news = {item['title']: item for item in all_news}.values()
    return list(unique_news)[:limit]

def generate_roundup_post(news_items):
    news_text = ""
    for i, item in enumerate(news_items, 1):
        news_text += f"\nNews {i}:\nTitle: {item['title']}\nSummary: {item['summary']}\n"

    prompt = f"""Write a very punchy, professional LinkedIn "Daily AI Roundup" post based on these top updates:
{news_text}

STRICT RULES:
1. Output exactly the post content and nothing else. No conversational filler, no introductory text like "Here is your post".
2. Start with a strong hook about today's rapid AI advancements.
3. Use a bulleted list to briefly summarize the 3 news items in plain English.
4. End with one thought-provoking question for the audience.
5. Add exactly 4 relevant hashtags at the bottom."""
    
    response = model.generate_content(prompt)
    return response.text.strip()

def post_to_linkedin(post_text):
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        print("✅ Successfully auto-posted to LinkedIn!")
    else:
        print(f"❌ Failed to post. Status code: {response.status_code}")
        print(response.text)

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Starting AI LinkedIn Agent...")
    
    print("Fetching top AI news...")
    top_news = get_top_news(limit=3)
    
    if not top_news:
        print("❌ No news found.")
    else:
        print(f"✅ Found {len(top_news)} trending stories. Generating roundup post...")
        post_text = generate_roundup_post(top_news)
        
        print("\n--- PREVIEW OF POST ---")
        print(post_text)
        print("-----------------------\n")
        
        print("Posting directly to LinkedIn...")
        post_to_linkedin(post_text)
        print("🎉 Done! Go check your LinkedIn profile.")
