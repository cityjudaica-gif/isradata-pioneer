import feedparser
import requests
import os

# Секреты GitHub
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        return response.status_code
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        return 500

def main():
    # Маскируемся под обычный браузер Chrome, чтобы пробить Cloudflare
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print(f"Подключаемся к RSS через обход защиты...")
    
    try:
        # Загружаем RSS как текст с поддельными заголовками браузера
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Парсим полученный текст
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("RSS пуст. Возможно, защита всё еще блокирует доступ.")
            return

        # Работа с базой данных
        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        print(f"Найдено вакансий в ленте: {len(feed.entries)}")
        
        new_count = 0
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                message = f"<b>{entry.title}</b>\n\n{entry.link}"
                
                status = send_telegram(message)
                if status == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    print(f"Отправлено: {entry.title}")
                
        print(f"Завершено. Новых сообщений: {new_count}")

    except Exception as e:
        print(f"Ошибка доступа к сайту: {e}")

if __name__ == "__main__":
    main()
