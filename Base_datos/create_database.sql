\set ON_ERROR_STOP on

-- =========================================================
-- RECREAR COMPLETAMENTE LA BASE DE DATOS fichajes
-- Script para ejecutar con psql
-- =========================================================

-- Conectarse a una BD distinta de la que se va a borrar
\connect postgres

-- ---------------------------------------------------------
-- 1) Cerrar conexiones activas a la BD fichajes
-- ---------------------------------------------------------
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'fichajes'
  AND pid <> pg_backend_pid();

-- ---------------------------------------------------------
-- 2) Borrar y recrear la BD
-- ---------------------------------------------------------
DROP DATABASE IF EXISTS fichajes;
CREATE DATABASE fichajes;

-- ---------------------------------------------------------
-- 3) Entrar en la nueva BD
-- ---------------------------------------------------------
\connect fichajes

-- Opcional: asegurar esquema public
CREATE SCHEMA IF NOT EXISTS public;

-- =========================================================
-- 4) TABLAS
-- =========================================================

CREATE TABLE public.registros (
    id serial4 NOT NULL,
    uid_tarjeta varchar(50) NOT NULL,
    fecha_hora timestamp NOT NULL DEFAULT now(),
    tipo varchar(20) NOT NULL,
    CONSTRAINT registros_pkey PRIMARY KEY (id)
);

CREATE TABLE public.usuarios (
    id serial4 NOT NULL,
    nombre varchar(120) NOT NULL,
    uid_tarjeta varchar(50) NOT NULL,
    CONSTRAINT usuarios_pkey PRIMARY KEY (id),
    CONSTRAINT usuarios_uid_tarjeta_key UNIQUE (uid_tarjeta)
);

CREATE TABLE public.auth_usuarios (
    id serial4 NOT NULL,
    username varchar(50) NOT NULL,
    password_hash text NOT NULL,
    rol varchar(30) NOT NULL,
    activo bool NOT NULL DEFAULT true,
    creado_en timestamp NOT NULL DEFAULT now(),
    usuario_rfid varchar(255),
    CONSTRAINT auth_usuarios_pkey PRIMARY KEY (id),
    CONSTRAINT auth_usuarios_username_key UNIQUE (username)
);

CREATE TABLE public.asignaciones_tarjetas (
    id serial4 NOT NULL,
    uid_tarjeta text NOT NULL,
    nombre_usuario text NOT NULL,
    fecha_inicio timestamp NOT NULL DEFAULT now(),
    fecha_fin timestamp NULL,
    CONSTRAINT asignaciones_tarjetas_pkey PRIMARY KEY (id)
);

-- =========================================================
-- 5) ÍNDICES
-- =========================================================

CREATE INDEX idx_registros_uid_fecha
    ON public.registros (uid_tarjeta, fecha_hora DESC);

CREATE INDEX idx_registros_fecha
    ON public.registros (fecha_hora);

CREATE INDEX idx_asignaciones_uid_fecha_fin
    ON public.asignaciones_tarjetas (uid_tarjeta, fecha_fin);

CREATE INDEX idx_usuarios_uid_tarjeta
    ON public.usuarios (uid_tarjeta);

CREATE INDEX idx_auth_usuarios_username
    ON public.auth_usuarios (username);

-- =========================================================
-- 6) FUNCIONES
-- =========================================================

CREATE OR REPLACE FUNCTION public.asignacion_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE public.asignaciones_tarjetas
    SET fecha_fin = NOW()
    WHERE uid_tarjeta = OLD.uid_tarjeta
      AND fecha_fin IS NULL;

    RETURN OLD;
END;
$function$;

CREATE OR REPLACE FUNCTION public.asignacion_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    fecha_baja_anterior TIMESTAMP;
    primer_registro_sin_asignar TIMESTAMP;
    fecha_inicio_final TIMESTAMP;
