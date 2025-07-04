import os
import yt_dlp
import logging
import zipfile  # Necesario para comprimir
import zipfile
from variablesGlobales import progreso_actual

DOWNLOAD_DIR = "static/download"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Logger para debug
logger = logging.getLogger("yt_dlp")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def hook_progreso(d):
    if d['status'] == 'downloading':
        try:
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")

            if downloaded and total:
                porcentaje = round((downloaded / total) * 100, 1)
            else:
                porcentaje = 0
        except Exception as e:
            porcentaje = 0

        progreso_actual["porcentaje"] = porcentaje
        print(f"[] Progreso actual: {porcentaje}%")

    elif d['status'] == 'finished':
        progreso_actual["porcentaje"] = 100
        progreso_actual["completado"] = True
        print("[] Descarga finalizada, progreso 100%")


def descargar_video(url, audio=False, calidad="best", subtitulos=False):
    
     #  Reiniciar progreso antes de comenzar
    progreso_actual["porcentaje"] = 0
    progreso_actual["completado"] = False
    progreso_actual["error"] = None

    opciones = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        'format': 'bestaudio/best' if audio else calidad,
        "noplaylist": True,
        "quiet": False,
        "ignoreerrors": True,
        "overwrites": True,
        "ffmpeg_location": "ffmpeg/bin",
        "logger": logger,
        "progress_hooks": [hook_progreso],
        # 👇 Esto es lo nuevo
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    }

    if subtitulos:
        opciones.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["es", "en"],
            "subtitlesformat": "srt"
        })

    if audio:
        opciones["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
        opciones["prefer_ffmpeg"] = True
        opciones["keepvideo"] = False
    # Solo añadir merge_output_format si NO es audio
    if not audio:
        opciones["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                print(f"[] yt-dlp lanzó un error: {e}")
                return None

            if info is None:
                print("[] yt-dlp no devolvió info")
                return None

            filename = ydl.prepare_filename(info)
            if audio:
                filename = os.path.splitext(filename)[0] + ".mp3"

            if os.path.exists(filename):
                print(f"[] Archivo generado: {filename}")

                # 🔍 Buscar subtítulo
                srt_file = None
                if subtitulos:
                    base = os.path.splitext(filename)[0]
                    for lang in ["es", "en"]:
                        posible_srt = f"{base}.{lang}.srt"
                        if os.path.exists(posible_srt):
                            srt_file = posible_srt
                            break

                # Si hay subtítulo, hacer ZIP
                if srt_file:
                    zip_path = os.path.splitext(filename)[0] + ".zip"
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        zipf.write(filename, arcname=os.path.basename(filename))
                        zipf.write(srt_file, arcname=os.path.basename(srt_file))
                    print(f"[] ZIP creado: {zip_path}")
                    return {
                        "archivo": os.path.basename(zip_path),
                        "titulo": info.get("title", "descarga"),
                        "zip": True
                    }

                #  Retornar el archivo simple
                return {
                    "archivo": os.path.basename(filename),
                    "titulo": info.get("title", "descarga"),
                    "zip": False
                }

            else:
                print("[] Archivo no encontrado después de descarga")
                return None

    except Exception as e:
        progreso_actual["error"] = str(e)
        print(f"[] Error durante descarga: {e}")
        return None
