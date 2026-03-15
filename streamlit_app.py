# instalar
# pip install requests
# pip install streamlit requests
# pip install streamlit requests azure-cognitiveservices-speech


# =========================
# CONFIG
# =========================



import os
import tempfile
from pathlib import Path
import re
import requests
import streamlit as st
import azure.cognitiveservices.speech as speechsdk

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
GENRES_URL = "https://api.themoviedb.org/3/genre/movie/list"
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

# Ejemplo region: eastus, westus2, brazilsouth, etc.



# ==========================================
# TMDB
# ==========================================
def obtener_generos():
    params = {
        "api_key": TMDB_API_KEY,
        "language": "es-MX"
    }
    response = requests.get(GENRES_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("genres", [])


def descubrir_peliculas_por_genero(genero_id):
    params = {
        "api_key": TMDB_API_KEY,
        "language": "es-MX",
        "sort_by": "popularity.desc",
        "include_adult": False,
        "include_video": False,
        "page": 1,
        "with_genres": genero_id
    }
    response = requests.get(DISCOVER_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])


def buscar_peliculas_por_texto(query):
    params = {
        "api_key": TMDB_API_KEY,
        "language": "es-MX",
        "query": query,
        "page": 1,
        "include_adult": False
    }
    response = requests.get(SEARCH_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])


# ==========================================
# AZURE SPEECH - STT
# ==========================================
def reconocer_voz_desde_archivo_wav(ruta_audio):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )
    speech_config.speech_recognition_language = "es-MX"

    audio_config = speechsdk.audio.AudioConfig(filename=ruta_audio)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text

    if result.reason == speechsdk.ResultReason.NoMatch:
        return None

    if result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        raise Exception(
            f"Reconocimiento cancelado. Motivo: {details.reason}. "
            f"Detalles: {details.error_details}"
        )

    return None




# ==========================================
# AZURE SPEECH - TTS
# ==========================================
def hablar_texto(texto, voz="es-MX-DaliaNeural"):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )
    speech_config.speech_synthesis_voice_name = voz

    # Le pedimos WAV simple para Streamlit
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None
    )

    result = synthesizer.speak_text_async(texto).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data

    if result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        raise Exception(
            f"Síntesis cancelada. Motivo: {details.reason}. "
            f"Detalles: {details.error_details}"
        )

    raise Exception("No se pudo sintetizar el audio.")


# ==========================================
# LÓGICA SIMPLE DE INTERPRETACIÓN
# ==========================================
def normalizar_texto(texto):
    texto = texto.lower().strip()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)
    return texto


def construir_mapa_sinonimos():
    return {
        "miedo": "Horror",
        "terrorificas": "Horror",
        "terrorifica": "Horror",
        "de miedo": "Horror",
        "graciosas": "Comedy",
        "graciosa": "Comedy",
        "comicas": "Comedy",
        "comica": "Comedy",
        "romanticas": "Romance",
        "romantica": "Romance",
        "amor": "Romance",
        "accion": "Action",
        "aventuras": "Adventure",
        "aventura": "Adventure",
        "animadas": "Animation",
        "animada": "Animation",
        "infantiles": "Family",
        "familiar": "Family",
        "familiares": "Family",
        "ciencia ficcion": "Science Fiction",
        "sci fi": "Science Fiction",
        "ficcion": "Science Fiction",
        "suspenso": "Thriller",
        "thriller": "Thriller",
        "documentales": "Documentary",
        "documental": "Documentary",
        "crimen": "Crime",
        "criminales": "Crime",
        "fantasia": "Fantasy",
        "historicas": "History",
        "historica": "History",
        "musicales": "Music",
        "musical": "Music",
        "misterio": "Mystery",
        "belicas": "War",
        "belica": "War",
        "guerra": "War",
        "western": "Western",
        "vaqueros": "Western"
    }


