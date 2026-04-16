import feedparser
import cloudscraper
import os
import time
import requests

# Константы (берутся из Secrets вашего репозитория)
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
        print(f"[!] Ошибка сети при отправке: {e}")
        return 500

def main():
    print("=== ЗАПУСК ПРОВЕРКИ ISRADATA ===")
    
    # Настройка обхода Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    try:
        # 1. Получение данных RSS
        response = scraper.get(RSS_URL, timeout=30)
        print(f"[LOG] Статус ответа сайта: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[!] Ошибка доступа к сайту. Код: {response.status_code}")
            return

        feed = feedparser.parse(response.text)
        if not feed.entries:
            print("[!] Лента пуста или заблокирована (проверьте логи выше).")
            return

        print(f"[LOG] Найдено вакансий в RSS: {len(feed.entries)}")

        # 2. Загрузка базы данных отправленных ссылок
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, 'w', encoding='utf-8') as f: pass
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        # 3. Рассылка новых вакансий
        new_count = 0
        # Обрабатываем от старых к новым (reversed)
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                title = entry.title.strip()
                message = f"<b>{title}</b>\n\n{entry.link}"
                
                print(f"[SENDING] Отправка: {title}")
                if send_telegram(message) == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    time.sleep(3) # Защита от спам-фильтра Telegram
                else:
                    print(f"[SKIP] Не удалось отправить вакансию: {title}")

        print(f"=== ИТОГ: Отправлено новых вакансий: {new_count} ===")

    except Exception as e:
        print(f"[CRITICAL] Критическая ошибка в работе скрипта: {e}")

if __name__ == "__main__":
    main()
