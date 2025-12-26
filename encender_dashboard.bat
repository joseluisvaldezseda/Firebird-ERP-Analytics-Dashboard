@echo off
title Lanzador Maestro - Dashboard Jose
echo ==================================================
echo 1. INICIANDO STREAMLIT (Puerto 8501)
echo ==================================================
esto @echo off
:: 1. Iniciar Streamlit en una ventana
start cmd /k ""C:\Users\JOSE\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run Dashboard.py --server.port 8501"
echo Esperando 8 segundos a que cargue el servidor...
timeout /t 8
echo.
echo ==================================================
echo 2. INICIANDO NGROK (Tunel Remoto)
echo ==================================================
:: Usamos la ruta completa de Ngrok que creamos en C:\ngrok
"C:\ngrok\ngrok.exe" http --url=dynamitic-prosthionic-eddie.ngrok-free.dev 8501
echo.
echo Si ves este mensaje, es que algo fallo.
pause