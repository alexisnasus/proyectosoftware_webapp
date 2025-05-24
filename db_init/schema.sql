-- Habilitar extensión para UUID
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Tabla de productos
CREATE TABLE IF NOT EXISTS producto (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    precio DECIMAL(10, 2) NOT NULL
);

-- Tabla de transacciones (ventas)
CREATE TABLE IF NOT EXISTS transaccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmado_en TIMESTAMP NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'CONFIRMADA', 'FALLIDA'))
);

CREATE TABLE IF NOT EXISTS item (
    id SERIAL PRIMARY KEY,
    transaccion_id UUID NOT NULL REFERENCES transaccion(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL UNIQUE REFERENCES producto(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL DEFAULT 0
);

-- 1) Creamos la tabla de usuarios (custom AbstractUser)
CREATE TABLE IF NOT EXISTS users_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    role VARCHAR(10) NOT NULL
);

-- 2) Tabla para que Django marque migraciones aplicadas
CREATE TABLE IF NOT EXISTS django_migrations (
    id SERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMP WITH TIME ZONE NOT NULL
);

-- 3) Insertamos registro en django_migrations para "users/0001_initial"
INSERT INTO django_migrations (app, name, applied)
VALUES ('users', '0001_initial', NOW())
ON CONFLICT DO NOTHING;

-- 4) Insertamos los dos usuarios de prueba
INSERT INTO users_user (
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
