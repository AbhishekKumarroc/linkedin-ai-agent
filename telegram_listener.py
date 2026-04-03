import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def fetch_telegram_messages():
    print("🔍 Checking Telegram for new messages...")
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 1. Check if the API token is even valid
        if not data.get("ok"):
            print(f"❌ Telegram API Error: {data}")
            return
            
        messages = data.get("result", [])
        
        # 2. Tell us if the queue is empty
        if not messages:
            print("💤 No new messages found in Telegram queue.")
            return
            
        print(f"✅ Found {len(messages)} raw updates in the queue!")
        
        new_logs = []
        highest_update_id = 0
        
        for msg in messages:
            update_id = msg.get("update_id", 0)
            if update_id > highest_update_id:
                highest_update_id = update_id
                
            text = msg.get("message", {}).get("text")
            if text:
                new_logs.append(text)
        
        # 3. Write to the file and confirm
        if new_logs:
            with open("daily_log.txt", "a") as f:
                for log in new_logs:
                    f.write(log + "\n")
            print(f"📝 Successfully wrote {len(new_logs)} messages to daily_log.txt")
            
            # 4. VERY IMPORTANT: Acknowledge the messages so they don't repeat
            requests.get(f"{url}?offset={highest_update_id + 1}")
            print("🧹 Cleared read messages from Telegram queue.")
        else:
            print("⚠️ Updates found, but no text messages to log (maybe an image or sticker?).")

    except Exception as e:
        print(f"❌ Python Crash: {e}")

if __name__ == "__main__":
    fetch_telegram_messages()
