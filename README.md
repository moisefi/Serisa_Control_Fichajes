# SERISA Control de Fichajes

Aplicacion de escritorio en Python para la gestion de fichajes RFID, con autenticacion por roles, conexion a PostgreSQL en red y un modulo auxiliar para Raspberry Pi que registra lecturas de tarjetas.

## Descripcion

El repositorio contiene un sistema completo de control horario compuesto por:

- una aplicacion de escritorio Tkinter para consulta y administracion de fichajes;
- una base de datos PostgreSQL con tablas, funciones y triggers;
- un servicio auxiliar para Raspberry Pi que escucha un lector RFID USB;
- scripts de empaquetado para generar ejecutables e instaladores.

La aplicacion principal permite trabajar con distintos perfiles de usuario y centraliza la operativa diaria de consulta, alta, edicion y exportacion de registros.

## Funcionalidades principales

- Inicio de sesion con usuarios de la aplicacion.
- Roles `admin`, `rrhh` y `basic`.
- Conexion automatica por hostname o manual por IP al servidor PostgreSQL.
- Refresco periodico de fichajes y estado de conexion.
- Filtros por usuario, UID, tipo y rango de fechas.
- Alta y baja de usuarios RFID.
- Edicion de fecha/hora y tipo de fichaje desde la tabla principal.
- Exportacion de informes a Excel y PDF.
- Gestion de usuarios de acceso desde una ventana de administracion.
- Logs de aplicacion por fecha.
- Servicio RFID independiente para Raspberry Pi / Linux.

## Roles

- `admin`: acceso completo, incluida la administracion de usuarios de acceso.
- `rrhh`: gestion de fichajes, usuarios RFID, conexion y exportaciones.
- `basic`: consulta restringida a los registros asociados a su usuario RFID.

Los usuarios `basic` deben estar vinculados a un `usuario_rfid`.

## Estructura del repositorio

```text
APP_Proyecto/
|-- Base_datos/
|   `-- create_database.sql
|-- imagenes/
|-- infraestructura/
|   |-- escaner_red.py
|   |-- registro_logs.py
|   |-- repositorio_autenticacion.py
|   `-- repositorio_fichajes.py
|-- instaladores/
|   |-- linux/
|   |-- macos/
|   `-- windows/
|-- interfaz/
|   |-- ventana_administracion.py
|   |-- ventana_exportacion.py
|   |-- ventana_login.py
|   `-- ventana_principal.py
|-- pytest/
|   |-- conftest.py
|   |-- test_configuracion.py
|   |-- test_interfaz_login.py
|   |-- test_interfaz_principal_admin.py
|   |-- test_repositorio_autenticacion.py
|   |-- test_repositorio_fichajes.py
|   |-- test_servicio_autenticacion.py
|   |-- test_servicio_conexion.py
|   |-- test_servicio_exportacion.py
|   `-- test_servicio_fichajes.py
|-- RPI_Code/
|   |-- lector_rfid_usb.py
|   `-- requirements.txt
|-- servicios/
|   |-- servicio_autenticacion.py
|   |-- servicio_conexion.py
|   |-- servicio_exportacion.py
|   `-- servicio_fichajes.py
|-- configuracion.py
|-- crear_admin.py
|-- main.py
|-- requirements.txt
|-- rutas.py
`-- config.json
```

## Requisitos

### Aplicacion principal

- Python 3.12
- PostgreSQL accesible por red
- `pip`

### Modulo Raspberry Pi

- Raspberry Pi o Linux con lector RFID USB compatible
- acceso a dispositivos `evdev`

## Instalacion en desarrollo

### 1. Crear entorno virtual

```bash
python -m venv .venv
```

### 2. Activar el entorno

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

La aplicacion combina configuracion persistente en disco y variables de entorno.

### `config.json`

Incluye parametros funcionales de la aplicacion:

