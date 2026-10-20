# Proyecto de Generación de Storyboards con IA

Este repositorio contiene el flujo de trabajo utilizado para transformar historias y guiones generados por Inteligencia Artificial en **storyboards visuales**, utilizando diferentes herramientas especializadas en la generación de imágenes y secuencias.

## 📊 Matriz de Flujo de Trabajo

Las historias base (archivos `.md`) fueron procesadas y aplicadas en las siguientes plataformas de storyboard:

| IA de Texto (Historia) | ➡️ Mapeo ➡️ | IA de Storyboard (Resultado) |
| :--- | :---: | :--- |
| `promt_uno_perplexity.md` | ➡️ | `boords.ia/` |
| `promt_uno_chatGPT.md` | ➡️ | `storyboarder.ia/` |
| `promt_uno_gemini.md` | ➡️ | `Drawstory.ia/` |

> *Nota: Los archivos `promt_uno_claude.md` y la carpeta `LTXstudio` forman parte del material complementario y de pruebas de exploración dentro del directorio.*

## 📂 Estructura del Directorio

A continuación se detalla la organización de los archivos y carpetas del proyecto:

```text
├── boords.ia/              # Resultados del storyboard generado con Boords
├── Drawstory.ia/           # Resultados del storyboard generado con Drawstory
├── LTXstudio/              # Pruebas adicionales en la plataforma LTX Studio
├── storyboarder.ia/        # Resultados del storyboard generado con Storyboarder
│
├── promt_uno_chatGPT.md    # Historia original de ChatGPT
├── promt_uno_claude.md     # Historia original de Claude
├── promt_uno_gemini.md     # Historia original de Gemini
├── promt_uno_perplexity.md # Historia original de Perplexity
│
└── correo_personal_prueba_promt_uno.txt  # Archivo de texto con notas de prueba de correo
```


