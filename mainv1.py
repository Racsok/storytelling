import os
import yaml
import asyncio
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama

# 1. Configuración de los modelos locales (Ollama)
# qwen2.5 es ideal para estructurar (seguir formatos y JSON/Markdown)
llm_estructurador = Ollama(model="qwen2.5")
# llama3.2 es bueno para la escritura creativa y fluida
llm_escritor = Ollama(model="llama3.2")

def cargar_yaml(ruta_archivo):
    """Carga un archivo YAML."""
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        return yaml.safe_load(archivo)

# ---------- Orquestador ----------
async def main():
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
                    "conceptos_clave": [
                        "Redención",
                        "Amor prohibido",
                        "Secretos del pasado",
                        "Lucha de clases"
                        ]
                    },
                "narrador": {
                    "tipo": "Omnisciente en tercera persona",
                    "enfoque": "Focalización variable (permite saltar entre los pensamientos de Santiago, Valeria y las intrigas de Mauro para maximizar el drama)."
                    },
                "contexto": {
                    "espacio": {
                        "nombre": "San Pedro de los Olivos",
                        "descripcion": "Ciudad ficticia latinoamericana que mezcla el caos de una urbe moderna con la tradición de grandes haciendas agrícolas y viñedos en la periferia. Marcado contraste entre barrios populares y zonas residenciales exclusivas."
                        },
                    "tiempo": {
                        "premisa_temporal": "Época actual, desarrollo lineal.",
                        "punto_de_partida": "El día exacto en que el protagonista sale de la cárcel tras cumplir una condena injusta."
                        }
                    },
                "personajes": [
                    {
                        "rol": "Protagonista Masculino",
                        "nombre": "Santiago 'Santi' Mendoza",
                        "personalidad": "Hombre de origen humilde, sumamente trabajador, leal y con un gran talento para la mecánica de autos clásicos. Pasó cinco años en prisión por un crimen que no cometió. Es reservado, de mirada dura pero corazón noble; busca limpiar su nombre y recuperar su vida."
                        },
                    {
                        "rol": "Protagonista Femenina",
                        "nombre": "Valeria del Castillo",
                        "personalidad": "Mujer con un fuerte sentido de la justicia. Hija menor de una familia terrateniente y empresarial muy rica. Estudia derecho y trabaja en una fundación. Es apasionada, decidida, independiente y no se deja intimidar por su entorno privilegiado."
                        },
                    {
                        "rol": "Antagonista Recurrente",
                        "nombre": "Mauricio 'Mauro' de la Vega",
                        "personalidad": "Prometido de Valeria impuesto por la familia. Tipo de clase alta, frío, manipulador y el verdadero responsable del delito por el que culparon a Santiago. Controla negocios turbios bajo una fachada de empresario filántropo."
                        }
                    ],
                "conflicto": {
                    "problematica_principal": "Santiago regresa para recuperar el taller mecánico de su padre, el cual está bajo el control indirecto de la familia de Valeria. El nudo gira en torno al amor prohibido entre ambos, truncado porque el prometido de ella es el hombre que destruyó la vida de Santiago. Valeria tendrá que elegir entre la lealtad familiar o descubrir la oscura verdad."
                    },
                "trama": {
                        "inicio": "Santiago sale de prisión con la meta de recuperar el taller de su padre. En su primer día, rescata a Valeria cuando su auto se queda varado en una zona peligrosa. La atracción es inmediata, pero ambos ignoran la identidad del otro.",
                        "desarrollo": "Santiago descubre que el emporio Del Castillo compró los terrenos de su barrio. Valeria empieza a frecuentar el taller para ayudar legalmente a los vecinos contra el desalojo. Al trabajar juntos, se enamoran profundamente. El conflicto estalla cuando Santiago descubre que el prometido de Valeria es Mauro, su antiguo enemigo.",
                        "climax": "Mauro descubre el romance y organiza una trampa legal para enviar a Santiago de vuelta a prisión, amenazando con destruir el taller. Valeria intercepta los documentos que prueban la inocencia pasada de Santiago y la corrupción de Mauro. En una confrontación bajo la lluvia en la hacienda familiar, se revelan todas las verdades.",
                        "desenlace": "Mauro es arrestado. La familia Del Castillo cede los terrenos a los vecinos. Santiago limpia su nombre, reabre el taller con éxito y Valeria decide forjar su propio camino a su lado, demostrando que el amor venció las barreras sociales."
                        }
                }
            }

    print("Cargando configuraciones YAML...")
    config_agentes = cargar_yaml('config/agentes.yaml')
    config_tareas = cargar_yaml('config/tareas.yaml')

    print("Instanciando Agentes...")
