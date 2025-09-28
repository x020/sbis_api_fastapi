#!/bin/bash

# Quick deployment script for SBIS API FastAPI
# Быстрый запуск для тестирования

set -e

echo "🚀 SBIS API FastAPI - Quick Deploy"
echo "=================================="

# Generate Caddyfile from template
echo "📄 Generating Caddyfile..."
python3 deploy/generate_caddyfile.py

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.example to .env and configure your settings:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Check required environment variables
required_vars=(
    "SABY_APP_CLIENT_ID"
    "SABY_APP_SECRET"
    "SABY_SECRET_KEY"
)

echo "🔍 Checking configuration..."
for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        echo "❌ Missing required variable: $var"
        exit 1
    fi
done

echo "✅ Configuration looks good!"

# Generate Caddyfile from template
echo "📄 Generating Caddyfile..."
python3 deploy/simple_generate.py

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check health
echo "🏥 Checking health..."

# Load domain from .env
if [[ -f ".env" ]]; then
    source .env
fi
domain="${DOMAIN:-localhost}"

if curl -f -s "http://localhost:8000/api/v1/health" > /dev/null; then
    echo "✅ API is healthy!"
    if curl -f -s -k "https://$domain/api/v1/health" > /dev/null; then
        echo "✅ Caddy is working!"
    fi
else
    echo "❌ API health check failed"
    echo "📊 Check logs:"
    echo "   docker-compose logs api"
    exit 1
fi

# Show status
echo ""
echo "🎉 Deployment successful!"
echo "========================="
echo "🌐 API URL: https://$domain"
echo "📚 Documentation: https://$domain/docs"
echo "🏥 Health Check: https://$domain/api/v1/health"
echo ""
echo "📊 Monitoring:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📜 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Restart: docker-compose restart"
echo "   Stop: docker-compose down"
echo ""
echo "✅ Ready to use!"