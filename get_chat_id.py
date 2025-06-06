import requests

def get_updates(token):
    """Get updates from Telegram bot"""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url)
    return response.json()

def main():
    token = "7796587103:AAEbm-ElYdPQY8DRucO3GVVO4ivT_FtPJ5Q"
    
    print("Please follow these steps:")
    print("1. Start a chat with your bot on Telegram")
    print("2. Send any message to the bot")
    print("3. Press Enter after you've sent the message")
    input("Press Enter to continue...")
    
    updates = get_updates(token)
    
    if updates.get('ok') and updates.get('result'):
        for update in updates['result']:
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                print(f"\nYour chat ID is: {chat_id}")
                print("\nUpdate your CHAT_ID in views.py with this value")
                return
    
    print("\nNo messages found. Please make sure you've sent a message to the bot and try again.")

if __name__ == "__main__":
    main() 