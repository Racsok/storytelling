#!/usr/bin/env python3
"""
Orquestador mínimo (solo librería estándar de Python).

Flujo (igual que tu PlantUML):
  1. Metadatos -> LLM -> guion en JSON
  2. En paralelo: audio por diálogo + imagen por prompt visual
  3. Validar que todo coincide con el JSON
  4. Dejar los archivos organizados en una carpeta

Uso:
  python orquestador.py --mock      # sin LLM ni APIs, para ver el flujo
  python orquestador.py             # usa Ollama en localhost:11434
"""
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

MOCK = "--mock" in sys.argv
OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen2.5"  # cambia por el que tengas con `ollama list`
SALIDA = Path("salida")

SYSTEM = (
    "Eres guionista. Responde SOLO con JSON válido con esta forma exacta: "
    '{"capitulo": 1, "escenas": [{"id": 1, "personaje": "...", '
    '"dialogo": "...", "prompt_visual": "..."}]}'
)


# ---------- 1. LLM narrativo ----------
def pedir_guion(metadatos: dict) -> dict:
    if MOCK:
        return {
            "capitulo": metadatos["capitulo"],
            "escenas": [
                {"id": 1, "personaje": "Ana", "dialogo": "¿Oíste ese ruido?",
                 "prompt_visual": "pasillo oscuro, una mujer asustada"},
                {"id": 2, "personaje": "Luis", "dialogo": "Es solo el viento.",
                 "prompt_visual": "hombre sereno junto a una ventana"},
            ],
        }
    payload = {
        "model": MODELO,
        "stream": False,
        "format": "json",  # fuerza salida JSON en Ollama
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(metadatos, ensure_ascii=False)},
        ],
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        contenido = json.loads(r.read())["message"]["content"]
    return json.loads(contenido)


def guion_valido(g: dict) -> bool:
    try:
        return all(
            {"id", "personaje", "dialogo", "prompt_visual"} <= e.keys()
            for e in g["escenas"]
        ) and len(g["escenas"]) > 0
    except (KeyError, TypeError, AttributeError):
        return False


def obtener_guion(metadatos: dict, intentos: int = 3) -> dict:
    # El LLM a veces devuelve JSON roto: reintentar es parte del orquestador
    for n in range(1, intentos + 1):
        try:
            g = pedir_guion(metadatos)
            if guion_valido(g):
                return g
            print(f"  guion inválido (intento {n}/{intentos})")
        except (json.JSONDecodeError, OSError) as e:
            print(f"  error del LLM (intento {n}/{intentos}): {e}")
    raise RuntimeError("No se obtuvo un guion válido")


# ---------- 2. Workers (aquí conectas tus herramientas reales) ----------
def generar_audio(escena: dict, carpeta: Path) -> Path:
    destino = carpeta / f"escena_{escena['id']:02d}_{escena['personaje']}.mp3"
    # TODO: llamar a ElevenLabs, o a Piper (TTS local) con escena["dialogo"]
    destino.write_bytes(b"AUDIO-PLACEHOLDER")
    return destino


def generar_imagen(escena: dict, carpeta: Path) -> Path:
    destino = carpeta / f"escena_{escena['id']:02d}.png"
    # TODO: llamar a ComfyUI / Stable Diffusion local con escena["prompt_visual"]
    destino.write_bytes(b"IMAGEN-PLACEHOLDER")
    return destino


async def generar_todo(escenas: list, carpeta: Path) -> list:
    # to_thread permite que las llamadas bloqueantes corran en paralelo
    tareas = []
    for e in escenas:
        tareas.append(asyncio.to_thread(generar_audio, e, carpeta / "audio"))
        tareas.append(asyncio.to_thread(generar_imagen, e, carpeta / "imagenes"))
    return await asyncio.gather(*tareas, return_exceptions=True)


# ---------- 3. Validación ----------
def validar(escenas: list, carpeta: Path) -> list:
    problemas = []
    for e in escenas:
        audios = list((carpeta / "audio").glob(f"escena_{e['id']:02d}_*.mp3"))
        imagen = carpeta / "imagenes" / f"escena_{e['id']:02d}.png"
        if not audios or audios[0].stat().st_size == 0:
            problemas.append(f"falta audio de escena {e['id']}")
        if not imagen.exists() or imagen.stat().st_size == 0:
            problemas.append(f"falta imagen de escena {e['id']}")
    return problemas


# ---------- Orquestador ----------
async def main():
    metadatos = {
        "capitulo": 1,
        "tono": "misterio ligero",
        "personajes": {"Ana": "curiosa, nerviosa", "Luis": "calmado, escéptico"},
    }
    carpeta = SALIDA / f"capitulo_{metadatos['capitulo']:02d}"
    (carpeta / "audio").mkdir(parents=True, exist_ok=True)
    (carpeta / "imagenes").mkdir(parents=True, exist_ok=True)

    print("1/4 Pidiendo guion al LLM...")
    guion = obtener_guion(metadatos)
    (carpeta / "guion.json").write_text(
        json.dumps(guion, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("2/4 Generando audio e imágenes en paralelo...")
    resultados = await generar_todo(guion["escenas"], carpeta)
    for r in resultados:
        if isinstance(r, Exception):
            print(f"  fallo en un worker: {r}")

    print("3/4 Validando...")
    problemas = validar(guion["escenas"], carpeta)

    print("4/4 Resultado")
    if problemas:
        print("  Problemas:", *problemas, sep="\n  - ")
    else:
        print(f"  Todo listo en: {carpeta.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
