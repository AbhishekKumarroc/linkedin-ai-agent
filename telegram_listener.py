import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Config at the top of telegram_listener.py
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GH_PAT")  # This matches the Secret name you just made
REPO = "Abhishekkumarroc/linkedin-ai-agent"
FILE_PATH = "daily_log.txt"

def get_latest_messages():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url).json()
    
    if not response.get("result"):
        return None

    # Get the very last message sent to the bot
    last_msg = response["result"][-1]
    msg_text = last_msg["message"]["text"]
    user_id = str(last_msg["message"]["from"]["id"])

    # Security: Only listen to YOUR chat ID
    if user_id == CHAT_ID:
        return msg_text
    return None

def update_github_log(content):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. Get the current file (to get the 'sha' fingerprint)
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha", "")
    
    # 2. Update the file
    message = "Update daily log via Telegram"
    content_encoded = base64.b64encode(content.encode()).decode()
    
    payload = {"message": message, "content": content_encoded, "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        print("✅ Log updated on GitHub!")
    else:
        print(f"❌ Error: {res.text}")

if __name__ == "__main__":
    msg = get_latest_messages()
    if msg:
        update_github_log(msg)
