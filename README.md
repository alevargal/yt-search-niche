# YouTube Niche Discovery Agent

AI-агент который сам находит горячие YouTube ниши прямо сейчас — без указания темы. Анализирует конкуренцию, тренды и даёт стратегию входа по каждой нише.

## Что делает

- Собирает trending данные с YouTube, Google Trends, Reddit, HackerNews
- Claude находит топ 10 горячих ниш из всех сигналов
- По каждой нише: топ видео, конкуренты, тренды, монетизация, стратегия

## Быстрый старт

```bash
# 1. Клонируй репо
git clone https://github.com/alevargal/yt-search-niche.git
cd yt-search-niche

# 2. Установи зависимости
uv sync

# 3. Добавь ключи
cp .env.example .env
# Открой .env и вставь ключи

# 4. Запускай
uv run main.py
```

## Необходимые ключи

| Ключ | Где взять | Стоимость |
|------|-----------|-----------|
| `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) → YouTube Data API v3 | Бесплатно (10k req/day) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) | Платно |

Reddit и HackerNews работают без ключей.

## Использование

```bash
uv run main.py                  # US, топ 10 ниш
uv run main.py --region RU      # другой регион
uv run main.py --top 5          # меньше ниш, быстрее
```

## Стек

- Python 3.11+
- Claude Opus (Anthropic API)
- YouTube Data API v3
- Google Trends (pytrends)
- Reddit JSON API (без ключей)
- HackerNews Firebase API (без ключей)
- Rich (терминальный UI)
- uv (управление зависимостями)

## Пример вывода

```
📊 СВОДНЫЙ РЕЙТИНГ НИШИ
╔═══╤════════════════════╤══════════╤═════════╤══════════╤═══════╤══════════╤═════════╗
║ # │ Ниша               │ Overall  │ Возможн │ Конкурен │ Рост  │   CPM    │ Входить ║
╟───┼────────────────────┼──────────┼─────────┼──────────┼───────┼──────────┼─────────╢
║ 1 │ AI Productivity    │   8.1    │   8.4   │   3.2    │  8.7  │  $6–$18  │ ✅ Да   ║
║ 2 │ Personal Finance   │   7.8    │   7.5   │   6.1    │  8.2  │  $8–$22  │ ✅ Да   ║
║ 3 │ Gaming Tutorials   │   7.2    │   6.8   │   7.9    │  7.5  │  $3–$8   │ ✅ Да   ║
╚═══╧════════════════════╧══════════╧═════════╧══════════╧═══════╧══════════╧═════════╝
```

## Лицензия

MIT
