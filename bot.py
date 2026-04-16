import feedparser
import cloudscraper
import os
import time
import requests

# Загрузка переменных
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
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code != 200:
            print(f"--- [!] Ошибка TG: {r.status_code} - {r.text}")
        return r.status_code
    except Exception as e:
        print(f"--- [!] Критическая ошибка сети при отправке: {e}")
        return 500

def main():
    print("--- СТАРТ ПРОВЕРКИ ---")
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    try:
        # Получаем RSS
        response = scraper.get(RSS_URL, timeout=30)
        
        if response.status_code != 200:
            print(f"--- [!] Сайт Isradata вернул код: {response.status_code}")
            return

        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("--- [!] RSS лента пуста или заблокирована.")
            return

        # Загружаем базу отправленных
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w', encoding='utf-8') as f: pass
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        print(f"--- Найдено в ленте: {len(feed.entries)} вакансий")
        
        new_count = 0
        # Обрабатываем от старых к новым
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                title = entry.title.strip()
                message = f"<b>{title}</b>\n\n{entry.link}"
                
                print(f"--- Попытка отправки: {title}")
                res_code = send_telegram(message)
                
                if res_code == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    time.sleep(3) # Пауза между постами обязательна!
                elif res_code == 429:
                    print("--- [!] Слишком много запросов (Flood Limit). Ждем...")
                    break # Останавливаемся, чтобы не получить бан

        print(f"--- Итог: Отправлено {new_count} новых вакансий.")

    except Exception as e:
        print(f"--- [!] Ошибка в main: {e}")

if __name__ == "__main__":
    main()
