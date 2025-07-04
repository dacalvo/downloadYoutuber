import os, yt_dlp, zipfile
import logging
from variablesGlobales import progreso_actual, resultado_queue, contador_descargas
# Nuevas variables globales para playlist
contador_descargas = {"actual": 0, "total": 1}


DOWNLOAD_DIR = "static/download"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Logger para ver qué está pasando
logger = logging.getLogger("yt_dlp")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

def hook_progreso(d):

    if d['status'] == 'downloading':
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        porcentaje = round((downloaded / total) * 100, 1) if downloaded and total else 0

        progreso_actual["porcentaje"] = porcentaje
        progreso_actual["descargados"] = contador_descargas.get("actual", 0)
        progreso_actual["total"] = contador_descargas.get("total", 0)  # <- esta línea faltaba

        print(f"[] Progreso actual ({contador_descargas['actual']}/{contador_descargas['total']}): {porcentaje}%")

    elif d['status'] == 'finished':
        contador_descargas["actual"] += 1
        progreso_actual["porcentaje"] = round((contador_descargas["actual"] / contador_descargas["total"]) * 100, 1)
        progreso_actual["descargados"] = contador_descargas["actual"]
        progreso_actual["total"] = contador_descargas["total"]
        print(f"[] Video terminado. Progreso global: {progreso_actual['porcentaje']}%")

def descargar_playlist_videos(url, subtitulos):
    opciones = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(playlist_title)s/%(title)s.%(ext)s"),  # Organiza por carpeta
        "format":"best",  # MP4 si es posible
        "merge_output_format": "mp4",  # Evita .mkv por defecto
        "noplaylist": False,           # Descarga toda la lista
        "quiet": False,
        "ignoreerrors": True,
        "overwrites": True,
        "ffmpeg_location": "ffmpeg/bin",
        "logger": logger,
        "prefer_ffmpeg": True,
        "keepvideo": True,             # Mantiene el video
        "progress_hooks": [hook_progreso],
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    }
    
    srt_file = None
    if subtitulos:
        opciones.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["es", "en"],
            "subtitlesformat": "srt"
        })
        
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
        
            try:
                # Reiniciamos el progreso ANTES de iniciar la descarga
                progreso_actual["porcentaje"] = 0
                progreso_actual["completado"] = False
                progreso_actual["descargados"] = 0
                contador_descargas["actual"] = 0
                progreso_actual["total"] = 0
                # se inicia la descarga y se instancia en la variable info
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                print(f"[] yt-dlp lanzó un error: {e}")
                return None
            
            entradas = info.get("entries")
            if entradas:
                total = len(entradas)
            else:
                total = 1  # Es un solo video

            progreso_actual["total"] = total
            contador_descargas["total"] = total

            if info is None:
                print("[⚠️] yt-dlp no devolvió info")
                return None
            
            # Aquí lo insertás:
            progreso_actual["total"] = len(info.get("entries", []))  # <<< ESTA ES LA LÍNEA CLAVE
            
            #  Total de elementos
            contador_descargas["total"] = len(info.get("entries", [])) or 1
            playlist_title = info.get("title", "descarga")
            carpeta = os.path.join(DOWNLOAD_DIR, playlist_title)


            # Crear ZIP de toda la carpeta
            nombre_zip = f"{playlist_title}.zip"
            ruta_zip = os.path.join(DOWNLOAD_DIR, nombre_zip)
            print("[] Creando ZIP en:", ruta_zip)  #  LOG para verificar
            print("[] Archivos actuales en carpeta:", os.listdir(DOWNLOAD_DIR))
            with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for raiz, _, archivos in os.walk(carpeta):
                    for archivo in archivos:
                        path_archivo = os.path.join(raiz, archivo)
                        zipf.write(path_archivo, os.path.relpath(path_archivo, carpeta))


             #  Calculamos total SOLO si es playlist (tiene entries)
            #playlist_title = info.get("title", "descarga")
            #print(f"[] Playlist descargada: {playlist_title}")

            # Enviar redirección al frontend en return, de aca se alimentan las rutas
            progreso_actual["completado"] = True
            return {
                "archivo": nombre_zip,              # rchivo que se va a descargar (el .zip)
                 "titulo": playlist_title,           # nombre visible en la UI
                "zip": True,                        # necesario para mostrar botón de ZIP
                "elementos": total,
                "ruta": carpeta
                }

    except Exception as e:
        print(f"[] Error durante descarga: {e}")
        return None
    

