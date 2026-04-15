# 🕒 Serisa Control de Fichajes

Aplicación desarrollada en Python para la gestión y control de fichajes,
permitiendo la conexión con dispositivos de red, registro de accesos y
exportación de datos.

------------------------------------------------------------------------

## 📌 Descripción

Este proyecto implementa un sistema de control de fichajes orientado a
entornos empresariales.\
Permite conectarse a dispositivos de registro, almacenar los datos y
ofrecer funcionalidades de exportación y visualización mediante interfaz
gráfica.

------------------------------------------------------------------------

## 🚀 Funcionalidades

-   🔌 Conexión con dispositivos de red
-   📝 Registro de fichajes
-   📦 Almacenamiento estructurado de datos
-   📊 Exportación de información
-   🖥️ Interfaz gráfica para interacción del usuario
-   📁 Sistema de logs para seguimiento de actividad

------------------------------------------------------------------------

## 🧱 Estructura del proyecto

    APP_Proyecto/
    │
    ├── main.py                  # Punto de entrada de la aplicación
    ├── configuracion.py         # Configuración general
    ├── config.json              # Parámetros de configuración
    ├── errores.py               # Gestión de errores
    │
    ├── servicios/               # Lógica de negocio
    │   ├── servicio_conexion.py
    │   ├── servicio_fichajes.py
    │   └── servicio_exportacion.py
    │
    ├── infraestructura/         # Acceso a datos y sistema
    │   ├── escaner_red.py
    │   ├── registro_logs.py
    │   └── repositorio_fichajes.py
    │
    ├── interfaz/                # Interfaz gráfica
    │   ├── ventana_principal.py
    │   └── ventana_exportacion.py
    │
    ├── logs/                    # Archivos de logs
    ├── imagenes/                # Recursos gráficos
    └── requirements.txt         # Dependencias

------------------------------------------------------------------------

## ⚙️ Instalación

### 1. Clonar el repositorio

``` bash
git clone git@github.com:moisefi/Serisa_Control_Fichajes.git
cd Serisa_Control_Fichajes
```

### 2. Crear entorno virtual

``` bash
python -m venv .venv
```

### 3. Activar entorno

**Windows:**

``` bash
.venv\Scripts\activate
```

**Linux/Mac:**

``` bash
source .venv/bin/activate
```

### 4. Instalar dependencias

``` bash
pip install -r requirements.txt
```

### 5. Instalar dependencias
``` bash
Crea un archivo .env con:
DB_USER=Usuario_postgres
DB_PASSWORD=Contraseña_postgres
```
------------------------------------------------------------------------

## ▶️ Ejecución

``` bash
python main.py
```

------------------------------------------------------------------------

## ⚙️ Configuración

El archivo `config.json` contiene los parámetros de configuración del
sistema (conexiones, rutas, etc.).


------------------------------------------------------------------------

## 🧪 Logs

Los logs de la aplicación se almacenan en:

    /logs/

Permiten analizar errores y actividad del sistema.

------------------------------------------------------------------------

## 🧠 Arquitectura

El proyecto sigue una separación por capas:

-   Interfaz → interacción con el usuario\
-   Servicios → lógica de negocio\
-   Infraestructura → acceso a datos y red

Esto facilita el mantenimiento y escalabilidad.

------------------------------------------------------------------------

## 📌 Requisitos

-   Python 3.12.7
-   pip

------------------------------------------------------------------------

## ✍️ Autor

-   Sergio (moisefi)

------------------------------------------------------------------------

## 📄 Licencia

Uso educativo / proyecto personal
