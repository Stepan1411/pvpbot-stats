# Инструкция по деплою на Railway

## Шаг 1: Подготовка

Убедись что все файлы на месте:
- ✅ `backend/server.py` - основной код сервера
- ✅ `backend/requirements.txt` - зависимости Python
- ✅ `backend/Procfile` - команда запуска для Railway
- ✅ `backend/railway.json` - конфигурация Railway
- ✅ `backend/runtime.txt` - версия Python

## Шаг 2: Деплой на Railway

1. Зайди на https://railway.app
2. Войди через GitHub
3. Нажми **"New Project"**
4. Выбери **"Deploy from GitHub repo"**
5. Выбери свой репозиторий PVPBOT
6. Railway начнёт деплой

## Шаг 3: Настройка Root Directory

**ВАЖНО!** Railway должен запускаться из папки `backend`:

1. Открой проект в Railway
2. Перейди в **Settings**
3. Найди **"Root Directory"**
4. Установи значение: `backend`
5. Нажми **"Save"**
6. Railway автоматически перезапустит деплой

## Шаг 4: Проверка деплоя

1. Дождись завершения деплоя (статус "Active")
2. Railway покажет URL типа: `https://your-app.up.railway.app`
3. Открой в браузере: `https://your-app.up.railway.app/health`
4. Должен вернуться: `{"status": "ok"}`

## Шаг 5: Обновление мода

Теперь нужно обновить URL в моде:

1. Открой файл `src/main/java/org/stepan1411/pvp_bot/stats/StatsReporter.java`
2. Найди строку:
   ```java
   private static final String STATS_ENDPOINT = "https://api.github.com/gists/YOUR_GIST_ID";
   ```
3. Замени на:
   ```java
   private static final String STATS_ENDPOINT = "https://your-app.up.railway.app/api/stats";
   ```
   (подставь свой URL от Railway)
4. Пересобери мод: `./gradlew build`

## Шаг 6: Обновление сайта

1. Открой файл `docs/script.js`
2. Найди строку:
   ```javascript
   const BACKEND_URL = 'https://your-app.up.railway.app/api/stats';
   ```
3. Замени на свой URL от Railway
4. Закоммить и запушить изменения
5. GitHub Pages автоматически обновится

## Шаг 7: Тестирование

1. Запусти сервер Minecraft с модом
2. Подожди 1-2 минуты
3. Открой `https://your-app.up.railway.app/api/stats`
4. Должна появиться статистика с 1 сервером
5. Открой свой сайт на GitHub Pages
6. Статистика должна обновиться

## Возможные проблемы

### "ModuleNotFoundError: No module named 'main'"
- **Решение**: Проверь что Root Directory = `backend`
- **Решение**: Проверь что Procfile содержит `web: gunicorn server:app`

### "Application failed to respond"
- **Решение**: Проверь логи в Railway Dashboard
- **Решение**: Убедись что requirements.txt установлен правильно

### CORS ошибки на сайте
- **Решение**: Backend уже настроен с `flask-cors`, должно работать
- **Решение**: Проверь что URL в script.js правильный

### Статистика не обновляется
- **Решение**: Проверь что мод отправляет данные (логи сервера)
- **Решение**: Проверь что настройка `sendStats` включена в моде
- **Решение**: Проверь логи Railway на наличие входящих запросов

## Мониторинг

Railway предоставляет:
- **Metrics** - CPU, Memory, Network usage
- **Logs** - все логи приложения в реальном времени
- **Deployments** - история всех деплоев

## Бесплатный тариф Railway

- ✅ 500 часов выполнения в месяц
- ✅ 512 MB RAM
- ✅ 1 GB Disk
- ✅ Достаточно для статистики

Если превысишь лимит - Railway приостановит сервис до следующего месяца.

## Альтернативы

Если Railway не подходит, можно использовать:
- **Render.com** - 750 часов бесплатно
- **Fly.io** - 3 приложения бесплатно
- **Heroku** - требует карту даже на free tier

## Поддержка

Если что-то не работает:
1. Проверь логи в Railway Dashboard
2. Проверь что все файлы закоммичены в Git
3. Проверь что Root Directory = `backend`
4. Попробуй переделать деплой заново
