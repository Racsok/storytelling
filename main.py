import os
import yaml
import edge_tts
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Usamos qwen2.5 para ambas tareas
llm_estructurador = LLM(model="ollama/qwen2.5", base_url="http://localhost:11434")
llm_escritor = LLM(model="ollama/qwen2.5", base_url="http://localhost:11434")

async def generar_audio_capitulo(texto_limpio: str, ruta_salida_mp3: Path):
    """Genera el archivo .mp3 usando la voz de Edge TTS."""
    voz = "es-MX-JorgeNeural"  # O "es-MX-DaliaNeural" para voz femenina
    communicate = edge_tts.Communicate(texto_limpio, voz)
    await communicate.save(str(ruta_salida_mp3))
    print(f"🎙️ Audio generado exitosamente en: {ruta_salida_mp3}")

def cargar_yaml(ruta_archivo):
    """Carga un archivo YAML."""
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        return yaml.safe_load(archivo)

# ---------- Orquestador Síncrono ----------
def main():
    metadatos = {
        "historia": {
            "titulo_sugerido": "Secretos de San Pedro",
            "formato": {
                "duracion": "Historia corta / Formato Mini-Serie",
                "cantidad_capitulos": "15 a 20 capítulos",
                "promedio_palabras_por_capitulo": 2500
            },
            "tema": {
                "idea_central": "La justicia, la superación y el amor prohibido frente a las diferencias sociales.",
                "conceptos_clave": ["Redención", "Amor prohibido", "Secretos del pasado", "Lucha de clases"]
            },
            "narrador": {
                "tipo": "Omnisciente en tercera persona",
                "enfoque": "Focalización variable para maximizar el drama."
            },
            "contexto": {
                "espacio": {
                    "nombre": "San Pedro de los Olivos",
                    "descripcion": "Ciudad ficticia latinoamericana..."
                },
                "tiempo": {
                    "premisa_temporal": "Época actual, desarrollo lineal.",
                    "punto_de_partida": "El día exacto en que el protagonista sale de la cárcel."
                }
            },
            "personajes": [
                {"rol": "Protagonista Masculino", "nombre": "Santiago 'Santi' Mendoza"},
                {"rol": "Protagonista Femenina", "nombre": "Valeria del Castillo"},
                {"rol": "Antagonista Recurrente", "nombre": "Mauricio 'Mauro' de la Vega"}
            ],
            "conflicto": {
                "problematica_principal": "Santiago regresa para recuperar el taller mecánico de su padre..."
            },
            "trama": {
                "inicio": "Santiago sale de prisión...",
                "desarrollo": "Santiago descubre que el emporio Del Castillo...",
                "climax": "Mauro descubre el romance...",
                "desenlace": "Mauro es arrestado..."
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

    directorio_salida = Path("salida/pruebas")
    directorio_salida.mkdir(parents=True, exist_ok=True)
    
    ruta_md = directorio_salida / "Capitulo_1_Secretos_de_San_Pedro.md"
    ruta_mp3 = directorio_salida / "Capitulo_1_Secretos_de_San_Pedro.mp3"

    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write(capitulo_resultado)

    print(f"\n===================================================")
    print(f"\n✅ Capítulo guardado en texto: {ruta_md}")

    # 8. Generación automática del Audio (.mp3)
    print("🎙️ Convirtiendo capítulo a audio (Edge TTS)...")
    texto_para_leer = limpiar_markdown_para_tts(capitulo_resultado)
    
    # Ejecutamos la función asíncrona de audio
    asyncio.run(generar_audio_capitulo(texto_para_leer, ruta_mp3))

    print(f"\n===================================================")
    print(f"🚀 ¡ENTREGABLE COMPLETO GENERADO!")
    print(f"📄 Texto: {ruta_md}")
    print(f"🎧 Audio: {ruta_mp3}")


if __name__ == "__main__":
    main()
