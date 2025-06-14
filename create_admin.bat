@echo off
echo Creando usuario administrador...
docker-compose exec ventas_api python manage.py create_admin
echo.
echo Usuario administrador creado. Credenciales:
echo Username: admin
echo Password: admin123
pause
