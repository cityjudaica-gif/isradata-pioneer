import feedparser
import cloudscraper
import os
import time
import requests

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=20)
        return r.status_code
    except Exception as e:
        print(f"Ошибка сети: {e}")
        return 500

def main():
    print("--- ЗАПУСК ПРОВЕРКИ ---")
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    try:
        response = scraper.get(RSS_URL, timeout=30)
        if response.status_code != 200:
            print(f"Сайт недоступен: {response.status_code}")
            return

        feed = feedparser.parse(response.text)
        if not feed.entries:
            print("Лента пуста.")
            return

        # Загрузка базы
        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(line.strip() for line in f.read().splitlines() if line.strip())

        new_count = 0
        for entry in reversed(feed.entries):
            link = entry.link.strip()
            
            if link not in sent_urls:
                title = entry.title.strip()
                print(f"Новая вакансия: {title}")
                
                if send_telegram(f"<b>{title}</b>\n\n{link}") == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(link + "\n")
                    sent_urls.add(link)
                    new_count += 1
                    time.sleep(3) # Анти-спам пауза

        print(f"--- ИТОГ: Отправлено {new_count} ---")

    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
