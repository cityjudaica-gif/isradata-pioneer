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
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code
    except:
        return 500

def main():
    print("--- Запуск системы Isradata (Ультра-обход) ---")
    
    # Создаем скрейпер с имитацией конкретного браузера
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:
        # Добавляем паузу перед запросом, чтобы не выглядеть как мгновенный бот
        time.sleep(2)
        
        # Получаем RSS
        response = scraper.get(RSS_URL, timeout=30)
        
        # Если Cloudflare все еще злится, пробуем получить главную, чтобы "согреть" куки
        if response.status_code != 200:
            print(f"Прямой доступ закрыт ({response.status_code}). Пробуем через сессию...")
            scraper.get("https://www.isradata.com/", timeout=20)
            response = scraper.get(RSS_URL, timeout=20)

        # Печатаем первые 100 символов ответа для отладки в логах GitHub
        print(f"Ответ сервера (первые 100 симв): {response.text[:100]}")

        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("ОШИБКА: Вакансии не найдены. Сайт прислал пустой ответ или страницу блокировки.")
            return

        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        print(f"Успех! Найдено в ленте: {len(feed.entries)}")

        new_count = 0
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                # Очищаем заголовок от лишних пробелов
                title = entry.title.strip()
                message = f"<b>{title}</b>\n\n{entry.link}"
                
                if send_telegram(message) == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    print(f"Отправлено: {title}")
                    time.sleep(1)

        print(f"--- Завершено. Отправлено: {new_count} ---")

    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
