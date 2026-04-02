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
model = genai.GenerativeModel('gemini-2.5-flash')

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

    prompt = f"""Write a high-quality, insightful LinkedIn "Daily AI Roundup" post based on these updates:
{news_text}

STRICT STYLING & CONTENT RULES:
1. START with a strong, one-sentence hook about the state of AI innovation followed by a relevant emoji (like 🚀 or ✨).
2. FOR EACH news item, write a dedicated 3-4 sentence paragraph. 
3. FORMAT: Start each news paragraph with a unique, relevant emoji.
4. CONTENT: Explain exactly what happened and provide a deep insight into why this matters for the tech industry or the environment. Do not just summarize; provide value.
5. NO MARKDOWN: DO NOT use any asterisks like **bold** or *italics*. Use only plain text.
6. SPACING: Ensure there is a full empty line between every paragraph so it is easy to read.
7. CONCLUSION: End with a thoughtful, open-ended question to engage the audience.
8. HASHTAGS: Add exactly 5 relevant hashtags at the very bottom.

Output exactly the post content and nothing else."""
    
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
    current_hour = datetime.now().hour # UTC time
    
    # 4:30 AM UTC = 10:00 AM IST
    if current_hour == 4:
        print("🌅 Morning Mode: Fetching AI News...")
        news = get_top_news(limit=3)
        if news:
            post = generate_roundup_post(news)
            post_to_linkedin(post)
            save_history([item['link'] for item in news])
            
    # 2:30 PM UTC = 8:00 PM IST
    elif current_hour == 14:
        print("🌇 Evening Mode: Generating Journey Post...")
        post = generate_journey_post() # Reads from daily_log.txt
        if post:
            post_to_linkedin(post)
            # Optional: Clear the log after posting so it's ready for tomorrow
            open("daily_log.txt", "w").close()
        post_to_linkedin(post_text)
        print("🎉 Done! Go check your LinkedIn profile.")
