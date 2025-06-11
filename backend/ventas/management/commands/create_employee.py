from django.core.management.base import BaseCommand
from django.db import IntegrityError
from ventas.models import User


class Command(BaseCommand):
    help = 'Crear usuario empleado de prueba'

    def handle(self, *args, **options):
        try:
            # Verificar si ya existe el usuario trabajador
            if User.objects.filter(username='trabajador').exists():
                self.stdout.write(
                    self.style.WARNING('El usuario "trabajador" ya existe.')
                )
                return

            # Crear usuario empleado
            employee_user = User.objects.create_user(
                username='trabajador',
                password='worker123',
                email='trabajador@manumarket.com',
                first_name='Juan',
                last_name='Pérez',
                role='EMPLOYEE',
                is_staff=False,
                is_superuser=False,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuario empleado creado exitosamente:\n'
                    f'  - Username: {employee_user.username}\n'
                    f'  - Role: {employee_user.role}\n'
                    f'  - Email: {employee_user.email}\n'
                    f'  - Password: worker123'
                )
            )

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear el usuario empleado: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inesperado: {e}')
            )
