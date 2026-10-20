import asyncio
import edge_tts

TEXTO_PRUEBA = """
La penumbra se reflejaba en las celdas de piedra cuando Santiago Mendoza despierta. 
Hace tiempo que el susurro de la cárcel es solo un recuerdo, aunque aún tiemblen sus manos bajo la sábana. 
Coloca una maleta llena de ropa arrugada y papeles viejos a un lado, siente la frescura del alba en su piel.
"""

VOZ = "es-MX-JorgeNeural"  # Voz masculina fluida en español latino
ARCHIVO_SALIDA = "salida/pruebas/prueba_santiago.mp3"

async def generar_audio():
    communicate = edge_tts.Communicate(TEXTO_PRUEBA, VOZ)
    await communicate.save(ARCHIVO_SALIDA)
    print(f"✅ Audio de prueba generado en: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    asyncio.run(generar_audio())
