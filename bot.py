import feedparser
import cloudscraper
import os
import time
import requests

# Константы
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=20)
        if r.status_code != 200:
            print(f"[!] Ошибка Telegram: {r.status_code} - {r.text}")
        return r.status_code
    except Exception as e:
        print(f"[!] Ошибка сети: {e}")
        return 500

def main():
    print("--- ЗАПУСК ПРОВЕРКИ ISRADATA ---")
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    try:
        response = scraper.get(RSS_URL, timeout=30)
        if response.status_code != 200:
            print(f"[!] Сайт недоступен, код: {response.status_code}")
            return

        feed = feedparser.parse(response.text)
        if not feed.entries:
            print("[!] Лента пуста.")
            return

        # Загрузка базы данных
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w', encoding='utf-8') as f: pass
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            # strip() важен, чтобы избежать дублей из-за невидимых символов
            sent_urls = set(line.strip() for line in f.read().splitlines() if line.strip())

        print(f"[LOG] Вакансий в RSS: {len(feed.entries)}. Уже отправлено: {len(sent_urls)}")

        new_count = 0
        # Обработка от старых к новым
        for entry in reversed(feed.entries):
            clean_link = entry.link.strip()
            
            if clean_link not in sent_urls:
                title = entry.title.strip()
                message = f"<b>{title}</b>\n\n{clean_link}"
                
                print(f"[SEND] Отправка: {title}")
                if send_telegram(message) == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(clean_link + "\n")
                    # Сразу добавляем в локальный сет, чтобы не отправить дубль в одном цикле
                    sent_urls.add(clean_link)
                    new_count += 1
                    time.sleep(3) # Пауза против спам-фильтра
                else:
                    print(f"[SKIP] Не удалось отправить: {title}")

        print(f"--- ИТОГ: Отправлено новых вакансий: {new_count} ---")

    except Exception as e:
        print(f"[CRITICAL] Ошибка: {e}")

if __name__ == "__main__":
    main()
