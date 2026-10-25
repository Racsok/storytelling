import os
import yaml
import edge_tts
import asyncio
import re
import json
import time
import requests
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Usamos qwen2.5 para ambas tareas
llm_estructurador = LLM(model="ollama/qwen2.5", base_url="http://localhost:11434")
llm_escritor = LLM(model="ollama/qwen2.5", base_url="http://localhost:11434")
llm_storyboarder = LLM(model="ollama/qwen2.5", base_url="http://localhost:11434")

async def generar_audio_capitulo(texto_limpio: str, ruta_salida_mp3: Path):
    """Genera el archivo .mp3 usando la voz de Edge TTS."""
    voz = "es-MX-JorgeNeural"  # O "es-MX-DaliaNeural" para voz femenina
    communicate = edge_tts.Communicate(texto_limpio, voz)
    await communicate.save(str(ruta_salida_mp3))
    print(f"🎙️ Audio generado exitosamente en: {ruta_salida_mp3}")

def generar_imagen_pollinations(prompt_escena: str, ruta_salida_imagen: Path, max_reintentos=3):
    """Genera y descarga una imagen usando la API gratuita de Pollinations.ai con reintentos automáticos."""
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
        
        # Espera progresiva antes del siguiente intento
        if intento < max_reintentos:
            tiempo_espera = intento * 5
            print(f"🔄 Reintentando en {tiempo_espera} segundos...")
            time.sleep(tiempo_espera)
            
    print(f"❌ No se pudo descargar esta escena tras {max_reintentos} intentos. Saltando...")
    return False

def cargar_yaml(ruta_archivo):
    """Carga un archivo YAML."""
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        return yaml.safe_load(archivo)

