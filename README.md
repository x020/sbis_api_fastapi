# SBIS API FastAPI - Интеграция с Saby CRM

Высокопроизводительный API сервер на базе FastAPI для интеграции с Saby CRM с использованием сервисной авторизации.

## 🚀 Возможности

- **Сервисная авторизация** в Saby CRM с автоматическим обновлением токенов
- **RESTful API** для создания и управления сделками
- **Валидация данных** с использованием Pydantic
- **Структурированное логирование** с поддержкой JSON формата
- **Обработка ошибок** с детальными сообщениями
- **CORS поддержка** для веб-приложений
- **Rate limiting** для защиты от перегрузки
- **Health checks** для мониторинга состояния
- **Docker контейнеризация** для простого развертывания
- **Caddy reverse proxy** с автоматическим SSL
- **Prometheus метрики** для мониторинга

## 📋 Требования

- Python 3.11+
- Docker и Docker Compose
- Любой домен с настроенными DNS записями
- Учетные данные Saby CRM (app_client_id, app_secret, secret_key)

## 🛠️ Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd sbis_api_fastapi
```

### 2. Настройка переменных окружения

```bash
# Копировать шаблон конфигурации
cp .env.example .env

# Отредактировать .env файл с вашими настройками
nano .env
```

**Обязательные настройки в .env:**

```env
# Saby CRM API Configuration
SABY_APP_CLIENT_ID=your_actual_app_client_id
SABY_APP_SECRET=your_actual_app_secret
SABY_SECRET_KEY=your_actual_secret_key

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
ENVIRONMENT=production

# Security
SECRET_KEY=your-super-secret-key-change-this

# Domain Configuration (укажите ваш домен)
DOMAIN=example.com
CADDY_EMAIL=admin@example.com
```

### 3. Получение учетных данных Saby CRM

1. Войдите в личный кабинет Saby по адресу https://saby.ru
2. Перейдите в раздел "Настройки" → "Интеграция" → "API"
3. Добавьте внешнее приложение:
   - Название: "SBIS API FastAPI"
   - Тип: "Сервисное приложение"
   - URL: `https://{{DOMAIN}}`
4. Получите параметры:
   - `app_client_id`
   - `app_secret`
   - `secret_key`

### 4. Сборка и запуск с Docker Compose

```bash
# Сборка и запуск всех сервисов
docker-compose up -d --build

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f api
docker-compose logs -f caddy
```

### 5. Проверка работоспособности

```bash
# Health check
curl https://{{DOMAIN}}/api/v1/health

# API информация
curl https://{{DOMAIN}}/api/v1/info

# Документация API
# Откройте в браузере: https://{{DOMAIN}}/docs
```

## 📚 Использование API

### Создание сделки

```bash
curl -X POST "https://{{DOMAIN}}/api/v1/deals" \
  -H "Content-Type: application/json" \
  -d '{
    "regulation": 123456,
    "contact_person": {
      "name": "Иванов Иван Иванович",
      "phone": "+79991234567",
      "email": "ivanov@example.com"
    },
    "note": "Сделка из внешней системы",
    "nomenclatures": [
      {
        "code": "PRODUCT001",
        "price": 1500.50,
        "count": 2
      }
    ]
  }'
```

### Получение статуса сделки

```bash
curl https://{{DOMAIN}}/api/v1/deals/12345
```

### Получение темы отношений

