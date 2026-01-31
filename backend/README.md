# PVPBOT Statistics Backend

Простой backend для сбора статистики с серверов.

## Деплой на бесплатный хостинг

### Вариант 1: Render.com (рекомендуется)

1. Зарегистрируйся на https://render.com
2. New → Web Service
3. Connect GitHub repository
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`
   - Environment: Python 3
5. Deploy

### Вариант 2: Railway.app

1. Зарегистрируйся на https://railway.app
2. New Project → Deploy from GitHub
3. Выбери репозиторий
4. Settings → Root Directory: `backend`
5. Settings → Start Command: `gunicorn server:app` (должно быть автоматически)
6. Deploy

**Важно:** Railway должен автоматически определить Python и использовать `Procfile`

### Вариант 3: Heroku

1. Создай `Procfile`:
   ```
   web: gunicorn server:app
   ```
2. Deploy через Heroku CLI или GitHub

## Локальный запуск

```bash
cd backend
pip install -r requirements.txt
python server.py
```

Сервер запустится на `http://localhost:5000`

## API Endpoints

### POST /api/stats
Принимает статистику от серверов

Request:
```json
{
  "server_id": "uuid",
  "bots_count": 5,
  "mod_version": "1.0.0",
  "minecraft_version": "1.21.11"
}
```

### GET /api/stats
Возвращает агрегированную статистику

Response:
```json
{
  "servers_online": 10,
  "bots_active": 50,
  "total_downloads": 1000,
  "mod_version": "1.0.0",
  "last_update": "2026-01-31T14:00:00Z"
}
```

## Настройка в моде

После деплоя обнови URL в `StatsReporter.java`:

```java
private static final String STATS_ENDPOINT = "https://your-app.onrender.com/api/stats";
```
