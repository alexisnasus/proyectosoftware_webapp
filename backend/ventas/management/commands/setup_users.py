from django.core.management.base import BaseCommand
from django.db import IntegrityError
from ventas.models import User


class Command(BaseCommand):
    help = 'Crear usuarios predeterminados del sistema (admin y empleado)'

    def handle(self, *args, **options):
        users_created = 0
        users_skipped = 0

        # Lista de usuarios a crear
        default_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'admin@manumarket.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            },
            {
                'username': 'trabajador',
                'password': 'worker123',
                'email': 'trabajador@manumarket.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'role': 'EMPLOYEE',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True
            }
        ]

        self.stdout.write(
            self.style.HTTP_INFO('Creando usuarios predeterminados...\n')
        )

        for user_data in default_users:
            try:
                # Verificar si ya existe el usuario
                if User.objects.filter(username=user_data['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f'El usuario "{user_data["username"]}" ya existe. Saltando...')
                    )
                    users_skipped += 1
                    continue

                # Crear usuario
                user = User.objects.create_user(**user_data)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Usuario creado: {user.username} ({user.get_role_display()})'
                    )
                )
                users_created += 1

            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error al crear "{user_data["username"]}": {e}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error inesperado con "{user_data["username"]}": {e}')
                )

        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.HTTP_INFO(
                f'RESUMEN:\n'
                f'  - Usuarios creados: {users_created}\n'
                f'  - Usuarios saltados: {users_skipped}\n'
                f'  - Total de usuarios en la base de datos: {User.objects.count()}'
            )
        )
        
        if users_created > 0:
            self.stdout.write('\n' + self.style.SUCCESS('¡Usuarios predeterminados configurados correctamente!'))
            self.stdout.write(
                self.style.HTTP_INFO(
                    'Credenciales de acceso:\n'
                    '  - Admin: admin / admin123\n'
                    '  - Empleado: trabajador / worker123'
                )
            )
