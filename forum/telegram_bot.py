import requests
import os

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        
        try:
            response = requests.get(f"{self.api_url}/getMe")
            if response.status_code != 200:
                raise Exception("Failed to connect to Telegram API")
        except Exception as e:
            raise Exception(f"Bot initialization error: {e}")
    
    def send_message(self, chat_id, text):
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            return None

    def format_contact_message(self, form_data):
        return (
            f"<b>Обратная связь от пользователя</b>\n\n"
            f"<b>Имя:</b> {form_data['name']}\n"
            f"<b>Email:</b> {form_data['email']}\n"
            f"<b>Тема:</b> {form_data['subject']}\n"
            f"<b>Сообщение:</b>\n{form_data['message']}"
        )

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = TelegramBot(BOT_TOKEN) 