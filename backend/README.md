# PVPBOT Stats Backend

Backend сервер для сбора и отображения статистики PVPBOT мода.

## Быстрый старт

### Локальная разработка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте `.env` файл:
```bash
cp .env.example .env
nano .env
```

3. Заполните переменные в `.env`:
```env
GITHUB_REPO=https://github.com/Stepan1411/pvpbot-stats-data.git
GITHUB_TOKEN=your_github_token
ADMIN_PASSWORD=your_password
GITHUB_BRANCH=main
```

4. Проверьте конфигурацию:
```bash
python3 check_config.py
```

5. Запустите сервер:
```bash
python3 server.py
```

Сервер будет доступен на `http://localhost:5000`

### Деплой на PythonAnywhere

См. [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) для пошаговой инструкции.

## Структура проекта

```
backend/
├── server.py           # Основной сервер
├── wsgi.py            # WSGI конфигурация для PythonAnywhere
├── requirements.txt   # Python зависимости
├── .env.example       # Пример конфигурации
├── .env              # Ваша конфигурация (не коммитится)
├── check_config.py   # Скрипт проверки конфигурации
└── data/             # Данные (Git репозиторий)
    ├── servers.json
    ├── global_stats.json
    ├── global_history.json
    └── server_*.json
```

## API Endpoints

### Публичные
- `GET /` - Главная страница со статистикой
- `GET /health` - Проверка здоровья сервера
- `POST /api/stats` - Приём статистики от мода
- `GET /api/stats` - Получение текущей статистики
- `GET /api/history` - Получение глобальной истории

### Админские (требуют Authorization)
- `GET /admin` - Админ панель
- `POST /api/admin/auth` - Авторизация
- `GET /api/admin/servers` - Список серверов
- `GET /api/admin/server/<id>` - Детали сервера
- `GET /api/admin/server/<id>/history` - История сервера
- `DELETE /api/admin/server/<id>` - Удаление сервера
- `POST /api/admin/backup` - Ручной бэкап в Git
- `POST /api/admin/reload` - Перезагрузка данных из Git
- `PUT /api/admin/stats` - Обновление глобальных счётчиков

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `GITHUB_REPO` | URL Git репозитория для бэкапов | - |
| `GITHUB_TOKEN` | GitHub Personal Access Token | - |
| `GITHUB_BRANCH` | Ветка Git | `main` |
| `ADMIN_PASSWORD` | Пароль админ панели | `admin123` |

## Получение GitHub Token

1. Зайдите на https://github.com/settings/tokens
2. "Generate new token" → "Generate new token (classic)"
3. Выберите права: `repo` (full control of private repositories)
4. Скопируйте токен и добавьте в `.env`

## Автоматические бэкапы

Сервер автоматически сохраняет данные в Git:
- При каждом обновлении данных (каждые 5 секунд от мода)
- Фоновый поток делает commit и push каждые 5 минут
- Можно сделать ручной бэкап через админ панель

## Хранение данных

Данные хранятся в папке `data/`:
- `servers.json` - информация о серверах
- `global_stats.json` - глобальные счётчики
- `global_history.json` - глобальная история (до 1 года)
- `server_<uuid>.json` - история каждого сервера (до 7 дней)

Все файлы автоматически коммитятся в Git репозиторий.

## Отладка

### Проверка логов
```bash
# Последние 100 строк
curl http://localhost:5000/api/logs?lines=100
```

### Проверка конфигурации
```bash
python3 check_config.py
```

### Проверка Git статуса
```bash
cd data
git status
git log --oneline -10
```

## Troubleshooting

### Ошибка "Unauthorized" в админ панели
- Проверьте что `ADMIN_PASSWORD` установлен в `.env`
- Очистите localStorage в браузере
- Войдите заново

### Git push не работает
- Проверьте что `GITHUB_TOKEN` правильный
- Проверьте права токена (нужен `repo`)
- Проверьте что репозиторий существует

### Данные не сохраняются
- Проверьте права на запись в папку `data/`
- Проверьте логи: `/api/logs`
- Проверьте что Git репозиторий инициализирован

## Лицензия

См. [LICENSE](../LICENSE) в корне проекта.
