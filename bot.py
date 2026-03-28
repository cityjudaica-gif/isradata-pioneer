import feedparser
import requests
import os

# Загружаем секреты
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload)
        return response.status_code
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return 500

def main():
    print(f"--- Попытка обхода Cloudflare для: {RSS_URL} ---")
    
    # Имитируем реальный браузер (User-Agent)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Сначала скачиваем содержимое RSS как текст с нашими заголовками
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Теперь парсим полученный текст через feedparser
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("RSS лента пуста (возможно, Cloudflare все еще блокирует или нет новых записей).")
            return

        # Проверка базы
        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        print(f"Найдено вакансий: {len(feed.entries)}. В базе: {len(sent_urls)}")

        new_count = 0
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                # Формируем сообщение
                message = f"<b>{entry.title}</b>\n\n{entry.link}"
                
                status = send_telegram(message)
                if status == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    print(f"Отправлено: {entry.title}")
                else:
                    print(f"Telegram вернул ошибку: {status}")

        print(f"--- Готово. Отправлено новых: {new_count} ---")

    except Exception as e:
        print(f"Критическая ошибка при чтении сайта: {e}")

if __name__ == "__main__":
    main()
