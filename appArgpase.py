import yt_dlp
import argparse
import os
# 🎯 Carpeta donde se guardarán los archivos descargados
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt_downloader")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
def descargar_video(url, audio=False, calidad="best", subtitulos=False):
    opciones = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': 'bestaudio/best' if audio else calidad,
        'quiet': False,
        'ffmpeg_location': os.path.abspath('ffmpeg/bin'),
    }
    if subtitulos:
         opciones.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['es', 'en'],
            'subtitlesformat': 'srt'
        })
    if audio:
        opciones.update({
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
  


    with yt_dlp.YoutubeDL(opciones) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            nombre_archivo = ydl.prepare_filename(info_dict)
            titulo = info_dict.get("title", "Video sin título")
            ydl.download([url])
            print("✅ Descarga completada.")
            return{
                "arhivo":os.path.basename(nombre_archivo),
                "titulo":titulo
            }
        except Exception as e:
            print(f"[!] Error al descargar: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Descargador de YouTube con yt-dlp")
    parser.add_argument("url", help="URL del video o playlist de YouTube")
    parser.add_argument("-a", "--audio", action="store_true", help="Descargar solo audio en formato MP3")
    parser.add_argument("-q", "--quality", default="best", help="Formato/calidad a descargar (por defecto: best)")
    parser.add_argument("--subtitulos", action="store_true", help="Descargar subtítulos en es/en (si están disponibles)")
    args = parser.parse_args()

    descargar_video(args.url, audio=args.audio, calidad=args.quality, subtitulos=args.subtitulos)

if __name__ == "__main__":
    main()