```bash
curl https://{{DOMAIN}}/api/v1/themes/Продажи
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `SABY_APP_CLIENT_ID` | ID приложения Saby | Обязательная |
| `SABY_APP_SECRET` | Секрет приложения Saby | Обязательная |
| `SABY_SECRET_KEY` | Сервисный ключ Saby | Обязательная |
| `SERVER_PORT` | Порт сервера | 8000 |
| `DEBUG` | Режим отладки | false |
| `LOG_LEVEL` | Уровень логирования | INFO |
| `CORS_ORIGINS` | Разрешенные источники CORS | ["https://{{DOMAIN}}"] |

### Структура проекта

```
sbis_api_fastapi/
├── app/
│   ├── api/
│   │   └── routes.py          # API эндпоинты
│   ├── exceptions/
│   │   └── handlers.py        # Обработка ошибок
│   ├── models/
│   │   └── schemas.py         # Pydantic модели
│   ├── services/
│   │   ├── auth.py           # Авторизация в Saby
│   │   └── saby_client.py    # Saby CRM API клиент
│   └── utils/
│       └── logger.py          # Система логирования
├── config/
│   └── config.py             # Конфигурация приложения
├── docker/
│   └── Dockerfile            # Docker образ
├── deploy/
│   └── scripts               # Скрипты развертывания
├── logs/                     # Логи приложения
├── backups/                  # Резервные копии
├── main.py                   # Главный файл приложения
├── requirements.txt          # Python зависимости
├── .env.example             # Шаблон конфигурации
├── Caddyfile               # Конфигурация Caddy
└── docker-compose.yml      # Docker Compose конфигурация
```

## 🚀 Развертывание

### Развертывание на сервере

1. **Подготовка сервера:**
```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Установка Caddy (если не используется Docker)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

2. **Настройка DNS:**
   - Создайте A запись: `{{DOMAIN}}` → IP вашего сервера
   - Создайте A запись: `api.{{DOMAIN}}` → IP вашего сервера

3. **Запуск приложения:**
```bash
# Клонирование и настройка
git clone <repository-url>
cd sbis_api_fastapi
cp .env.example .env
nano .env  # Настройте переменные

# Запуск
docker-compose up -d --build
```

### Мониторинг

```bash
# Статус сервисов
docker-compose ps

# Логи
docker-compose logs -f api
docker-compose logs -f caddy

# Метрики Prometheus
curl http://localhost:9090/metrics

# Grafana (если настроена)
# URL: http://your-server:3000
# Логин: admin / пароль из .env
```

## 🔒 Безопасность

### SSL/TLS
- Автоматические сертификаты Let's Encrypt через Caddy
- HTTP → HTTPS редирект
- Безопасные заголовки

### Аутентификация
- Сервисная авторизация в Saby CRM
- Автоматическое обновление токенов
- Защищенные учетные данные

### Rate Limiting
- Ограничение запросов: 60 в минуту
- Burst: 10 запросов
- Настраиваемые лимиты

## 🛠️ Разработка

### Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# С тестами
pytest

# Проверка кода
black .
isort .
flake8 .
```

### API Документация

После запуска откройте в браузере:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📊 Мониторинг

### Метрики Prometheus

Доступные метрики:
- `http_requests_total` - общее количество запросов
- `http_request_duration_seconds` - длительность запросов
- `saby_api_calls_total` - вызовы Saby API
- `saby_auth_errors_total` - ошибки авторизации

### Логи

Логи сохраняются в:
- JSON формат для продакшена
- Файлы ротируются автоматически
- Уровни: DEBUG, INFO, WARNING, ERROR

### Health Checks

```bash
# Проверка здоровья API
curl https://{{DOMAIN}}/api/v1/health

# Проверка подключения к Saby
curl https://{{DOMAIN}}/api/v1/health
# Должно вернуть: "saby_connected": true
```

## 🔧 Troubleshooting

### Проблемы с авторизацией Saby

1. Проверьте учетные данные в .env
2. Убедитесь, что приложение активно в Saby
3. Проверьте логи: `docker-compose logs api`

### Проблемы с SSL сертификатами

```bash
# Проверка сертификатов
docker-compose exec caddy caddy list-certs

# Перезапуск Caddy
docker-compose restart caddy
```

### Проблемы с производительностью

1. Увеличьте количество workers в Dockerfile
2. Настройте Redis для кеширования
3. Проверьте лимиты ресурсов в docker-compose.yml

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь в корректности конфигурации .env
3. Проверьте статус сервисов: `docker-compose ps`
4. Создайте issue в репозитории

## 📄 Лицензия

Этот проект лицензирован под MIT License.

## 🔄 Обновления

```bash
# Получение обновлений
git pull origin main

# Пересборка контейнеров
docker-compose build --no-cache
docker-compose up -d
```

---

**Примечание**: Перед развертыванием в продакшн обязательно измените все секретные ключи и пароли в файле .env!