def limpiar_frase_para_busqueda(frase):
    frase = normalizar_texto(frase)

    patrones = [
        r"^ensename\s+peliculas\s+de\s+",
        r"^ensename\s+peliculas\s+del\s+genero\s+",
        r"^ensename\s+peliculas\s+",
        r"^ensename\s+",
        r"^muestrame\s+peliculas\s+de\s+",
        r"^muestrame\s+peliculas\s+del\s+genero\s+",
        r"^muestrame\s+peliculas\s+",
        r"^muestrame\s+",
        r"^busca\s+peliculas\s+de\s+",
        r"^busca\s+peliculas\s+del\s+genero\s+",
        r"^busca\s+peliculas\s+",
        r"^busca\s+",
        r"^quiero\s+ver\s+peliculas\s+de\s+",
        r"^quiero\s+ver\s+peliculas\s+del\s+genero\s+",
        r"^quiero\s+ver\s+peliculas\s+",
        r"^quiero\s+ver\s+",
        r"^peliculas\s+de\s+",
        r"^peliculas\s+",
        r"^dame\s+peliculas\s+de\s+",
        r"^dame\s+peliculas\s+",
    ]

    for patron in patrones:
        frase = re.sub(patron, "", frase).strip()

    return frase


def detectar_genero(frase_usuario, mapa_generos_normalizado, sinonimos_genero):
    frase_norm = normalizar_texto(frase_usuario)

    for nombre_genero_norm, nombre_genero_real in mapa_generos_normalizado.items():
        patron = rf"\b{re.escape(nombre_genero_norm)}\b"
        if re.search(patron, frase_norm):
            return nombre_genero_real

    for sinonimo, genero_real_tmdb in sinonimos_genero.items():
        patron = rf"\b{re.escape(normalizar_texto(sinonimo))}\b"
        if re.search(patron, frase_norm):
            return genero_real_tmdb

    return None


def detectar_genero_o_texto(frase_usuario, mapa_generos, mapa_generos_normalizado):
    sinonimos_genero = construir_mapa_sinonimos()

    genero_detectado = detectar_genero(
        frase_usuario,
        mapa_generos_normalizado,
        sinonimos_genero
    )

    if genero_detectado and genero_detectado in mapa_generos:
        return ("genero", genero_detectado)

    texto_busqueda = limpiar_frase_para_busqueda(frase_usuario)

    if texto_busqueda:
        return ("texto", texto_busqueda)

    return (None, None)


# ==========================================
# UI
# ==========================================
def mostrar_resultados(resultados, titulo_seccion):
    st.subheader(titulo_seccion)

    if not resultados:
        st.info("No se encontraron películas.")
        return

    num_columnas = 3
    cols = st.columns(num_columnas)

    for i, pelicula in enumerate(resultados):
        titulo = pelicula.get("title", "Sin título")
        fecha = pelicula.get("release_date", "Sin fecha")
        rating = pelicula.get("vote_average", "N/A")
        overview = pelicula.get("overview", "Sin sinopsis.")
        poster_path = pelicula.get("poster_path")

        with cols[i % num_columnas]:
            if poster_path:
                poster_url = f"{IMAGE_BASE_URL}{poster_path}"
                st.image(poster_url, use_container_width=True)
            else:
                st.write("Sin póster")

            st.markdown(f"**{titulo}**")
            st.caption(f"📅 {fecha}")
            st.caption(f"⭐ {rating}")

            with st.expander("Ver sinopsis"):
                st.write(overview)


def construir_mensaje_hablado(tipo_busqueda, valor, resultados):
    cantidad = len(resultados)

    if tipo_busqueda == "genero":
        return f"Encontré {cantidad} películas del género {valor}."
    if tipo_busqueda == "texto":
        return f"Encontré {cantidad} resultados para {valor}."
    return "Ya tengo los resultados listos."


