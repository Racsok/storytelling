import asyncio, edge_tts
from pathlib import Path

texto = Path("salida/pruebas/Capitulo_1.md").read_text(encoding="utf-8")
asyncio.run(edge_tts.Communicate(texto[:300], "es-MX-JorgeNeural").save("test.mp3"))
