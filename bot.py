import feedparser
import requests
import os

# Получаем секретные ключи из настроек GitHub
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
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")

def main():
    # 1. Загружаем и парсим RSS ленту
    feed = feedparser.parse(RSS_URL)
    
    # 2. Проверяем наличие файла-базы данных. Если нет - создаем пустой.
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    
    # 3. Читаем список уже отправленных ссылок
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        sent_urls = set(f.read().splitlines())

    new_links = []
    
    # 4. Обрабатываем записи (от старых к новым)
    for entry in reversed(feed.entries):
        if entry.link not in sent_urls:
            # Формируем текст сообщения
            # entry.title - заголовок вакансии
            # entry.link - ссылка
            message = f"<b>{entry.title}</b>\n\n{entry.link}"
            
            # Отправляем
            send_telegram(message)
            
            # Добавляем в список новых
            new_links.append(entry.link)
            print(f"Отправлено: {entry.title}")

    # 5. Записываем новые ссылки в базу, чтобы не слать их повторно
    if new_links:
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            for link in new_links:
                f.write(link + "\n")
    else:
        print("Новых вакансий не найдено.")

if __name__ == "__main__":
    main()
