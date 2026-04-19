from __future__ import annotations

from configuracion import RepositorioConfiguracion
from dotenv import load_dotenv
from infraestructura.repositorio_autenticacion import RepositorioAutenticacion
from infraestructura.repositorio_fichajes import RepositorioFichajes
from servicios.servicio_autenticacion import ServicioAutenticacion
from servicios.servicio_conexion import ServicioConexion
from infraestructura.escaner_red import EscanerRed
from infraestructura.registro_logs import configurar_logger


def main() -> None:
    logger = configurar_logger()
    logger.info("Creación de usuario admin")

    load_dotenv()

    # =========================
    # CONFIGURACIÓN
    # =========================
    repositorio_configuracion = RepositorioConfiguracion()
    configuracion = repositorio_configuracion.cargar()

    repositorio_bd = RepositorioFichajes(
        usuario=configuracion.usuario_bd,
        contrasena=configuracion.contrasena_bd,
        nombre_bd=configuracion.nombre_bd,
        puerto=configuracion.puerto_bd,
    )

    escaner_red = EscanerRed(
        puerto_bd=configuracion.puerto_bd,
        nombre_host=configuracion.hostname_raspberry,
    )

    servicio_conexion = ServicioConexion(
        repositorio_bd=repositorio_bd,
        repositorio_configuracion=repositorio_configuracion,
        configuracion=configuracion,
        escaner_red=escaner_red,
    )

    # =========================
    # CONEXIÓN A BD
    # =========================
    conectado = False

    if configuracion.ip_bd:
        try:
            servicio_conexion.conectar_a_ip(configuracion.ip_bd)
            conectado = True
            logger.info(f"Conectado a BD usando IP guardada: {configuracion.ip_bd}")
        except Exception as e:
            logger.warning(f"No se pudo conectar con IP guardada: {e}")

    if not conectado:
        try:
            ip = servicio_conexion.buscar_ip()
            if ip:
                servicio_conexion.conectar_a_ip(ip)
                conectado = True
                logger.info(f"Conectado a BD tras búsqueda automática: {ip}")
        except Exception as e:
            logger.error(f"No se pudo conectar automáticamente: {e}")

    if not conectado:
        print("\n❌ No se pudo conectar a la base de datos.")
        print("Introduce manualmente la IP:")
        ip_manual = input("IP: ").strip()

        try:
            servicio_conexion.conectar_a_ip(ip_manual)
            logger.info(f"Conectado manualmente a {ip_manual}")
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return

    # =========================
    # SERVICIOS
    # =========================
    repo_auth = RepositorioAutenticacion(repositorio_bd)
    servicio_auth = ServicioAutenticacion(repo_auth)

    # =========================
    # CREACIÓN DE USUARIO
    # =========================
    username = "admin"
    password = "admin"
    rol = "admin"

    try:
        # comprobar si ya existe
        existente = repo_auth.obtener_usuario_por_username(username)

        if existente:
            print(f"\n⚠️ El usuario '{username}' ya existe.")
            return

        servicio_auth.crear_usuario(username, password, rol, True)

        print("\n✅ Usuario admin creado correctamente:")
        print("   usuario: admin")
        print("   contraseña: admin")

    except Exception as e:
        logger.exception("Error creando usuario admin")
        print(f"\n❌ Error: {e}")

    finally:
        try:
            servicio_conexion.desconectar()
        except Exception:
            pass


if __name__ == "__main__":
    main()