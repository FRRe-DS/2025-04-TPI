@echo off
echo ============================================
echo    SETUP COMPLETO - DesarrolloAPP
echo ============================================
echo.

echo [1/3] Aplicando migraciones...
python manage.py migrate

echo.
echo [2/3] Creando datos de prueba...
python manage.py shell < setup_datos_prueba.py

echo.
echo [3/3] Verificando instalacion...
python verificar_instalacion.py

echo.
echo ============================================
echo           SETUP COMPLETADO
echo ============================================
pause
