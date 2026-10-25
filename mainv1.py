import json
import time
from pathlib import Path
import requests
from urllib.parse import quote

def generar_imagen_pollinations(prompt_escena: str, ruta_salida_imagen: Path, max_reintentos=3):
    """Genera y descarga una imagen con reintentos automáticos si el servidor falla"""
    prompt_codificado = quote(prompt_escena)
    url = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=1280&height=720&nologo=true"
    
    for intento in range(1, max_reintentos + 1):
        try:
            print(f"🎨 [Intento {intento}/{max_reintentos}] Generando: {prompt_escena[:50]}...")
            respuesta = requests.get(url, timeout=60)
            
            if respuesta.status_code == 200:
                with open(ruta_salida_imagen, 'wb') as f:
                    f.write(respuesta.content)
                print(f"✅ ¡Guardada con éxito en: {ruta_salida_imagen}!")
                return True
            else:
                print(f"⚠️ Servidor ocupado (Código HTTP {respuesta.status_code}).")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
        
        # Si falla, esperamos más tiempo antes del siguiente intento (espera exponencial)
        if intento < max_reintentos:
            tiempo_espera = intento * 5  # Intento 1: espera 5s, Intento 2: espera 10s...
            print(f"🔄 El servidor rechazó la petición. Reintentando en {tiempo_espera} segundos...")
            time.sleep(tiempo_espera)
            
    print(f"❌ No se pudo descargar esta escena tras {max_reintentos} intentos. Saltando a la siguiente...")
    return False

def main():
    ruta_json = Path("salida/pruebas/Capitulo_1_storyboard.json")
    directorio_imagenes = Path("salida/pruebas/imagenes_capitulo_1")
    directorio_imagenes.mkdir(parents=True, exist_ok=True)

    if not ruta_json.exists():
        print(f"❌ No se encontró el archivo del storyboard en: {ruta_json}")
        return

    print(f"📂 Leyendo storyboard desde: {ruta_json}")
    with open(ruta_json, 'r', encoding='utf-8') as f:
        contenido_archivo = f.read()

    json_limpio = contenido_archivo.strip()
    if json_limpio.startswith("```json"):
        json_limpio = json_limpio[7:]
    if json_limpio.endswith("```"):
        json_limpio = json_limpio[:-3]

    try:
        lista_escenas = json.loads(json_limpio.strip())
    except json.JSONDecodeError as e:
        print(f"❌ Error al decodificar el JSON del storyboard: {e}")
        return

    print(f"🎬 Se encontraron {len(lista_escenas)} escenas. Iniciando descarga resiliente...")

    for i, escena in enumerate(lista_escenas, start=1):
        num_escena = escena.get("numero_escena")
        prompt_img = escena.get("prompt_ingles")
        
        if prompt_img and num_escena:
            ruta_img_salida = directorio_imagenes / f"escena_{num_escena}.jpg"
            
            # Llamamos a la función con reintentos
            generar_imagen_pollinations(prompt_img, ruta_img_salida)
            
            # Pausa fija entre escenas exitosas para cuidar la cuota del servidor
            if i < len(lista_escenas):
                print("⏳ Pausa de cortesía de 5 segundos para la siguiente escena...\n")
                time.sleep(5)

    print(f"\n===================================================")
    print(f"✨ ¡Proceso de imágenes finalizado!")
    print(f"📁 Revisa tu carpeta de salida: {directorio_imagenes.resolve()}")

if __name__ == "__main__":
    main()