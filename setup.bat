@echo off
title DevNet Setup
echo 🚀 Iniciando configuracao automatica...

:: 1. Criando o ambiente isolado
echo 📦 Criando venv...
python -m venv venv

:: 2. Ativando e atualizando
echo 🔌 Ativando ambiente virtual...
call venv\Scripts\activate
echo 🔄 Atualizando o pip...
python -m pip install --upgrade pip

:: 3. Instalando suas dependencias
echo 📥 Instalando pacotes de requeriments.txt...
pip install -r requeriments.txt

echo.
echo ✅ Tudo pronto! O motor da DevNet esta configurado.
echo 💡 Para rodar, use: python app.py
pause