# 3. Crear el Agente Guionista (usando qwen2.5)
    guionista = Agent(
        role=config_agentes['guionista_estructurador']['role'],
        goal=config_agentes['guionista_estructurador']['goal'],
        backstory=config_agentes['guionista_estructurador']['backstory'],
        verbose=True,
        allow_delegation=False,
        llm=llm_estructurador
    )

# 4. Crear el Agente Escritor (usando llama3.2)
    escritor = Agent(
        role=config_agentes['escritor_creativo_capitulos']['role'],
        goal=config_agentes['escritor_creativo_capitulos']['goal'],
        backstory=config_agentes['escritor_creativo_capitulos']['backstory'],
        verbose=True,
        allow_delegation=False,
        llm=llm_escritor
    )

    print("\n--- INICIANDO FASE 1: CREACIÓN DE LA ESCALETA (CAPÍTULO 1) ---")
        
        # 5. Modificamos la tarea para enfocarnos SOLO en el Capítulo 1 y añadir la lógica de revisión manual
        descripcion_tarea_estructurar = config_tareas['estructurar_capitulos_task']['description'] + f"\n\nGenera EXCLUSIVAMENTE la escaleta para el CAPÍTULO 1 basándote en los siguientes metadatos:\n{metadatos}"
        
        tarea_estructurar = Task(
            description=descripcion_tarea_estructurar,
            expected_output=config_tareas['estructurar_capitulos_task']['expected_output'],
            agent=guionista
        )

        # Bucle de iteración (hasta 5 intentos) para la escaleta
        max_intentos = 5
        intento_actual = 1
        escaleta_aprobada = False
        escaleta_resultado = ""

        while intento_actual <= max_intentos and not escaleta_aprobada:
            print(f"\nGenerando escaleta... Intento {intento_actual} de {max_intentos}")
            
            # Ejecutamos solo al guionista para esta tarea
            equipo_escaleta = Crew(
                agents=[guionista],
                tasks=[tarea_estructurar],
                process=Process.sequential
            )
            
            escaleta_resultado = equipo_escaleta.kickoff()
            
            print("\n================ ESCALETA GENERADA ================")
            print(escaleta_resultado)
            print("===================================================")
            
            # Validación Humana (Aquí interactúas tú en la terminal)
            respuesta = input("\n¿La escaleta es decente y está lista para redactar? (s/n): ").strip().lower()
            if respuesta == 's':
                escaleta_aprobada = True
                print("¡Escaleta aprobada! Pasando al escritor...")
            else:
                feedback = input("¿Qué debemos corregir/mejorar para el siguiente intento? (Escribe el feedback): ")
                # Añadimos el feedback a la descripción de la tarea para la siguiente iteración
                tarea_estructurar.description += f"\n\n[FEEDBACK DEL EDITOR PARA EL INTENTO {intento_actual + 1}]: {feedback}. Corrige la escaleta basándote en este feedback."
                intento_actual += 1

        if not escaleta_aprobada:
            print("\nSe alcanzó el máximo de 5 iteraciones. Procediendo con la última versión de la escaleta generada.")

        print("\n--- INICIANDO FASE 2: REDACCIÓN DEL CAPÍTULO 1 ---")
        
        # 6. Tarea para el Escritor, pasándole la escaleta aprobada
        descripcion_tarea_redactar = config_tareas['redactar_capitulo_task']['description'] + f"\n\nBasate estrictamente en esta escaleta aprobada para escribir el texto:\n{escaleta_resultado}"
        
        tarea_redactar = Task(
            description=descripcion_tarea_redactar,
            expected_output=config_tareas['redactar_capitulo_task']['expected_output'],
            agent=escritor
        )

        equipo_redactor = Crew(
            agents=[escritor],
            tasks=[tarea_redactar],
            process=Process.sequential
        )

        capitulo_resultado = equipo_redactor.kickoff()

        # 7. Guardar el resultado final en la carpeta correspondiente
        directorio_salida = Path("salida/pruebas")
        directorio_salida.mkdir(parents=True, exist_ok=True) # Crea las carpetas si no existen
        
        # Puedes generar el nombre dinámicamente o usar uno fijo por ahora
        nombre_archivo = "Capitulo_1_Secretos_de_San_Pedro.md"
        ruta_archivo = directorio_salida / nombre_archivo

        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(capitulo_resultado)

        print(f"\n===================================================")
        print(f"✅ ¡Proceso completado! Capítulo redactado y guardado en: {ruta_archivo}")


if __name__ == "__main__":
    asyncio.run(main())