def procesar_consulta(frase_usuario, mapa_generos, mapa_generos_normalizado, hablar=False):
    tipo_busqueda, valor = detectar_genero_o_texto(
        frase_usuario,
        mapa_generos,
        mapa_generos_normalizado
    )

    if tipo_busqueda == "genero":
        genero_id = mapa_generos[valor]
        resultados = descubrir_peliculas_por_genero(genero_id)
        mostrar_resultados(resultados, f"Resultados por género: {valor}")

    elif tipo_busqueda == "texto":
        resultados = buscar_peliculas_por_texto(valor)
        mostrar_resultados(resultados, f"Resultados por nombre o franquicia: {valor}")

    else:
        st.error("No pude interpretar tu búsqueda.")
        return

    if hablar:
        try:
            mensaje = construir_mensaje_hablado(tipo_busqueda, valor, resultados)
            audio_bytes = hablar_texto(mensaje)

            st.success(f"🔊 Respuesta: {mensaje}")
            st.audio(audio_bytes, format="audio/wav", autoplay=True)

        except Exception as e:
            st.error(f"No pude generar la respuesta hablada: {e}")


# ==========================================
# APP
# ==========================================
st.set_page_config(page_title="SpeechMovies con TMDb + Azure Speech", layout="wide")
st.title("⭐⭐ SpeechMovies con MS AZURE ⭐⭐")
st.write("Bienvenido al sistema de búsqueda de películas usando la API de Microsoft Azure Speech Service")
st.write(" ")
st.write(" ")
st.write("Instrucciones:")
st.write("Para buscar una película puedes escribir o hablar frases como:")
st.write("🟢 Busca películas de terror")
st.write("🟢 Busca películas de dragon ball")
st.write("🟢 Quiero ver películas románticas")
st.write(" ")
st.write(" ")

if not TMDB_API_KEY or TMDB_API_KEY == "TU_TMDB_API_KEY_AQUI":
    st.warning("Coloca tu API key de TMDb.")
    st.stop()

try:
    generos = obtener_generos()
except Exception as e:
    st.error(f"Error al obtener géneros de TMDb: {e}")
    st.stop()

mapa_generos = {g["name"]: g["id"] for g in generos}
mapa_generos_normalizado = {
    normalizar_texto(nombre): nombre for nombre in mapa_generos.keys()
}

modo = st.radio("Modo de entrada", ["", "Micrófono"], horizontal=True)
activar_respuesta_hablada = st.checkbox("Activar respuesta hablada", value=True)

if modo == "Texto":
    frase_usuario = st.text_input(
        "Escribe tu solicitud",
        placeholder="Ejemplo: busca películas de terror"
    )

    if st.button("Buscar por texto"):
        if not frase_usuario.strip():
            st.warning("Escribe una frase.")
        else:
            try:
                procesar_consulta(
                    frase_usuario,
                    mapa_generos,
                    mapa_generos_normalizado,
                    hablar=activar_respuesta_hablada
                )
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

else:

    if not AZURE_SPEECH_KEY or AZURE_SPEECH_KEY == "TU_AZURE_SPEECH_KEY_AQUI":
        st.warning("Coloca tu Azure Speech key.")
        st.stop()

    if not AZURE_SPEECH_REGION or AZURE_SPEECH_REGION == "TU_AZURE_SPEECH_REGION_AQUI":
        st.warning("Coloca tu Azure Speech region.")
        st.stop()

    audio_usuario = st.audio_input(
        "🎤 Graba tu búsqueda por voz",
        sample_rate=16000
    )

    if audio_usuario is not None:
        st.audio(audio_usuario)

        if st.button("Procesar audio con Azure"):
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_usuario.read())
                    temp_path = tmp_file.name

                texto_reconocido = reconocer_voz_desde_archivo_wav(temp_path)

                if texto_reconocido:
                    st.success(f"Texto reconocido: {texto_reconocido}")
                    procesar_consulta(
                        texto_reconocido,
                        mapa_generos,
                        mapa_generos_normalizado,
                        hablar=activar_respuesta_hablada
                    )
                else:
                    st.warning("No pude reconocer voz. Intenta grabar de nuevo.")

            except Exception as e:
                st.error(f"Error con Azure Speech: {e}")

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)


