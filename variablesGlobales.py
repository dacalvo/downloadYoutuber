# progreso_estado.py (o en memoria global del servidor)
from queue import Queue
resultado_queue = Queue()
contador_descargas = {"actual": 0}
progreso_actual = {
    "porcentaje": 0,
    "completado": False,
    "descargados": 0,
    "error": None
}