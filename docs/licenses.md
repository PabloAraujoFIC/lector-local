# Motores, modelos y dependencias

Revisión inicial: 5 de octubre de 2026. Las licencias se deben volver a revisar para cada release y voz importada.

| Componente | Fuente | Licencia | Implicación |
|---|---|---|---|
| Código propio | Este repositorio | MIT | Permite uso comercial con aviso de licencia |
| Kokoro-82M pesos/voces | [hexgrad](https://huggingface.co/hexgrad/Kokoro-82M) | Apache-2.0 | Permisiva; conservar licencia/avisos; revisar model card |
| kokoro-onnx | [repositorio](https://github.com/thewh1teagle/kokoro-onnx) | MIT | Adaptador local y exportación ONNX usados |
| ONNX Runtime | [Microsoft](https://github.com/microsoft/onnxruntime) | MIT | Runtime CPU; desactivar eventos de telemetría |
| Piper actual | [OHF-Voice](https://github.com/OHF-Voice/piper1-gpl) | GPL-3.0 | Incluido; conservar avisos y proporcionar fuentes correspondientes |
| Voces Piper | Model card de cada voz | Variable | No se descarga ninguna automáticamente; verificar uso y distribución |
| PyMuPDF / MuPDF | [Artifex](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) | AGPL o comercial | Distribuir de forma compatible con AGPL o adquirir licencia; no anunciar binario cerrado MIT |
| Phonemizer | [repositorio](https://github.com/bootphon/phonemizer) | GPL-3.0 | Dependencia de fonemización; revisar también fork y eSpeak NG |
| eSpeak NG | [repositorio](https://github.com/espeak-ng/espeak-ng) | GPL-3.0+ | Biblioteca y datos locales incluidos por espeakng-loader; avisos/copyleft |
| Readability | [Mozilla](https://github.com/mozilla/readability) | Apache-2.0 | Extracción local de artículos |
| Tauri | [repositorio](https://github.com/tauri-apps/tauri) | MIT / Apache-2.0 | Shell escritorio |
| React | [repositorio](https://github.com/facebook/react) | MIT | Interfaz compartida |

Las dependencias copyleft permiten uso comercial bajo sus términos; **no son equivalentes a licencia permisiva**. El archivo LICENSE cubre solamente el código propio. Antes de distribuir, generar SBOM, incluir los textos de licencia de dependencias/bibliotecas nativas/modelos, conservar avisos y proporcionar el código fuente correspondiente según corresponda. El repositorio no presenta asesoramiento legal ni una auditoría legal completa.

Kokoro se prioriza por licencia del modelo, tamaño y ejecución en CPU. PyMuPDF se adopta por su extracción y OCR; si se busca una distribución permisiva de todo el binario, reemplazar por PDFium/pypdf más OCR independiente y evaluar cómo sustituir la fonemización GPL. Chatterbox y alternativas Coqui no se adoptan en esta versión: requieren evaluación de modelo/licencia/requisitos y comparación real de español; no se les atribuye una licencia comercial genérica.
