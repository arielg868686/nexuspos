# Script para activar la configuración completa del Asistente Llama
Write-Host "🚀 Iniciando configuración del Asistente Llama..." -ForegroundColor Cyan

# Verificar Python
Write-Host "`n📋 Verificando Python..." -ForegroundColor Yellow
python --version

# Instalar dependencias
Write-Host "`n📦 Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt

# Verificar Ollama
Write-Host "`n📋 Verificando Ollama..." -ForegroundColor Yellow
ollama --version

# Iniciar servidor
Write-Host "`n🚀 Iniciando servidor..." -ForegroundColor Cyan
python main.py 