BEGIN
    -- 1. Obtener fecha_fin de la última asignación
    SELECT MAX(fecha_fin)
    INTO fecha_baja_anterior
    FROM public.asignaciones_tarjetas
    WHERE uid_tarjeta = NEW.uid_tarjeta;

    -- 2. Buscar el PRIMER registro después de esa baja
    SELECT MIN(r.fecha_hora)
    INTO primer_registro_sin_asignar
    FROM public.registros r
    WHERE r.uid_tarjeta = NEW.uid_tarjeta
      AND (fecha_baja_anterior IS NULL OR r.fecha_hora > fecha_baja_anterior);

    -- 3. Decidir fecha_inicio
    IF primer_registro_sin_asignar IS NOT NULL THEN
        fecha_inicio_final := primer_registro_sin_asignar - INTERVAL '10 seconds';
    ELSE
        fecha_inicio_final := NOW();
    END IF;

    -- 4. Insertar asignación
    INSERT INTO public.asignaciones_tarjetas (
        uid_tarjeta,
        nombre_usuario,
        fecha_inicio
    )
    VALUES (
        NEW.uid_tarjeta,
        NEW.nombre,
        fecha_inicio_final
    );

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_asignar_tipo_registro()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    ultimo_tipo VARCHAR(20);
    ultima_fecha TIMESTAMP;
BEGIN
    IF NEW.fecha_hora IS NULL THEN
        NEW.fecha_hora := date_trunc('second', NOW());
    ELSE
        NEW.fecha_hora := date_trunc('second', NEW.fecha_hora);
    END IF;

    SELECT r.tipo, r.fecha_hora
    INTO ultimo_tipo, ultima_fecha
    FROM public.registros r
    WHERE r.uid_tarjeta = NEW.uid_tarjeta
    ORDER BY r.fecha_hora DESC, r.id DESC
    LIMIT 1;

    -- Si la misma tarjeta se ha pasado en menos de 2 minutos, no insertar
    IF ultima_fecha IS NOT NULL
       AND NEW.fecha_hora < (ultima_fecha + INTERVAL '2 minutes') THEN
        RETURN NULL;
    END IF;

    -- Si ya viene el tipo informado, lo respetamos
    IF NEW.tipo IS NOT NULL AND TRIM(NEW.tipo) <> '' THEN
        RETURN NEW;
    END IF;

    -- Alternancia automática entrada/salida
    IF ultimo_tipo IS NULL THEN
        NEW.tipo := 'entrada';
    ELSIF ultimo_tipo = 'salida' THEN
        NEW.tipo := 'entrada';
    ELSE
        NEW.tipo := 'salida';
    END IF;

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_cerrar_registros_pendientes(p_fecha date DEFAULT CURRENT_DATE)
RETURNS integer
LANGUAGE plpgsql
AS $function$
DECLARE
    registros_insertados INTEGER;
BEGIN
    INSERT INTO public.registros (uid_tarjeta, fecha_hora, tipo)
    SELECT pendientes.uid_tarjeta,
           (p_fecha + TIME '18:00:00')::timestamp,
           'salida'
    FROM (
        SELECT DISTINCT ON (r.uid_tarjeta)
               r.uid_tarjeta,
               r.tipo,
               r.fecha_hora
        FROM public.registros r
        WHERE r.fecha_hora::date = p_fecha
        ORDER BY r.uid_tarjeta, r.fecha_hora DESC, r.id DESC
    ) AS pendientes
    WHERE pendientes.tipo = 'entrada'
      AND NOT EXISTS (
          SELECT 1
          FROM public.registros r2
          WHERE r2.uid_tarjeta = pendientes.uid_tarjeta
            AND r2.fecha_hora = (p_fecha + TIME '18:00:00')::timestamp
            AND r2.tipo = 'salida'
      );

    GET DIAGNOSTICS registros_insertados = ROW_COUNT;
    RETURN registros_insertados;
END;
$function$;

-- =========================================================
-- 7) TRIGGERS
-- =========================================================

CREATE TRIGGER trg_asignar_tipo_registro
BEFORE INSERT ON public.registros
FOR EACH ROW
EXECUTE FUNCTION public.fn_asignar_tipo_registro();

CREATE TRIGGER trigger_insert_asignacion
AFTER INSERT ON public.usuarios
FOR EACH ROW
EXECUTE FUNCTION public.asignacion_insert();

CREATE TRIGGER trigger_delete_asignacion
AFTER DELETE ON public.usuarios
FOR EACH ROW