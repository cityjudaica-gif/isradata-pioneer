import feedparser
import cloudscraper
import os
import time
import requests

# Конфигурация
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        return r.status_code
    except Exception as e:
        print(f" Ошибка запроса к Telegram: {e}")
        return 500

def main():
    print("--- [LOG] Запуск проверки Isradata ---")
    
    # Инициализация скрейпера
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:
        # 1. Попытка получить RSS
        response = scraper.get(RSS_URL, timeout=30)
        
        if response.status_code != 200:
            print(f"--- [LOG] Код {response.status_code}. Пробуем прогрев сессии... ---")
            scraper.get("https://www.isradata.com/", timeout=20)
            response = scraper.get(RSS_URL, timeout=20)

        # Отладочная информация в логах GitHub
        print(f"--- [LOG] Статус сервера: {response.status_code}")
        print(f"--- [LOG] Размер полученных данных: {len(response.text)} симв.")

        if "Cloudflare" in response.text or "Just a moment" in response.text:
            print("--- [ALERT] Обнаружена страница проверки Cloudflare! Данные не получены. ---")
            return

        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("--- [LOG] RSS лента пуста (записей не найдено). ---")
            return

        print(f"--- [LOG] Всего вакансий в ленте: {len(feed.entries)} ---")

        # 2. Работа с базой данных
        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
            print("--- [LOG] Создан новый файл базы данных. ---")
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        # 3. Рассылка новых вакансий
        new_count = 0
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                title = entry.title.strip()
                message = f"<b>{title}</b>\n\n{entry.link}"
                
                status = send_telegram(message)
                
                if status == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    print(f"--- [OK] Отправлено: {title}")
                    time.sleep(2) # Пауза для защиты от спам-фильтра TG
                else:
                    print(f"--- [ERROR] Ошибка TG ({status}) на вакансии: {title}")

        print(f"--- [LOG] Завершено. Новых постов: {new_count} ---")

    except Exception as e:
        print(f"--- [CRITICAL] Ошибка выполнения: {e} ---")

if __name__ == "__main__":
    main()
