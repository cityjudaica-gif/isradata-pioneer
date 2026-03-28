import feedparser
import cloudscraper
import os
import time

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    import requests
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload)
        return r.status_code
    except:
        return 500

def main():
    print("--- Запуск бронебойного режима (Cloudscraper) ---")
    
    # Создаем скрейпер, который умеет обходить проверки Cloudflare
    scraper = cloudscraper.create_scraper() 

    try:
        # Пытаемся получить содержимое RSS
        response = scraper.get(RSS_URL, timeout=30)
        
        if response.status_code != 200:
            print(f"Ошибка: Сайт вернул код {response.status_code}")
            return

        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("RSS лента пуста. Проверьте путь: " + RSS_URL)
            return

        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        print(f"Успех! Найдено вакансий: {len(feed.entries)}")

        new_count = 0
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                message = f"<b>{entry.title}</b>\n\n{entry.link}"
                if send_telegram(message) == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    print(f"Пост отправлен: {entry.title}")
                    time.sleep(2)

        print(f"Работа завершена. Новых постов: {new_count}")

    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