- `ip_bd`: IP conocida del servidor PostgreSQL.
- `hostname_raspberry`: hostname a resolver en la red.
- `puerto_bd`: puerto de PostgreSQL.
- `nombre_bd`: nombre de la base de datos.
- `intervalo_refresco_ms`: frecuencia de refresco de la interfaz.

En el codigo actual, el fichero de configuracion persistente se guarda en el perfil del usuario:

- Windows: `%APPDATA%\SERISA\config.json`
- fallback multiplataforma: `~/.serisa/config.json`

Las credenciales no se persisten en ese archivo.

### `.env`

La aplicacion principal lee estas variables:

```env
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_postgres
```

Actualmente el empaquetado de Windows incluye el `.env` dentro de la aplicacion distribuida, por lo que esas credenciales forman parte del build si el archivo existe en el momento de empaquetar.

## Base de datos

El script [Base_datos/create_database.sql](Base_datos/create_database.sql) recrea la base `fichajes` e incluye:

- tablas `registros`, `usuarios`, `auth_usuarios` y `asignaciones_tarjetas`;
- indices para consultas por UID, fecha y username;
- triggers para alternancia automatica de `entrada` / `salida`;
- cierre de asignaciones activas al borrar usuarios;
- creacion automatica de asignaciones al registrar usuarios RFID;
- funcion para cerrar registros pendientes de salida en una fecha.

## Ejecucion

Iniciar la aplicacion principal:

```bash
python main.py
```

Crear el usuario administrador inicial:

```bash
python crear_admin.py
```

Si no existe un administrador previo, el script crea este acceso:

- usuario: `admin`
- contrasena: `admin`

Conviene cambiar esa contrasena en cuanto se valide el primer acceso.

## Modulo Raspberry Pi

La carpeta `RPI_Code/` contiene un servicio que detecta automaticamente un lector RFID USB compatible, escucha los eventos del dispositivo y registra los UIDs en la base de datos.

Instalacion minima:

```bash
cd RPI_Code
pip install -r requirements.txt
python lector_rfid_usb.py
```

Variables esperadas por ese modulo:

```env
BD_USUARIO=tu_usuario_postgres
BD_CONTRASENA=tu_password_postgres
BD_NOMBRE=fichajes
BD_HOST=ip_o_hostname
BD_PUERTO=5432
```

## Tests

El repositorio incluye pruebas unitarias y de integracion ligera sobre configuracion, servicios, repositorios, logging e interfaz.

Ejecucion:

```bash
pytest
```

## Empaquetado e instaladores

El proyecto ya incluye configuracion de empaquetado:

- `instaladores/windows/SERISA.spec` para PyInstaller en Windows.
- `instaladores/windows/` para ejecutable e instalador NSIS en Windows.
- `instaladores/linux/` para build Linux y empaquetado `tar.gz` / opcional `.deb`.
- `instaladores/macos/` para app macOS y empaquetado `zip` / opcional `.dmg`.

Cada subcarpeta de `instaladores/` contiene su propio `README.md` con los pasos concretos.

En Windows, el script principal es:

```powershell
.\instaladores\windows\build_windows.ps1
```

## Arquitectura

El proyecto sigue una separacion por capas:

- `interfaz/`: ventanas Tkinter y flujo de usuario.
- `servicios/`: logica de negocio y casos de uso.
- `infraestructura/`: acceso a datos, red y logging.
- `Base_datos/`: esquema SQL, funciones y triggers.
- `RPI_Code/`: captura de eventos RFID en hardware externo.

## Dependencias principales

- `psycopg2` para PostgreSQL.
- `bcrypt` para hash de contrasenas.
- `pandas` y `openpyxl` para exportacion a Excel.
- `reportlab` para PDF.
- `Pillow` y `tkcalendar` para recursos e interfaz.
- `python-dotenv` para variables de entorno.
- `pytest` para pruebas.

## Autor

Sergio Rojo

## Licencia

Proyecto academico y de uso educativo.
