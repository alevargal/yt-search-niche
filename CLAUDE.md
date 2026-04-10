# yt-search-niche

YouTube нише-разведчик — агент который **сам** находит горячие ниши прямо сейчас, анализирует конкуренцию по каждой и выдаёт полную аналитику с рекомендациями.

## Что делает агент

1. **Собирает сигналы** из 4 источников без указания темы:
   - YouTube trending top 100 (mostPopular chart)
   - Google Trends — трендовые запросы сегодня
   - Reddit r/all — горячие посты
   - HackerNews — front page
2. **Claude #1** находит топ 10 горячих ниш из всех данных
3. **По каждой нише** собирает YouTube видео, каналы, тренды, RSS конкурентов
4. **Claude #2** делает глубокий анализ каждой ниши
5. Выводит **полный отчёт**: сводная таблица + детальный блок по каждой нише

## Запуск

```bash
# Установка зависимостей (нужен uv)
uv sync

# Запуск (регион US по умолчанию)
uv run main.py

# С другим регионом
uv run main.py --region RU

# Меньше ниш (быстрее)
uv run main.py --top 5
```

## Структура файлов

```
yt-search-niche/
├── main.py                      # точка входа
├── pyproject.toml               # зависимости (uv)
├── .env                         # ключи (не в git)
├── .env.example                 # шаблон ключей
└── src/
    ├── config.py                # настройки через pydantic-settings
    ├── models.py                # Pydantic модели данных
    ├── youtube/
    │   ├── client.py            # YouTube API v3 клиент
    │   ├── trending.py          # trending videos + keyword search
    │   └── stats.py             # метрики, channel details
    ├── trends/
    │   └── google.py            # Google Trends: trending + keyword analysis
    ├── reddit/
    │   └── search.py            # Reddit r/all hot (без API ключей)
    ├── hackernews/
    │   └── search.py            # HackerNews front page (без API ключей)
    ├── rss/
    │   └── youtube.py           # RSS каналов конкурентов (без квоты)
    ├── discovery/
    │   ├── finder.py            # сбор всех трендовых данных
    │   └── claude_discover.py   # Claude находит топ ниши из сырых данных
    ├── ai/
    │   └── claude.py            # Claude глубокий анализ одной ниши
    └── report/
        └── formatter.py         # Rich: красивый вывод в терминал
```

## Необходимые ключи (.env)

- `YOUTUBE_API_KEY` — [Google Cloud Console](https://console.cloud.google.com/) → YouTube Data API v3 (бесплатно, 10k запросов/день)
- `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com/)

Reddit и HackerNews работают **без ключей**.

## Что выводит агент

```
📊 СВОДНЫЙ РЕЙТИНГ НИШИ        ← таблица топ 10 с оценками

🌐 СЫРЫЕ СИГНАЛЫ               ← Google Trends, Reddit, HN

── #1 — AI PRODUCTIVITY TOOLS ──
  📊 СТАТИСТИКА                 ← просмотры, медиана, длина видео
  🏆 ТОП ВИДЕО                  ← топ 8 видео с цифрами
  👥 ТОП КОНКУРЕНТЫ             ← топ 6 каналов, подписчики, частота
  📈 GOOGLE TRENDS              ← рост 30д/90д, растущие запросы
  ⚔️  КОНКУРЕНЦИЯ & 💰 МОНЕТИЗАЦИЯ ← уровень, CPM, sponsor потенциал
  🎯 НЕЗАКРЫТЫЕ УГЛЫ            ← 5 конкретных возможностей
  📋 РЕКОМЕНДАЦИЯ CLAUDE        ← стратегия, вывод, overall score
```

## Модели данных (src/models.py)

- `RawTrendingData` — сырые данные со всех источников
- `NicheReport` — полный анализ одной ниши
- `NicheAnalysis` — Claude анализ (оценки, стратегия, углы)
- `FullDiscoveryReport` — итоговый отчёт со всеми нишами
