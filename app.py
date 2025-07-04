import os
import re
import shutil
import threading
import queue
import time
import glob
from urllib.parse import unquote

from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, send_from_directory, send_file
from downloader import descargar_video
from estado import cancelar_descarga
from download_playListmp4 import descargar_playlist_videos
from download_playmp3 import descargar_lista_audio
from variablesGlobales import progreso_actual, contador_descargas


# 🚀 Configuración inicial
app = Flask(__name__)
app.secret_key = "yakuzatube_secret_key_2025"
resultado_queue = queue.Queue()

# 🧠 Validación básica de URL de YouTube
def es_url_valida(url):
    patron = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
    return bool(re.match(patron, url.strip()))

# 🌐 Página principal
@app.route("/")
def index():
    return render_template("index.html")

# 🎬 Procesamiento de descarga (video/audio/playlist)
@app.route("/descargar", methods=["POST"])
def descargar():
    url = request.form.get("url")
    modo = request.form.get("modo")
    solo_audio = modo == "audio"
    subtitulo = request.form.get("subt") == "1"

    if not es_url_valida(url):
        flash("⚠️ Debes ingresar una URL válida.")
        return redirect(url_for("index"))

    def tarea():
        try:
            if modo == "playlist_audio":
                resultado=descargar_lista_audio(url=url)
            elif  modo == "playlist_video":
                resultado=descargar_playlist_videos(
                    url=url,
                    subtitulos=subtitulo
                    )
            else:
                resultado = descargar_video(
                    url=url,
                    audio=solo_audio,
                    subtitulos=subtitulo
                )
            if resultado:
                with app.app_context():
                    with app.test_request_context():
                        redirect_url = url_for(
                            "resultado",
                            archivo=resultado["archivo"],
                            titulo=resultado["titulo"],
                            zip=resultado.get("zip", False)
                        )
                        print(f"[🚀] Redirigiendo a: {redirect_url}")
                        resultado_queue.put({"redirect": redirect_url})
            else:
                resultado_queue.put({
                    "error": "❌ Descarga cancelada o ningún video fue procesado."
                })
        except Exception as e:
            resultado_queue.put({
                "error": f"❌ Error: {str(e)}"
            })
    # 🔄 Ejecutar descarga en un hilo separado
    threading.Thread(target=tarea).start()
    return render_template("cargando.html")

# 📥 Resultado final (usado si redireccionás después)
@app.route("/resultado")
def resultado():
    print("[🐞 DEBUG] Params recibidos:", request.args)
    archivo = request.args.get("archivo")
    titulo = request.args.get("titulo", "Video sin título")
    es_zip = request.args.get("zip") == "True"
    if not archivo:
        return "❌ Error: archivo no especificado", 400  # ✅ Agrega esto para debug
    
    archivo = unquote(archivo)  # ✅ ← Esto resuelve el problema
    titulo = unquote(titulo)
    return render_template("resultado.html", archivo=archivo, titulo=titulo, zip=es_zip)



@app.route("/descarga/<filename>")
def descarga(filename):
    # obtengo la ruta del archivo a descargar
    ruta_archivo = os.path.join("static/download", filename)

    if not os.path.exists(ruta_archivo):
        return "Archivo no encontrado", 404

    # Enviar archivo como respuesta
    respuesta = send_file(ruta_archivo, as_attachment=True)

    def eliminar_archivo_y_relacionados(ruta):
        time.sleep(5)
        try:
            base = os.path.splitext(ruta)[0]  # sin extensión
            # Eliminar archivo original
            os.remove(ruta)
            print(f"[🧹] Eliminado: {ruta}")

            # Si es ZIP, intentar eliminar video y SRT
            if ruta.endswith(".zip"):
                for ext in [".mp4", ".mp3", ".srt"]:
                    archivo_rel = base + ext
                    if os.path.exists(archivo_rel):
                        os.remove(archivo_rel)
                        print(f"[🧹] Eliminado relacionado: {archivo_rel}")
            
            for srt_file in glob.glob(base + "*.srt"):
                os.remove(srt_file)
                print(f"[🧹] Eliminado subtítulo: {srt_file}")

            # elimnar carpetas si las hay 
            carpeta_base="static/download/"
            for nombre in os.listdir(carpeta_base):
                ruta_completa = os.path.join(carpeta_base, nombre)
                if os.path.isdir(ruta_completa):
                    shutil.rmtree(ruta_completa)
                    print(f"✅ Carpeta eliminada: {ruta_completa}")
                    
        except Exception as e:
            print(f"[⚠️] Error al eliminar archivos: {e}")

    threading.Thread(target=eliminar_archivo_y_relacionados, args=(ruta_archivo,)).start()

    return respuesta

# 📡 Endpoint que consulta el progreso (AJAX polling)
@app.route("/progreso")
def progreso():
    if not resultado_queue.empty():
        resultado = resultado_queue.get()
        if "redirect" in resultado:
            progreso_actual["redirect"] = resultado["redirect"]   # ✅ 💾 Guarda la redirección
            progreso_actual["completado"] = True   
            return jsonify({
                "redirect": resultado["redirect"],
                "completado": True,
                "porcentaje": progreso_actual.get("porcentaje", 100),
               
                "descargados": contador_descargas.get("actual", 0),
                "total": progreso_actual.get("total", 0)  # 💡 ← Agregado aquí
                })
        else:
            return jsonify(resultado)
    else:
        return jsonify({
            "porcentaje": progreso_actual["porcentaje"],
            "completado": progreso_actual.get("completado", False),
            "descargados": progreso_actual.get("descargados", 0),
            "esperando": True
            })

# Página de error
@app.route("/error")
def error():
    msg = request.args.get("msg", "Error desconocido.")
    flash(f" {msg}")
    return redirect(url_for("index"))

@app.route("/cancelar")
def cancelar():
    cancelar_descarga.set()
    return redirect(url_for("index"))

#  Ejecutar app
if __name__ == "__main__":
    app.run(debug=True)
