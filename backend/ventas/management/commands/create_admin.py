from django.core.management.base import BaseCommand
from django.db import IntegrityError
from ventas.models import User


class Command(BaseCommand):
    help = 'Crear usuarios predeterminados (admin y trabajador)'

    def handle(self, *args, **options):
        # Credenciales predefinidas
        users_to_create = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'juan@manumarket.com',
                'first_name': 'Juan',
                'last_name': 'Negrete',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            },
            {
                'username': 'seba',
                'password': 'worker123',
                'email': 'trabajador@manumarket.com',
                'first_name': 'Sebastian',
                'last_name': 'Alonzo',
                'role': 'EMPLOYEE',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True
            }
        ]

        created_users = []
        
        try:
            for user_data in users_to_create:
                username = user_data['username']
                password = user_data.pop('password')  # Extraer password antes de crear
                
                # Verificar si ya existe el usuario
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'El usuario "{username}" ya existe.')
                    )
                    continue

                # Crear usuario
                user = User.objects.create_user(
                    password=password,
                    **user_data
                )
                
                created_users.append({
                    'username': username,
                    'password': password,
                    'role': user.role,
                    'email': user.email
                })
                
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario "{username}" creado exitosamente')
                )

            # Mostrar resumen de credenciales
            if created_users:
                self.stdout.write(
                    self.style.SUCCESS('\n' + '='*50)
                )
                self.stdout.write(
                    self.style.SUCCESS('CREDENCIALES DE ACCESO CREADAS:')
                )
                self.stdout.write(
                    self.style.SUCCESS('='*50)
                )
                
                for user in created_users:
                    role_display = 'ADMINISTRADOR' if user['role'] == 'ADMIN' else 'EMPLEADO'
                    self.stdout.write(f'\n{role_display}:')
                    self.stdout.write(f'  Username: {user["username"]}')
                    self.stdout.write(f'  Password: {user["password"]}')
                    self.stdout.write(f'  Email: {user["email"]}')
                
                self.stdout.write('\n' + '='*50)
            else:
                self.stdout.write(
                    self.style.WARNING('No se crearon usuarios nuevos.')
                )

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear usuarios: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inesperado: {e}')
            )
