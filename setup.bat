@echo off
title DevNet - Instalador de Ambiente
cls

echo 🛠️  Iniciando configuracao do ambiente DevNet...
echo ------------------------------------------------

:: 1. Cria o ambiente virtual se ele nao existir
if not exist venv (
    echo [1/5] Criando ambiente virtual (venv)...
    python -m venv venv
) else (
    echo [1/5] Ambiente virtual ja existe. Pulando...
)

:: 2. Ativa o ambiente virtual
echo [2/5] Ativando ambiente virtual...
call venv\Scripts\activate

:: 3. Instala as dependencias do requirements.txt
if exist requirements.txt (
    echo [3/5] Instalando dependencias do requirements.txt...
    pip install -r requirements.txt
) else (
    echo [3/5] AVISO: requirements.txt nao encontrado. Pulando instalacao.
)

:: 4. Cria o arquivo .env vazio se nao existir
if not exist .env (
    echo [4/5] Criando arquivo .env vazio...
    type nul > .env
    echo # Adicione seu GITHUB_CLIENT_ID e SECRET aqui >> .env
) else (
    echo [4/5] Arquivo .env ja existe.
)

:: 5. Cria o arquivo .gitignore vazio se nao existir
if not exist .gitignore (
    echo [5/5] Criando arquivo .gitignore basico...
    type nul > .gitignore
    echo venv/ >> .gitignore
    echo *.pyc >> .gitignore
    echo __pycache__/ >> .gitignore
    echo .env >> .gitignore
    echo devnet.db >> .gitignore
) else (
    echo [5/5] Arquivo .gitignore ja existe.
)

echo ------------------------------------------------
echo ✅ Ambiente configurado com sucesso!
echo 💡 Agora voce pode rodar o app.py.
pause