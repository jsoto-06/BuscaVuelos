@echo off
title Vuelos Baratos - Panel Visual
echo ===================================================
echo Iniciando panel visual interactivo de Vuelos Baratos...
echo ===================================================
py -3.14 -m streamlit run app.py
if errorlevel 1 (
    python main.py web
)
pause
