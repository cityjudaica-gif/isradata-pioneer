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
            print(f"Ошибка доступа к сайту: {response.status_code}")
            return

        feed = feedparser.parse(response.text)
        if not feed.entries:
            print("Лента RSS пуста.")
            return

        # Загружаем базу и очищаем её от лишних пробелов
        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(line.strip() for line in f.read().splitlines() if line.strip())

        new_count = 0
        for entry in reversed(feed.entries):
            clean_link = entry.link.strip() # Очистка ссылки
            
            if clean_link not in sent_urls:
                title = entry.title.strip()
                message = f"<b>{title}</b>\n\n{clean_link}"
                
                print(f"Отправка новой вакансии: {title}")
                if send_telegram(message) == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(clean_link + "\n")
                    sent_urls.add(clean_link)
                    new_count += 1
                    time.sleep(3) # Пауза против бана

        print(f"--- ИТОГ: Отправлено {new_count} новых сообщений ---")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
