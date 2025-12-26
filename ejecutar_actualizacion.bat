@echo off
title Actualizacion de Dashboard Streamlit
echo ==================================================
echo INICIANDO PROCESO DE ACTUALIZACION SEMANAL
echo Fecha: %date% Hora: %time%
echo ==================================================
echo.

:: 1. Entrar a la carpeta del proyecto
cd /d "C:\Users\JOSE\Downloads\Streamlit App"

:: 2. Ejecutar el orquestador de Python
echo Ejecutando Notebooks... esto tomara unos 17-20 minutos.
echo NO CIERRES ESTA VENTANA.
echo.

"C:\Users\JOSE\AppData\Local\Programs\Python\Python312\python.exe" run_pipeline.py

echo.
echo ==================================================
echo PROCESO FINALIZADO
echo ==================================================
echo.
pause