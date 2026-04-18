from __future__ import annotations

from configuracion import RepositorioConfiguracion
from dotenv import load_dotenv
from infraestructura.escaner_red import EscanerRed
from infraestructura.registro_logs import configurar_logger
from infraestructura.repositorio_autenticacion import RepositorioAutenticacion
from infraestructura.repositorio_fichajes import RepositorioFichajes
from interfaz.ventana_login import VentanaLogin
from interfaz.ventana_principal import VentanaPrincipal
from servicios.servicio_autenticacion import ServicioAutenticacion
from servicios.servicio_conexion import ServicioConexion
from servicios.servicio_fichajes import ServicioFichajes


if __name__ == "__main__":
    logger = configurar_logger()
    logger.info("Inicio de la aplicación")

    load_dotenv()
    repositorio_configuracion = RepositorioConfiguracion()
    try:
        configuracion = repositorio_configuracion.cargar()
    except Exception as error:
        logger.warning(str(error))
        configuracion = repositorio_configuracion.cargar()

    repositorio_fichajes = RepositorioFichajes(
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
        repositorio_bd=repositorio_fichajes,
        repositorio_configuracion=repositorio_configuracion,
        configuracion=configuracion,
        escaner_red=escaner_red,
    )
    servicio_fichajes = ServicioFichajes(repositorio_fichajes)

    repositorio_autenticacion = RepositorioAutenticacion(repositorio_fichajes)
    servicio_autenticacion = ServicioAutenticacion(repositorio_autenticacion)

    login = VentanaLogin(
        servicio_autenticacion=servicio_autenticacion,
        servicio_conexion=servicio_conexion,
        logger=logger,
    )
    sesion = login.mostrar()

    if sesion is None:
        logger.info("Aplicación cerrada antes de iniciar sesión")
    else:
        app = VentanaPrincipal(
            configuracion=configuracion,
            servicio_conexion=servicio_conexion,
            servicio_fichajes=servicio_fichajes,
            servicio_autenticacion=servicio_autenticacion,
            logger=logger,
            sesion=sesion,
        )
        app.mainloop()