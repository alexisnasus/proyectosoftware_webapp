from django.core.management.base import BaseCommand
from django.db import IntegrityError
from ventas.models import User


class Command(BaseCommand):
    help = 'Crear usuario administrador predeterminado'

    def handle(self, *args, **options):
        try:
            # Verificar si ya existe el usuario admin
            if User.objects.filter(username='admin').exists():
                self.stdout.write(
                    self.style.WARNING('El usuario "admin" ya existe.')
                )
                return

            # Crear usuario administrador
            admin_user = User.objects.create_user(
                username='admin',
                password='admin123',
                email='admin@manumarket.com',
                first_name='Juan',
                last_name='Negrete',
                role='ADMIN',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuario administrador creado exitosamente:\n'
                    f'  - Username: {admin_user.username}\n'
                    f'  - Role: {admin_user.role}\n'
                    f'  - Email: {admin_user.email}\n'
                    f'  - Password: admin123'
                )
            )

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear el usuario administrador: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inesperado: {e}')
            )
