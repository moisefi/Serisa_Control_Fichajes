import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler

import psycopg2
from dotenv import load_dotenv
from evdev import InputDevice, categorize, ecodes, list_devices


load_dotenv()


def obtener_variable_entorno(nombre, valor_por_defecto=None, obligatoria=True):
    valor = os.getenv(nombre, valor_por_defecto)
    if obligatoria and (valor is None or str(valor).strip() == ""):
        raise ValueError(f"Falta la variable de entorno obligatoria: {nombre}")
    return valor


USUARIO_BD = obtener_variable_entorno("BD_USUARIO")
CONTRASENA_BD = obtener_variable_entorno("BD_CONTRASENA")
NOMBRE_BD = obtener_variable_entorno("BD_NOMBRE")
HOST_BD = obtener_variable_entorno("BD_HOST", "localhost", obligatoria=False)
PUERTO_BD = int(obtener_variable_entorno("BD_PUERTO", "5432", obligatoria=False))

TIEMPO_BLOQUEO_MISMA_TARJETA = 3

PALABRAS_CLAVE_PRIORIDAD = [
    "rfid",
    "reader",
    "card",
    "usb",
    "hid",
    "keyboard",
    "teclado"
]

RUTA_BASE = "/home/srojo/Lector_tarjetas"
RUTA_LOGS = os.path.join(RUTA_BASE, "logs")
ARCHIVO_LOG = os.path.join(RUTA_LOGS, "lector_rfid.log")


def configurar_logger():
    os.makedirs(RUTA_LOGS, exist_ok=True)

    logger = logging.getLogger("lector_rfid")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = TimedRotatingFileHandler(
        filename=ARCHIVO_LOG,
        when="W0",
        interval=1,
        backupCount=8,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


logger = configurar_logger()


def conectar_bd():
    return psycopg2.connect(
        host=HOST_BD,
        port=PUERTO_BD,
        user=USUARIO_BD,
        password=CONTRASENA_BD,
        dbname=NOMBRE_BD
    )


def registrar_uid(uid):
    conexion = None
    try:
        conexion = conectar_bd()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO registros (uid_tarjeta) VALUES (%s)",
                (uid,)
            )
        conexion.commit()
        logger.info("UID registrado correctamente: %s", uid)
    except Exception as error:
        logger.exception("Error al registrar UID %s: %s", uid, error)
    finally:
        if conexion:
            conexion.close()


def obtener_dispositivos_entrada():
    dispositivos = []
    for ruta in list_devices():
        try:
            dispositivo = InputDevice(ruta)
            caps = dispositivo.capabilities(verbose=True)
            dispositivos.append((dispositivo, caps))
        except Exception:
            continue
    return dispositivos


def es_dispositivo_tipo_teclado(capacidades):
    try:
        for clave, valores in capacidades.items():
            nombre_evento = clave[0] if isinstance(clave, tuple) else str(clave)
            if "EV_KEY" in str(nombre_evento):
                return True
        return False
    except Exception:
        return False


def puntuacion_dispositivo(nombre):
    nombre = (nombre or "").lower()
    puntuacion = 0

    for palabra in PALABRAS_CLAVE_PRIORIDAD:
        if palabra in nombre:
            puntuacion += 10

    if "gpio" in nombre or "virtual" in nombre:
        puntuacion -= 5

    return puntuacion


def detectar_lector():
    candidatos = []

    for dispositivo, capacidades in obtener_dispositivos_entrada():
        nombre = dispositivo.name or ""
        if es_dispositivo_tipo_teclado(capacidades):
            candidatos.append((puntuacion_dispositivo(nombre), dispositivo))

    if not candidatos:
        raise RuntimeError("No se ha encontrado ningún dispositivo de entrada compatible")

    candidatos.sort(key=lambda x: x[0], reverse=True)
    mejor = candidatos[0][1]

    logger.info("Lector detectado automáticamente: %s - %s", mejor.path, mejor.name)
    return mejor


def convertir_tecla_a_caracter(tecla):
    mapa = {
        "KEY_0": "0",
        "KEY_1": "1",
        "KEY_2": "2",
        "KEY_3": "3",
        "KEY_4": "4",
        "KEY_5": "5",
        "KEY_6": "6",
        "KEY_7": "7",
        "KEY_8": "8",
        "KEY_9": "9",
        "KEY_A": "A",
        "KEY_B": "B",
        "KEY_C": "C",
        "KEY_D": "D",
        "KEY_E": "E",
        "KEY_F": "F",
        "KEY_G": "G",
        "KEY_H": "H",
        "KEY_I": "I",
        "KEY_J": "J",
        "KEY_K": "K",
        "KEY_L": "L",
        "KEY_M": "M",
        "KEY_N": "N",
        "KEY_O": "O",
        "KEY_P": "P",
        "KEY_Q": "Q",
        "KEY_R": "R",
        "KEY_S": "S",
        "KEY_T": "T",
        "KEY_U": "U",
        "KEY_V": "V",
        "KEY_W": "W",
        "KEY_X": "X",
        "KEY_Y": "Y",
        "KEY_Z": "Z",
    }
    return mapa.get(tecla, "")


def leer_uid_desde_dispositivo(dispositivo):
    buffer = ""
    ultimo_uid = None
    ultimo_instante = 0

    for evento in dispositivo.read_loop():
        if evento.type != ecodes.EV_KEY or evento.value != 1:
            continue

        tecla = categorize(evento).keycode

        if isinstance(tecla, list):
            tecla = tecla[0]

        if tecla == "KEY_ENTER":
            uid = buffer.strip()
            buffer = ""

            if not uid:
                continue

            ahora = time.time()

            if uid == ultimo_uid and (ahora - ultimo_instante) < TIEMPO_BLOQUEO_MISMA_TARJETA:
                logger.info("UID duplicado ignorado temporalmente: %s", uid)
                continue

            ultimo_uid = uid
            ultimo_instante = ahora

            registrar_uid(uid)
            continue

        caracter = convertir_tecla_a_caracter(tecla)
        if caracter:
            buffer += caracter


def main():
    logger.info("Iniciando lector RFID USB...")

    while True:
        try:
            dispositivo = detectar_lector()
            leer_uid_desde_dispositivo(dispositivo)

        except KeyboardInterrupt:
            logger.info("Servicio detenido manualmente")
            break

        except Exception as error:
            logger.exception("Error en el lector: %s", error)
            logger.info("Reintentando detección en 3 segundos...")
            time.sleep(3)


if __name__ == "__main__":
    main()