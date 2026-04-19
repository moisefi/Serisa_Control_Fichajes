# SERISA Control de Fichajes

Aplicacion de escritorio en Python para gestionar fichajes RFID con interfaz grafica, autenticacion por roles y conexion a una base de datos PostgreSQL alojada en red.

## Descripcion

El proyecto centraliza el registro y consulta de fichajes de personal. La aplicacion de escritorio permite:

- iniciar sesion con usuarios de la aplicacion;
- conectarse automaticamente o manualmente al servidor PostgreSQL;
- consultar y filtrar registros de fichaje;
- asignar tarjetas RFID a usuarios internos;
- editar registros de entrada y salida;
- exportar informes a Excel y PDF;
- administrar usuarios y permisos desde una ventana exclusiva para administradores.

El repositorio incluye ademas un modulo independiente para Raspberry Pi que lee tarjetas RFID por USB y registra sus UIDs en la base de datos.

## Funcionalidades principales

- Login con reconexion a base de datos desde la propia interfaz.
- Roles `admin`, `rrhh` y `basic`.
- Refresco periodico de registros.
- Filtros por usuario, UID, tipo y rango de fechas.
- Alta y baja de usuarios RFID.
- Edicion de fecha/hora y tipo de registro desde la tabla.
- Exportacion de informes en `Excel` y `PDF`.
- Ventana de administracion de usuarios de acceso.
- Sistema de logs diario para la aplicacion principal.
- Servicio auxiliar para lectura RFID en Raspberry Pi.

## Roles de usuario

- `admin`: acceso completo, incluida la ventana de administracion de usuarios.
- `rrhh`: gestion de fichajes, usuarios RFID, conexion y exportaciones.
- `basic`: consulta restringida de sus registros asociados.

Los usuarios `basic` deben tener asociado un `usuario_rfid`.

## Estructura del proyecto

```text
APP_Proyecto/
|-- main.py
|-- crear_admin.py
|-- configuracion.py
|-- config.json
|-- requirements.txt
|-- servicios/
|   |-- servicio_autenticacion.py
|   |-- servicio_conexion.py
|   |-- servicio_exportacion.py
|   `-- servicio_fichajes.py
|-- infraestructura/
|   |-- escaner_red.py
|   |-- registro_logs.py
|   |-- repositorio_autenticacion.py
|   `-- repositorio_fichajes.py
|-- interfaz/
|   |-- ventana_login.py
|   |-- ventana_principal.py
|   |-- ventana_exportacion.py
|   `-- ventana_administracion.py
|-- imagenes/
|-- logs/
`-- RPI_Code/
    |-- lector_rfid_usb.py
    `-- requirements.txt
```

## Requisitos

- Python 3.12
- PostgreSQL accesible por red
- `pip`

Para el modulo `RPI_Code`:

- Raspberry Pi o Linux con lector RFID USB
- acceso a dispositivos `evdev`

## Instalacion

### 1. Crear entorno virtual

```bash
python -m venv .venv
```

### 2. Activar entorno

En Windows:

```bash
.venv\Scripts\activate
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Configuracion

La aplicacion usa `config.json` y variables de entorno.

### `config.json`

Parametros principales:

- `ip_bd`: IP conocida del servidor PostgreSQL.
- `hostname_raspberry`: hostname que la aplicacion intentara resolver en red.
- `puerto_bd`: puerto de PostgreSQL.
- `usuario_bd`: usuario de base de datos.
- `contrasena_bd`: contrasena de base de datos.
- `nombre_bd`: nombre de la base de datos.
- `intervalo_refresco_ms`: frecuencia de actualizacion de la interfaz.

### `.env`

La aplicacion principal puede sobreescribir el usuario y la contrasena de base de datos con:

```env
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_postgres
```

## Ejecucion

Iniciar la aplicacion principal:

```bash
python main.py
```

Crear el usuario administrador inicial:

```bash
python crear_admin.py
```

El script crea, si no existe, este acceso por defecto:

- usuario: `admin`
- contrasena: `admin`

Conviene cambiar esa contrasena despues del primer acceso.

## Modulo Raspberry Pi

La carpeta `RPI_Code/` contiene un servicio que detecta automaticamente un lector RFID USB compatible, escucha eventos de teclado y registra los UIDs en la tabla de registros.

Instalacion basica:

```bash
cd RPI_Code
pip install -r requirements.txt
python lector_rfid_usb.py
```

Variables de entorno esperadas por ese modulo:

```env
BD_USUARIO=tu_usuario_postgres
BD_CONTRASENA=tu_password_postgres
BD_NOMBRE=fichajes
BD_HOST=ip_o_hostname
BD_PUERTO=5432
```

## Base funcional del sistema

Segun el codigo actual, la aplicacion trabaja sobre entidades equivalentes a:

- usuarios con nombre y tarjeta RFID;
- registros de fichaje con UID, fecha/hora y tipo;
- usuarios de acceso a la aplicacion con rol, password cifrada y enlace opcional a usuario RFID.

## Arquitectura

El proyecto esta organizado por capas:

- `interfaz/`: ventanas Tkinter y flujo de usuario.
- `servicios/`: reglas de negocio, autenticacion, exportacion y conexion.
- `infraestructura/`: acceso a PostgreSQL, red y logging.

Esta separacion facilita extender la interfaz o sustituir componentes de acceso a datos sin mezclar responsabilidades.

## Dependencias principales

- `psycopg2` para PostgreSQL.
- `bcrypt` para hashing de contrasenas.
- `pandas` y `openpyxl` para exportacion a Excel.
- `reportlab` para generacion de PDF.
- `Pillow` y `tkcalendar` para la interfaz.
- `python-dotenv` para configuracion por entorno.

## Logs

La aplicacion principal genera logs rotados por fecha en `logs/`.

El modulo Raspberry mantiene sus propios logs en la ruta configurada dentro de `RPI_Code/lector_rfid_usb.py`.

## Autor

Sergio Rojo

## Licencia

Proyecto academico y de uso educativo.
