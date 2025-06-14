@echo off
echo Configurando usuarios predeterminados del sistema...
echo.
docker-compose exec ventas_api python manage.py setup_users
echo.
echo ¡Configuración completada!
pause
