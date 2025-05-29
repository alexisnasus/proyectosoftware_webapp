-- Insertar usuarios en la tabla correcta según tu nuevo modelo en ventas
INSERT INTO ventas_user (
    password,
    last_login,
    is_superuser,
    username,
    first_name,
    last_name,
    email,
    is_staff,
    is_active,
    date_joined,
    role
) VALUES
(
    -- admin/admin123
    'pbkdf2_sha256$1000000$0MPV2emWd8hNlQ4iNxpcJ5$d/3Z9Uyo3XGMjcVlM+cNSTeuWI6gum/2loTqvlzM2ZA=',
    NULL,
    TRUE,
    'admin',
    '',
    '',
    '',
    TRUE,
    TRUE,
    NOW(),
    'ADMIN'
),
(
    -- trabajador/worker123
    'pbkdf2_sha256$1000000$S7wtLCJhXrutNag8u0rkpJ$dfhKCFLNLEyf03hqr0y7IdA653C+yN58QBk01a05bBk=',
    NULL,
    FALSE,
    'trabajador',
    '',
    '',
    '',
    FALSE,
    TRUE,
    NOW(),
    'EMPLOYEE'
)
ON CONFLICT (username) DO NOTHING;
