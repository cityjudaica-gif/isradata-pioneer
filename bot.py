import feedparser
import requests
import os
import time

# Данные из секретов
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RSS_URL = "https://www.isradata.com/rss.xml"
DB_FILE = "sent_jobs.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload)
        return r.status_code
    except:
        return 500

def main():
    # Создаем сессию для имитации поведения человека
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    print(f"--- Запуск обхода защиты для Isradata ---")

    try:
        # Делаем запрос через сессию
        response = session.get(RSS_URL, timeout=20)
        
        # Если Cloudflare все еще блокирует, мы увидим это в логах
        if response.status_code != 200:
            print(f"Ошибка доступа: Код {response.status_code}. Сайт блокирует запрос.")
            return

        # Парсим полученный текст
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print("RSS прочитан, но он пуст. Проверьте содержимое ленты на сайте.")
            return

        # Инициализация базы
        if not os.path.exists(DB_FILE):
            open(DB_FILE, 'w', encoding='utf-8').close()
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_urls = set(f.read().splitlines())

        print(f"Найдено в ленте: {len(feed.entries)} вакансий.")

        new_count = 0
        # Обработка от старых к новым
        for entry in reversed(feed.entries):
            if entry.link not in sent_urls:
                msg = f"<b>{entry.title}</b>\n\n{entry.link}"
                if send_telegram(msg) == 200:
                    with open(DB_FILE, 'a', encoding='utf-8') as f:
                        f.write(entry.link + "\n")
                    new_count += 1
                    print(f"Отправлено: {entry.title}")
                    time.sleep(1) # Пауза, чтобы Telegram не забанил за спам

        print(f"Успешно завершено. Новых: {new_count}")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