def limpiar_markdown_para_tts(texto: str) -> str:
    """Quita la sintaxis Markdown para que el TTS no lea símbolos."""
    texto = re.sub(r"```.*?```", "", texto, flags=re.DOTALL)
    texto = re.sub(r"`([^`]*)`", r"\1", texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)
    texto = re.sub(r"^\s{0,3}#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"(\*\*|__)(.*?)\1", r"\2", texto)
    texto = re.sub(r"(\*|_)(.*?)\1", r"\2", texto)
    texto = re.sub(r"^\s*>\s?", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*([-*_]\s*){3,}$", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

# ---------- Orquestador Síncrono ----------
def main():
    metadatos = {
        "historia": {
            "titulo_sugerido": "Anectodtas de vieje a la universidad en bicicleta",
            "formato": {
                "duracion": "Historia corta / Formato Mini-series",
                "cantidad_capitulos": "15 a 20 capítulos",
                "promedio_palabras_por_capitulo": 2500
            },
            "tema": {
                "idea_central": "HIstorias/anecdotas que pueden surgir en un viaje en bicicleta",
                "conceptos_clave": ["Recuentos", "Anecdotas divertidas", "cituaciones peligrosas de ir en bicicleta", "Anecdotas de vieje en bicicleta"]
            },
            "narrador": {
                "tipo": "Protagonista en una conversacion",
                "enfoque": "Contar historias interesantes de alguien que monta mucho bicicleta"
            },
            "contexto": {
                "espacio": {
                    "nombre": "Ruta entre la casa y la universidad",
                    "descripcion": "Ciudad urbana, en el camino hay cicloruta, puentes peatonales, lugares que tiene que ir por la calle de carros, lugares que tieneque debe ir caminando"
                },
                "tiempo": {
                    "premisa_temporal": "Época actual, desarrollo lineal.",
                    "punto_de_partida": "Sin punto de partida pues cualquier dia puede surguir una historia"
                }
            },
            "personajes": [
                {"rol": "Protagonista Masculino", "nombre": "Oscar Gacha 'Oscar'"},
            ],
            "conflicto": {
                "problematica_principal": "Situaciones diversas que suceden en el camino de la universidad a la casa, y de la casa a la universidad"
            },
            "trama": {
                "inicio": "Empieza a contar una nueva historia",
                "desarrollo": "Explica el contexto de donde se desarrlla la historia",
                "climax": "Cuenta el porque es una historia digna de mencion",
                "desenlace": "Explica como termina la histroia"
            }
        }
    }

    print("Cargando configuraciones YAML...")
    config_agentes = cargar_yaml('config/agentes.yaml')
    config_tareas = cargar_yaml('config/tareas.yaml')

    print("Instanciando Agentes...")
    guionista = Agent(
        role=config_agentes['guionista_estructurador']['role'],
        goal=config_agentes['guionista_estructurador']['goal'],
        backstory=config_agentes['guionista_estructurador']['backstory'],
        verbose=True,
        allow_delegation=False,
        llm=llm_estructurador
    )

    escritor = Agent(
        role=config_agentes['escritor_creativo_capitulos']['role'],
        goal=config_agentes['escritor_creativo_capitulos']['goal'],
        backstory=config_agentes['escritor_creativo_capitulos']['backstory'],
        verbose=True,
        allow_delegation=False,
        llm=llm_escritor
    )
    
    estoryboarder = Agent(
        role=config_agentes['director_storyboard']['role'],
        goal=config_agentes['director_storyboard']['goal'],
        backstory=config_agentes['director_storyboard']['backstory'],
        verbose=True,
        allow_delegation=False,
        llm=llm_storyboarder
    )

    print("\n--- CONFIGURANDO LAS TAREAS ---")
    
    descripcion_base = config_tareas['estructurar_capitulos_task']['description']
    contexto_tarea = f"\n\nGenera EXCLUSIVAMENTE la escaleta para el CAPÍTULO 1 basándote en los siguientes metadatos:\n{metadatos}"
    
    tarea_estructurar = Task(
        description=descripcion_base + contexto_tarea,
        expected_output=config_tareas['estructurar_capitulos_task']['expected_output'],
        agent=guionista
    )

    equipo_escaleta = Crew(
        agents=[guionista],
        tasks=[tarea_estructurar],
        process=Process.sequential
    )

    max_intentos = 5
    intento_actual = 1
    escaleta_aprobada = False
    escaleta_resultado = ""

    print("\n--- INICIANDO FASE 1: CREACIÓN DE LA ESCALETA (CAPÍTULO 1) ---")
    while intento_actual <= max_intentos and not escaleta_aprobada:
        print(f"\nGenerando escaleta... Intento {intento_actual} de {max_intentos}")
        
        resultado_crew = equipo_escaleta.kickoff()
        escaleta_resultado = resultado_crew.raw
        
        print("\n================ ESCALETA GENERADA ================")
        print(escaleta_resultado)
        print("===================================================")
        
        respuesta = input("\n¿La escaleta es decente y está lista para redactar? (s/n): ").strip().lower()
        if respuesta == 's':
            escaleta_aprobada = True
            print("¡Escaleta aprobada! Pasando al escritor...")
        else:
            feedback = input("¿Qué debemos corregir/mejorar para el siguiente intento?: ")
            intento_actual += 1
            tarea_estructurar.description = f"{descripcion_base}{contexto_tarea}\n\n[FEEDBACK ANTERIOR]: {feedback}. Corrige los errores mencionados."

    if not escaleta_aprobada:
        print("\nSe alcanzó el máximo de iteraciones. Procediendo con la última versión.")

    print("\n--- INICIANDO FASE 2: REDACCIÓN DEL CAPÍTULO 1 ---")
    
    descripcion_redactar = config_tareas['redactar_capitulo_task']['description']
    tarea_redactar = Task(
        description=f"{descripcion_redactar}\n\nBásate strictly en esta escaleta aprobada para escribir el texto:\n{escaleta_resultado}",
        expected_output=config_tareas['redactar_capitulo_task']['expected_output'],
        agent=escritor
    )

    equipo_redactor = Crew(
        agents=[escritor],
        tasks=[tarea_redactar],
        process=Process.sequential
    )

    print("Redactando el capítulo final...")
    capitulo_resultado = equipo_redactor.kickoff().raw

    # FASE 3: GENERACIÓN DEL STORYBOARD
    print("\n--- INICIANDO FASE 3: DISEÑO DEL STORYBOARD ---")
    
    descripcion_storyboard = config_tareas['generar_storyboard_task']['description']
    tarea_storyboard = Task(
        description=f"{descripcion_storyboard}\n\nCapítulo a analizar:\n{capitulo_resultado}",
        expected_output=config_tareas['generar_storyboard_task']['expected_output'],
        agent=estoryboarder
    )

    equipo_storyboarder = Crew(
        agents=[estoryboarder],
        tasks=[tarea_storyboard],
        process=Process.sequential
    )

    print("Generando prompts y desglose de escenas para el storyboard...")
    storyboard_resultado = equipo_storyboarder.kickoff().raw

    # ---------- GUARDADO DE ENTREGABLES ----------
    directorio_salida = Path("salida/pruebas")
    directorio_salida.mkdir(parents=True, exist_ok=True)
    
    # Subcarpeta para las imágenes del capítulo
    directorio_imagenes = directorio_salida / "imagenes_capitulo_1"
    directorio_imagenes.mkdir(parents=True, exist_ok=True)
    
    ruta_md = directorio_salida / "Capitulo_1.md"
    ruta_mp3 = directorio_salida / "Capitulo_1.mp3"
    ruta_json = directorio_salida / "Capitulo_1_storyboard.json"

    with open(ruta_md, 'w', encoding='utf-8') as f:
        f.write(capitulo_resultado)

    with open(ruta_json, 'w', encoding='utf-8') as f:
        f.write(storyboard_resultado)

    print(f"\n===================================================")
    print(f"✅ Capítulo guardado en texto: {ruta_md}")
    print(f"🎬 Storyboard guardado en: {ruta_json}")

    # Generación automática del Audio (.mp3)
    print("🎙️ Convirtiendo capítulo a audio (Edge TTS)...")
    texto_para_leer = limpiar_markdown_para_tts(capitulo_resultado)
    asyncio.run(generar_audio_capitulo(texto_para_leer, ruta_mp3))

    # Generación automática de Imágenes con Pollinations.ai (con reintentos y pausas)
    print("🖼️ Procesando storyboard y descargando imágenes de las escenas...")
    
    try:
        json_limpio = storyboard_resultado.strip()
        if json_limpio.startswith("```json"):
            json_limpio = json_limpio[7:]
        if json_limpio.endswith("```"):
            json_limpio = json_limpio[:-3]
            
        lista_escenas = json.loads(json_limpio.strip())
        
        for i, escena in enumerate(lista_escenas, start=1):
            num_escena = escena.get("numero_escena")
            prompt_img = escena.get("prompt_ingles")
            
            if prompt_img and num_escena:
                ruta_img_salida = directorio_imagenes / f"escena_{num_escena}.jpg"
                generar_imagen_pollinations(prompt_img, ruta_img_salida)
                
                # Pausa entre peticiones para cuidar el servidor gratuito
                if i < len(lista_escenas):
                    print("⏳ Pausa de cortesía de 5 segundos para la siguiente escena...\n")
                    time.sleep(5)
                    
        print(f"\n✨ ¡Todas las imágenes del storyboard fueron procesadas!")
        
    except Exception as e:
        print(f"⚠️ Hubo un error al parsear el JSON del storyboard para las imágenes: {e}")

    print(f"\n===================================================")
    print(f"🚀 ¡ENTREGABLE COMPLETO GENERADO!")
    print(f"📄 Texto: {ruta_md}")
    print(f"🎧 Audio: {ruta_mp3}")
    print(f"🖼️ Storyboard: {ruta_json}")
    print(f"🎨 Carpeta de Imágenes: {directorio_imagenes.resolve()}")

if __name__ == "__main__":
    main()