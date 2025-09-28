#!/bin/bash

# SBIS API FastAPI Deployment Script
# Автоматизированный скрипт развертывания

set -e  # Прервать выполнение при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}


# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."

    local dependencies=("docker" "docker-compose" "curl" "git")
    local missing_deps=()

    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Отсутствуют зависимости: ${missing_deps[*]}"
        log_info "Установите их командой:"
        log_info "sudo apt update && sudo apt install -y ${missing_deps[*]}"
        exit 1
    fi

    log_success "Все зависимости установлены"
}

# Создание резервной копии
create_backup() {
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"

    if [[ -d "logs" ]] || [[ -d "backups" ]]; then
        log_info "Создание резервной копии..."

        mkdir -p "backups"
        tar -czf "backups/${backup_name}.tar.gz" logs/ backups/ 2>/dev/null || true

        log_success "Резервная копия создана: backups/${backup_name}.tar.gz"
    fi
}

# Генерация Caddyfile из шаблона
generate_caddyfile() {
    log_info "Генерация Caddyfile из шаблона..."

    if [[ -f "deploy/generate_caddyfile.py" ]]; then
        python3 deploy/generate_caddyfile.py
        log_success "Caddyfile сгенерирован"
    else
        log_warning "Скрипт генерации Caddyfile не найден"
    fi
}

# Получение обновлений
update_code() {
    if [[ -d ".git" ]]; then
        log_info "Получение обновлений из репозитория..."

        git fetch origin
        local local_commit=$(git rev-parse HEAD)
        local remote_commit=$(git rev-parse origin/main)

        if [[ "$local_commit" != "$remote_commit" ]]; then
            log_info "Обновление кода..."
            git pull origin main
            log_success "Код обновлен"
            return 0
        else
            log_info "У вас последняя версия кода"
            return 1
        fi
    else
        log_warning "Git репозиторий не найден, пропуск обновления"
        return 1
    fi
}

# Настройка конфигурации
setup_configuration() {
    log_info "Настройка конфигурации..."

    # Копирование шаблона .env если файл не существует
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warning "Создан .env файл из шаблона"
            log_warning "Отредактируйте .env файл с вашими настройками!"
            read -p "Продолжить развертывание? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Развертывание отменено. Отредактируйте .env и запустите скрипт снова."
                exit 0
            fi
        else
            log_error ".env.example не найден"
            exit 1
        fi
    fi

    # Проверка обязательных переменных
    local required_vars=(
        "SABY_APP_CLIENT_ID"
        "SABY_APP_SECRET"
        "SABY_SECRET_KEY"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "В .env файле отсутствуют обязательные переменные: ${missing_vars[*]}"
        exit 1
    fi

    log_success "Конфигурация настроена"
}

# Остановка существующих контейнеров
stop_containers() {
    log_info "Остановка существующих контейнеров..."

    docker-compose down 2>/dev/null || true
    log_success "Контейнеры остановлены"
}

# Сборка образов
build_images() {
    log_info "Сборка Docker образов..."

    if docker-compose build --no-cache; then
        log_success "Образы собраны"
    else
        log_error "Ошибка при сборке образов"
        exit 1
    fi
}

# Запуск сервисов
start_services() {
    log_info "Запуск сервисов..."

    if docker-compose up -d; then
        log_success "Сервисы запущены"
    else
        log_error "Ошибка при запуске сервисов"
        exit 1
    fi
}

# Проверка здоровья
check_health() {
    log_info "Проверка здоровья сервисов..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        log_info "Попытка $attempt/$max_attempts..."

        if curl -f -s "http://localhost/api/v1/health" > /dev/null 2>&1; then
            log_success "API сервис здоров"

            # Проверка Caddy
            if curl -f -s -k "https://localhost/api/v1/health" > /dev/null 2>&1; then
                log_success "Caddy работает корректно"
                return 0
            fi
        fi

        sleep 10
        ((attempt++))
    done

    log_error "Сервисы не прошли проверку здоровья"
    return 1
}

# Отображение статуса
show_status() {
    log_info "Статус развертывания:"

    echo
    log_success "=== СТАТУС СЕРВИСОВ ==="
    docker-compose ps

    echo
    log_success "=== ИНФОРМАЦИЯ О СЕРВИСЕ ==="
    echo "🌐 API Документация: https://sabby.ru/docs"
    echo "🔍 Health Check: https://sabby.ru/api/v1/health"
    echo "📊 Метрики: http://localhost:9090 (если настроен Prometheus)"
    echo "📈 Grafana: http://localhost:3000 (если настроена)"

    echo
    log_success "=== ЛОГИ ==="
    echo "API: docker-compose logs -f api"
    echo "Caddy: docker-compose logs -f caddy"
    echo "Redis: docker-compose logs -f redis"

    echo
    log_success "=== УПРАВЛЕНИЕ ==="
    echo "Перезапуск: docker-compose restart"
    echo "Остановка: docker-compose down"
    echo "Обновление: $0"
}

# Основная функция
main() {
    echo
    log_success "🚀 НАЧАЛО РАЗВЕРТЫВАНИЯ SBIS API FASTAPI"
    echo

    check_dependencies
    create_backup

    local code_updated=false
    if update_code; then
        code_updated=true
    fi

    generate_caddyfile
    setup_configuration

    if [[ "$code_updated" == true ]]; then
        stop_containers
        build_images
    fi

    start_services
    check_health
    show_status

    echo
    log_success "✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!"
    echo
    log_info "API доступен по адресу: https://sabby.ru"
    log_info "Документация: https://sabby.ru/docs"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "update")
        log_info "Режим обновления..."
        update_code && setup_configuration && build_images && start_services
        ;;
    "restart")
        log_info "Перезапуск сервисов..."
        stop_containers && start_services && check_health
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose logs -f "${2:-api}"
        ;;
    "backup")
        create_backup
        ;;
    *)
        main
        ;;
esac