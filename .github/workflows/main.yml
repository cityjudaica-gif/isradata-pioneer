name: Isradata Auto Poster

on:
  schedule:
    - cron: '*/30 * * * *' # Запуск каждые 30 минут
  workflow_dispatch:      # Кнопка для ручного запуска

jobs:
  run-bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write    # Разрешение боту записывать данные в репозиторий
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install feedparser requests

      - name: Run Bot Script
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python bot.py

      - name: Save database changes
        run: |
          git config --global user.name "Isradata Bot"
          git config --global user.email "bot@isradata.com"
          git add sent_jobs.txt
          git commit -m "Update sent jobs database [skip ci]" || echo "No changes to commit"
          git push
